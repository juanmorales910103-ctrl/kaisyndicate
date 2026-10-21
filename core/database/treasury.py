from core.database.models import SessionLocal, DBPosition
import logging

class TreasuryManager:
    def __init__(self):
        self.net_worth = 1000000.0  # Capital inicial base en COP
        self.available_cash = 10000.0
        self._calculate_treasury()

    def _calculate_treasury(self):
        session = SessionLocal()
        try:
            pending = session.query(DBPosition).filter_by(status="PENDING").all()
            self.locked_cash = sum([p.stake_usd for p in pending])
            # Efectivo disponible restando lo bloqueado
            self.available_cash = max(0.0, self.net_worth - self.locked_cash)
        except Exception as e:
            logging.error(f"Error calculando tesorería: {e}")
            self.locked_cash = 0.0
        finally:
            session.close()

    def record_transaction(self, t_type, amount, description):
        session = SessionLocal()
        try:
            if t_type == "SETTLEMENT_WIN":
                self.net_worth += amount
            elif t_type == "STAKE_PLACED":
                self.net_worth -= amount
            session.commit()
            self._calculate_treasury()
        except Exception as e:
            logging.error(f"Error registrando transacción: {e}")
        finally:
            session.close()
