import logging
from playwright.sync_api import sync_playwright
from core.database.models import SessionLocal, DBPosition
from core.database.treasury import TreasuryManager
import os

class ClosedLoopSettlement:
    @staticmethod
    def process_pending_settlements():
        """
        Verifica en tiempo real en Betano si los partidos pendientes han finalizado,
        contrastando el marcador oficial y liquidando la tesorería de forma autónoma.
        """
        session = SessionLocal()
        treasury = TreasuryManager()
        
        try:
            pending_positions = session.query(DBPosition).filter_by(status="PENDING").all()
            if not pending_positions:
                return

            logging.info("🔍 [SETTLEMENT REAL] Verificando resultados oficiales en Betano...")
            
            with sync_playwright() as p:
                context = p.chromium.launch_persistent_context(
                    os.path.abspath("./user_session"),
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://www.betano.co/myaccount/history/sportsbook/", timeout=60000, wait_until="domcontentloaded")
                import time
                time.sleep(5)

                for pos in pending_positions:
                    # Buscar el estado de la apuesta en el historial de Betano
                    try:
                        history_text = page.locator("body").inner_text()
                        if pos.match_name in history_text:
                            if "Ganada" in history_text or "Won" in history_text:
                                pos.status = "WON"
                                payout = pos.stake_usd * pos.odds_placed
                                treasury.record_transaction("SETTLEMENT_WIN", payout, f"Ganado: {pos.match_name}")
                                logging.info(f"🏆 [SETTLEMENT REAL] ¡Apuesta GANADA en Betano! Pago acreditado: ${payout:,.0f} COP")
                                session.commit()
                            elif "Perdida" in history_text or "Lost" in history_text:
                                pos.status = "LOST"
                                logging.info(f"❌ [SETTLEMENT REAL] Apuesta perdida en Betano para: {pos.match_name}")
                                session.commit()
                    except Exception as ex:
                        logging.error(f"Error verificando apuesta {pos.match_name}: {ex}")

                context.close()
        except Exception as e:
            logging.error(f"❌ Error crítico en ClosedLoopSettlement real: {e}")
        finally:
            session.close()
