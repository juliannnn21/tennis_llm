import pandas as pd
from llm import client

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

        prompt = f"""
        From the query extract the referenced tennis player and return it in form e.g. Novak Djokovic -> Djokovic N.
        Their initial of their first name should be capitalised and come after their last name, followed by a full stop
        If they have middle names the initial of each should be capitalised and come straight after the first name initial,
        and its full stop, and have a full stop of its own, e.g. Struff J.L.
        Their last name should come first, and if consists of multiple words, each should have their first letter capitalised,
        e.g. De Minaur A.
        
        If unable to identify a tennis player only return the word unknown

        The query is: {query}
        """

        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
        )

        player_name = response.choices[0].message.content
        # hallucination prevention
        #print(f"LLM returned {player_name}")
        if player_name in unique_players:
            return player_name
        else:
            return None
        
    elif len(matches) == 1:
        return matches[0]
    # else we have multiple matches
    else:
        
        fil_matches = df[df["Player_1"].isin(matches) | df["Player_2"].isin(matches)]
        match_counts = {}
        for player in matches:
            match_count = len(fil_matches[(fil_matches["Player_1"] == player) | (fil_matches["Player_2"] == player)])
            match_counts[player] = match_count
        sorted_match_counts = sorted(match_counts.values(), reverse=True)
        top_candidate = sorted_match_counts[0]
        second_candidate = sorted_match_counts[1]
        if top_candidate > 5 * second_candidate:
            # find key with highest value from dict
            return max(match_counts, key = match_counts.get)
        else:
            return matches


















        return matches
        













# if run file directly
if __name__ == "__main__":
    df = pd.read_csv("data/atp_tennis.csv")
    print(find_player("kyrgos", df))