"""
llm.py

LLM-powered functions for the ATP Tennis Statistics Assistant pipeline.

Contains three core components:
    - Intent classification: determines query type (h2h, surface_performance, etc.)
      using Llama 3.3 70B via Groq API with conversation history for context
    - Entity extraction: extracts relevant entities (players, surfaces, tournaments)
      from user queries, using last message context for pronoun resolution
    - Response formatting: converts raw data dictionaries into natural language
      responses using streaming for real-time output

Also includes classify_intent_batch() for efficient bulk evaluation testing.
"""

from llm_client import safe_llm_call
from name_matching import match_tournament

def classify_intent(query, history = []):

    """
    Classifies a user query into one of 7 intents using the LLM.

    Args:
        query: User's natural language query
        history: List of previous conversation messages for context, defaults to []

    Returns:
        Intent string, one of: 'h2h', 'surface_performance', 'player_stats',
        'on_form_players', 'tournament_favourites', 'tournament_performance', 'unknown'
    """

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
    response = safe_llm_call(messages, False)
    intent = response.choices[0].message.content

    return intent

def classify_intent_batch(queries):

    """
    Classifies multiple queries in a single API call for evaluation efficiency.
    Used by the evaluation framework instead of calling classify_intent() per query.

    Args:
        queries: List of query strings to classify

    Returns:
        List of intent strings in the same order as input queries
        e.g. ['h2h', 'surface_performance', 'unknown']
    """

    intent_descriptions = {
    "h2h": "general head to head record between two players only across all tournaments",
    "surface_performance": "how a player performs on a specific surface or all surfaces",
    "player_stats": "overall win rate, win rates on each surface, win rate vs higher/lower ranked opponents, best tournament, recent form",
    "on_form_players": "which players are currently in form, best performing players recently, either for all surfaces/specific one",
    "tournament_favourites": "who is likely to win an upcoming tournament",
    "tournament_performance": "how a specific player has performed at a specific tournament",
    "unknown": "questions about rankings, grand slam titles, prize money, coaching, playing style, or anything not covered by the other intents"
    }   

    # number queries for positional matching in response
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

    messages=[{"role": "user", "content": prompt}]
    response = safe_llm_call(messages, False)

    # parse numbered response into list, stripping "1. " prefixes
    lines = response.choices[0].message.content.strip().split("\n")
    intents = []
    for line in lines:
        if line.strip():
            intents.append(line.split(". ", 1)[1].strip())
    
    # fallback to individual classification if batch response is malformed
    if len(intents) != len(queries):
        return [classify_intent(q) for q in queries]

    return intents

def extract_entities(query, intent, unique_tournaments, last_message = None):

    """
    Extracts relevant entities from a user query based on the classified intent.
    Uses last message for pronoun resolution e.g. 'him' -> player from previous query.

    Args:
        query: User's natural language query
        intent: Classified intent string e.g. 'h2h', 'surface_performance'
        unique_tournaments: Precomputed list of valid tournament names for matching
        last_message: Previous user message for pronoun context, defaults to None

    Returns:
        Dict of extracted entities, structure depends on intent:
            - h2h: {'player_1': str, 'player_2': str}
            - surface_performance: {'player': str, 'surface': str}
            - player_stats: {'player': str}
            - on_form_players: {'surface': str}
            - tournament_favourites: {'tournament': str}
            - tournament_performance: {'player': str, 'tournament': str}
        None if entities cannot be extracted or intent not recognised
    """

    if intent == "h2h":
        prompt = f"""
        From the query extract the 2 players in the head-to-head question, and return ONLY them in the form: 
        player_1,player_2 
        Do not add any explanation.
        Use last message ONLY FOR identifying the player names if not in query
        If unable to do this return the word unknown

        query: {query}
        last message: {last_message}
        """

        messages = [{"role": "user", "content": prompt}]
        response = safe_llm_call(messages, False)
        players = response.choices[0].message.content
        if players == "unknown":
            return None
        parts = players.split(",", 1)
        if len(parts) != 2:
            return None
        player1, player2 = parts
        players_dict = {"player_1": player1.strip(), "player_2": player2.strip()}
        return players_dict
    
    elif intent == "surface_performance":
        prompt = f"""
        From the query extract the player and the surface, and return them ONLY in the form: 
        player,surface 
        Do not add any explanation
        If no surface mentioned or all surfaces mentioned return: player,all
        Use last message ONLY FOR identifying the player name or surface if not in query
        If unable to identify player then return the word unknown

        query: {query}
        last message: {last_message}
        """

        messages = [{"role": "user", "content": prompt}]
        response = safe_llm_call(messages, False)
        surface_data = response.choices[0].message.content
        if surface_data == "unknown":
            return None
        parts = surface_data.split(",", 1)
        if len(parts) != 2:
            return None
        player, surface = parts
        # capitalize surface to match dataset format e.g. 'clay' -> 'Clay'
        surface = surface.capitalize()
        surface_dict = {"player": player.strip(), "surface": surface.strip()}
        return surface_dict
    
    elif intent == "player_stats":
        prompt = f"""
        From the query extract player name and return ONLY in the form:
        player_name
        Without adding any explanation
        Use last message ONLY FOR identifying the player name if it is not in query
        If unable to identify player then return the word unknown

        query: {query}
        last message: {last_message}
        """

        messages = [{"role": "user", "content": prompt}]
        response = safe_llm_call(messages, False)
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
        Use last message ONLY FOR identifying the OPTIONAL surface if it is not in query
        If no surface mentioned or all surfaces mentioned return the word all
        
        query: {query}
        last message: {last_message}
        """
        messages = [{"role": "user", "content": prompt}]
        response = safe_llm_call(messages, False)
        surface = response.choices[0].message.content
        surface = surface.capitalize()
        on_form_dict = {"surface": surface.strip()}
        return on_form_dict

    elif intent == "tournament_favourites":

        prompt = f"""
        From the query match the tournament name EXACTLY to the closest one from this list:
        {unique_tournaments} 
        Return ONLY the matched tournament name in the form:
        tournament_name
        Without adding any explanation
        Use last message ONLY FOR identifying the tournament name if it is not in query
        If unable to identify tournament then return the word unknown

        query: {query}
        last message: {last_message}
        """
        messages = [{"role": "user", "content": prompt}]
        response = safe_llm_call(messages, False)
        tournament_name = response.choices[0].message.content
        # fuzzy match it as a safety fallback
        tournament_name_match = match_tournament(tournament_name, unique_tournaments)
        if tournament_name_match is None:
            return None
        tournament_favourites_dict = {"tournament": tournament_name_match}
        return tournament_favourites_dict

    elif intent == "tournament_performance":

        prompt = f"""
        From the query extract the player and match the tournament name EXACTLY to the closest one from this list:
        {unique_tournaments} 
        Return them ONLY in the form:
        player,tournament_name
        Without adding any explanation
        Use last message ONLY FOR identifying the player and tournament name if not in query
        If unable to identify the player or tournament then return the word unknown

        query: {query}
        last message: {last_message}
        """
        messages = [{"role": "user", "content": prompt}]
        response = safe_llm_call(messages, False)
        player_tournament_data = response.choices[0].message.content
        if player_tournament_data == "unknown":
            return None
        parts = player_tournament_data.split(",", 1)
        if len(parts) != 2:
            return None
        player, tournament_name = parts
        tournament_name_match = match_tournament(tournament_name, unique_tournaments)
        if tournament_name_match is None:
            return None
        player_tournament_dict = {"player": player.strip(), "tournament": tournament_name_match}
        return player_tournament_dict
    
    else:
        return None


def format_response(query, result, history):

    """
    Formats raw data into a natural language response using streaming.

    Args:
        query: Original user query for context
        result: Raw data dict from tennis_stats functions, or error message string
        history: List of previous conversation messages for context

    Yields:
        String chunks of the response as they are generated by the LLM
        Use with st.write_stream() in Streamlit for real-time streaming output
    """
    prompt = f"""
    Based on the original query generate a natural conversational response using JUST the data below, DO NOT
    question the data.
    Format names NATURALLY e.g. Sinner J. -> Jannik Sinner

    If receive message NOT data, output ONLY that EXACT message EVERY TIME, even if same question is asked multiple times
    
    The original query is: {query}
    The data is: {result}
    """

    # make message list including previous history and new question asked
    messages = []
    for message in history:
        messages.append({"role": message["role"], "content": message["content"]})
    messages.append({"role": "user", "content": prompt})

    # we give LLM a chat history: old prompts without data, and latest prompt WITH data (old data is engrained into old responses)
    response = safe_llm_call(messages, True)
    # loop through each data chunk
    # if it contains text extract text and send to caller
    # delta means new data added in this chunk
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content






    