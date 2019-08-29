import hashlib
import hmac
import base64
import pandas as pd
from configparser import ConfigParser
from os.path import join, abspath, dirname
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE


class Client:
    def __init__(self, debug=None):
        config = ConfigParser()
        config.read(join(dirname(abspath(__file__)), 'config/config.ini'))
        self.apiKey = config['KEYS']['apiKey']
        self.secretKey = config['KEYS']['secretKey']
        self.cmcKey = config['KEYS']['cmcKey']
        self.emailUser = config['EMAIL']['user']
        self.emailPass = config['EMAIL']['password']
        self.debug = debug if debug is not None else int(config['EMAIL']['debug'])
        self.banList = ['USDT', 'BSV']


    def calcIndex(self, fundSize=100):
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        parameters = {
            'start': '1',
            'limit': '13',
            'convert': 'USD'
        }
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.cmcKey
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
        except(ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
        total = 0
        index = []
        weights = []
        prices_usd = []
        prices_base = []
        base_symbol = data['data'][0]['symbol']
        base_price = data['data'][0]['quote']['USD']['price']
        for datum in data['data']:
            symbol = datum['symbol']
            if symbol in self.banList:
                continue
            index.append(symbol)
            prices_usd.append(datum['quote']['USD']['price'])
            weights.append(datum['quote']['USD']['market_cap'])
            total += weights[-1]
            if len(index) == 10:
                break
        weights = [w / total for w in weights]
        val_usd = [fundSize * w for w in weights]
        balances = [val_usd[i] / prices_usd[i] for i in range(len(index))]
        val_base = [val_usd[i] / base_price for i in range(len(index))]
        df = pd.DataFrame({'weights': weights,
                           'balances':balances,
                           'val_usd': val_usd,
                           f'val_{base_symbol}': val_base}, index=index)
        df.loc['total'] = df.sum()

        return df

    def getBalance(self):
        session = Session()
        headers = {
            'X-MBX-APIKEY': self.apiKey
        }
        session.headers.update(headers)

        timestamp = session.get('https://binance.com/api/v1/time')
        timestamp = int(json.loads(timestamp.text)['serverTime'])

        secret = bytes(self.secretKey, encoding='utf-8')
        message = bytes(f'timestamp={timestamp}', encoding='utf-8')
        signature = hmac.new(secret, message, digestmod=hashlib.sha256).hexdigest()
        url = f'https://api.binance.com/api/v3/account?timestamp={timestamp}&signature={signature}'

        try:
            response = session.get(url)
            data = json.loads(response.text)
        except(ConnectionError, Timeout, TooManyRedirects) as e:
            print(e)
        index = []
        balances = []
        val_btc = []
        for datum in data['balances']:
            bal = float(datum['free']) + float(datum['locked'])
            if bal == 0:
                continue
            asset = datum['asset']
            index.append(asset)
            balances.append(bal)
            if asset == 'BTC':
                price_btc = 1.0
            elif asset in ['USDT','TUSD','USDC','PAX']:
                price_btc = session.get(f'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
                price_btc = 1 / float(json.loads(price_btc.text)['price'])
            else:
                price_btc = session.get(f'https://api.binance.com/api/v3/ticker/price?symbol={asset+"BTC"}')
                price_btc = float(json.loads(price_btc.text)['price'])
            val_btc.append(balances[-1] * price_btc)

        btc_price = session.get(f'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
        btc_price = float(json.loads(btc_price.text)['price'])
        val_usd = [x * btc_price for x in val_btc]
        weights = [x / sum(val_usd) for x in val_usd]
        
        df = pd.DataFrame({'weights': weights,
                           'balances':balances,
                           'val_usd': val_usd,
                           f'val_btc': val_btc,}, index=index)
        df = df.sort_values('val_usd', ascending=False)
        df.loc['total'] = df.sum()
        
        return df


    def sendEmail(self, txt, subject, reciever, csvData=[]):
        if self.debug:
            reciever = ['victorv.suriel@gmail.com']
        if not isinstance(reciever, list):
            reciever = [reciever]
        msg = MIMEMultipart()
        msg.attach(MIMEText(txt))
        msg['Subject'] = subject
        msg['To'] = COMMASPACE.join(reciever)
        msg['From'] = self.emailUser

        if not isinstance(csvData, list):
            csvData = [csvData]
        for datum in csvData:
            attachment = MIMEApplication(datum['file'], Name=datum['name'])
            msg.attach(attachment)

        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.ehlo()
        s.starttls()
        s.login(self.emailUser, self.emailPass)
        s.send_message(msg)
        s.quit()
        

if __name__ == '__main__':
    fundSize = 1500
    c = Client()
    bal = c.getBalance()
    print('Current balance:')
    print(bal)
    fundSize = bal.loc['total', 'val_usd']
    idx = c.calcIndex(fundSize)
    print('Target index:')
    print(idx)






