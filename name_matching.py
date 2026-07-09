import pandas as pd
from rapidfuzz import process

CONFIDENCE_LEVEL = 70

def find_player(query, df):
    players_p1 = df[["Player_1"]].rename(columns={"Player_1": "Player"})
    players_p2 = df[["Player_2"]].rename(columns={"Player_2": "Player"})
    combined_players = pd.concat([players_p1, players_p2])
    unique_players = combined_players["Player"].str.strip().unique()

    matches = []
    for player in unique_players:
        if query.lower() in player.lower():
            matches.append(player)
        
    if not matches:
        # returns best match, confidence score, index in the array of the best match
        result = process.extractOne(query, unique_players)
        print(query, result[1])
        if result[1] >= CONFIDENCE_LEVEL:
            return result[0]
        else:
            return None


    elif len(matches) == 1:
        return matches[0]
    else:
        return matches













# if run file directly
if __name__ == "__main__":
    df = pd.read_csv("data/atp_tennis.csv")
    print(find_player("kyrgos", df))
    print(find_player("alkora", df))