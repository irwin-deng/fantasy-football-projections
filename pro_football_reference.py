"""
File: pro_football_reference.py
Description: Downloads historical data from pro-football-reference.com
"""

import requests
import pandas as pd
import importlib
from bs4 import BeautifulSoup
import time
import random

import util_scripts
importlib.reload(util_scripts)

def scrape(year, week, webdriver, save_path="historical_{year}_{week}_pro-football-reference.csv"):
    """
    scrapes projections from pro-football-reference.com.com.

    :param year: the year to be scraped
    :param week: the week to be scraped
    :return: A DataFrame of each player's stats
    """ 
    
    # Find all games for that week
    landing_page_url = "https://www.pro-football-reference.com/years/{year}/week_{week}.htm".format(
        year=year, week=week)
    
    page = requests.get(landing_page_url)
    time.sleep(3 + random.uniform(0, 2))
    soup = BeautifulSoup(page.text, 'html.parser')
    
    games_html = soup.find("div", {"class":"game_summaries"})
    games_html = games_html.find_all("div", {"class":"game_summary"})
    base_url = "https://www.pro-football-reference.com"
    game_urls = [base_url + game_html.find("td", {"class":"gamelink"}).find("a")["href"] 
                 for game_html in games_html]
    
    """"""
    webdriver.set_page_load_timeout(10)
    try:
        webdriver.get(game_urls[0])
    except Exception as e:
        print(e)
    
    #time.sleep(11 + random.uniform(0, 5))

    html = webdriver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    
    """
    def_df = _get_team_defense_stats(soup)
    def_df.to_csv(path_or_buf=save_path.format(year=year, week=week), index=False, na_rep='-')
    """

    
    """
    for game_url in game_urls:
        webdriver.get(game_url)
        print("reading: {url}".format(url=game_url))
        time.sleep(11 + random.uniform(0, 5))

        html = webdriver.page_source
        soup = BeautifulSoup(html, 'html.parser')
    
        _get_team_stats(soup)
        
    """

    """
    # Save to CSV
    from functools import reduce
    df = reduce(lambda df1,df2: pd.merge(df1,df2,how="full"), [off_df, k_df, def_df])
    df = df.replace("-", 0)
    df.to_csv(path_or_buf=save_path.format(year=year, week=week), index=False, na_rep='-')
    """

def _get_player_position_dict(soup):
    """
    Gets map of player name -> position

    :param soup: BeautifulSoup object representing the HTML page
    :return: map of player name -> position
    """
    h_roster_table = soup.find("table", {"id": "home_snap_counts"})
    h_roster_df = util_scripts.read_raw_html_table(h_roster_table)

    a_roster_table = soup.find("table", {"id": "vis_snap_counts"})
    a_roster_df = util_scripts.read_raw_html_table(a_roster_table)

    roster_df = pd.concat([h_roster_df, a_roster_df], axis=0, ignore_index=True)

    players_list = list(map(lambda player: player.get_text(), roster_df["_Player"]))
    pos_list = list(map(lambda pos: pos.get_text(), roster_df["_Pos"]))

    players_dict = dict(zip(players_list, pos_list))
    return players_dict


def _get_offense_stats(soup):
    raw_stats_table = soup.find("table", {"id": "player_offense"})
    raw_stats_df = pd.read_html(str(raw_stats_table))[0]
    
    # transpose df and fix headers
    #raw_stats_df = raw_stats_df.T
    #raw_stats_df.columns = raw_stats_df.iloc[0]
    #raw_stats_df = raw_stats_df[1:]

    player_pos_dict = _get_player_position_dict(soup=soup)
    
    """
    TODO: implement position lookup
    """

    print(raw_stats_df)
    
def _get_team_defense_stats(soup):
    raw_stats_table = soup.find("table", {"id": "team_stats"})
    raw_stats_df = pd.read_html(str(raw_stats_table))[0]
    
    # transpose df and fix headers
    raw_stats_df = raw_stats_df.T
    raw_stats_df.columns = raw_stats_df.iloc[0]
    raw_stats_df = raw_stats_df[1:]
    
    stats_list = []
    # find first downs
    stats_list.append(_get_series(df=raw_stats_df, header="First Downs", index=None, reverse=True, new_name="Def 1D Allow"))
    
    # find rush attempts allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Rush-Yds-TDs", index=0, reverse=True, new_name="Def Rush Att Allow"))
    # find rush yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Rush-Yds-TDs", index=1, reverse=True, new_name="Def Rush Yd Allow"))
    # find rush TDs allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Rush-Yds-TDs", index=2, reverse=True, new_name="Def Rush TD Allow"))
    
    # find pass completions allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT", index=0, reverse=True, new_name="Def Pass Comp Allow"))
    # find pass attempts allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT", index=1, reverse=True, new_name="Def Pass Att Allow"))
    # find (gross) pass yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT", index=2, reverse=True, new_name="Def Pass Yd Allow Gross"))
    # find pass TDs allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT", index=3, reverse=True, new_name="Def Pass TD Allow"))
    # find interceptions
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT", index=4, reverse=True, new_name="Def Int"))
    
    # find sacks
    stats_list.append(_get_series(df=raw_stats_df, header="Sacked-Yards", index=0, reverse=True, new_name="Def Sack"))
    # find sack yards
    stats_list.append(_get_series(df=raw_stats_df, header="Sacked-Yards", index=1, reverse=True, new_name="Def Sack Yd"))
    
    # find (net) pass yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Net Pass Yards", index=None, reverse=True, new_name="Def Pass Yd Allow Net"))
    
    # find (net) total yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Total Yards", index=None, reverse=True, new_name="Def Yd Allow"))
    
    # find fumbles
    stats_list.append(_get_series(df=raw_stats_df, header="Fumbles-Lost", index=0, reverse=True, new_name="Def Fum"))
    # find fumbles recovered
    stats_list.append(_get_series(df=raw_stats_df, header="Fumbles-Lost", index=1, reverse=True, new_name="Def Fum Rec"))
    
    # find turnovers
    stats_list.append(_get_series(df=raw_stats_df, header="Turnovers", index=None, reverse=True, new_name="Def TO"))
    
    """
    def_int
    def_saf
    def_sack
    def_td
    def_block
    ret_yd
    def_pt
    """

    stats_df = pd.concat(stats_list, axis=1)

    # Move name from index to a new column
    stats_df.reset_index(inplace=True)
    stats_df = stats_df.rename(columns={"index":"Team"})

    # Add team name (get from team abbreviation)
    stats_df.insert(loc=0, column="Name", value=list(map(
        util_scripts.get_team_name_from_abbreviation, stats_df.Team)))

    # Add position
    stats_df.insert(loc=2, column="Pos", value="DST")

    return stats_df
    
def _get_series(df, header, index=None, reverse=False, new_name=None):
    """
    gets a stat series (one element per player/team)

    :param df: the DataFrame to parse
    :param header: the header to look for
    :param index: the index within the header (if multiple stats
                are under the same header but separated by a hyphen)
                Must be an integer or None
    :param reverse: whether to reverse the series (used for reversing offense / defense stats)
    :return: A Series of each player/team's stat
    """ 
    series = df[header]
    
    if isinstance(index, int):
        series = series.apply(lambda text: text.split("-")[index])
    elif index is not None:
        raise Exception("Index should be an integer or None")
    
    if reverse:
        num_entries = len(series)
        if num_entries != 2:
            raise Exception("There should be 2 entries if reversing")
        series = _reverse_series(series)
    
    series = series.rename(new_name)
    
    return series
    
def _reverse_series(series):
    # get indices as list
    indices = list(series.index)
    
    # reverse indices
    indices = indices[::-1]
    
    # set series index 
    series = series.set_axis(indices)
    
    # return reversed series
    return series