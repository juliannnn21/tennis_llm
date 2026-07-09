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

if __name__ == "__main__":
    q1 = "who wins in Zverev vs taylor fritz?"
    q2 = "how does Djokovic perform on grass"
    q3 = "nadal statistics"
    q4 = "who is playing well right now?"
    q5 = "who are the wimbledon favourites?"
    q6 = "what time is it?"
    
    for q in [q1,q2,q3,q4,q5,q6]:
        print(classify_intent(q))