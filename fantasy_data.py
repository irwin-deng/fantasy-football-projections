"""
File: fantasy_data.py
Description: Downloads Fantasy Football projections from fantasydata.com
"""

import time
import random
import requests
import pandas as pd
import importlib
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of
import traceback

import util_scripts
importlib.reload(util_scripts)


NEXT_REQUEST_TIME = 0


def scrape(year: int, week: int, webdriver: webdriver, playoffs=False,
           save_path="projections/projections_{year}_{week}_fantasydata.csv"):
    """
    scrapes projections from NFL.com.

    :param year: the year to be scraped
    :param week: the week to be scraped
    :return: A DataFrame of each player's projected stats
    """

    dfs = []

    # Keeps track of progress to be printed to the console
    ordinal_pos_indx = 1

    # Iterates through QB, RB, WR, TE, K, DST, DL, LB, DB, respectively
    for pos_indx in [2, 3, 4, 5, 6, 7, 9, 10, 11]:
        print(f"\tReading position {ordinal_pos_indx} / 9...")
        ordinal_pos_indx = ordinal_pos_indx + 1

        for team_indx in range(0, 32):
            df = _get_team_position_df(year=year, week=week, playoffs=playoffs,
                                       team_indx=team_indx, pos_indx=pos_indx,
                                       webdriver=webdriver)
            dfs.append(df)
        time.sleep(10 + random.uniform(0, 5))

    # Save to CSV
    save_path = save_path.format(year=year, week=week)

    merged_df = pd.concat(objs=dfs, join="outer")
    merged_df.to_csv(path_or_buf=save_path, index=False, na_rep='-')
    print(f"Year {year}, week {week} saved to {save_path}\n")

    return df


def _get_team_position_df(year: int, week: int, playoffs: bool, team_indx: int,
                          pos_indx: int, webdriver: webdriver):
    """
    gets DataFrame and then standardizes its headers

    :param week: the week to be scraped
    :param position: the position to be scraped. One of
                     [0: Offense, 7: Kicker, 8: Team Defense]
    :return: A DataFrame with standardized headers
    """
    # Expected labels and labels to change them to
    if pos_indx == 2:  # QB
        labels = {"TEAM": "Team", "POS": "Pos", "WK": "Week", "OPP": "Opp",
                  "PASSING_CMP": "Pass Comp", "PASSING_ATT": "Pass Att",
                  "PASSING_PCT": "Pass Comp Pct", "PASSING_YDS": "Pass Yd",
                  "PASSING_AVG": "Pass Avg", "PASSING_TD": "Pass Td",
                  "PASSING_INT": "Pass Int", "PASSING_RAT": "Pass Rate",
                  "RUSHING_ATT": "Rush Att", "RUSHING_YDS": "Rush Yd",
                  "RUSHING_AVG": "Rush Avg", "RUSHING_TD": "Rush Td",
                  "FPTS/G": "FPTPG", "FPTS": "FPT"}
    elif pos_indx == 3:  # RB
        labels = {"TEAM": "Team", "POS": "Pos", "WK": "Week", "OPP": "Opp",
                  "RUSHING_ATT": "Rush Att", "RUSHING_YDS": "Rush Yd",
                  "RUSHING_AVG": "Rush Avg", "RUSHING_TD": "Rush Td",
                  "RECEIVING_TGTS": "Rec Tgt", "RECEIVING_REC": "Rec",
                  "RECEIVING_YDS": "Rec Yd", "RECEIVING_TD": "Rec Td",
                  "FUMBLES_FUM": "Off Fum", "FUMBLES_LST": "Off Fum Lost",
                  "FPTS/G": "FPTPG", "FPTS": "FPT"}
    elif pos_indx in [4, 5]:  # WR, TE
        labels = {"TEAM": "Team", "POS": "Pos", "WK": "Week", "OPP": "Opp",
                  "RECEIVING_TGTS": "Rec Tgt", "RECEIVING_REC": "Rec",
                  "RECEIVING_PCT": "Rec Pct", "RECEIVING_YDS": "Rec Yd",
                  "RECEIVING_TD": "Rec Td", "RECEIVING_LNG": "Rec Long",
                  "RECEIVING_Y/T": "Rec YPT", "RECEIVING_Y/R": "Rec YPR",
                  "RUSHING_ATT": "Rush Att", "RUSHING_YDS": "Rush Yd",
                  "RUSHING_AVG": "Rush Avg", "RUSHING_TD": "Rush Td",
                  "FUMBLES_FUM": "Off Fum", "FUMBLES_LST": "Off Fum Lost",
                  "FPTS/G": "FPTPG", "FPTS": "FPT"}
    elif pos_indx == 6:  # K
        labels = {"TEAM": "Team", "POS": "Pos", "WK": "Week", "OPP": "Opp",
                  "FIELD GOALS_FG MADE": "FG Made",
                  "FIELD GOALS_FG ATT": "FG Att", "FIELD GOALS_PCT": "FG Pct",
                  "FIELD GOALS_LNG": "FG Long",
                  "EXTRA POINTS_XP MADE": "XP Made",
                  "EXTRA POINTS_XP ATT": "XP Att", "FPTS/G": "FPTPG",
                  "FPTS": "FPT"}
    elif pos_indx == 7:  # DST
        labels = {"TEAM": "Team", "POS": "Pos", "WK": "Week", "OPP": "Opp",
                  "TFL": "Tkl Loss", "SCK": "Def Sack",
                  "QB HIT": "Tkl QBHit", "INT": "Def Int",
                  "FR": "Def Fum Rec", "SFTY": "Def Saf", "DEF TD": "Def Td",
                  "RETURN TD": "Ret Td", "PTS ALLOWED": "Def Pt",
                  "FPTS/G": "FPTPG", "FPTS": "FPT"}
    elif pos_indx in [9, 10, 11]:  # IDP
        labels = {"TEAM": "Team", "POS": "Pos", "WK": "Week", "OPP": "Opp",
                  "SOLO": "Tkl Solo", "AST": "Tkl Ast", "TFL": "Tkl Loss",
                  "SCK": "Def Sack", "SCK YDS": "Def Sack Yd",
                  "QB HIT": "Def QBHit", "PASS DEF": "Def PD",
                  "INT": "Def Int", "FF": "Def FF", "FR": "Def Fum Rec",
                  "TD": "Def Td", "FPTS/G": "FPTPG", "FPTS": "FPT"}
    else:
        raise ValueError(f"Position is {pos_indx}, should be one of "
                         "[2, 3, 4, 5, 6, 7, 9, 10, 11]")

    if playoffs:
        seasontype = 3
    else:  # regular season
        seasontype = 1
    url = ("https://fantasydata.com/nfl/fantasy-football-weekly-projections?"
           f"position={pos_indx}&team={team_indx}&season={year}"
           f"&seasontype={seasontype}&scope=2&startweek={week}&endweek={week}")

    # Wait before scraping next URL
    global NEXT_REQUEST_TIME
    current_time = time.time()
    if current_time < NEXT_REQUEST_TIME:
        time.sleep(NEXT_REQUEST_TIME - current_time)

    # Try scraping URL
    while True:
        try:
            min_delay = 2 + random.uniform(0, 1)
            current_time = time.time()
            NEXT_REQUEST_TIME = current_time + min_delay

            webdriver.get(url)
            WebDriverWait(webdriver, timeout=30).until(
                staleness_of(webdriver.find_element_by_tag_name("html"))
            )
            break  # continue if successful
        except Exception:  # If unsuccessful, wait and try again
            print(traceback.format_exc())
            print("\nWaiting 30 min to retry...\n")
            time.sleep(1800)

    # Get page contents
    html = webdriver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    # Get headers   
    headers_table = soup.find("div", {"class": "k-grid-header"})
    headers_table = headers_table.find("table", {"role": "grid"})  
    headers_df = pd.read_html(str(headers_table))[0]

    # Merge multi-level headers if applicable:
    if type(headers_df.columns.values.tolist()[0]) == tuple:
        headers_df.columns = ['_'.join(col)
                                 for col in headers_df.columns.values]

    actual_labels = headers_df.columns.values.tolist()

    # Check that labels have not changed
    expected_labels = list(labels.keys())

    if len(expected_labels) != len(actual_labels):
        raise Exception(f"Expected labels for position {pos_indx}, team "
                        f"{team_indx} are {expected_labels}, got labels "
                        f"{actual_labels}")
    for indx in range(len(expected_labels)):
        if expected_labels[indx] not in actual_labels[indx].upper():
            raise Exception(
                f"Expected labels for position {pos_indx}, team {team_indx} "
                f"are {expected_labels}, got labels {actual_labels}")

    cleaned_labels = list(labels.values())

    proj_rows = []
    name_rows = []

    # read proj table
    proj_table = soup.find("section", {"class": "fantasy-stats-section"})
    proj_table = proj_table.find("div", {"class": "stats-grid-container"})
    proj_table = proj_table.find("div", {"class": "k-display-block"})
    proj_table = proj_table.find("div", {"class": "k-grid-content"})
    proj_table = proj_table.find("table", {"role": "grid"})    

    table_rows = proj_table.find("tbody", {"role": "rowgroup"}).find_all(
                                        "tr", {"class": "ng-scope"})

    # get rid of scrambled (paywalled) rows
    table_rows = [tag for tag in table_rows if 'scrambled' not in
                                                ''.join(tag['class'])]
    num_rows = len(table_rows)

    for table_row in table_rows:            
        row_cells = table_row.find_all("td", {"role": "gridcell"})
        row_cells = [cell.get_text() for cell in row_cells]

        proj_rows.append(row_cells)

    # read name table
    info_table = soup.find("section", {"class": "fantasy-stats-section"})
    info_table = info_table.find("div", {"class": "stats-grid-container"})
    info_table = info_table.find("div", {"class": "k-display-block"})
    info_table = info_table.find("div", {"class": "k-grid-content-locked"})
    info_table = info_table.find("table")

    table_rows = info_table.find("tbody")
    table_rows = table_rows.find_all("tr", {"class": "ng-scope"})

    for table_row in range(num_rows):
        row = table_rows[table_row]
        info_col = row.find("td", {"class": "align-left"})
        name = info_col.find("a", {"style": "font-weight:bold;"}).get_text()

        name_rows.append([name])

    # combine the two DataFrames
    name_df = pd.DataFrame(name_rows, columns=["Name"])
    proj_df = pd.DataFrame(proj_rows, columns=cleaned_labels)
    df = pd.concat([name_df, proj_df], axis=1)
    df.reset_index(drop=True)

    return df
