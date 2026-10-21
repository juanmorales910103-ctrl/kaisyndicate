import time
import logging
from core.quant.autobot import QuantAutobot
from core.database.treasury import TreasuryManager
from core.database.models import SessionLocal, DBPosition
from core.execution.settlement import ClosedLoopSettlement
from core.execution.live_broker import RealBookmakerBroker
from core.notifications import SystemNotifier

logging.basicConfig(
    filename="logs/kai_daemon.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class InstitutionalDaemon:
    def __init__(self, interval_seconds=120):
        self.interval = interval_seconds
        self.broker = RealBookmakerBroker()

    def run(self):
        logging.info("🛡️ KAI SYNDICATE 100% INSTITUCIONAL: Ciclo autónomo cerrado activo.")
        SystemNotifier.send_alert("KAI SYNDICATE", "Motor 100% Autónomo con Liquidación en Vivo Activo.")

        while True:
            try:
                treasury = TreasuryManager()
                
                # FASE 1: Liquidación de posiciones anteriores
                logging.info("🔄 [1/4] Ejecutando Closed-Loop Settlement (Liquidación Contable)...")
                ClosedLoopSettlement.process_pending_settlements()

                # FASE 2: Control de Riesgo (Circuit Breaker)
                initial_cap = 1000000.0
                drawdown = ((initial_cap - treasury.net_worth) / initial_cap) * 100.0
                if drawdown >= 15.0:
                    logging.critical("🚨 CIRCUIT BREAKER ACTIVADO: Límite de pérdida superado.")
                    time.sleep(self.interval)
                    continue

                # FASE 3: Escaneo de Cuotas en Vivo y Dixon-Coles MLE
                logging.info("🔍 [2/4] Extrayendo cuotas en vivo de Betano y calculando +EV...")
                df_opps = QuantAutobot.run_autonomous_scan(treasury)
                logging.info(f"📊 Oportunidades +EV detectadas: {len(df_opps)}")

                # FASE 4: Ejecución en Betano y Bloqueo Anti-Doble Apuesta
                if not df_opps.empty:
                    session = SessionLocal()
                    try:
                        for _, row in df_opps.iterrows():
                            match_name = row["Partido"]
                            market = row["Mercado"]
                            stake = row["Raw_Stake"]
                            ev = row["Raw_EV"]
                            p_model = row["Raw_P"]
                            odds = row["Raw_Odds"]

                            existing = session.query(DBPosition).filter_by(
                                match_name=match_name,
                                market=market,
                                status="PENDING"
                            ).first()

                            if existing:
                                continue

                            max_stake = treasury.net_worth * 0.03
                            final_stake = min(stake, max_stake)

                            if treasury.available_cash >= final_stake:
                                logging.info(f"⚡ [3/4] Ejecutando orden en Betano: {match_name} | Stake: ${final_stake:,.0f}")
                                exec_success = self.broker.execute_live_order(
                                    "https://www.betano.co", 
                                    match_name, 
                                    market, 
                                    final_stake,
                                    auto_confirm=True
                                )

                                treasury.record_transaction("LOCK_STAKE", final_stake, match_name)
                                db_pos = DBPosition(
                                    match_name=match_name,
                                    league="Betano Live Engine",
                                    market=market,
                                    odds_placed=odds,
                                    odds_fair_model=1.0 / p_model,
                                    expected_value_ev=ev,
                                    stake_usd=final_stake,
                                    status="PENDING" if exec_success else "FAILED"
                                )
                                session.add(db_pos)
                                session.commit()
                                
                                SystemNotifier.send_alert("🎯 ORDEN EJECUTADA", f"Betano: {match_name} | EV: {ev*100:+.2f}%")
                                break
                    finally:
                        session.close()

            except Exception as e:
                logging.error(f"❌ Error crítico en ciclo del Daemon: {e}")

            logging.info(f"⏳ Ciclo completado. Próximo escaneo en {self.interval} segundos...")
            time.sleep(self.interval)

if __name__ == "__main__":
    daemon = InstitutionalDaemon(interval_seconds=120)
    daemon.run()
