"""
File: sportsline.py
Description: Downloads Fantasy Football projections from SportsLine
"""

import requests
import pandas as pd
import util_scripts
from bs4 import BeautifulSoup
import time


def scrape(year, week, save_location="projections_{year}_{week}_footballguys.csv"):
    """
    scrapes projections from FootballGuys

    :param year: the current year
    :param week: the week to be scraped
    :return: A DataFrame of each player's projected stats
    """ 
    
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
    from functools import reduce
    df = reduce(lambda df1,df2: pd.merge(df1,df2,how="outer"), [qb_df, rec_df, k_df, td_df, idp_df])
    df.to_csv(path_or_buf=save_location.format(year=year, week=week), index=False, na_rep='-')
    
    return df


def _get_position_df(week, position):
    """
    gets DataFrame and then standardizes its headers

    :param week: the week to be scraped
    :param position: the position to be scraped
    :return: A DataFrame with standardized headers
    """
    
    # Expected labels and labels to change them to
    if position == "qb":
        expected_labels = ["NAME", "TEAM", "OPP", "CMP", "ATT", "PYD", "PTD", "INT", "RSH", "YD", "TD", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Pass Comp", "Pass Att", "Pass Yd", "Pass Td", "Pass Int",
                      "Rush Att", "Rush Yd", "Rush Td", "FPT"]
    elif position == "flex":
        expected_labels = ["NAME", "TEAM", "OPP", "POS", "RSH", "YD", "TD", "REC", "YD.1", "TD.1", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Rush Att", "Rush Yd", "Rush Td", "Rec", "Rec Yd", "Rec Td", "FPT"]
    elif position == "pk":
        expected_labels = ["NAME", "TEAM", "OPP", "FGM", "FGA", "XPM", "XPA", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "FG Made Total", "FG Att", "XP Made", "XP Att", "FPT"]
    elif position == "td":
        expected_labels = ["NAME", "TEAM", "OPP", "SCK", "FR", "INT", "TD", "YDALLOW", "PTALLOW", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Def Sack", "Def FR", "Def Int",
                      "Def TD", "Def Yd", "Def Pt", "FPT"]
    elif position == "flexidp":
        expected_labels = ["NAME", "TEAM", "OPP", "POS", "TKL", "AST", "SCK", "FF", "FR", "INT", "PD", "TD", "FPT"]
        new_labels = ["Name", "Team", "Opp", "Pos", "Def Tkl", "Def Ast", "Def Sack",
                      "Def FF", "Def FR", "Def Int", "Def PD", "Def TD", "FPT"]
    else:
        raise ValueError("Position is {pos}, should be one of [qb, flex, pk, td, flexidp]".format(pos=position))
        
        
    # Get data from site
    url = 'https://www.footballguys.com/projections/inseason?pos={position}&who=996&week={week}'.format(position=position, week=week)

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    
    tables = soup.select("table.table.data")
    
    if len(tables) != 1:
        raise Exception("Expected one table, page has {num} tables".format(num=len(tables)))
    
    # Convert to DataFrame
    html_table = str(tables[0])
    
    df = pd.read_html(html_table)[0]
    
    # the first col is indices. The last col is blank. Drop those
    df = df.drop(df.columns[0], axis=1)
    df = df.drop(df.columns[-1], axis=1)
    
        
    # Check that labels have not changed
    actual_labels = df.columns.values.tolist()
    if len(expected_labels) != len(actual_labels):
        raise Exception("Expected labels for position {pos} are {expected}, got labels {actual}".format(
            pos=position, expected=expected_labels, actual=actual_labels))
    for indx in range(len(expected_labels)):
        if expected_labels[indx] != actual_labels[indx].upper():
            raise Exception("Expected labels for position {pos} are {expected}, got labels {actual}".format(
                pos=position, expected=expected_labels, actual=actual_labels))
    
    # Add position column to players whose position isn't specified in their table
    if position == "qb":
        df.insert(3, "Pos", "QB")
    elif position == "pk":
        df.insert(3, "Pos", "K")
    elif position == "td":
        df.insert(3, "Pos", "DST")
    
    # replce labels
    df = df.set_axis(new_labels, axis=1)
    return df