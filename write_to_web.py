import pandas as pd
import mysql.connector
from core import Fund

fund = Fund()
db_cred = {'host':'victorsuriel.com',
                'user':'victorsu_a',
                'password':'FUCK!heart@2292#mys',
                'db':'victorsu_fund'}

cnx = mysql.connector.connect(**db_cred)
cursor = cnx.cursor()

add_idx = """INSERT INTO fund_data
             (idxusd, idxbtc, weights)
             VALUES (%s, %s, %s);"""

weights = fund.balance.weights.round(4)
weights = weights[weights > 0]
data_idx = (fund.getIdx('USD'), fund.getIdx('BTC'), weights.to_json())

cursor.execute(add_idx, data_idx)

