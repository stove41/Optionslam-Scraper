import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import numpy as np
import sys

def slam_scraper(ticker):
	#create session to make login persistent
	session = requests.session()
	#Scrape login page
	login_url = 'https://www.optionslam.com/accounts/login/'
	response = session.get(login_url)
	content = response.content
	soup = BeautifulSoup(content, 'html.parser')
	#retrieve authentication token from html
	auth_token = soup.find(attrs={'name': 'csrfmiddlewaretoken'})['value']

	#Create login data
	payload = {
		'username': '-------',
		'password': '-------',
		'csrfmiddlewaretoken': auth_token
	}

	#Use post to send login info
	results = session.post(login_url, data = payload, headers =
						   dict(referer=login_url))
	#Use f strings to bring in command line arg to the url
	stock = ticker
	target_url = f'https://www.optionslam.com/earnings/stocks/{stock}'
	#Scrape stock page
	target_result = session.get(target_url, headers = dict(referer = target_url))
	target_content = target_result.content
	target_soup = BeautifulSoup(target_content, 'html.parser')
	#get table rows
	stockrows = target_soup.find_all(True, {'class':['stockrow1', 'stockrow2']})
	#Parse rows into list of lists with each list being a row of the table.
	rows = []
	for j in range(len(stockrows)):
		td = stockrows[j].find_all('td')
		row = [k.text for k in td]
		for i in range(len(row)):
			row[i] = re.sub('\s+','', row[i])
		rows.append(row)
	return rows


def formatting(raw_table):
	rows = raw_table
	for i in range(len(rows)):
		rows[i] = [row for row in rows[i] if row]
		if(rows[i][1][0] != '$'):
			rows[i] = [rows[i][0], rows[i][1], '','','', '', '', '', '', rows[i][2],
					   rows[i][3], rows[i][4], rows[i][5]]
	#Transpose table to format all dates at once.
	rows = np.transpose(rows)
	#Create AC/BO list from date column and remove AC/BO from date.
	ac_bo = [text[-2:] for text in rows[0]]
	rows[0] = [text[:-2] for text in rows[0]]

	#Convert date strings to datetime object based on formatting of the string.
	for i in range(len(rows[0])):
		if(rows[0][i][3] == '.'):
			rows[0][i] = pd.to_datetime(rows[0][i], format = '%b.%d,%Y')
		else:
			rows[0][i] = pd.to_datetime(rows[0][i], format = '%B%d,%Y')
	#Transpose rows back
	rows = np.transpose(rows)
	#Create dataframe
	df = pd.DataFrame(rows)
	#Make new column from ac_bo list
	df['ac_bo'] = ac_bo
	#create list of column names with no caps or spaces
	cols = ['earnings_date', 'pre_earnings_close', 'post_earnings_open', 'open',
			'high', 'low', 'close', 'close_%', 'max_%', 'mean', 'median', 'mean_raw',
			'median_raw', 'ac_bo']
	#Set new col names.
	df.columns = cols
	
	#remove $ and convert to numeric type for appropriate columns. Also handles "tobecalculateds", "None%" and "-None%" in cells.
	for i in range(len(df['earnings_date'])):
		for j in [1,3,4,5,6]:
			if(df.iloc[i,j] == 'ToBeCalculatedAfterEarningsDate' or df.iloc[i,j] == 'None%' or df.iloc[i,j] == '-None%'):
				continue
			else:
				df.iloc[i,j] = pd.to_numeric(re.sub('\$','', df.iloc[i,j]))
	#Remove % and change to numeric for appropriate columns. Also handles "tobecalculateds", "None%" and "-None%" in cells.
	for k in range(len(df['earnings_date'])):
		for l in [2,7,8,9,10,11,12]:
			if(df.iloc[k,l] == 'ToBeCalculatedAfterEarningsDate' or df.iloc[k,l] == 'None%' or df.iloc[k,l] == '-None%'):
				continue
			else:
				df.iloc[k,l] = pd.to_numeric(re.sub('\%', '', df.iloc[k,l]))
				df.iloc[k,l] = df.iloc[k,l] / 100
	#returns dataframe
	print(df)
	return df


#Run program from command line with ticker as first argument. >python optionslam_scraper.py AAPL. This wont do much since it doesnt output anything externally. it just returns a dataframe. Let me know if you want me to make it save the table to a file of some kind.

#Otherwise run it in the ide by just changing the argument for slam_scraper to the ticker string, 'AAPL' for instance. Then you can do whatever you want with the resulting dataframe.
if __name__ == "__main__":
	[ticker] = sys.argv[1:]# pylint: disable=unbalanced-tuple-unpacking
	raw_table = slam_scraper(ticker)
	output = formatting(raw_table)
	
	
##############################################	
#Mikes code here

