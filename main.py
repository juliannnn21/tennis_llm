"""
main.py

Core query pipeline for the ATP Tennis Statistics Assistant.
Orchestrates the full flow from user query to data retrieval:

    1. Intent classification - identifies query type (h2h, surface_performance, etc.)
    2. Entity extraction - extracts player names, surfaces, tournaments from query
    3. Name resolution - resolves player/tournament names to dataset format
    4. Data retrieval - calls appropriate tennis_stats function
    5. Caching - session-level cache by intent-entity key to avoid redundant computation

Handles rate limiting, ambiguous player names and general error handling.
"""

from llm import classify_intent, extract_entities
from tennis_stats import get_h2h, get_surface_performance, get_player_stats, get_on_form_players, get_favourites, get_tournament_performance
from name_matching import find_player, get_unique_players, get_unique_tournaments
import pandas as pd

def handle_query(df, query, unique_players, unique_tournaments, history = [], cache = None):
    
    """
    Orchestrates the full query pipeline from user input to data retrieval.

    Args:
        df: ATP match dataframe
        query: User's natural language query e.g. 'how does Djokovic perform on clay'
        unique_players: Precomputed array of unique player names
        unique_tournaments: Precomputed list of unique tournament names
        history: List of previous conversation messages for context, defaults to []
        cache: Session-level cache dict for intent-entity pairs, defaults to None

    Returns:
        Tuple of (query, result) where:
            - query: Original query string
            - result: Data dict from tennis_stats functions, or error message string

    Raises:
        No exceptions - all errors caught and returned as user-friendly messages
    """

    try:
        if cache is None:
            cache = {}

        # 1) classify intent

        intent = classify_intent(query, history)

        # 2) extract the entities
        if intent == "unknown":
            result = """I can only answer questions about the ATP tour on 
                        head-to-head records, player surface performance, player stats, on-form players, 
                        tournament favourites or player tournament performance."""
            return query, result
        
        # get previous user message for pronoun resolution e.g. "what about him on clay"
        # will either contain last assistant message OR be empty
        if len(history) >= 2: 
            last_message = history[-2]["content"]
        else:
            last_message = None

        entities = extract_entities(query, intent, unique_tournaments, last_message)
        if entities is None:
            result = """I can only answer questions about the ATP tour on 
                head-to-head records, player surface performance, player stats, on-form players, 
                tournament favourites or player tournament performance."""
            return query, result
        #3 ) if entities contain a name then resolve name

        
        for key in entities:
            if key in ["player", "player_1", "player_2"]:
                potential_player = find_player(entities[key], df, unique_players)
                if isinstance(potential_player, list):
                    result = f"Multiple players found, did you mean: {', '.join(potential_player)}?"
                    return query, result
                elif potential_player is None:
                    result = f"Could not find ATP player: {entities[key]}, please try again"
                    return query, result
                else:
                    entities[key] = potential_player

        cache_key = f"{intent}_{str(entities)}"

        # check if intent-entity pair is already in cache
        cached_result = None
        if cache_key in cache:
            cached_result = cache[cache_key]
          
        if cached_result is None:
            if intent == "h2h":
                result = get_h2h(df, entities["player_1"], entities["player_2"])
                if result is not None and len(result) == 0:
                    return query, f"No matches found between {entities['player_1']} and {entities['player_2']} in the dataset."
            elif intent == "surface_performance":
                # surface is either specific/all
                result = get_surface_performance(df, entities["player"], entities["surface"])
            elif intent == "player_stats":
                result = get_player_stats(df, entities["player"])
            elif intent == "on_form_players":
                # surface is either specific/all
                result = get_on_form_players(df, entities["surface"])
                if result is not None and len(result) == 0:
                    return query, f"No players found with sufficient recent matches on {entities['surface']} — this surface may not be in season right now."
            elif intent == "tournament_favourites":
                result = get_favourites(df, entities["tournament"])
            elif intent == "tournament_performance":
                result = get_tournament_performance(df, entities["player"], entities["tournament"])
            else:
                # system error
                result = "An error occurred in classifying intent"

            if result is not None:
                cache[cache_key] = result
        else:
            result = cached_result
        return query, result
    # error messages either due to rate limiting or general error message
    except Exception as e:
        if "rate_limit" in str(e):
            result = "Too many requests - please wait a moment and try again."
        else:
            result = "Something went wrong, please try again."
        return query, result

# for testing pipeline directly without Streamlit
if __name__ == "__main__":
    df = pd.read_csv("data/atp_tennis.csv")
    unique_players = get_unique_players(df)
    unique_tournaments = get_unique_tournaments(df)

    test_queries = [
        "who wins in A.Zverev vs taylor fritz?",
        "how does Novak Djokovic perform on grass",
        "who are the roland garros favourites"
        ]
  
    for q in test_queries:
        query, result = handle_query(df, q, unique_players, unique_tournaments)
        print(f"Q: {q}")
        print(f"Result: {result}\n")
  