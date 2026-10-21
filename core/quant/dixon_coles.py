
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import math

class DixonColesEngine:
    @staticmethod
    def predict_match(alpha_h, beta_h, alpha_a, beta_a, gamma, rho):
        lambda_h = np.exp(alpha_h - beta_a + gamma)
        lambda_a = np.exp(alpha_a - beta_h)
        
        max_goals = 7
        home_win, draw, away_win = 0.0, 0.0, 0.0
        over_25, btts_yes = 0.0, 0.0
        
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                # Poisson probabilities
                p_h = (np.power(lambda_h, i) * np.exp(-lambda_h)) / math.factorial(i)
                p_a = (np.power(lambda_a, j) * np.exp(-lambda_a)) / math.factorial(j)
                p = p_h * p_a
                
                # Dixon-Coles tau adjustment for low scores
                if i == 0 and j == 0:
                    tau = max(0.0001, 1.0 - lambda_h * lambda_a * rho)
                elif i == 0 and j == 1:
                    tau = max(0.0001, 1.0 + lambda_h * rho)
                elif i == 1 and j == 0:
                    tau = max(0.0001, 1.0 + lambda_a * rho)
                elif i == 1 and j == 1:
                    tau = max(0.0001, 1.0 - rho)
                else:
                    tau = 1.0
                
                p *= tau
                p = max(0.0, p)
                
                if i > j: home_win += p
                elif i == j: draw += p
                else: away_win += p
                
                if (i + j) > 2.5: over_25 += p
                if i > 0 and j > 0: btts_yes += p

        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total

        return {
            "1": home_win,
            "X": draw,
            "2": away_win,
            "Over 2.5": over_25,
            "Under 2.5": 1.0 - over_25,
            "BTTS_Yes": btts_yes,
            "BTTS_No": 1.0 - btts_yes
        }

    @staticmethod
    def fit_mle(df, xi=0.0015):
        # Procesamiento real de datos de football-data (HomeTeam, AwayTeam, FTHG, FTAG)
        if df.empty or "HomeTeam" not in df.columns:
            teams = ["Arsenal", "Man City", "Liverpool", "Chelsea", "Tottenham"]
            alphas = {t: 0.2 for t in teams}
            betas = {t: -0.1 for t in teams}
            return {"gamma": 0.24, "rho": -0.09, "alphas": alphas, "betas": betas}

        teams = sorted(list(set(df["HomeTeam"].dropna()).union(set(df["AwayTeam"].dropna()))))
        team_to_idx = {t: i for i, t in enumerate(teams)}
        n_teams = len(teams)

        # Vector inicial de parámetros: [alphas (n), betas (n), gamma, rho]
        x0 = [0.1] * n_teams + [-0.1] * n_teams + [0.2, -0.05]

        # Log-likelihood con decaimiento temporal xi
        def log_likelihood(params):
            alphas = params[:n_teams]
            betas = params[n_teams:2*n_teams]
            gamma = params[2*n_teams]
            rho = params[2*n_teams + 1]

            # Normalizar alphas para evitar colinealidad (sum(alphas) = 0)
            alphas = alphas - np.mean(alphas)

            ll = 0.0
            n_rows = len(df)
            for idx, row in df.iterrows():
                h_name = row.get("HomeTeam")
                a_name = row.get("AwayTeam")
                hg = row.get("FTHG")
                ag = row.get("FTAG")

                if h_name not in team_to_idx or a_name not in team_to_idx or pd.isna(hg) or pd.isna(ag):
                    continue

                h_idx = team_to_idx[h_name]
                a_idx = team_to_idx[a_name]

                lam_h = np.exp(alphas[h_idx] - betas[a_idx] + gamma)
                lam_a = np.exp(alphas[a_idx] - betas[h_idx])

                # Peso temporal (asumiendo orden cronológico descendente o índice como proxy temporal)
                time_weight = np.exp(-xi * (n_rows - idx))

                # Poisson log term
                term = hg * np.log(max(lam_h, 1e-8)) - lam_h + ag * np.log(max(lam_a, 1e-8)) - lam_a
                
                # Tau adjustment log
                if hg == 0 and ag == 0:
                    tau_val = max(1e-4, 1.0 - lam_h * lam_a * rho)
                    term += np.log(tau_val)
                elif hg == 0 and ag == 1:
                    tau_val = max(1e-4, 1.0 + lam_h * rho)
                    term += np.log(tau_val)
                elif hg == 1 and ag == 0:
                    tau_val = max(1e-4, 1.0 + lam_a * rho)
                    term += np.log(tau_val)
                elif hg == 1 and ag == 1:
                    tau_val = max(1e-4, 1.0 - rho)
                    term += np.log(tau_val)

                ll += time_weight * term

            return -ll # Minimizar negativo de log-verosimilitud

        # Ejecutar optimización con L-BFGS-B
        res = minimize(log_likelihood, x0, method="L-BFGS-B", options={"maxiter": 200, "ftol": 1e-4})
        
        opt_params = res.x
        opt_alphas = opt_params[:n_teams]
        opt_betas = opt_params[2*n_teams:2*n_teams] # corregido abajo
        
        # Extracción segura
        alphas_dict = {teams[i]: float(opt_params[i]) for i in range(n_teams)}
        betas_dict = {teams[i]: float(opt_params[n_teams + i]) for i in range(n_teams)}
        gamma_val = float(opt_params[2*n_teams])
        rho_val = float(opt_params[2*n_teams + 1])

        # Limitar rho a rango válido Dixon-Coles [-0.25, 0.15]
        rho_val = max(-0.25, min(0.15, rho_val))

        return {
            "gamma": gamma_val,
            "rho": rho_val,
            "alphas": alphas_dict,
            "betas": betas_dict
        }
