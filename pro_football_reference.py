"""
File: pro_football_reference.py
Description: Downloads historical data from pro-football-reference.com
"""

import requests
import pandas as pd
import importlib
import bs4
from bs4 import BeautifulSoup
import time
import random
from functools import reduce
import traceback
import sys
import re

import util_scripts
importlib.reload(util_scripts)


def scrape(year, week, webdriver,
           save_path="historical_{year}_{week}_pro-football-reference.csv"):
    """
    scrapes projections from pro-football-reference.com.com.

    :param year: the year to be scraped
    :param week: the week to be scraped
    :return: A DataFrame of each player's stats
    """

    # Find all games for that week
    landing_page_url = ("https://www.pro-football-reference.com/years/"
                        f"{year}/week_{week}.htm")

    print(f"Reading year {year}, week {week}...")
    page = requests.get(landing_page_url)
    time.sleep(6 + random.uniform(0, 4))
    soup = BeautifulSoup(page.text, 'html.parser')

    games_html = soup.find("div", {"class": "game_summaries"})
    games_html = games_html.find_all("div", {"class": "game_summary"})
    base_url = "https://www.pro-football-reference.com"

    game_urls = []

    for game_html in games_html:
        game_element = game_html.find("td", {"class": "gamelink"})
        path = game_element.find("a")["href"]
        game_urls.append(base_url + path)

    """"""
    stat_dfs = []

    webdriver.set_page_load_timeout(10)

    num_games = len(games_html)
    game_index = 1

    for game_url in game_urls:
        print(f"\tReading game {game_index} / {num_games}...")
        game_index = game_index + 1

        webdriver.get(game_url)
        time.sleep(6 + random.uniform(0, 4))

        html = webdriver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        off_df = _get_offense_stats(soup)
        idp_df = _get_idp_stats(soup)
        kick_df = _get_kick_stats(soup)
        ret_df = _get_ret_stats(soup)
        dst_df = _get_team_defense_stats(soup)

        player_pos_dict = _get_player_position_dict(soup=soup)

        off_df.insert(loc=3, column="Pos",
                      value=off_df["ID"].map(player_pos_dict))
        idp_df.insert(loc=3, column="Pos",
                      value=idp_df["ID"].map(player_pos_dict))
        kick_df.insert(loc=3, column="Pos",
                       value=kick_df["ID"].map(player_pos_dict))
        ret_df.insert(loc=3, column="Pos",
                      value=ret_df["ID"].map(player_pos_dict))

        merged_df = reduce(lambda df1, df2:
                           pd.merge(df1, df2, how="outer"),
                           [off_df, idp_df, dst_df, kick_df, ret_df])

        stat_dfs.append(merged_df)

    # Save to CSV
    save_path = save_path.format(year=year, week=week)

    df = pd.concat(stat_dfs)
    df = df.sort_values(by=["Pos", "Name"])

    df = df.replace(re.compile("^\s*$"), "-")
    df = df.fillna("-")

    df.to_csv(path_or_buf=save_path, index=False)
    print(f"Year {year}, week {week} saved to {save_path}")


def _get_offense_stats(soup):
    """
    Gets offensive player stats

    :param soup: BeautifulSoup representation of the page
    :return: DataFrame of each offensive player's stats
    """

    labels = {"_Player": "Name", "ID": "ID", "_Tm": "Team",
              "Passing_Cmp": "Pass Comp", "Passing_Att": "Pass Att",
              "Passing_Yds": "Pass Yd", "Passing_TD": "Pass Td",
              "Passing_Int": "Pass Int", "Passing_Sk": "Pass Sack",
              "Passing_Yds2": "Pass Sack Yd", "Passing_Lng": "Pass Long",
              "Passing_Rate": "Pass Rate", "Rushing_Att": "Rush Att",
              "Rushing_Yds": "Rush Yd", "Rushing_TD": "Rush Td",
              "Rushing_Lng": "Rush Long", "Receiving_Tgt": "Rec Tgt",
              "Receiving_Rec": "Rec", "Receiving_Yds": "Rec Yd",
              "Receiving_TD": "Rec Td", "Receiving_Lng": "Rec Long",
              "Fumbles_Fmb": "Off Fum", "Fumbles_FL": "Off Fum Lost"}

    off_table = soup.find("table", {"id": "player_offense"})
    stats_df = _parse_pfr_table(table=off_table)
    stats_df.name = "Offense Stats"

    stats_df = util_scripts.set_df_headers(df=stats_df, labels=labels,
                                           check=True, check_order=True)

    return stats_df


def _get_idp_stats(soup):
    """
    Gets defensive player stats

    :param soup: BeautifulSoup representation of the page
    :return: DataFrame of each defensive player's stats
    """
    
    labels = {"_Player": "Name", "ID": "ID", "_Tm": "Team",
              "Def Interceptions_Int": "Def Int",
              "Def Interceptions_Yds": "Def Int Yd",
              "Def Interceptions_TD": "Def Int Td",
              "Def Interceptions_Lng": "Def Int Long",
              "Def Interceptions_PD": "Def PD",
              "_Sk": "Def Sack", "Tackles_Comb": "Tkl Total",
              "Tackles_Solo": "Tkl Solo", "Tackles_Ast": "Tkl Ast",
              "Tackles_TFL": "Tkl Loss", "Tackles_QBHits": "Tkl QBHit",
              "Fumbles_FR": "Def Fum Rec", "Fumbles_Yds": "Def Fum Yd",
              "Fumbles_TD": "Def Fum Td", "Fumbles_FF": "Def FF"}

    idp_table = soup.find("table", {"id": "player_defense"})
    stats_df = _parse_pfr_table(table=idp_table)
    stats_df.name = "IDP Stats"

    stats_df = util_scripts.set_df_headers(df=stats_df, labels=labels,
                                           check=True, check_order=True)

    return stats_df


def _get_ret_stats(soup):
    """
    Gets kick and punt return stats

    :param soup: BeautifulSoup representation of the page
    :return: DataFrame of each returner's stats (may be empty)
    """

    labels = {"_Player": "Name", "ID": "ID", "_Tm": "Team",
              "Kick Returns_Rt": "KR", "Kick Returns_Yds": "KR Yd",
              "Kick Returns_Y/Rt": "KR Avg", "Kick Returns_TD": "KR Td",
              "Kick Returns_Lng": "KR Long", "Punt Returns_Ret": "PR",
              "Punt Returns_Yds": "PR Yd", "Punt Returns_Y/R": "PR Avg",
              "Punt Returns_TD": "PR Td", "Punt Returns_Lng": "PR Long"}

    ret_table = soup.find("table", {"id": "returns"})

    # May not exist (e.g. 2014 NOR vs GNB)
    if ret_table is None:
        stats_df = pd.DataFrame(columns=list(labels.keys()))
    else:
        stats_df = _parse_pfr_table(table=ret_table)

        stats_df = util_scripts.set_df_headers(df=stats_df, labels=labels,
                                               check=True, check_order=True)

    stats_df.name = "Return Stats"
    return stats_df


def _get_kick_stats(soup):
    """
    Gets kick and punt stats

    :param soup: BeautifulSoup representation of the page
    :return: DataFrame of each kicker's stats (may be empty)
    """

    labels = {"_Player": "Name", "ID": "ID", "_Tm": "Team",
              "Scoring_XPM": "XP Made", "Scoring_XPA": "XP Att",
              "Scoring_FGM": "FG Made", "Scoring_FGA": "FG Att",
              "Punting_Pnt": "Punt", "Punting_Yds": "Punt Yd",
              "Punting_Y/P": "Punt Avg", "Punting_Lng": "Punt Long"}

    kick_table = soup.find("table", {"id": "kicking"})
    stats_df = _parse_pfr_table(table=kick_table)
    stats_df.name = "Kicking Stats"

    stats_df = util_scripts.set_df_headers(df=stats_df, labels=labels,
                                           check=True, check_order=True)

    return stats_df


def _get_team_defense_stats(soup):
    """
    Gets team defense stats

    :param soup: BeautifulSoup representation of the page
    :return: DataFrame of each team's defense stats
    """
    raw_stats_table = soup.find("table", {"id": "team_stats"})
    raw_stats_df = pd.read_html(str(raw_stats_table))[0]

    # transpose df and fix headers
    raw_stats_df = raw_stats_df.T
    raw_stats_df.columns = raw_stats_df.iloc[0]
    raw_stats_df = raw_stats_df[1:]

    stats_list = []
    # find first downs
    stats_list.append(_get_series(df=raw_stats_df, header="First Downs",
                      index=None, reverse=True, new_name="Def 1D"))

    # find rush attempts allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Rush-Yds-TDs",
                      index=0, reverse=True, new_name="Def Rush Att"))
    # find rush yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Rush-Yds-TDs",
                      index=1, reverse=True, new_name="Def Rush Yd"))
    # find rush TDs allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Rush-Yds-TDs",
                      index=2, reverse=True, new_name="Def Rush TD"))

    # find pass completions allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT",
                      index=0, reverse=True, new_name="Def Pass Comp"))
    # find pass attempts allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT",
                      index=1, reverse=True, new_name="Def Pass Att"))
    # find (gross) pass yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT",
                      index=2, reverse=True, new_name="Def Pass Yd Gross"))
    # find pass TDs allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT",
                      index=3, reverse=True, new_name="Def Pass TD"))
    # find interceptions
    stats_list.append(_get_series(df=raw_stats_df, header="Cmp-Att-Yd-TD-INT",
                      index=4, reverse=True, new_name="Def Int"))

    # find sacks
    stats_list.append(_get_series(df=raw_stats_df, header="Sacked-Yards",
                      index=0, reverse=True, new_name="Def Sack"))
    # find sack yards
    stats_list.append(_get_series(df=raw_stats_df, header="Sacked-Yards",
                      index=1, reverse=True, new_name="Def Sack Yd"))

    # find (net) pass yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Net Pass Yards",
                      index=None, reverse=True, new_name="Def Pass Yd Net"))

    # find (net) total yards allowed
    stats_list.append(_get_series(df=raw_stats_df, header="Total Yards",
                      index=None, reverse=True, new_name="Def Yd"))

    # find fumbles
    stats_list.append(_get_series(df=raw_stats_df, header="Fumbles-Lost",
                      index=0, reverse=True, new_name="Def Fum"))
    # find fumbles recovered
    stats_list.append(_get_series(df=raw_stats_df, header="Fumbles-Lost",
                      index=1, reverse=True, new_name="Def Fum Rec"))

    # find turnovers
    stats_list.append(_get_series(df=raw_stats_df, header="Turnovers",
                      index=None, reverse=True, new_name="Def TO"))

    stats_df = pd.concat(stats_list, axis=1)

    # Move name from index to a new column
    stats_df.reset_index(inplace=True)
    stats_df = stats_df.rename(columns={"index": "Team"})

    # Add team name (get from team abbreviation)
    stats_df.insert(loc=0, column="Name", value=list(map(
        util_scripts.get_team_name_from_abbreviation, stats_df.Team)))

    # Add position
    stats_df.insert(loc=2, column="Pos", value="DST")

    stats_df.name = "DST Stats"
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
    """
    reverses order of data relative to indices. Useful for swapping one team's
    offense with the opposing team's defense

    :param df: the DataFrame to parse
    :param header: the header to look for
    :param index: the index within the header (if multiple stats
                are under the same header but separated by a hyphen)
                Must be an integer or None
    :param reverse: whether to reverse the series (used for reversing offense / defense stats)
    :return: A Series of each player/team's stat
    """
    # get indices as list
    indices = list(series.index)
    
    # reverse indices
    indices = indices[::-1]
    
    # set series index
    series = series.set_axis(indices)
    
    # return reversed series
    return series


def _get_player_position_dict(soup):
    """
    Gets map of player ID -> position

    :param soup: BeautifulSoup object representing the HTML page
    :return: map of player ID -> position
    """
    home_table = soup.find("table", {"id": "home_snap_counts"})
    home_df = _parse_pfr_table(home_table)

    away_table = soup.find("table", {"id": "vis_snap_counts"})
    away_df = _parse_pfr_table(away_table)

    combined_df = pd.concat([home_df, away_df], axis=0, ignore_index=True)

    players_dict = dict(zip(combined_df["ID"], combined_df["_Pos"]))
    return players_dict


def _parse_pfr_table(table: bs4.element.Tag):
    """
    Parses a table from PFR in which data rows begin with a linked cell.
    Also inserts a column consisting of each player's ID
    Is able to ignore header rows in the middle of the table body

    :param table: the table to be parsed
    :return: A plaintext DataFrame of each player's stats
    """
    raw_df = util_scripts.read_raw_html_table(table)

    for index, row in raw_df.iterrows():
        # Drop row if it isn't a data row
        first_cell = row.values[0]
        links = first_cell.find_all("a")

        if len(links) == 1:
            continue
        else:
            raw_df = raw_df.drop(axis=0, index=index)

    # Add ID column
    raw_df.insert(loc=1, column="ID",
                  value=raw_df["_Player"].map(
                      lambda tag: tag["data-append-csv"]))

    # Get unformatted strings from tags
    # doesn't modify cell if it is already a string (e.g. the ID column)
    plaintext_df = raw_df.applymap(lambda cell: cell.get_text()
                                   if type(cell) is bs4.element.Tag else cell)
    plaintext_df = plaintext_df.reset_index(drop=True)

    return plaintext_df