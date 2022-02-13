"""
File: sportsline.py
Description: Downloads Fantasy Football projections from SportsLine
"""

import importlib
import time
from functools import reduce
import requests
import pandas as pd
from bs4 import BeautifulSoup

import util_scripts
importlib.reload(util_scripts)


def scrape(year, week, 
           save_path="projections/projections_{year}_{week}_footballguys.csv"):
    """
    scrapes projections from FootballGuys

    :param year: the current year
    :param week: the week to be scraped
    :return: A DataFrame of each player's projected stats
    """

    print(f"Reading year {year}, week {week}...")

    # Read qb page
    qb_df = _get_position_df(week=week, position="qb")
    time.sleep(1)

    # Read offensive flex page
    rec_df = _get_position_df(week=week, position="flex")
    time.sleep(1)

    # Read kicker page
    k_df = _get_position_df(week=week, position="pk")
    time.sleep(1)

    # Read team defense page
    td_df = _get_position_df(week=week, position="td")
    time.sleep(1)

    # Read individual defensive player page
    idp_df = _get_position_df(week=week, position="flexidp")

    # Save to CSV
    formatted_week = str(week).zfill(2)
    save_path = save_path.format(year=year, week=formatted_week)

    merged_df = reduce(lambda df1, df2: pd.merge(df1, df2, how="outer"),
                       [qb_df, rec_df, k_df, td_df, idp_df])
    merged_df.to_csv(path_or_buf=save_path, index=False, na_rep='-')
    print(f"Year {year}, week {week} saved to {save_path}\n")

    return merged_df


def _get_position_df(week, position):
    """
    gets DataFrame and then standardizes its headers

    :param week: the week to be scraped
    :param position: the position to be scraped
    :return: A DataFrame with standardized headers
    """

    # Expected labels and labels to change them to
    if position == "qb":
        expected_labels = ["NAME", "TEAM", "OPP", "CMP", "ATT", "PYD", "PTD",
                           "INT", "RSH", "YD", "TD", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Pass Comp", "Pass Att",
                      "Pass Yd", "Pass Td", "Pass Int", "Rush Att", "Rush Yd",
                      "Rush Td", "FPT"]
    elif position == "flex":
        expected_labels = ["NAME", "TEAM", "OPP", "POS", "RSH", "YD", "TD",
                           "REC", "YD.1", "TD.1", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Rush Att", "Rush Yd",
                      "Rush Td", "Rec", "Rec Yd", "Rec Td", "FPT"]
    elif position == "pk":
        expected_labels = ["NAME", "TEAM", "OPP", "FGM", "FGA", "XPM", "XPA",
                           "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "FG Made Total", "FG Att",
                      "XP Made", "XP Att", "FPT"]
    elif position == "td":
        expected_labels = ["NAME", "TEAM", "OPP", "SCK", "FR", "INT", "TD",
                           "YDALLOW", "PTALLOW", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Def Sack", "Def FR",
                      "Def Int", "Def TD", "Def Yd", "Def Pt", "FPT"]
    elif position == "flexidp":
        expected_labels = ["NAME", "TEAM", "OPP", "POS", "TKL", "AST", "SCK",
                           "FF", "FR", "INT", "PD", "TD", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Def Tkl", "Def Ast",
                      "Def Sack", "Def FF", "Def FR", "Def Int", "Def PD",
                      "Def TD", "FPT"]
    else:
        raise ValueError(f"Position is {position}, should be one of "
                          "[qb, flex, pk, td, flexidp]")

    # Get data from site
    url = (f"https://www.footballguys.com/projections/inseason?pos={position}"
           f"&who=996&week={week}")

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    tables = soup.select("table.table.data")

    if len(tables) != 1:
        raise Exception(f"Expected one table, page has {len(tables)} tables")

    # Convert to DataFrame
    html_table = str(tables[0])

    position_df = pd.read_html(html_table)[0]

    # the first col is indices. The last col is blank. Drop those
    position_df = position_df.drop(position_df.columns[0], axis=1)
    position_df = position_df.drop(position_df.columns[-1], axis=1)

    # Check that labels have not changed
    actual_labels = position_df.columns.values.tolist()
    if len(expected_labels) != len(actual_labels):
        raise Exception(f"Expected labels for position {position} are "
                        f"{expected_labels}, got labels {actual_labels}")
    for _ , (expected_label, actual_label) in enumerate(
            zip(expected_labels, actual_labels)):
        if expected_label != actual_label.upper():
            raise Exception(f"Expected labels for position {position} are "
                            f"{expected_labels}, got labels {actual_labels}")

    # Add position column to players whose position isn't specified in their table
    if position == "qb":
        position_df.insert(3, "Pos", "QB")
    elif position == "pk":
        position_df.insert(3, "Pos", "K")
    elif position == "td":
        position_df.insert(3, "Pos", "DST")

    # replce labels
    position_df = position_df.set_axis(new_labels, axis=1)
    return position_df
