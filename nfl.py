"""
File: nfl.py
Description: Downloads Fantasy Football projections from NFL.com
"""

import requests
import pandas as pd
import util_scripts
from bs4 import BeautifulSoup
import time


def scrape(year, week, save_location="projections_{year}_{week}_nfl.csv"):
    """
    scrapes projections from NFL.com.

    :param year: the current year
    :param week: the week to be scraped
    :return: A DataFrame of each player's projected stats
    """ 
    
    off_df = _get_position_df(18, 7)
    
    off_df.to_csv(path_or_buf="projections_{year}_{week}_nfl.csv".format(year = year, week=week), index=False)
        
    """
    
    # Read defense pages
    for offset in range(1, 33, 25):
        url = 'https://fantasy.nfl.com/research/projections?offset={offset}&position=8&statCategory=projectedStats&statSeason=2021&statType=weekProjectedStats&statWeek={week}'.format(
                offset=offset, week=input_week)

        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        #print(soup)
        
        # Get contents
        table_rows = soup.find("table").find("tbody").find_all("tr")

        for table_row in table_rows:
            row = []
            
            name_info = table_row.find("td", {"class": "playerNameAndInfo first"})
            row.append(name_info.find("a").get_text())
            row.append("DST")
            row.append("-")  # will figure out team later
            for i in range(13):
                row.append("-")
            
            fpts = table_row.find("td", {"class": "stat projected numeric sorted last"})
            row.append(fpts.get_text())
            
            rows.append(row)
            
        time.sleep(1)

    print(rows)
    
    # Save to CSV
    df = pd.DataFrame(rows, columns=headers)
    df
    df.to_csv(path_or_buf="projections_{year}_{week}_nfl.csv".format(year = CURRENT_YEAR, week=input_week), index=False)
    
    """
    
    
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
                           "Receiving_Rec", "Receiving_Yds", "Receiving_TD", "Misc_FumTD", "Misc_2PT", "Fum_Lost", "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Team", "Opp", "Pass Yd", "Pass Td", "Pass Int",
                      "Rush Yd", "Rush Td", "Rec", "Rec Yd", "Rec Td", "Ret Td", "Fum Td", "2pt", "Fum Lost", "FPT"]
        max_offset = 500
    elif position == "7": # Kicker
        expected_labels = ["Player", "Opp", "PAT_Made", "FG Made_0-19", "FG Made_20-29", "FG Made_30-39", "FG Made_40-49",
                           "FG Made_50+", "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Team", "Opp", "XP Made", "FG Made 0-19", "FG Made 20-29", "FG Made 30-39",
                      "FG Made 40-49", "FG Made 50+", "FPT"]
    elif position == "8": # Team Defense
        expected_labels = ["Team", "Opp", "Tackles_Sack", "Turnover_Int", "Turnover_Fum Rec", "Score_Saf", "Score_TD",
                          "Score_Def 2pt Ret", "Ret TD", "Points_Pts Allow", "Fantasy_Points"]
        new_labels = ["Name", "Pos", "Opp", "Def Sack", "Def Int", "Def Fum Rec", "Def Saf", "Def Td", "Def 2pt Ret",
                      "Ret Td", "Def Pt", "FPT"]
    else:
        raise ValueError("Position is {pos}, should be one of [0, 7, 8]".format(pos=position))
        
    dfs = []   # list of dataframes, each of which has the 25 players displayed on a page
    
    base_url = 'https://fantasy.nfl.com/research/projections?offset={offset}&position={position}&statCategory=projectedStats&statSeason=2021&statType=weekProjectedStats&statWeek={week}'
    
    # find number of players
    url = base_url.format(offset=1, position=position, week=week)
    page = requests.get(url)
    time.sleep(5)
    soup = BeautifulSoup(page.text, 'html.parser')
    num_players = int(soup.find("span", {"class": "paginationTitle"}).get_text().strip().split(" of ")[1])
    print("Position {position}: found {num} players".format(position=position, num=num_players))
    
    # iterate through each page of 25 players
    for offset in range(1, num_players+1, 25):
        url = base_url.format(offset=offset, position=position, week=week)
        page = requests.get(url)
        time.sleep(1.2)
        print("Scraping position {pos}, offset {offset}...".format(pos=position, offset=offset))
        soup = BeautifulSoup(page.text, 'html.parser')
        
        tables = soup.find_all("table")
        if len(tables) != 1:
            raise Exception("Expected one table, page has {num} tables".format(num=len(tables)))

        # Convert to DataFrame
        html_table = str(tables[0])

        df = pd.read_html(html_table)[0]
        df.columns = df.columns.map("_".join)
        dfs.append(df)
        
    # df contains all players of that position
    df = pd.concat(dfs, axis=0)
    
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
        df.insert(loc=1, column="Pos", value="DST")
        
    if position == "0" or position == "7":
        for row_indx, row in df.iterrows():
            print(row)
            player_info = row[0].split(" - ")
            name_pos = player_info[0]
            team = player_info[1]
            
            last_space_indx = name_pos.rfind(" ")
            name = name_pos[0:last_space_indx]
            pos = name_pos[last_space_indx+1:]
            
            df.at[row_indx, "Name"] = name
            df.at[row_indx, "Pos"] = pos
            df.at[row_indx, "Team"] = team
                         
            df = df.drop(df.columns[0], axis=1)
            
    return df
    