# -*- coding: utf-8 -*-
"""
Created on Sun Aug 25 09:44:32 2024

@author: kiennn
"""

import os
import pandas as pd
from bs4 import BeautifulSoup  
import logging
import requests
import re
#from newspaper import Article
#from newspaper import fulltext
from tqdm import tqdm
from selenium import webdriver


logging.basicConfig(filename="crawl.log",level=logging.ERROR)
public_company_list = pd.read_excel("public_company_list.xlsx")

def get_new_data(symbol):
    r = requests.get('http://s.cafef.vn/Ajax/Events_RelatedNews_New.aspx?symbol=' + str(symbol) + '&floorID=0&configID=0&PageIndex=1&PageSize=10000&Type=2')
    soup = BeautifulSoup(r.content, "html.parser")
    data = soup.find("ul", {"class": "News_Title_Link"})
    raw = data.find_all('li')
    data_dicts = []
    for row in raw:
        row_dict = {}
        row_dict['newsdate'] = row.span.text
        row_dict['title'] = row.a.text
        row_dict['url']  = "http://s.cafef.vn/" + str(row.a['href'])
        row_dict['Ma CK'] = str(symbol)
        data_dicts.append(row_dict)
    return data_dicts


all_datas = pd.DataFrame()
for ticker in tqdm(public_company_list['Ma CK'].values):
    tickernews = pd.DataFrame(get_new_data(ticker))
    all_datas = pd.concat([all_datas, tickernews], ignore_index=True)

all_news = pd.read_excel('ctc_data.xlsx')
all_news = pd.concat([all_datas, all_news], ignore_index=True)
all_news = all_news.drop_duplicates()
    
all_news.to_excel('news_data.xlsx',index=False)
'''cong ty con'''
def get_ctc(symbol):
    ctc = requests.get('https://s.cafef.vn/Ajax/CongTy/CongTyCon.aspx?sym=' + str(symbol))
    soup = BeautifulSoup(ctc.content, "html.parser")
    rows = soup.find_all('tr', style=lambda x: x and 'font-weight:normal;' in x)
    data = []
    for row in rows:
        cols = row.find_all('td')
        company_name = cols[0].text.strip()
        first_value = cols[1].text.strip().replace(",", "")
        second_value = cols[2].text.strip().replace(",", "")
        ownership = cols[3].text.strip()
        
        # Append to the data list
        data.append([company_name, first_value, second_value, ownership])
    
    # Create a DataFrame
    ctcdf = pd.DataFrame(data, columns=['Company Name', 'Von dieu le', 'Von thuc gop', 'Ownership Percentage'])
    ctcdf['Ma CK'] = str(symbol)
    return ctcdf
all_ctc_datas = pd.DataFrame()
for ticker in tqdm(public_company_list['Ma CK'].values):
    ctc_info = pd.DataFrame(get_ctc(ticker))
    all_ctc_datas = pd.concat([all_ctc_datas, ctc_info], ignore_index=True)
    
#mo file cu ra va ghep vao
all_ctc = pd.read_excel('ctc_data.xlsx')
all_ctc = pd.concat([all_ctc_datas, all_ctc], ignore_index=True)
all_ctc = all_ctc.drop_duplicates()

all_ctc.to_excel('ctc_data.xlsx',index=False)


''' tai cac bao cao phan tich'''
final_df = pd.DataFrame()
browser = webdriver.Chrome()
browser.maximize_window()
browser.get('https://s.cafef.vn/phan-tich-bao-cao.chn')

html = browser.page_source
soup = BeautifulSoup(html, 'html.parser')
table = soup.find("table", {"id": "tblGridData"})
# Extract the header row
header_row = table.find("tr")
headers = [th.get_text(strip=True) for th in header_row.find_all("td")]
headers.append("File Name")
# Extract the data rows
data_rows = []
for row in table.find_all("tr")[1:]:  # Skip the header row
    columns = row.find_all("td")
    data = [col.get_text(strip=True) for col in columns]
    onclick_text = columns[4].find("a")["onclick"] if columns[4].find("a") and columns[4].find("a").has_attr("onclick") else None
    file_name = None
    if onclick_text:
        match = re.search(r"'([^']+\.pdf)'", onclick_text)
        if match:
            file_name = match.group(1)
    data.append(file_name)
    data_rows.append(data)

# Create a pandas DataFrame from the data
df = pd.DataFrame(data_rows, columns=headers)
df['Link'] = 'https://cafef1.mediacdn.vn/Images/Uploaded/DuLieuDownload/PhanTichBaoCao/' + df['File Name']
final_df = pd.concat([final_df, df], ignore_index=True)
bc_df = pd.read_excel('DSbaocao.xlsx')
bc_df = pd.concat([final_df, bc_df], ignore_index=True)
bc_df = bc_df.drop_duplicates()
bc_df.to_excel('DSbaocao.xlsx',index=None)

pdf_dir = "downloaded_pdfs"
if not os.path.exists(pdf_dir):
    os.makedirs(pdf_dir)

# Loop through the DataFrame and download each PDF
for index, row in bc_df.iterrows():
    pdf_link = row['Link']  # The URL for the PDF
    file_name = row['File Name']  # The name of the PDF file
    
    if pdf_link and file_name:  # Check if both PDF link and file name are not None
        # Construct the full path for saving the PDF
        file_path = os.path.join(pdf_dir, file_name)
        
        # Download the PDF
        response = requests.get(pdf_link)
        
        if response.status_code == 200:  # Check if the request was successful
            # Write the content to a file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {file_name}")
        else:
            print(f"Failed to download {file_name}")
            
