from llm import classify_intent, extract_entities
from tennis_stats import get_h2h, get_surface_performance, get_player_stats, get_on_form_players, get_favourites, get_tournament_performance
from name_matching import find_player
import pandas as pd

def handle_query(df, query, history = []):
    
    print(query)
    # 1) classify intent

    intent = classify_intent(query, history)

    print(f"intent: {intent}")
    # 2) extract the entities

    entities = extract_entities(df, query, intent)

    print(f"entities: {entities}")
    if entities is None:
        result = "I couldn't understand your query, please try rephrasing."
        return query, result
    #3 ) if entities contain a name then resolve name

    if entities:
        for key in entities:
            if key in ["player", "player_1", "player_2"]:
                potential_player = find_player(entities[key], df)

                if isinstance(potential_player, list):
                    return query, f"Multiple players found, did you mean: {', '.join(potential_player)}?"
                elif potential_player is None:
                    return query, f"Could not find player: {entities[key]}, please try again"
                else:
                    entities[key] = potential_player

        #print(f"Resolved name: {entities}")

    #4 ) call right function
    #print(df['Tournament'].unique())
    if intent == "h2h":
        result = get_h2h(df, entities["player_1"], entities["player_2"])
    elif intent == "surface_performance":
        # surface is either specific/all
        result = get_surface_performance(df, entities["player"], entities["surface"])
    elif intent == "player_stats":
        result = get_player_stats(df, entities["player"])
    elif intent == "on_form_players":
        # surface is either specific/all
        result = get_on_form_players(df, entities["surface"])
    elif intent == "tournament_favourites":
        # this gets the data
        result = get_favourites(df, entities["tournament"])
    elif intent == "tournament_performance":
        result = get_tournament_performance(df, entities["player"], entities["tournament"])
    elif intent == "unknown":
        result =  """I can only answer questions on the following topics: 
        head to head records, a player's surface performance, player stats, on-form players and tournament favourites."""
    else:
        result = "Something went wrong, please try again."

    print(f"Result: {result}")
    return query, result












# if run file directly, for testing
if __name__ == "__main__":
    df = pd.read_csv("data/atp_tennis.csv")

    q1 = "who wins in A.Zverev vs taylor fritz?"
    q2 = "how does Novak Djokovic perform on grass"
    q3 = "Djokovic statistics"
    q4 = "who is playing well right now?"
    q5 = "who are the wimbledon favourites?"
    q6 = "what time is it?"
    #qs = [q1,q2,q3,q4,q5,q6]

    q7 = "broady vs ruud"
    q8 = "liam broady clay"
    q9 = "liam broady stats"
    q10 = "alcaraz surface"
    q11 = "alcaraz wimbledon"
    q12 = "murray roland garros"
    q13 = "who are the roland garros favourites"
    qs= [q13]
    for q in qs:
        handle_query(df, q)
