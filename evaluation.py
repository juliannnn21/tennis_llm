from main import classify_intent
from llm_client import client
import pandas as pd
import json
import random


manual_cases = [

    #obvious ones

    {"query": "who wins Nadal vs Federer", "expected_intent": "h2h", "source": "manual"},
    {"query": "head to head of sinner and alcaraz", "expected_intent": "h2h", "source": "manual"},

    {"query": "how does Djokovic perform on clay", "expected_intent": "surface_performance", "source": "manual"},
    {"query": "how does Dimitrov play on grass", "expected_intent": "surface_performance", "source": "manual"},
    
    {"query": "what are fritz statistics", "expected_intent": "player_stats", "source": "manual"},
    {"query": "statistics of Auger-Alliasime", "expected_intent": "player_stats", "source": "manual"},

    {"query": "who is on form right now?", "expected_intent": "on_form_players", "source": "manual"},
    {"query": "who are the on-form players currently?", "expected_intent": "on_form_players", "source": "manual"},

    {"query": "who are the tournament favourites for US open?", "expected_intent": "tournament_favourites", "source": "manual"},
    {"query": "who are the clear favourites for Wimbledon?", "expected_intent": "tournament_favourites", "source": "manual"},

    {"query": "how does zverev perform at the Australian Open?", "expected_intent": "tournament_performance", "source": "manual"},
    {"query": "what is Tommy Paul's performance like at Indian Wells?", "expected_intent": "tournament_performance", "source": "manual"},

    {"query": "what time is it", "expected_intent": "unknown", "source": "manual"},
    {"query": "capital of France", "expected_intent": "unknown", "source": "manual"},


    # slightly ambiguous ones

    {"query": "Alexander Z vs novak", "expected_intent": "h2h", "source": "manual"},
    {"query": "who wins tomy paul or perricard?", "expected_intent": "h2h", "source": "manual"},

    {"query": "taylor f clay", "expected_intent": "surface_performance"},
    {"query": "stan warinka on hard courts", "expected_intent": "surface_performance", "source": "manual"},

    {"query": "how good was Federer", "expected_intent": "player_stats", "source": "manual"},
    {"query": "is Shelton a good player?", "expected_intent": "player_stats", "source": "manual"},

    {"query": "best grass players", "expected_intent": "on_form_players", "source": "manual"},
    {"query": "best players right now", "expected_intent": "on_form_players", "source": "manual"},

    {"query": "who should i bet on for paris masters", "expected_intent": "tournament_favourites", "source": "manual"},
    {"query": "who will win ATP finals?", "expected_intent": "tournament_favourites", "source": "manual"},

    {"query": "murray roland garros", "expected_intent": "tournament_performance", "source": "manual"},
    {"query": "Tommy Paul at Queen's club", "expected_intent": "tournament_performance", "source": "manual"},
 
    {"query": "who coaches Draper?", "expected_intent": "unknown", "source": "manual"},
    {"query": "how tall is djokovic", "expected_intent": "unknown", "source": "manual"},

    # ambiguous ones

    {"query": "jannik and carlos", "expected_intent": "h2h", "source": "manual"},
    {"query": "medvedev hard", "expected_intent": "surface_performance", "source": "manual"},
    {"query": "Tommy P summary", "expected_intent": "player_stats", "source": "manual"},
    {"query": "current clay court specialists", "expected_intent": "on_form_players", "source": "manual"},
    {"query": "who should i watch at Miami", "expected_intent": "tournament_favourites", "source": "manual"},
    {"query": "sinner wimbledon match stats", "expected_intent": "unknown", "source": "manual"},
]

def generate_test_cases_llm(intent, intent_description, n=10):
    prompt = f"""Generate {n} diverse, realistic queries about ATP men's tour only for intent: {intent}.
    Based off intent description: {intent_description}
    Mix obvious, slightly ambiguous and ambiguous ones where intent is only implied. Return as a list, one per line."""


    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages = [{"role": "user", "content": prompt}]
 
    )

    # need list of dict

    queries = response.choices[0].message.content.strip().split("\n")
    test_cases_llm = []
    for query in queries:
        test_cases_llm.append({"query": query.strip().lstrip("0123456789. "), "expected_intent": intent, "source": "llm"})

    return test_cases_llm












def evaluate(test_cases):
    correct = 0
    total = len(test_cases)
    failures = []
    
    for test in test_cases:
        predicted = classify_intent(test["query"])
        expected = test["expected_intent"]
        
        if predicted == expected:
            correct += 1
        else:
            failures.append({
                "query": test["query"],
                "expected": expected,
                "predicted": predicted
            })
    
    accuracy = round((correct / total) * 100, 1)
    return accuracy, failures


def generate_cases(n=10):
    intent_descriptions = {
    "h2h": "general head to head record between two players only across all tournaments",
    "surface_performance": "how a player performs on a specific surface or all surfaces",
    "player_stats": "overall win rate, win rates on each surface, win rate vs higher/lower ranked opponents, best tournament, recent form",
    "on_form_players": "which players are currently in form, best performing players recently, either for all surfaces/specific one",
    "tournament_favourites": "who is likely to win an upcoming tournament",
    "tournament_performance": "how a specific player has performed at a specific tournament",
    "unknown": "questions about rankings, grand slam titles, prize money, coaching, playing style, or anything not covered by the other intents"
        }   
    
    llm_cases = []
    for intent, description in intent_descriptions.items():
        llm_cases.extend(generate_test_cases_llm(intent, description,n))
    all_cases = manual_cases + llm_cases
    with open("test_cases.json", "w") as f:
        json.dump(all_cases, f, indent=2)

def load_cases():
    with open("test_cases.json", "r") as f:
        all_cases = json.load(f)
    return all_cases




if __name__ == "__main__":

    #generate_cases(10)
    test_cases = load_cases()
    random.shuffle(test_cases)
    print(f"manual_cases: {len(manual_cases)}, llm_cases: {len(test_cases)-len(manual_cases)}")
    print(test_cases)

    accuracy, failures = evaluate(test_cases)
    print(f"accuracy: {accuracy}, failures: {failures}")