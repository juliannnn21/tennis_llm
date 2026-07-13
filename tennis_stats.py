import pandas as pd
RECENT_WIN_RATE_MATCHES = 20
ON_FORM_NUMBER = 3
df = pd.read_csv('data/atp_tennis.csv')

def get_h2h(df, p1, p2):
    head_to_head = df[((df['Player_1'] == p1) & (df['Player_2'] == p2)) | ((df['Player_1'] == p2) & (df['Player_2'] == p1))]
    counts = head_to_head['Winner'].value_counts()
    #print(f"counts: {counts}")
    return counts

def get_surface_performance(df,p,surface):
    if surface == "All":
        fil = df[((df['Player_1'] == p) | (df['Player_2'] == p))]

        surface_performance_dict = {}
        for surface in ["Grass", "Clay", "Hard", "Carpet"]:
            surface_filter = fil[fil["Surface"] == surface]
            surface_filter_wins = len(surface_filter[surface_filter["Winner"] == p])
            if len(surface_filter) == 0:
                surface_performance_dict[surface] = None
            else:
                surface_performance_dict[surface] = {
                    "win_rate": round((surface_filter_wins/len(surface_filter) * 100),1),
                    "matches": len(surface_filter)
                }
        return surface_performance_dict
    
    else:
        fil = df[((df['Player_1'] == p) | (df['Player_2'] == p)) & (df['Surface'] == surface)]

        wins = len(fil[fil['Winner'] == p])
        matches = len(fil)
        if matches == 0:
            win_percentage = None
        else:
            win_percentage = round((wins/matches * 100),1)
        surface_performance_dict = {}
        surface_performance_dict["surface_win_percentage"] = win_percentage
        surface_performance_dict["surface_matches"] = matches
        return surface_performance_dict

def get_player_stats(df,p):
    # get win rate
    fil = df[((df['Player_1'] == p) | (df['Player_2'] == p))]

    recent_player_match = fil.sort_values('Date').iloc[-1]
    if recent_player_match["Player_1"] == p:
        recent_player_rank = recent_player_match["Rank_1"]
    else:
        recent_player_rank = recent_player_match["Rank_2"]
   


    wins = len(fil[fil['Winner'] == p])
    if len(fil) == 0:
        win_rate = None
    else:
        win_rate = round((wins/len(fil) * 100),1)

    # get win rate per surface

    surface_win_rates = {}

    for surface in ["Grass", "Clay", "Hard", "Carpet"]:
        surface_filter = fil[fil["Surface"] == surface]
        surface_filter_wins = len(surface_filter[surface_filter["Winner"] == p])
        if len(surface_filter) == 0:
            surface_win_rates[surface] = None
        else:
            surface_win_rate = round((surface_filter_wins/len(surface_filter) * 100),1)
            surface_win_rates[surface] = surface_win_rate

    higher_lower_win_rates = {}
    # get win rate against higher/lower ranked opponents
    #performance against BETTER players, here higher ranked players mean a BETTER rank
    higher_fil = fil[((fil['Player_1'] == p) & (fil["Rank_1"] > fil["Rank_2"])) | ((fil['Player_2'] == p) & (fil["Rank_2"] > fil["Rank_1"]))]
    #performance against WORSE players
    lower_fil = fil[((fil['Player_1'] == p) & (fil["Rank_1"] < fil["Rank_2"])) | ((fil['Player_2'] == p) & (fil["Rank_2"] < fil["Rank_1"]))]
    if len(higher_fil) == 0:
        higher_fil_win_rate = None
    else:
        higher_fil_wins = len(higher_fil[higher_fil["Winner"] == p])
        higher_fil_win_rate = round((higher_fil_wins/len(higher_fil) * 100),1)
    if len(lower_fil) == 0:
        lower_fil_win_rate = None
    else:
        lower_fil_wins = len(lower_fil[lower_fil["Winner"] == p])
        lower_fil_win_rate = round((lower_fil_wins/len(lower_fil) * 100),1)
    higher_lower_win_rates["win_rate_higher_rank"] = higher_fil_win_rate
    higher_lower_win_rates["win_rate_lower_rank"] = lower_fil_win_rate

    best_tournament_dict = {}
    # get mean win rate per tournament
    fil = fil.copy()
    fil['won'] = fil['Winner'] == p

    # get meaning of minimum matches
    if recent_player_rank > 50:
        minimum_matches = 10
    else:
        minimum_matches = 20

    tournament_win_rates = fil.groupby('Tournament')['won'].agg(mean="mean", count="count")
    tournament_win_rates = tournament_win_rates[tournament_win_rates['count'] >= minimum_matches]
    if len(tournament_win_rates) == 0:
        best_tournament_dict = 0
    else:
        best_tournament = tournament_win_rates["mean"].idxmax()
        best_tournament_win_rate = float(round((tournament_win_rates["mean"].max() * 100),1))
        best_tournament_matches_played = int(tournament_win_rates.loc[best_tournament, 'count'])
        best_tournament_dict["best_tournament"] = best_tournament
        best_tournament_dict["best_tournament_win_rate"] = best_tournament_win_rate
        best_tournament_dict["best_tournament_matches_played"] = best_tournament_matches_played

    recent_win_rate_dict = {}
    fil = fil.sort_values('Date')
    recent_match_fil = fil.tail(RECENT_WIN_RATE_MATCHES) 
    recent_wins = len(recent_match_fil[recent_match_fil["Winner"] == p])
    recent_win_rate = round((recent_wins/len(recent_match_fil) * 100),1)
    recent_win_rate_dict["recent_win_rate"] = recent_win_rate
    recent_win_rate_dict["recent_win_rate_matches"] = RECENT_WIN_RATE_MATCHES

    statistics = {"overall_win_rate": win_rate, "win_rate_by_surface": surface_win_rates, "higher_lower_win_rates": higher_lower_win_rates
                  , "best_tournament_stats": best_tournament_dict, "recent_win_rate_stats": recent_win_rate_dict}
    return statistics

# on_form_number controls how MANY players to list
def get_on_form_players(df, surface = None, on_form_number = ON_FORM_NUMBER):

    if surface and surface != "All":
        fil = df[df["Surface"] == surface]
    else:
        fil = df.copy()
    # cutoff date for best 'recent' form
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months = 3)
    # convert date column to date time so can do comparison
    fil = fil[pd.to_datetime(fil['Date']) >= cutoff_date]
    p1 = fil[['Date', 'Player_1', 'Winner']].rename(columns={'Player_1': 'Player'})
    p2 = fil[['Date', 'Player_2', 'Winner']].rename(columns={'Player_2': 'Player'})
    combined_players = pd.concat([p1, p2])
    combined_players["Won"] = combined_players["Winner"] == combined_players["Player"]
    # aggregate table has player name, count (matches played in last 3 months), and mean (win rate of these matches)
    player_forms = combined_players.groupby('Player')['Won'].agg(matches_played ="count", win_rate = "mean")
    # minimum 10 matches seems reasonable
    player_forms = player_forms[player_forms["matches_played"] >= 10]
    # sort descending
    player_forms = player_forms.sort_values("win_rate", ascending = False)
    player_forms["win_rate"] = player_forms["win_rate"].round(3)
    player_forms["win_rate"] = player_forms["win_rate"] * 100

    return player_forms.head(on_form_number)

def get_favourites(df, tournament):

    # get tournament's surface by getting surface of most recent tournament of its kind

    most_recent_tournament = df[df['Tournament'] == tournament].sort_values('Date').iloc[-1]
    surface = most_recent_tournament['Surface']

    # get candidates

    candidate_fil_p1 = df[['Date', 'Player_1', 'Rank_1', "Winner"]].rename(columns={'Player_1': 'Player', "Rank_1": "Rank"})
    candidate_fil_p2 = df[['Date', 'Player_2', 'Rank_2', "Winner"]].rename(columns={'Player_2': 'Player', "Rank_2": "Rank"})
    candidate_fil = pd.concat([candidate_fil_p1, candidate_fil_p2])
    candidate_fil["Won"] = candidate_fil["Winner"] == candidate_fil["Player"]
    # candidates must have played a match in past 12 months
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months = 12)
    # convert date column to date time so can do comparison
    candidate_fil = candidate_fil[pd.to_datetime(candidate_fil['Date']) >= cutoff_date]

    #get the candidates
    
    # sort by date ascending
    candidate_fil = candidate_fil.sort_values('Date')
    # 1 group for each player, then get their most recent rank
    most_recent_ranks = candidate_fil.groupby('Player').last()  
    candidates = most_recent_ranks[most_recent_ranks["Rank"] <= 100]
    candidates = candidates.sort_values("Rank")
    #print(candidates.head(10))

    # slim candidate history to mast 3 months for recent form

    form_cutoff_date = pd.Timestamp.now() - pd.DateOffset(months = 3)
    form_fil = candidate_fil[pd.to_datetime(candidate_fil['Date']) >= form_cutoff_date]

    # get tournament history of each player last 5 years

    tournament_fil = df[(df["Tournament"] == tournament)]
    tournament_fil_p1 = tournament_fil[["Tournament", 'Date', 'Player_1', "Winner"]].rename(columns={'Player_1': 'Player'})
    tournament_fil_p2 = tournament_fil[["Tournament", 'Date', 'Player_2', "Winner"]].rename(columns={'Player_2': 'Player'})
    tournament_fil = pd.concat([tournament_fil_p1, tournament_fil_p2])
    tournament_fil["Won"] = tournament_fil["Winner"] == tournament_fil["Player"]
    tournament_cutoff_date = pd.Timestamp.now() - pd.DateOffset(years = 5)
    tournament_fil = tournament_fil[pd.to_datetime(tournament_fil['Date']) >= tournament_cutoff_date]

    # get surface history of each player last 5 years

    surface_fil = df[df["Surface"] == surface]
    surface_fil_p1 = surface_fil[["Tournament", "Surface", 'Date', 'Player_1', "Winner"]].rename(columns={'Player_1': 'Player'})
    surface_fil_p2 = surface_fil[["Tournament", "Surface", 'Date', 'Player_2', "Winner"]].rename(columns={'Player_2': 'Player'})
    surface_fil = pd.concat([surface_fil_p1, surface_fil_p2])
    surface_fil["Won"] = surface_fil["Winner"] == surface_fil["Player"]
    surface_cutoff_date = pd.Timestamp.now() - pd.DateOffset(years = 5)
    surface_fil = surface_fil[pd.to_datetime(surface_fil['Date']) >= surface_cutoff_date]

    scores = {}

    for player in candidates.index:
        # rank score
        rank = candidates.loc[player, 'Rank']
        rank_score = 1/rank
        # form score- filter candidate_fil for this player, last 3 months

        cutoff_date = pd.Timestamp.now() - pd.DateOffset(months=3)

        # get matches in last 3 months for given player
        recent_player_matches = form_fil[form_fil['Player'] == player]

        # min 5 matches over past 3 months
        if len(recent_player_matches) >= 5:
            form_score = recent_player_matches['Won'].mean() 
        else:
            form_score = None
        
        # previous performance at the tournament last 5 years, so get win rate at the tournament over past 5 years
        player_tournament = tournament_fil[tournament_fil["Player"] == player]
        
        if len(player_tournament) >= 5:
            tournament_score = player_tournament['Won'].mean() 
        else:
            tournament_score = None
        
        player_surface = surface_fil[surface_fil["Player"] == player]

        if len(player_surface) >= 5:
            surface_score = player_surface['Won'].mean() 
        else:
            surface_score = None

        # if haven't played the tournament in last 5 years use the surface score
        if tournament_score is None:
            tournament_score = surface_score

        if form_score is None:
            form_score = 0.5
        if tournament_score is None:
            tournament_score = 0.5
        if surface_score is None:
            surface_score = 0.5

        player_score = (0.35 * rank_score) + (0.25 * form_score) + (0.25 * tournament_score) + (0.15 * surface_score)
        scores[player] = float(player_score)

    scores_series = pd.Series(scores)
    top_scores = scores_series.sort_values(ascending=False).head(5)
    favourites = {}
    for i, player in enumerate(top_scores.index.tolist()):
        favourites[f"Favourite {i+1}"] = player

    return favourites
