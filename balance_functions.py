import os
import json
import time

import hashlib
import hmac
import base64
from requests import Session
from web3 import Web3

from erc20_utils import get_erc20_bal


_COINBASE_TRANSLATE_DICT = {
    'CGLD': 'CELO'
}


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
        if ticker in _COINBASE_TRANSLATE_DICT:
            ticker = _COINBASE_TRANSLATE_DICT[ticker]
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
    

BALANCE_FUNCTION_DICT = {
    'coinbase': getBalanceCoinbase,
    'kraken': getBalanceKraken,
    'ethereum': getBalanceEthereum,
}
