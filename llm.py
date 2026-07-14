from llm_client import client
from name_matching import match_tournament

def classify_intent(query, history = []):
    intent_descriptions = {
    "h2h": "general head to head record between two players only across all tournaments",
    "surface_performance": "how a player performs on a specific surface or all surfaces",
    "player_stats": "overall win rate, win rates on each surface, win rate vs higher/lower ranked opponents, best tournament, recent form",
    "on_form_players": "which players are currently in form, best performing players recently, either for all surfaces/specific one",
    "tournament_favourites": "who is likely to win an upcoming tournament",
    "tournament_performance": "how a specific player has performed at a specific tournament",
    "unknown": "questions about rankings, grand slam titles, prize money, coaching, playing style, or anything not covered by the other intents"
    }   
    prompt = f"""
    Classify this query into one of the following intents using their intent descriptions, returning ONLY the intent category name:
    intent descriptions: {intent_descriptions}
    
    The query is: {query}
    """
    messages = []
    for message in history:
        messages.append({"role": message["role"], "content": message["content"]})
    
    messages.append({"role": "user", "content": prompt})


    # user here means the user's message 

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=messages
 
    )

    intent = response.choices[0].message.content

    return intent

def classify_intent_batch(queries):

    intent_descriptions = {
    "h2h": "general head to head record between two players only across all tournaments",
    "surface_performance": "how a player performs on a specific surface or all surfaces",
    "player_stats": "overall win rate, win rates on each surface, win rate vs higher/lower ranked opponents, best tournament, recent form",
    "on_form_players": "which players are currently in form, best performing players recently, either for all surfaces/specific one",
    "tournament_favourites": "who is likely to win an upcoming tournament",
    "tournament_performance": "how a specific player has performed at a specific tournament",
    "unknown": "questions about rankings, grand slam titles, prize money, coaching, playing style, or anything not covered by the other intents"
    }   

    numbered_queries = ""
    for i, query in enumerate(queries):
        numbered_queries += f"\n{i+1}. {query}"

    prompt = f"""Classify these queries into one of the following intents using their intent descriptions, returning 
    ONLY a numbered list intent category names in the same order e.g:
    1. h2h
    2. unknown
    intent descriptions: {intent_descriptions}

    Queries: {numbered_queries}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    
    # split output string by line to get lines
    lines = response.choices[0].message.content.strip().split("\n")
    intents = []
    for line in lines:
        if line.strip():
            intents.append(line.split(". ", 1)[1].strip())
    
    return intents























def extract_entities(df, query, intent):
    """
    messages = []
    for message in history:
        messages.append({"role": message["role"], "content": message["content"]})
    """
    if intent == "h2h":

        prompt = f"""
        From the query extract the 2 players in the head-to-head question, and return ONLY them in the form: 
        player_1,player_2 
        Do not add any explanation.
        If unable to do this return the word unknown

        The query is: {query}
        """
       # messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": prompt}]
        )

        players = response.choices[0].message.content
        if players == "unknown":
            return None
        player1, player2 = players.split(",", 1)
        players_dict = {"player_1": player1.strip(), "player_2": player2.strip()}
        return players_dict
    
    elif intent == "surface_performance":

        prompt = f"""
        From the query extract the player and the surface, and return them ONLY in the form: 
        player,surface 
        Do not add any explanation
        If no surface mentioned or all surfaces mentioned return: player,all
        If unable to identify player then return the word unknown

        The query is: {query}
        """
     #   messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": prompt}]
        )

        surface_data = response.choices[0].message.content
        if surface_data == "unknown":
            return None
        #print(surface_data)
        player, surface = surface_data.split(",", 1)
        surface = surface.capitalize()
        surface_dict = {"player": player.strip(), "surface": surface.strip()}
        return surface_dict
    
    elif intent == "player_stats":

        prompt = f"""
        From the query extract player name and return ONLY in the form:
        player_name
        Without adding any explanation
        If unable to identify player then return the word unknown

        The query is: {query}
        """
      #  messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": prompt}]
        )

        player = response.choices[0].message.content
        if player == "unknown":
            return None
        stats_dict = {"player": player.strip()}
        return stats_dict

    elif intent == "on_form_players":

        prompt = f"""
        From the query extract the surface if given and return the surface name ONLY in the form:
        surface_name
        Without adding any explanation
        If no surface mentioned or all surfaces mentioned return the word all
        

        The query is: {query}
        """
       # messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": prompt}]
        )

        surface = response.choices[0].message.content
        surface = surface.capitalize()
        on_form_dict = {"surface": surface.strip()}
        return on_form_dict

    elif intent == "tournament_favourites":

        unique_tournaments = df['Tournament'].unique().tolist()

        prompt = f"""
        From the query match the tournament name EXACTLY to the closest one from this list:
        {unique_tournaments} 
        Return ONLY the matched tournament name in the form:
        tournament_name
        Without adding any explanation
        If unable to identify tournament then return the word unknown

        The query is: {query}
        """
     #   messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": prompt}]
        )

        tournament_name = response.choices[0].message.content

        # fuzzy match it as a safety fallback

        tournament_name_match = match_tournament(tournament_name, unique_tournaments)

        if tournament_name_match is None:
            return None
        tournament_favourites_dict = {"tournament": tournament_name_match}
        return tournament_favourites_dict


    elif intent == "tournament_performance":

        unique_tournaments = df['Tournament'].unique().tolist()

        prompt = f"""
        From the query extract the player and match the tournament name EXACTLY to the closest one from this list:
        {unique_tournaments} 
        Return them ONLY in the form:
        player,tournament_name
        Without adding any explanation
        If unable to identify the player or tournament then return the word unknown

        The query is: {query}
        """
     #   messages.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages = [{"role": "user", "content": prompt}]
        )

        player_tournament_data = response.choices[0].message.content
        if player_tournament_data == "unknown":
            return None

        player, tournament_name = player_tournament_data.split(",", 1)
        
        tournament_name_match = match_tournament(tournament_name, unique_tournaments)

        if tournament_name_match is None:
            return None

        player_tournament_dict = {"player": player.strip(), "tournament": tournament_name_match}
        return player_tournament_dict



    else:
        return None

# original query (question) so actually answers the question asked, use result (data) and chat history to make a response
# format response should technically always have history
def format_response(query, result, history):

    print(f"RECEIVED: {query}, {result}")
    # prompt = ORIGINAL QUERY + DATA
    prompt = f"""
    Based on the original query generate a natural conversation respons using the data below.
    Be concise, use all provided data, and don't use any data not provided.
    For player names ensure to you their full name
    If the query is about tournament favourites emphasise who is the number one favourite.
    If the result received is not data and instead a default message as original query was not classified,
    ensure to mention you can only help for men's ATP tour only and the topics the default message includes.
    If you receive the message that something went wrong, only output that message.

    The original query is: {query}
    The data is: {result}
    """

    # make message list including previous history and new question asked
    messages = []
    for message in history:
        messages.append({"role": message["role"], "content": message["content"]})
    
    messages.append({"role": "user", "content": prompt})

    # we give LLM a chat history: old prompts without data, and latest prompt WITH data (old data is engrained into old responses)
    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=messages,
    stream = True
    )

    # loop through each data chunk
    # if it contains text extract text and send to caller
    # delta means new data added in this chunk
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content






    