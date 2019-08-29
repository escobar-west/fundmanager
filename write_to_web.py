import pandas as pd
import mysql.connector
from core import Fund

fund = Fund()
config = ConfigParser()
config.read(join(dirname(abspath(__file__)), 'config/config.ini'))

db_cred = {'host': config['DB']['host'],
                'user': config['DB']['user'],
                'password': config['DB']['password'],
                'db': config['DB']['database']}

cnx = mysql.connector.connect(**db_cred)
cursor = cnx.cursor()

add_idx = """INSERT INTO fund_data
             (idxusd, idxbtc, weights)
             VALUES (%s, %s, %s);"""

weights = fund.balance.weights.round(4)
del weights['total']
weights = weights[weights > 0]
data_idx = (fund.getIdx('USD'), fund.getIdx('BTC'), weights.to_json())

cursor.execute(add_idx, data_idx)

