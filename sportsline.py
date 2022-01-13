"""
File: sportsline.py
Description: Downloads Fantasy Football projections from SportsLine
"""

import requests
import pandas as pd
import util_scripts
from bs4 import BeautifulSoup

def scrape(year, week, save_location="projections_{year}_{week}_sportsline.csv"):
    """
    scrapes projections from SportsLine. Note that changing the year and week
    parameters have no effect on the data that is scraped, since SportsLine
    only stores the current week's data.

    :param year: the current year
    :param week: the current week
    :return: A DataFrame of each player's projected stats
    """ 
    
    # Read page
    url = 'https://www.sportsline.com/nfl/expert-projections/simulation/'

    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    table = soup.find("table")
    
    # Convert to DataFrame
    df = util_scripts.get_dataframe_from_simple_table(table)
    
    # Save to CSV
    df.to_csv(path_or_buf=save_location.format(year=year, week=week), index=False, na_rep='-')
    
    return df