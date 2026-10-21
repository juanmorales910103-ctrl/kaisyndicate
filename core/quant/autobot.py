import pandas as pd
from core.quant.dixon_coles import DixonColesEngine
from core.risk.optimizer import PortfolioRiskOptimizer
from core.scrapers.live_betano_scraper import LiveBetanoScraper

class QuantAutobot:
    @staticmethod
    def run_autonomous_scan(treasury_manager, league_name=None, calibrated_model=None):
        scraper = LiveBetanoScraper()
        df = scraper.fetch_live_odds()
        
        if df.empty:
            return pd.DataFrame()

        if not calibrated_model:
            calibrated_model = DixonColesEngine.fit_mle(df)

        alphas = calibrated_model["alphas"]
        betas = calibrated_model["betas"]
        gamma = calibrated_model["gamma"]
        rho = calibrated_model["rho"]

        opportunities = []

        for _, row in df.iterrows():
            h_team = row.get("HomeTeam")
            a_team = row.get("AwayTeam")
            market_odds_home = float(row.get("B365H", 2.0))

            if h_team in alphas and a_team in alphas:
                ah, bh = alphas[h_team], betas[h_team]
                aa, ba = alphas[a_team], betas[a_team]

                probs = DixonColesEngine.predict_match(ah, bh, aa, ba, gamma, rho)
                p_model = probs["1"]

                if p_model > 0 and market_odds_home > 1.0:
                    fair_odds = 1.0 / p_model
                    ev_val = (p_model * market_odds_home) - 1.0

                    if ev_val >= 0.015:
                        stake = PortfolioRiskOptimizer.optimize_multivariate_kelly(
                            [{"p_model": p_model, "odds": market_odds_home}], 
                            treasury_manager.net_worth
                        )[0]

                        opportunities.append({
                            "Partido": f"{h_team} vs {a_team}",
                            "Mercado": "1 (Victoria Local)",
                            "Prob_Modelo": f"{p_model*100:.2f}%",
                            "Cuota_Fair": f"{fair_odds:.2f}",
                            "Cuota_Mercado": market_odds_home,
                            "EV_%": f"{ev_val*100:+.2f}%",
                            "Stake_USD": round(stake, 2),
                            "Raw_EV": ev_val,
                            "Raw_Stake": stake,
                            "Raw_P": p_model,
                            "Raw_Odds": market_odds_home
                        })

        return pd.DataFrame(opportunities)
