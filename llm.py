import os
from groq import Groq
from dotenv import load_dotenv
# read .env and load the api key into environment variables
load_dotenv()

# create API client using the key
client = Groq(api_key = os.getenv("GROQ_API_KEY"))

def classify_intent(query):
    prompt = f"""
    Classify this query into one of the following intents and return only the intent category name:
    1) h2h, 2) surface_performance, 3) player_stats, 4) on_form_players, 5) tournament_favourites
    Or if the query doesn't fit any intent then return only the word unknown

    The query is: {query}
    """

    # user here means the user's message 

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ]
    )

    intent = response.choices[0].message.content

    return intent


def extract_entities(query, intent):
    if intent == "h2h":

        prompt = f"""
        From the query extract the 2 players in the head-to-head question, and return them
        in the form player_1,player_2. If unable to do this return the word unknown

        The query is: {query}
        """

        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
        )

        players = response.choices[0].message.content
        if players == "unknown":
            return None
        player1, player2 = players.split(",")
        players_dict = {"player_1": player1.strip(), "player_2": player2.strip()}
        return players_dict
    
    elif intent == "surface_performance":

        prompt = f"""
        From the query extract the player and the surface, and return them
        in the form player,surface. 
        If no surface mentioned or all surfaces mentioned return: player,all
        If unable to identify player then return the word unknown

        The query is: {query}
        """

        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
        )

        surface_data = response.choices[0].message.content
        if surface_data == "unknown":
            return None
        #print(surface_data)
        player, surface = surface_data.split(",")
        surface = surface.capitalize()
        surface_dict = {"player": player.strip(), "surface": surface.strip()}
        return surface_dict
    
    elif intent == "player_stats":

        prompt = f"""
        From the query extract player name and return only that.
        If unable to identify player then return the word unknown

        The query is: {query}
        """

        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
        )

        player = response.choices[0].message.content
        if player == "unknown":
            return None
        stats_dict = {"player": player.strip()}
        return stats_dict

    elif intent == "on_form_players":

        prompt = f"""
        From the query extract the surface if given and return just the surface name.
        If no surface mentioned or all surfaces mentioned return the word all
        

        The query is: {query}
        """

        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
        )

        surface = response.choices[0].message.content
        surface = surface.capitalize()
        on_form_dict = {"surface": surface.strip()}
        return on_form_dict

    elif intent == "tournament_favourites":

        prompt = f"""
        From the query extract the tournament name and return only that.
        If unable to identify tournament then return the word unknown

        The query is: {query}
        """

        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ]
        )

        tournament_name = response.choices[0].message.content
        if tournament_name == "unknown":
            return None
        tournament_favourites_dict = {"tournament": tournament_name.strip()}
        return tournament_favourites_dict

    else:
        return None

# original query so actually answers the question asked, and intent so formats right type of response
def format_response(query, result):


    prompt = f"""
    Based on the original query generate a natural conversation respons using the data below.
    Be concise, use all provided data, and don't use any data not provided.
    For player names ensure to you their full name
    If the query is about tournament favourites emphasise who is the number one favourite

    
    The original query is: {query}
    The data is: {result}
    """

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ]
    )

    answer = response.choices[0].message.content

    return answer






# just for testing

if __name__ == "__main__":
    q1 = "who wins in Zverev vs taylor fritz?"
    q2 = "how does Novak Djokovic perform on grass"
    q3 = "nadal statistics"
    q4 = "who is playing well right now?"
    q5 = "who are the wimbledon favourites?"
    q6 = "what time is it?"
    
    for q in [q1,q2,q3,q4,q5,q6]:
        intent = classify_intent(q)
        print(extract_entities(q, intent))

    