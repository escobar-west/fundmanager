import pandas as pd
import argparse
import time
from configparser import ConfigParser
import client

class Fund:
    def __init__(self):
        config = ConfigParser()
        config.read('config/config.ini')
        self.c = client.Client()
        self.accounts = self._getAccounts(config['PATHS']['accounts'])
        self.totShares = self.accounts['shares'].sum()
        self._getBalance()


    def _getAccounts(self, path):
        return pd.read_csv(path, index_col='ID')


    def _getBalance(self):
        self.timestamp = time.time()
        self.balance = self.c.getBalance()
        self.idxusd = self.balance.loc['total','val_usd'] / self.totShares
        self.idxbtc = self.balance.loc['total','val_btc'] / self.totShares


    def getIndexPrice(self, base='USD'):
        return getattr(self, f'idx{base.lower()}')
        

    def getActBalance(self, a_id):
        shares = self.accounts.loc[a_id, 'shares']
        actWeight = shares / self.totShares
        
        actBalance = self.balance.copy()
        actBalance.loc[:,['balances','val_usd','val_btc']] *= actWeight

        return actBalance


    def sendBalanceReport(self, a_id):
        name = self.accounts.loc[a_id, 'name']
        shares = self.accounts.loc[a_id, 'shares']
        report = self.getActBalance(a_id)
        asset_msg = '\n'.join(['{}:\t${:,.2f}'.format(idx, report.loc[idx, 'val_usd']) for idx in report.index if report.loc[idx, 'val_usd'] >= 0.01])
        msg = f"""Hello {name},

Please look at your snapshot taken at {pd.to_datetime(int(self.timestamp-14400), unit='s')} EST:

Index Price (USD): ${round(self.getIndexPrice('USD'), 4)}
Index Price (BTC): \u20bf{round(self.getIndexPrice('BTC'), 7)}
Total shares: {self.totShares}
Your shares: {shares}
Value by asset:
{asset_msg}
"""
        subject = 'Weekly balance report'
        toAddress = self.accounts.loc[a_id, 'email']
        self.c.sendEmail(msg, subject, toAddress, {'file': report.to_csv(), 'name': 'balance_report.csv'})


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--send-balance', action='store_true', help='Send balance report')
    parser.add_argument('-d', '--debug', action='store_true', help='debug mode on')
    args = parser.parse_args()
    fund = Fund()
    print('IDXUSD: ', fund.getIndexPrice('USD'))
    print('IDXBTC: ', fund.getIndexPrice('BTC'))
    print(fund.balance)
    if args.send_balance:
        for ID in fund.accounts.index:
            fund.sendBalanceReport(ID)
    if args.debug:
            fund.sendBalanceReport(1)
