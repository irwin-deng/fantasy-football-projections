"""
File: util_scripts.py
Description: Misc functions for performing useful tasks
"""
import pandas as pd
import bs4

def set_df_headers(df: pd.DataFrame, labels: dict, check:bool=True,
                   check_order:bool=True):
    """
    Renames a DataFrame's columns. If 'check' is True, then it will check
    that each key in the dict is in the old DataFrame. If 'check_order' is
    True, then it will check that the order of the keys in dict is the same
    as the order of the headers in the old DataFrame.

    :param df: The DataFrame whose headers to change
    :param labels: a dict mapping old headers to new headers
    :param check: whether to check that all keys in the dict exist in df
    :param check_order: whether to check that all keys in the dict exist in df
                and in the same order
    :return: A DataFrame in which entries are BeautifulSoup objects
    """ 
    expected_labels = list(labels.keys())
    new_labels = list(labels.values())
    actual_labels = df.columns.values.tolist()

    # Check that the labels have not changed
    if check_order:
        if str(expected_labels) != str(actual_labels):
            raise Exception(f"Expected labels for dataframe {df.name} are"
                            f"{expected_labels}, got labels {actual_labels}")
    elif check:
        if len(expected_labels) != len(actual_labels):
            raise Exception(f"Expected labels for dataframe {df.name} are"
                            f"{expected_labels}, got labels {actual_labels}")
        for indx in range(len(expected_labels)):
            if expected_labels[indx].upper() not in actual_labels[indx].upper():
                raise Exception(f"Expected labels for dataframe {df.name} are"
                              f"{expected_labels}, got labels {actual_labels}")

    # replace labels:
    df = df.rename(columns=labels)

    return df

def read_raw_html_table(table: bs4.element.Tag):
    """
    :param table: HTML table represented as a BeautifulSoup object
    :return: A DataFrame in which entries are BeautifulSoup objects
    """ 
    
    # Get headers
    table_head = table.find("thead")
    header_rows = table_head.find_all("tr")
    
    headers = []
    
    for header_row in header_rows:
        header_row_list = read_row(header_row)
        
        #print(header_row_list)
        
        for i in range(len(header_row_list)):
            header_row_list[i] = header_row_list[i].get_text()
        
        if len(headers) == 0:
            headers = header_row_list
            #print(headers)
        else:
            #print(header_row_list)
            # combine multi-level headers
            if len(headers) != len(header_row_list):
                raise Exception("Lengths of lists aren't the same: {len1} vs {len2}".format(
                    len1=len(headers), len2=len(header_row_list)))
            
            for i in range(len(headers)):
                headers[i] = headers[i] + "_" + header_row_list[i]
    
    # Rename duplicate headers
    header_counts = {}
    for index in range(len(headers)):
        header = headers[index]

        if header not in header_counts:
            header_counts[header] = 1
        else:
            count = header_counts[header]
            new_count = count + 1
            header_counts[header] = new_count
            headers[index] = header + str(new_count)
    
    # Get contents
    table_body = table.find("tbody")
    table_rows = table_body.find_all("tr")
    rows = []

    for table_row in table_rows:
        row = read_row(table_row)
        #for i in range(len(row)):
        #    row[i] = str(row[i])

        rows.append(row)
    
    # Convert to DataFrame and return
    df = pd.DataFrame(rows, columns=headers)
    
    return df

def read_row(row):
    """
    :param table: HTML <tr> represented as a BeautifulSoup object
    :return: A list of raw BeautifulSoup objects corresponding to each cell in the table
    """ 
    
    cells_list = []
    cells = row.find_all(["th", "td"])
    # print(cells)
    
    for cell in cells:
        #print("here")
        colspan = 1
        # Address multiple column cells
        if cell.has_attr("colspan"):
            colspan = int(cell["colspan"])
            
        for col in range(colspan):
            cells_list.append(cell)
            
    return cells_list

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

def get_team_name_from_abbreviation(abbreviation):
    abbreviations = {
                        "ARI": "Cardinals", "ARZ": "Cardinals",
                        "ATL": "Falcons",
                        "BAL": "Ravens",
                        "BUF": "Bills",
                        "CAR": "Panthers",
                        "CHI": "Bears",
                        "CIN": "Bengals",
                        "CLE": "Browns", "CLV": "Browns",
                        "DAL": "Cowboys",
                        "DEN": "Broncos",
                        "DET": "Lions",
                        "GNB": "Packers", "GB": "Packers",
                        "HOU": "Texans", "HST": "Texans",
                        "IND": "Colts",
                        "JAX": "Jaguars", "JAC": "Jaguars",
                        "KAN": "Chiefs",
                        "LVR": "Raiders", "LV": "Raiders", "OAK": "Raiders",
                        "LAC": "Chargers", "SDG": "Chargers", "SD": "Chargers",
                        "LAR": "Rams", "STL": "Rams",
                        "MIA": "Dolphins",
                        "MIN": "Vikings",
                        "NWE": "Patriots", "NE": "Patriots", 
                        "NOR": "Saints", "NO": "Saints",
                        "NYG": "Giants",
                        "NYJ": "Jets",
                        "PHI": "Eagles",
                        "PIT": "Steelers",
                        "SFO": "49ers", "SF": "49ers",
                        "SEA": "Seahawks",
                        "TAM": "Buccaneers", "TB": "Buccaneers",
                        "TEN": "Titans",
                        "WAS": "Football Team"
                    }

    return abbreviations[abbreviation]