from app.database import SessionLocal, DBLedgerEntry

class TreasuryManager:
    def __init__(self, initial_capital: float = 1000000.0):
        self.initial_capital = initial_capital
        self.sync()

    def sync(self):
        session = SessionLocal()
        try:
            entries = session.query(DBLedgerEntry).all()
            if not entries:
                self.cash = self.initial_capital
                self.net_worth = self.initial_capital
                self.exposure = 0.0
                self._record_internal(session, "DEPOSIT", self.initial_capital, "INIT")
            else:
                latest = entries[-1]
                self.cash = latest.available_cash
                self.net_worth = latest.net_worth
                self.exposure = self.net_worth - self.cash
        finally:
            session.close()

    def _record_internal(self, session, tx_type, amount, pos_id):
        if tx_type == "LOCK_STAKE":
            self.cash -= amount
            self.exposure += amount
        elif tx_type == "WIN_SETTLEMENT":
            self.cash += amount
            self.exposure -= amount
        elif tx_type == "LOSS_SETTLEMENT":
            self.exposure -= amount
        self.net_worth = self.cash + self.exposure
        
        entry = DBLedgerEntry(
            position_id=pos_id,
            transaction_type=tx_type,
            amount=amount,
            available_cash=self.cash,
            net_worth=self.net_worth
        )
        session.add(entry)
        session.commit()

    def record(self, tx_type, amount, pos_id):
        session = SessionLocal()
        try:
            self._record_internal(session, tx_type, amount, pos_id)
            self.sync()
        finally:
            session.close()

class PricingRiskEngine:
    """Motor 2: Valora cuotas, calcula EV, márgenes y dimensiona con Kelly Fraccionado."""
    
    @staticmethod
    def calculate_fair_odds(prob: float) -> float:
        return 1.0 / prob if prob > 0 else 99.0

    @staticmethod
    def evaluate_market(p_model: float, odds_offered: float, min_ev: float = 0.025) -> dict:
        fair_odds = 1.0 / p_model
        ev = (p_model * odds_offered) - 1.0
        implied_prob = 1.0 / odds_offered
        house_margin = implied_prob - p_model

        if ev < min_ev:
            return {
                "decision": "SIN APUESTA (NO_BET)",
                "ev": ev,
                "fair_odds": fair_odds,
                "margin": house_margin,
                "reason": f"EV {ev*100:+.2f}% por debajo del umbral de seguridad institucional ({min_ev*100}%)."
            }
        
        return {
            "decision": "APROBADA (APPROVED)",
            "ev": ev,
            "fair_odds": fair_odds,
            "margin": house_margin,
            "reason": f"Oportunidad con valor positivo verificado (+EV {ev*100:+.2f}%)."
        }

    @staticmethod
    def calculate_kelly_stake(net_worth: float, p_model: float, odds: float, kelly_fraction: float = 0.10, max_cap_pct: float = 0.015) -> float:
        b = odds - 1.0
        q = 1.0 - p_model
        raw_kelly = (b * p_model - q) / b
        safe_kelly = max(0.0, raw_kelly * kelly_fraction)
        max_allowed = net_worth * max_cap_pct
        return min(net_worth * safe_kelly, max_allowed)
