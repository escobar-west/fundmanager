import hashlib
import hmac
import base64
import pandas as pd
from configparser import ConfigParser
from os.path import join, abspath, dirname
from requests import Session
import requests
import json
import time
from web3 import Web3
import os
from erc20_utils import get_erc20_bal


_KRAKEN_TRANSLATE_DICT = {
    'XXBT': 'BTC',
    'XETH': 'ETH',
    'XXMR': 'XMR',
    'ZUSD': 'USD',
}


def getBalanceCoinbase(apiKey, secretKey):
    secretKey = bytes(secretKey, encoding='utf-8')
    resource = '/v2/accounts'

    with Session() as session:
        timestamp = session.get('https://api.coinbase.com/v2/time')
        timestamp = str(json.loads(timestamp.text)['data']['epoch'])

        message = bytes(timestamp + 'GET' + resource, encoding='utf-8')
        signature = hmac.new(secretKey, message, digestmod=hashlib.sha256).hexdigest()

        headers = {
            'CB-ACCESS-KEY': apiKey,
            'CB-ACCESS-SIGN': signature,
            'CB-ACCESS-TIMESTAMP': timestamp
        }
        session.headers.update(headers)
        response = session.get('https://api.coinbase.com' + resource)
    packet = json.loads(response.text)

    asset_dict = {}
    for asset in packet['data']:
        ticker = asset['balance']['currency']
        balance = float(asset['balance']['amount'])
        if balance > 0:
            if ticker not in asset_dict:
                asset_dict[ticker] = balance
            else:
                asset_dict[ticker] += balance
    return asset_dict


def getBalanceKraken(apiKey, secretKey):
    secretKey = base64.b64decode(secretKey)
    resource = '/0/private/Balance'

    nonce = str(int(time.time()*1000))
    post_data = '&nonce=' + nonce
    hashed_post_data = hashlib.sha256(bytes(nonce + post_data, encoding='utf-8')).digest()
    message = bytes(resource, encoding='utf-8') + hashed_post_data

    signature = hmac.new(secretKey, message, digestmod=hashlib.sha512).digest()

    headers = {
        'API-Key': apiKey,
        'API-Sign': base64.b64encode(signature)
    }
    with Session() as session:
        session.headers.update(headers)
        response = session.post('https://api.kraken.com' + resource, data=bytes(post_data, encoding='utf-8'))
    packet = json.loads(response.text)

    asset_dict = {}
    for (asset, balance) in packet['result'].items():
        balance = float(balance)
        if asset in _KRAKEN_TRANSLATE_DICT:
            asset = _KRAKEN_TRANSLATE_DICT[asset]
        if balance > 0:
            asset_dict[asset] = balance
    return asset_dict


def getBalanceEthereum(ethAddress, *args, **kwargs):
    w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/' + os.getenv('INFURA_API_KEY')))
    asset_dict = get_erc20_bal(w3, ethAddress)
    weiBalance = int(w3.eth.getBalance(ethAddress))
    ethBalance = float(w3.fromWei(weiBalance, 'ether'))
    asset_dict['ETH'] = ethBalance
    return asset_dict
    

def getBalanceBinance(apiKey, secretKey):
    session = Session()
    headers = {
        'X-MBX-APIKEY': apiKey
    }
    session.headers.update(headers)

    timestamp = session.get('https://binance.com/api/v1/time')
    timestamp = int(json.loads(timestamp.text)['serverTime'])

    secretKey = bytes(secretKey, encoding='utf-8')
    message = bytes(f'timestamp={timestamp}', encoding='utf-8')
    signature = hmac.new(secretKey, message, digestmod=hashlib.sha256).hexdigest()
    url = f'https://api.binance.com/api/v3/account?timestamp={timestamp}&signature={signature}'

    response = session.get(url)
    data = json.loads(response.text)
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

BALANCE_FUNCTION_DICT = {
    'coinbase': getBalanceCoinbase,
    'kraken': getBalanceKraken,
    'binance': getBalanceBinance,
    'ethereum': getBalanceEthereum,
}
