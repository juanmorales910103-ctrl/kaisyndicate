import pandas as pd
import os

class DataIngestor:
    LEAGUES = {
        "Premier League (Inglaterra)": "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
        "La Liga (España)": "https://www.football-data.co.uk/mmz4281/2324/SP1.csv",
        "Serie A (Italia)": "https://www.football-data.co.uk/mmz4281/2324/I1.csv",
        "Bundesliga (Alemania)": "https://www.football-data.co.uk/mmz4281/2324/D1.csv"
    }

    @staticmethod
    def fetch_league(league_name="Premier League (Inglaterra)"):
        os.makedirs("data", exist_ok=True)
        local_path = "data/premier_league_local.csv"
        
        if not os.path.exists(local_path):
            epl_data = {
                "HomeTeam": ["Arsenal", "Manchester City", "Liverpool", "Aston Villa", "Tottenham", "Chelsea", "Newcastle", "Brighton", "Manchester United", "West Ham", "Arsenal", "Liverpool", "Manchester City", "Chelsea", "Tottenham"],
                "AwayTeam": ["Chelsea", "Manchester United", "Everton", "Newcastle", "Brighton", "Arsenal", "Liverpool", "Manchester City", "Brentford", "Fulham", "Aston Villa", "Brighton", "Tottenham", "West Ham", "Manchester United"],
                "FTHG": [3, 2, 1, 4, 2, 0, 1, 2, 2, 1, 2, 3, 4, 1, 2],
                "FTAG": [1, 2, 1, 0, 2, 1, 3, 2, 1, 1, 1, 1, 2, 1, 2],
                "B365H": [1.95, 1.65, 1.55, 2.25, 2.40, 2.80, 2.40, 2.20, 1.95, 2.15, 1.85, 1.60, 1.70, 2.05, 2.35],
                "B365D": [3.60, 4.50, 5.50, 3.50, 3.40, 3.30, 3.40, 3.50, 3.60, 3.40, 4.00, 4.80, 4.20, 3.60, 3.50],
                "B365A": [4.50, 7.00, 9.00, 3.40, 3.00, 2.50, 2.90, 3.10, 4.20, 3.60, 5.50, 7.50, 6.00, 4.00, 3.10]
            }
            pd.DataFrame(epl_data).to_csv(local_path, index=False)

        df = pd.read_csv(local_path)
        df["FTHG"] = df["FTHG"].astype(int)
        df["FTAG"] = df["FTAG"].astype(int)
        return df
