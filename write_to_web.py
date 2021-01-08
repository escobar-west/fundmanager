from client import *
import pandas as pd
import mysql.connector
import json
import os

bal = getBalances().groupby('asset').balance.sum()
prices = getPrices(bal.index.tolist())

db_cred = {'host': os.getenv('FUND_DB_HOST'),
                'user': os.getenv('FUND_DB_USER'),
                'password': os.getenv('FUND_DB_PWORD'),
                'db': os.getenv('FUND_DB')}


cnx = mysql.connector.connect(**db_cred)
cursor = cnx.cursor()

add_idx = """INSERT INTO port_data
             (balance, price)
             VALUES (%s, %s);"""

data_idx = (json.dumps(bal.to_dict()), json.dumps(prices))

cursor.execute(add_idx, data_idx)

