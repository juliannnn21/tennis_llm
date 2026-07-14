import os
from groq import Groq
from dotenv import load_dotenv

# read .env and load the api key into environment variables
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))