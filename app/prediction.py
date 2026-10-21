import math
import numpy as np

class PredictionEngine:
    """Motor 1: Estima probabilidades deportivas mediante Poisson Bivariada y Dixon-Coles."""
    
    @staticmethod
    def poisson_pmf(k: int, lmbda: float) -> float:
        return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

    @classmethod
    def dixon_coles_probabilities(cls, xg_home: float, xg_away: float, rho: float = -0.12) -> dict:
        max_goals = 6
        matrix = np.zeros((max_goals, max_goals))
        for x in range(max_goals):
            for y in range(max_goals):
                p_ind = cls.poisson_pmf(x, xg_home) * cls.poisson_pmf(y, xg_away)
                tau = 1.0
                if x == 0 and y == 0:
                    tau = 1.0 - (xg_home * xg_away * rho)
                elif x == 0 and y == 1:
                    tau = 1.0 + (xg_home * rho)
                elif x == 1 and y == 0:
                    tau = 1.0 + (xg_away * rho)
                elif x == 1 and y == 1:
                    tau = 1.0 - rho
                matrix[x, y] = max(0.0, p_ind * tau)
        matrix /= np.sum(matrix)

        prob_home = np.sum(np.triu(matrix, 1).T)
        prob_draw = np.trace(matrix)
        prob_away = np.sum(np.tril(matrix, -1))
        under_25 = sum(matrix[x, y] for x in range(max_goals) for y in range(max_goals) if x + y < 2.5)
        over_25 = 1.0 - under_25

        return {
            "1": float(prob_home),
            "X": float(prob_draw),
            "2": float(prob_away),
            "Over 2.5": float(over_25),
            "Under 2.5": float(under_25)
        }
