"""
File: nfl.py
Description: Downloads Fantasy Football projections from NFL.com
"""

import importlib
import time
import random
from functools import reduce
import pandas as pd
import traceback
import requests
from bs4 import BeautifulSoup

import util_scripts
importlib.reload(util_scripts)


def scrape(year, week, save_path="projections/projections_{year}_{week}_nfl.csv"):
    """
    scrapes projections from NFL.com.

    :param year: the current year
    :param week: the week to be scraped
    :return: A DataFrame of each player's projected stats
    """

    print(f"Reading year {year}, week {week}...")

    # Read offense pages
    off_df = _get_position_df(week=week, position=0)
    off_df.to_csv(path_or_buf=f"projections_{year}_{week}_nfl.csv",
                  index=False)

    # Read kicker pages
    k_df = _get_position_df(week=week, position=7)
    k_df.to_csv(path_or_buf=f"projections_{year}_{week}_nfl.csv",
                index=False)

    # Read defense pages
    def_df = _get_position_df(week=week, position=8)
    def_df.to_csv(path_or_buf=f"projections_{year}_{week}_nfl.csv",
                  index=False)

    # Save to CSV
    formatted_week = str(week).zfill(2)
    save_path = save_path.format(year=year, week=formatted_week)

    merged_df = reduce(lambda df1, df2: pd.merge(df1, df2, how="full"),
                       [off_df, k_df, def_df])
    merged_df = merged_df.replace("-", 0)
    merged_df.to_csv(path_or_buf=save_path,
                     index=False, na_rep='-')
    print(f"Year {year}, week {week} saved to {save_path}\n")

    return merged_df


def _get_position_df(week, position):
    """
    gets DataFrame and then standardizes its headers

    :param week: the week to be scraped
    :param position: the position to be scraped. One of [0: Offense, 7: Kicker, 8: Team Defense]
    :return: A DataFrame with standardized headers
    """

    position = int(position)

    # Expected labels and labels to change them to
    if position == 0:  # Offense
        expected_labels = ["Player", "Opp", "Passing_Yds", "Passing_TD",
                           "Passing_Int", "Rushing_Yds", "Rushing_TD",
                           "Receiving_Rec", "Receiving_Yds", "Receiving_TD",
                           "Ret_TD", "Misc_FumTD", "Misc_2PT", "Fum_Lost",
                           "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Team", "Opp", "Pass Yd", "Pass Td",
                      "Pass Int", "Rush Yd", "Rush Td", "Rec", "Rec Yd",
                      "Rec Td", "Ret Td", "Fum Td", "2pt", "Fum Lost", "FPT"]
    elif position == 7:  # Kicker
        expected_labels = ["Player", "Opp", "PAT_Made", "FG Made_0-19",
                           "FG Made_20-29", "FG Made_30-39", "FG Made_40-49",
                           "FG Made_50+", "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Team", "Opp", "XP Made", "FG Made 0-19",
                      "FG Made 20-29", "FG Made 30-39", "FG Made 40-49",
                      "FG Made 50+", "FPT"]
    elif position == 8:  # Team Defense
        expected_labels = ["Team", "Opp", "Tackles_Sack", "Turnover_Int",
                           "Turnover_Fum Rec", "Score_Saf", "Score_TD",
                           "Score_Def 2pt Ret", "Ret_TD", "Points_Pts Allow",
                           "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Opp", "Def Sack", "Def Int",
                      "Def Fum Rec", "Def Saf", "Def Td", "Def 2pt Ret",
                      "Ret Td", "Def Pt", "FPT"]
    else:
        raise ValueError(f"Position is {position}, should be one of [0, 7, 8]")

    merged_df = pd.DataFrame()

    base_url = ("https://fantasy.nfl.com/research/projections?offset={offset}"
                "&position={position}&statCategory=projectedStats"
                "&statSeason=2021&statType=weekProjectedStats&statWeek={week}")

    url = base_url.format(offset=1, position=position, week=week)

    # Try scraping URL
    while True:
        try:
            page = requests.get(url)
            break  # continue if successful
        except Exception:  # If unsuccessful, wait and try again
            print(traceback.format_exc())
            print("Waiting 30 min to retry...\n")
            time.sleep(1800)
    time.sleep(4 + random.uniform(0, 2))

    # find number of players
    soup = BeautifulSoup(page.text, 'html.parser')
    num_players = int(soup.find("span",
                      {"class": "paginationTitle"}).get_text().strip().split(
                      " of ")[1])
    print(f"Position {position}: found {num_players} players")

    # iterate through each page of 25 players
    for offset in range(1, num_players+1, 25):
        url = base_url.format(offset=offset, position=position, week=week)
        page = requests.get(url)
        time.sleep(3 + random.uniform(0, 2))
        print(f"Scraping position {position}, offset {offset}...")
        soup = BeautifulSoup(page.text, 'html.parser')

        tables = soup.find_all("table")
        if len(tables) != 1:
            raise Exception(f"Expected one table, "
                            f"page has {len(tables)} tables")

        # Convert to DataFrame
        html_table = tables[0]
        page_df = util_scripts.read_raw_html_table(html_table)
        merged_df = pd.concat([merged_df, page_df], axis=0, ignore_index=True)

    # Check that the labels have not changed
    actual_labels = merged_df.columns.values.tolist()
    if len(expected_labels) != len(actual_labels):
        raise Exception(f"Expected labels for position {position} are "
                        f"{expected_labels}, got labels {actual_labels}")
    for _, (expected_label, actual_label) in zip(
            expected_labels, actual_labels):
        if expected_label.upper() not in actual_label.upper():
            raise Exception(f"Expected labels for position {position} are "
                            f"{expected_labels}, got labels {actual_labels}")

    # Split player cell to get name, pos, team
    if position == "0":
        merged_df.insert(loc=1, column="Name", value="-")
        merged_df.insert(loc=2, column="Pos", value="-")
        merged_df.insert(loc=3, column="Team", value="-")
    elif position == "7":
        merged_df.insert(loc=1, column="Name", value="-")
        merged_df.insert(loc=2, column="Pos", value="K")
        merged_df.insert(loc=3, column="Team", value="-")
    elif position == "8":
        merged_df.insert(loc=1, column="Name", value="-")
        merged_df.insert(loc=2, column="Pos", value="DST")

    for row_indx, row in merged_df.iterrows():

        name = row[0].find("a", {"class": "playerName"}).get_text()
        merged_df.at[row_indx, "Name"] = name

        if position == "0" or position == "7":
            pos_team = row[0].find("em").get_text()
            pos_team_split = pos_team.split(" - ")
            if len(pos_team_split) == 1:  # If no team specified
                team = "FA"
                pos = pos_team_split[0]
            elif len(pos_team_split) == 2:  # If team is specified
                pos, team = pos_team_split
            else:
                raise Exception(f"Expected 1 or 2 arguments, got "
                                f"{len(pos_team_split)} in {str(row[0])}")

            merged_df.at[row_indx, "Team"] = team
            merged_df.at[row_indx, "Pos"] = pos

            for i in range(4, len(row)):
                merged_df.iat[row_indx, i] = row[i].get_text()
        elif position == "8":
            pos = "DST"
            merged_df.at[row_indx, "Pos"] = pos

            for i in range(3, len(row)):
                merged_df.iat[row_indx, i] = row[i].get_text()

    merged_df = merged_df.drop(merged_df.columns[0], axis=1)

    # replce labels
    merged_df = merged_df.set_axis(new_labels, axis=1)
    return merged_df
