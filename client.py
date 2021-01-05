import hashlib
import hmac
import base64
import pandas as pd
from configparser import ConfigParser
from os.path import join, abspath, dirname
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
from balance_functions import BALANCE_FUNCTION_DICT

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE
import os


def getPrices(asset_list):
    if not isinstance(asset_list, list):
        asset_list = [asset_list]

    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': os.getenv('CMC_API_KEY')
    }
    with Session() as session:
        session.headers.update(headers)
        response = session.get('https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=' + ','.join(asset_list))
    data = json.loads(response.text)
    if data['status']['error_message'] is not None:
        raise ConnectionError('getPrices failed with message: ' + data['status']['error_message'])
    price_dict = {}
    for asset in asset_list:
        price_dict[asset] = data['data'][asset]['quote']['USD']
    return data


def getBalances():
    port_keys = pd.read_csv(os.getenv('PORTFOLIO_VIEW_KEYS'))
    df_list = []
    for port in port_keys.itertuples():
        balance_func = BALANCE_FUNCTION_DICT[port.exchange]
        port_bal = balance_func(port.api_key, port.api_secret)
        df = pd.DataFrame(list(port_bal.items()), columns = ['asset', 'balance'])
        df['port_id'] = port.port_id
        df['exchange'] = port.exchange
        df_list.append(df[['port_id','exchange','asset','balance']])
    df = pd.concat(df_list, ignore_index=True)
    return df


if __name__ == '__main__':
    fundSize = 1500
    #bal = getBalances()
    print(getPrices(['BTC','ETH','asdf']))
    
    #print(bal)
    #fundSize = bal.loc['total', 'val_usd']
    #idx = c.calcIndex(fundSize)
    #print('Target index:')
    #print(idx)






