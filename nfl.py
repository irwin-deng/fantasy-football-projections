"""
File: nfl.py
Description: Downloads Fantasy Football projections from NFL.com
"""

import requests
import pandas as pd
import importlib
from bs4 import BeautifulSoup
import time
import random

import util_scripts
importlib.reload(util_scripts)


def scrape(year, week, save_path="projections_{year}_{week}_nfl.csv"):
    """
    scrapes projections from NFL.com.

    :param year: the current year
    :param week: the week to be scraped
    :return: A DataFrame of each player's projected stats
    """ 
    
    # Read offense pages
    off_df = _get_position_df(week=week, position=0)
    off_df.to_csv(path_or_buf="projections_{year}_{week}_nfl.csv".format(year = year, week=week), index=False)
    
    # Read kicker pages
    k_df = _get_position_df(week=week, position=7)
    k_df.to_csv(path_or_buf="projections_{year}_{week}_nfl.csv".format(year = year, week=week), index=False)
    
    # Read defense pages
    def_df = _get_position_df(week=week, position=8)
    def_df.to_csv(path_or_buf="projections_{year}_{week}_nfl.csv".format(year = year, week=week), index=False)
    
    # Save to CSV
    from functools import reduce
    df = reduce(lambda df1,df2: pd.merge(df1,df2,how="full"), [off_df, k_df, def_df])
    df = df.replace("-", 0)
    df.to_csv(path_or_buf=save_path.format(year=year, week=week), index=False, na_rep='-')
    
    return df
    
    
def _get_position_df(week, position):
    """
    gets DataFrame and then standardizes its headers

    :param week: the week to be scraped
    :param position: the position to be scraped. One of [0: Offense, 7: Kicker, 8: Team Defense]
    :return: A DataFrame with standardized headers
    """
    
    position = str(position)
    
    # Expected labels and labels to change them to
    if position == "0":  # Offense
        expected_labels = ["Player", "Opp", "Passing_Yds", "Passing_TD", "Passing_Int", "Rushing_Yds", "Rushing_TD",
                           "Receiving_Rec", "Receiving_Yds", "Receiving_TD", "Ret_TD", "Misc_FumTD", "Misc_2PT", "Fum_Lost", "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Team", "Opp", "Pass Yd", "Pass Td", "Pass Int",
                      "Rush Yd", "Rush Td", "Rec", "Rec Yd", "Rec Td", "Ret Td", "Fum Td", "2pt", "Fum Lost", "FPT"]
    elif position == "7": # Kicker
        expected_labels = ["Player", "Opp", "PAT_Made", "FG Made_0-19", "FG Made_20-29", "FG Made_30-39", "FG Made_40-49",
                           "FG Made_50+", "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Team", "Opp", "XP Made", "FG Made 0-19", "FG Made 20-29", "FG Made 30-39",
                      "FG Made 40-49", "FG Made 50+", "FPT"]
    elif position == "8": # Team Defense
        expected_labels = ["Team", "Opp", "Tackles_Sack", "Turnover_Int", "Turnover_Fum Rec", "Score_Saf", "Score_TD",
                          "Score_Def 2pt Ret", "Ret_TD", "Points_Pts Allow", "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Opp", "Def Sack", "Def Int", "Def Fum Rec", "Def Saf", "Def Td", "Def 2pt Ret",
                      "Ret Td", "Def Pt", "FPT"]
    else:
        raise ValueError("Position is {pos}, should be one of [0, 7, 8]".format(pos=position))
        
    df = pd.DataFrame()
    
    base_url = 'https://fantasy.nfl.com/research/projections?offset={offset}&position={position}&statCategory=projectedStats&statSeason=2021&statType=weekProjectedStats&statWeek={week}'
    
    # find number of players
    url = base_url.format(offset=1, position=position, week=week)
    page = requests.get(url)
    time.sleep(3 + random.uniform(0, 2))
    soup = BeautifulSoup(page.text, 'html.parser')
    num_players = int(soup.find("span", {"class": "paginationTitle"}).get_text().strip().split(" of ")[1])
    print("Position {position}: found {num} players".format(position=position, num=num_players))
    
    # iterate through each page of 25 players
    for offset in range(1, num_players+1, 25):
        url = base_url.format(offset=offset, position=position, week=week)
        page = requests.get(url)
        time.sleep(3 + random.uniform(0, 2))
        print("Scraping position {pos}, offset {offset}...".format(pos=position, offset=offset))
        soup = BeautifulSoup(page.text, 'html.parser')
        
        tables = soup.find_all("table")
        if len(tables) != 1:
            raise Exception("Expected one table, page has {num} tables".format(num=len(tables)))

        # Convert to DataFrame
        html_table = tables[0]

        page_df = util_scripts.read_raw_html_table(html_table)
        
        df = pd.concat([df, page_df], axis=0, ignore_index=True)
    
    # Check that the labels have not changed
    actual_labels = df.columns.values.tolist()
    if len(expected_labels) != len(actual_labels):
        raise Exception("Expected labels for position {pos} are {expected}, got labels {actual}".format(
            pos=position, expected=expected_labels, actual=actual_labels))
    for indx in range(len(expected_labels)):
        if expected_labels[indx].upper() not in actual_labels[indx].upper():
            raise Exception("Expected labels for position {pos} are {expected}, got labels {actual}".format(
                pos=position, expected=expected_labels, actual=actual_labels))
    
    
    # Split player cell to get name, pos, team    
    if position == "0":        
        df.insert(loc=1, column="Name", value="-")
        df.insert(loc=2, column="Pos", value="-")
        df.insert(loc=3, column="Team", value="-")
    elif position == "7":
        df.insert(loc=1, column="Name", value="-")
        df.insert(loc=2, column="Pos", value="K")
        df.insert(loc=3, column="Team", value="-")
    elif position == "8":
        df.insert(loc=1, column="Name", value="-")
        df.insert(loc=2, column="Pos", value="DST")
        
    
    for row_indx, row in df.iterrows():
            
        name = row[0].find("a", {"class": "playerName"}).get_text()
        df.at[row_indx, "Name"] = name
            
        if position == "0" or position == "7":
            pos_team = row[0].find("em").get_text()
            pos_team_split = pos_team.split(" - ")
            if len(pos_team_split) == 1: # If no team specified
                team = "FA"
                pos = pos_team_split[0]
            elif len(pos_team_split) == 2: # If team is specified
                pos, team = pos_team_split
            else:
                raise Exception("Expected 1 or 2 arguments, got {num} in {cell}".format(
                    num=len(pos_team_split), cell=str(row[0])))

            df.at[row_indx, "Team"] = team
            df.at[row_indx, "Pos"] = pos
            
            for i in range(4, len(row)):
                df.iat[row_indx, i] = row[i].get_text()
        elif position == "8":
            pos = "DST"
            df.at[row_indx, "Pos"] = pos
            
            for i in range(3, len(row)):
                df.iat[row_indx, i] = row[i].get_text()
        
    df = df.drop(df.columns[0], axis=1)
            
    # replce labels
    df = df.set_axis(new_labels, axis=1)
    return df
    