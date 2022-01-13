"""
File: util_scripts.py
Description: Misc functions for performing useful tasks
"""
import pandas as pd

def get_dataframe_from_simple_table(table):
    """
    :param table: HTML table represented as a string
    :return: A DataFrame corresponding to the HTML table
    """ 
    
    # Get headers
    table_head = table.find("thead")
    headers_elt = table_head.find_all("th")
    headers = []

    for header in headers_elt:
        headers.append(header.get_text())
    
    # Get contents
    table_body = table.find("tbody")
    table_rows = table_body.find_all("tr")
    rows = []

    for table_row in table_rows:
        row = []

        row_cells = table_row.find_all("td")
        for row_cell in row_cells:
            row.append(row_cell.get_text())

        rows.append(row)
    
    # Convert to DataFrame and return
    df = pd.DataFrame(rows, columns=headers)
    return df

def get_dataframe_from_table_tr_headers(table):
    """
    :param table: HTML table represented as a string, with the header row being <tr>
    :return: A DataFrame corresponding to the HTML table
    """ 
    
    table_rows = table.find_all("tr")
    
    # Get headers
    headers = []
    for header in table_rows[0]:
        headers.append(header.get_text())
        
    # Get contents
    rows = []
    for row_indx in range(1, len(table_rows)):
        row = []
        
        table_row = table_rows[row_indx]
        row_cells = table_row.find_all("td")
            
        for row_cell in row_cells:
            row.append(row_cell.get_text())

        rows.append(row)
    
    # Convert to DataFrame and return
    df = pd.DataFrame(rows, columns=headers)
    return df