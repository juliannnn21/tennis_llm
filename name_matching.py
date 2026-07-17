"""
name_matching.py

Resolves player and tournament names from user queries to dataset format.

Player name resolution uses a 3-tier approach:
    1. Contains search - fast exact substring matching
    2. LLM formatting - semantic understanding for full names, nicknames, misspellings
    3. Fuzzy matching - safety net for minor LLM formatting errors

Tournament name resolution uses fuzzy matching against known tournament names,
handling aliases (e.g. Roland Garros -> French Open) and case insensitivity.
"""

import pandas as pd
from llm_client import safe_llm_call
from rapidfuzz import process

def get_unique_players(df):

    """Returns array of unique player names from both Player_1 and Player_2 columns, stripped of whitespace."""

    players_p1 = df[["Player_1"]].rename(columns={"Player_1": "Player"})
    players_p2 = df[["Player_2"]].rename(columns={"Player_2": "Player"})
    combined_players = pd.concat([players_p1, players_p2])
    unique_players = combined_players["Player"].str.strip().unique()
    return unique_players

def get_unique_tournaments(df):

    """Returns list of unique tournament names from the dataset."""

    unique_tournaments = df['Tournament'].unique().tolist()
    return unique_tournaments


def find_player(query, df, unique_players):

    """
    Resolves a player name query to the correct dataset format using a 3-tier approach:
    1. Contains search - checks if query appears in any player name
    2. LLM formatting - uses LLM to format name correctly if no contains match
    3. Fuzzy matching - safety net for minor LLM formatting errors

    Args:
        query: Player name as typed by user e.g. 'Djokovic', 'Novak Djokovic', 'djokovick'
        df: ATP match dataframe
        unique_players: Precomputed array of unique player names from get_unique_players()

    Returns:
        Single player name string in dataset format e.g. 'Djokovic N.'
        List of player names if ambiguous e.g. ['Zverev A.', 'Zverev M.']
        None if player not found or not an ATP men's player
    """
    matches = []
    
    # tier 1: contains search
    for player in unique_players:
        if query.lower() in player.lower():
            matches.append(player)
    
    # tier 2: LLM formatting fallback
    if not matches:
        prompt = f"""
        From the query extract the referenced MEN'S ATP tennis player ONLY and return it in form e.g. Novak Djokovic -> Djokovic N.
        Their initial of their first name should be capitalised and come after their last name, followed by a full stop
        If they have middle names the initial of each should be capitalised and come straight after the first name initial,
        and its full stop, and have a full stop of its own, e.g. Struff J.L.
        Their last name should come first, and if consists of multiple words, each should have their first letter capitalised,
        e.g. De Minaur A.
        
        If the player isn't ATP men's e.g. WTA or unable to identify a tennis player only return the word unknown

        The query is: {query}
        """

        messages = [{"role": "user", "content": prompt}]
        response = safe_llm_call(messages, False)
 
        player_name = response.choices[0].message.content

        # tier 3: fuzzy safety net for minor LLM formatting errors

        if player_name == "unknown":
            return None
        elif player_name in unique_players:
            return player_name
        else:
            if len(unique_players) == 0:
                return None
            best_match, score, _ = process.extractOne(player_name, unique_players)
            if score >= 90:
                return best_match
            else:
                return None
 
    # beyond here we HAVE a match
    # if we get exactly 1 match without llm just return it
    elif len(matches) == 1:
        return matches[0]
    # else we have multiple matches
    else:
        # either return a single match/multiple if games played cannot break the tie
        fil_matches = df[df["Player_1"].isin(matches) | df["Player_2"].isin(matches)]
        match_counts = {}
        for player in matches:
            match_count = len(fil_matches[(fil_matches["Player_1"] == player) | (fil_matches["Player_2"] == player)])
            match_counts[player] = match_count
        sorted_match_counts = sorted(match_counts.values(), reverse=True)

        if len(sorted_match_counts) < 2:
            return matches[0]
        top_candidate = sorted_match_counts[0]
        second_candidate = sorted_match_counts[1]
        # auto-select most popular player if they have 5x more matches than second most popular
        if top_candidate > 5 * second_candidate:
            # find key with highest value from dict
            return max(match_counts, key = match_counts.get)
        else:
            return matches
        
def match_tournament(tournament, unique_tournaments):

    """
    Fuzzy matches a tournament name to the closest match in the dataset.

    Args:
        tournament: Tournament name as extracted by LLM e.g. 'Roland Garros', 'wimbledon'
        unique_tournaments: List of valid tournament names from get_unique_tournaments()

    Returns:
        Matched tournament name in dataset format e.g. 'French Open'
        None if no match found above 70% similarity threshold
    """
    if len(unique_tournaments) == 0:
        return None
    best_match, score, _ = process.extractOne(tournament, unique_tournaments)
    if score >= 70:
        return best_match
    else:
        return None


















        













