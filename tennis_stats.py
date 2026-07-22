"""
tennis_stats.py

Data retrieval functions for ATP tennis statistics.
Queries match data from the ATP dataset to answer questions about
player performance, head to head records, surface performance,
tournament history and tournament favourites.
"""

import pandas as pd
RECENT_WIN_RATE_MATCHES = 20
ON_FORM_NUMBER = 3

def get_h2h(df, p1, p2):
    """
    Returns head-to-head win count between two players
    
    args:
        df: ATP match dataframe
        p1: Player name in dataset format e.g. 'Djokovic N.'
        p2: Player name in dataset format e.g. 'Federer R.'
    
    Returns:
        pandas Series with win counts per player/None if df is empty
    """

    if len(df) == 0:
        return None
    head_to_head = df[((df['Player_1'] == p1) & (df['Player_2'] == p2)) | ((df['Player_1'] == p2) & (df['Player_2'] == p1))]
    counts = head_to_head['Winner'].value_counts()
    return counts

def get_surface_performance(df,p,surface):

    """
    Returns surface performance for a player including win % and matches played
    Can be for a specific surface/all surfaces
    
    Args:
        df: ATP match dataframe
        p: Player name in dataset format e.g. 'Djokovic N.'
        surface: surface name e.g. 'Clay', 'Grass','All'
    
    Returns:
        For single surface: dict with 'surface_win_percentage' and 'surface_matches'
        For 'All': dict with each surface as key containing win_rate and matches
        None if df is empty
    """

    if len(df) == 0:
        return None

    if surface == "All":
        fil = df[((df['Player_1'] == p) | (df['Player_2'] == p))]

        surface_performance_dict = {}

        # for each surface get win % and matches
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
    
    # if specified surface just do it for one surface
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

    """
    Returns comprehensive statistics for a player.

    Args:
        df: ATP match dataframe
        p: Player name in dataset format e.g. 'Nadal R.'

    Returns:
        dict containing:
            - overall_win_rate: win percentage across all matches
            - win_rate_by_surface: win % for each surface
            - higher_lower_win_rates: win % vs higher and lower ranked opponents
            - best_tournament_stats: best tournament with win % and matches played
            - recent_win_rate_stats: win % over last 20 matches
        None if df is empty or player not found
    """

    if len(df) == 0:
        return None
    
    # get win rate
    fil = df[((df['Player_1'] == p) | (df['Player_2'] == p))]

    if len(fil) == 0:
        return None
    
    wins = len(fil[fil['Winner'] == p])
    win_rate = round((wins/len(fil) * 100),1)

    recent_player_match = fil.sort_values('Date').iloc[-1]
    if recent_player_match["Player_1"] == p:
        recent_player_rank = recent_player_match["Rank_1"]
    else:
        recent_player_rank = recent_player_match["Rank_2"]
   
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
    # performance against BETTER players, here higher ranked players mean a BETTER rank
    higher_fil = fil[((fil['Player_1'] == p) & (fil["Rank_1"] > fil["Rank_2"])) | ((fil['Player_2'] == p) & (fil["Rank_2"] > fil["Rank_1"]))]
    # performance against WORSE players
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

    # minimum matches depends on player rank
    if recent_player_rank > 50:
        minimum_matches = 10
    else:
        minimum_matches = 20

    tournament_win_rates = fil.groupby('Tournament')['won'].agg(mean="mean", count="count")
    tournament_win_rates = tournament_win_rates[tournament_win_rates['count'] >= minimum_matches]
    if len(tournament_win_rates) == 0:
        best_tournament_dict = None
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


def get_on_form_players(df, surface = None, on_form_number = ON_FORM_NUMBER):

    """
    Returns the most in-form players based on recent win rate.

    Args:
        df: ATP match dataframe
        surface: Optional surface filter e.g. 'Clay', 'Grass', 'Hard', 'Carpet'
                If None or 'All', returns form across all surfaces
        on_form_number: Number of players to return, defaults to ON_FORM_NUMBER constant

    Returns:
        DataFrame with columns 'matches_played' and 'win_rate', sorted by win rate descending
        Only includes players with minimum 10 matches in last 3 months
        Empty DataFrame if no players meet criteria
        None if df is empty
    """

    if len(df) == 0:
        return None
    if surface and surface != "All":
        fil = df[df["Surface"] == surface]
    else:
        fil = df.copy()
    # cutoff date for best 'recent' form is last 6 months
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months = 6)
    # convert date column to date time so can do comparison
    fil = fil[pd.to_datetime(fil['Date'],dayfirst=True) >= cutoff_date]
    p1 = fil[['Date', 'Player_1', 'Winner']].rename(columns={'Player_1': 'Player'})
    p2 = fil[['Date', 'Player_2', 'Winner']].rename(columns={'Player_2': 'Player'})
    combined_players = pd.concat([p1, p2])
    combined_players["Won"] = combined_players["Winner"] == combined_players["Player"]
    # aggregate table has player name, count (matches played in last 3 months), and mean (win rate of these matches)
    player_forms = combined_players.groupby('Player')['Won'].agg(matches_played ="count", win_rate = "mean")
    # minimum 10 matches is reasonable
    player_forms = player_forms[player_forms["matches_played"] >= 10]
    # sort descending
    player_forms = player_forms.sort_values("win_rate", ascending = False)
    player_forms["win_rate"] = player_forms["win_rate"].round(3)
    player_forms["win_rate"] = player_forms["win_rate"] * 100

    return player_forms.head(on_form_number)

def get_favourites(df, tournament):

    """
    Returns top 5 tournament favourites based on weighted scoring of rank, form, 
    tournament history and surface performance.

    Args:
        df: ATP match dataframe
        tournament: Tournament name matching dataset format e.g. 'Wimbledon', 'French Open'

    Returns:
        dict with keys 'Favourite 1' through 'Favourite 5' mapping to player names
        None if tournament not found in dataset or df is empty

    Scoring weights:
        - Current ranking: 35%
        - Recent form (last 3 months): 25%
        - Tournament history (last 5 years): 25%
        - Surface win rate (last 5 years): 15%
    """
    if len(df) == 0:
        return None

    # get tournament's surface by getting surface of most recent tournament of its kind

    tournament_fil = df[(df["Tournament"] == tournament)]
    if len(tournament_fil) == 0:
        return None
    
    most_recent_tournament = tournament_fil.sort_values('Date').iloc[-1]
    surface = most_recent_tournament['Surface']

    # get candidate players

    candidate_fil_p1 = df[['Date', 'Player_1', 'Rank_1', "Winner"]].rename(columns={'Player_1': 'Player', "Rank_1": "Rank"})
    candidate_fil_p2 = df[['Date', 'Player_2', 'Rank_2', "Winner"]].rename(columns={'Player_2': 'Player', "Rank_2": "Rank"})
    candidate_fil = pd.concat([candidate_fil_p1, candidate_fil_p2])
    candidate_fil["Won"] = candidate_fil["Winner"] == candidate_fil["Player"]
    # candidates must have played a match in past 12 months
    cutoff_date = pd.Timestamp.now() - pd.DateOffset(months = 12)
    # convert date column to date time so can do comparison
    candidate_fil = candidate_fil[pd.to_datetime(candidate_fil['Date'],dayfirst=True) >= cutoff_date]
    
    # sort by date ascending
    candidate_fil = candidate_fil.sort_values('Date')
    # 1 group for each player, then get their most recent rank
    most_recent_ranks = candidate_fil.groupby('Player').last()  
    candidates = most_recent_ranks[most_recent_ranks["Rank"] <= 100]
    candidates = candidates.sort_values("Rank")
   
    # slim candidate history to mast 3 months for recent form

    form_cutoff_date = pd.Timestamp.now() - pd.DateOffset(months = 3)
    form_fil = candidate_fil[pd.to_datetime(candidate_fil['Date'],dayfirst=True) >= form_cutoff_date]

    # get tournament history of each player last 5 years
    
    tournament_fil_p1 = tournament_fil[["Tournament", 'Date', 'Player_1', "Winner"]].rename(columns={'Player_1': 'Player'})
    tournament_fil_p2 = tournament_fil[["Tournament", 'Date', 'Player_2', "Winner"]].rename(columns={'Player_2': 'Player'})
    tournament_fil = pd.concat([tournament_fil_p1, tournament_fil_p2])
    tournament_fil["Won"] = tournament_fil["Winner"] == tournament_fil["Player"]
    tournament_cutoff_date = pd.Timestamp.now() - pd.DateOffset(years = 5)
    tournament_fil = tournament_fil[pd.to_datetime(tournament_fil['Date'],dayfirst=True) >= tournament_cutoff_date]

    # get surface history of each player last 5 years

    surface_fil = df[df["Surface"] == surface]
    surface_fil_p1 = surface_fil[["Tournament", "Surface", 'Date', 'Player_1', "Winner"]].rename(columns={'Player_1': 'Player'})
    surface_fil_p2 = surface_fil[["Tournament", "Surface", 'Date', 'Player_2', "Winner"]].rename(columns={'Player_2': 'Player'})
    surface_fil = pd.concat([surface_fil_p1, surface_fil_p2])
    surface_fil["Won"] = surface_fil["Winner"] == surface_fil["Player"]
    surface_cutoff_date = pd.Timestamp.now() - pd.DateOffset(years = 5)
    surface_fil = surface_fil[pd.to_datetime(surface_fil['Date'],dayfirst=True) >= surface_cutoff_date]

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

    # output series saying favourite 1: player1, favourite 2: player2 etc...
    scores_series = pd.Series(scores)
    top_scores = scores_series.sort_values(ascending=False).head(5)
    favourites = {}
    for i, player in enumerate(top_scores.index.tolist()):
        favourites[f"Favourite {i+1}"] = player

    return favourites

def get_tournament_performance(df, p, tournament):

    """
    Returns a player's performance record at a specific tournament.

    Args:
        df: ATP match dataframe
        p: Player name in dataset format e.g. 'Murray A.'
        tournament: Tournament name matching dataset format e.g. 'Wimbledon'

    Returns:
        dict containing:
            - tournament_win_percentage: win % at that tournament
            - tournament_matches: total matches played at that tournament
        None if player has not played at tournament, tournament not found, or df is empty
    """

    if len(df) == 0:
        return None
    tournament_fil = df[((df['Player_1'] == p) | (df['Player_2'] == p)) & (df['Tournament'] == tournament)]
    tournament_matches = len(tournament_fil)
    if tournament_matches == 0:
        return None
    tournament_wins = len(tournament_fil[tournament_fil['Winner'] == p])
    tournament_win_rate = round((tournament_wins/tournament_matches * 100),1)
    tournament_performance_dict = {}
    tournament_performance_dict["tournament_win_percentage"] = tournament_win_rate
    tournament_performance_dict["tournament_matches"] = tournament_matches
    return tournament_performance_dict

