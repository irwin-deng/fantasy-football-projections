"""
File: util_scripts.py
Description: Misc functions for performing useful tasks
"""
import pandas as pd

def read_raw_html_table(table):
    """
    :param table: HTML table represented as a BeautifulSoup object
    :return: A DataFrame corresponding to the HTML table
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
    #print(headers)
    
    
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