
from difflib import get_close_matches

class TeamNameMatcher:
    @staticmethod
    def find_best_match(team_name, calibrated_teams, cutoff=0.5):
        if not calibrated_teams:
            return team_name
        
        matches = get_close_matches(team_name, calibrated_teams, n=1, cutoff=cutoff)
        if matches:
            return matches[0]
        return team_name
