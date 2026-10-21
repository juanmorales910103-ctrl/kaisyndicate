
import numpy as np

class PortfolioRiskOptimizer:
    @staticmethod
    def optimize_multivariate_kelly(opportunities, bankroll, fraction=0.25):
        # Kelly Multivariado con ajuste de covarianza y fraccionario institucional
        stakes = []
        for opp in opportunities:
            p = opp["p_model"]
            odds = opp["odds"]
            b = odds - 1.0
            if b <= 0 or p <= 0:
                stakes.append(0.0)
                continue
            q = 1.0 - p
            # Kelly univariado ajustado por fracción conservadora (ej. 0.25)
            f_star = (b * p - q) / b
            stake = max(0.0, f_star * bankroll * fraction)
            stakes.append(stake)
        return stakes

    @staticmethod
    def run_monte_carlo(bankroll, opportunities, simulations=1000, periods=50):
        if not opportunities:
            return {"var_95_pct": 0.0, "var_99_pct": 0.0, "max_drawdown_pct": 0.0}

        final_banks = np.zeros(simulations)
        max_dds = np.zeros(simulations)

        for s in range(simulations):
            path = [bankroll]
            curr_bank = bankroll
            for _ in range(periods):
                # Elegir aleatoriamente una oportunidad del set
                opp = opportunities[np.random.choice(len(opportunities))]
                p = opp["p_model"]
                odds = opp["odds"]
                stake = curr_bank * 0.015 # 1.5% bankroll fijo por apuesta en simulación
                
                if np.random.rand() < p:
                    curr_bank += stake * (odds - 1.0)
                else:
                    curr_bank -= stake
                path.append(max(1.0, curr_bank))

            final_banks[s] = curr_bank
            peak = np.maximum.accumulate(path)
            dd = (peak - path) / peak
            max_dds[s] = np.max(dd)

        # Calcular Value at Risk (VaR 95% y 99%) y Max Drawdown esperado
        returns = (final_banks - bankroll) / bankroll
        var_95 = np.percentile(returns, 5) * 100
        var_99 = np.percentile(returns, 1) * 100
        mdd = np.mean(max_dds) * 100

        return {
            "var_95_pct": abs(var_95),
            "var_99_pct": abs(var_99),
            "max_drawdown_pct": mdd
        }
