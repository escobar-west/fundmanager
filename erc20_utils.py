import json

ERC_20_LIST = {
    'MATIC': '0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0',
    'MKR': '0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2',
    'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
    'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
    'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
}


ABI = [
        {
          "constant": True,
          "inputs": [
            {
              "name": "owner",
              "type": "address"
            }
          ],
          "name": "balanceOf",
          "outputs": [
            {
              "name": "",
              "type": "uint256"
            }
          ],
          "payable": False,
          "stateMutability": "view",
          "type": "function"
        },
        {
          "constant": True,
          "inputs": [],
          "name": "decimals",
          "outputs": [
            {
              "name": "",
              "type": "uint8"
            }
          ],
          "payable": False,
          "stateMutability": "view",
          "type": "function"
        }
      ]


def get_erc20_bal(w3, account_address):
    json_abi = json.dumps(ABI)
    asset_dict = {}
    for (asset, address) in ERC_20_LIST.items():
        contract = w3.eth.contract(address, abi=json_abi)
        decimals = contract.functions.decimals().call()
        balance = contract.functions.balanceOf(account_address).call() / (10.0 ** decimals)
        if balance > 0:
            asset_dict[asset] = balance
    return asset_dict
