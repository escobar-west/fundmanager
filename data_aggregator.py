import pandas as pd
from requests import Session
import json
from balance_functions import BALANCE_FUNCTION_DICT
import os


def getPrices(asset_list):
    if not isinstance(asset_list, list):
        asset_list = [asset_list]
    if 'USD' in asset_list:
        price_dict = {'USD': 1.0}
        asset_list = set(asset_list) - {'USD'}
    else:
        price_dict = {}

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
    for asset in asset_list:
        price_dict[asset] = data['data'][asset]['quote']['USD']['price']
    return price_dict


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
    bal = getBalances()
    prices = getPrices(bal['asset'].unique().tolist())
    price_df = pd.Series(prices).to_frame(name='price')
    bal = pd.merge(bal, price_df, left_on='asset',right_index=True)
    bal['value'] = bal['balance'] * bal['price']
    print(bal)
    print('Total Portfolio Value: {}'.format(bal['value'].sum()))
