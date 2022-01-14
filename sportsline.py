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

    tables = soup.find_all("table")
    
    if len(tables) != 1:
        raise Exception("Expected one table, page has {num} tables".format(num=len(tables)))
    
    # Convert to DataFrame
    html_table = str(tables[0])
    
    df = pd.read_html(html_table)[0]
    
    # Save to CSV
    df.to_csv(path_or_buf=save_location.format(year=year, week=week), index=False, na_rep='-')
    
    return df