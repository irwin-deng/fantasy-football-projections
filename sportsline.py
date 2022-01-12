"""
File: sportsline.py
Description: Downloads Fantasy Football projections from SportsLine
"""

import requests
import pandas as pd
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

    # Get headers
    headers_elt = soup.find("table").find("thead").find_all("th")
    headers = []

    for header in headers_elt:
        headers.append(header.contents[0].contents[0])
    
    # Get contents
    table_rows = soup.find("table").find("tbody").find_all("tr")
    rows = []

    for table_row in table_rows:
        row = []

        row_cells = table_row.find_all("td")
        for row_cell in row_cells:
            row.append(row_cell.contents[0])

        rows.append(row)
    
    # Save to CSV
    df = pd.DataFrame(rows, columns=headers)
    df.to_csv(path_or_buf=save_location.format(year=year, week=week), index=False)
    
    return df