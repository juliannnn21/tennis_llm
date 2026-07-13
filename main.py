from llm import classify_intent, extract_entities, format_response
from tennis_stats import get_h2h, get_surface_performance, get_player_stats, get_on_form_players, get_favourites
from name_matching import find_player
import pandas as pd

def handle_query(df, query):
    
    print(query)
    # 1) classify intent

    intent = classify_intent(query)

    #print(f"intent: {intent}")
    # 2) extract the entities

    entities = extract_entities(query, intent)

    #print(f"entities: {entities}")
    #3 ) if entities contain a name then resolve name

    if entities:
        for key in entities:
            if key in ["player", "player_1", "player_2"]:
                potential_player = find_player(entities[key], df)

                if isinstance(potential_player, list):
                    return f"Multiple players found, did you mean: {', '.join(potential_player)}?"
                elif potential_player is None:
                    return f"Could not find player: {entities[key]}, please try again"
                else:
                    entities[key] = potential_player

        #print(f"Resolved name: {entities}")

    #4 ) call right function
    #print(f"intent: {intent}")
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
    elif intent == "unknown":
        result =  """I can only answer questions on the following topics: 
        head to head records, a player's surface performance, player stats, on-form players and tournament favourites."""
        return result
    else:
        result = "Something went wrong, please try again."
        return  result

    #print(f"Result: {result}")
    answer = format_response(query, result)
    return answer













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

    qs= [q7, q8, q9]
    for q in qs:
        print(handle_query(df, q))
