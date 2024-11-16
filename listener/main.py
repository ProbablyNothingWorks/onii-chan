import base64
import functions_framework
import requests
import json
from web3 import Web3
from cryptography.fernet import Fernet
from itsdangerous import URLSafeSerializer
import  yaml
'''example input
b'{"webhookId":"wh_2ym3rl5836gx9pdo","id":"whevt_swhs3ws83zul39l1","createdAt":"2023-07-20T13:53:02.749Z","type":"ADDRESS_ACTIVITY","event":{"network":"ETH_SEPOLIA","activity":[{"fromAddress":"0x130c81f86c7e53ecd6580dfa2ca4f7df0de84046","toAddress":"0x68187257e7ba86bd230786a5275486d4 fb1fcb0c","blockNum":"0x3bf911","hash":"0x74e2eb8688e1225b79556ebbe9d8c30173f20bbd7010c8f3fecd044ec3a215a7","value":0,"typeTraceAddress":"call_0_0","asset":"ETH","category":"internal","rawContract":{"rawValue":"0x0","decimals":18}}]}}'

{"event":{"activity":[{"fromAddress": "0xb944459501ae5e1fcf156ebe8ca36b76d46f3c15", 'toAddress': '0xb72f6e3527c217a90f627e09d04b72cd85daa3fa', 'blockNum': '0x2eb3b91', 'hash': '0x21d6aeafe956801222cacf00d41402b34270133fdd172cb44bd336a9363ae697', 'value': 0, 'asset': 'MATIC', 'category': 'external', 'rawContract': {'rawValue': '0x0', 'decimals': 18}}]}}
'''



@functions_framework.http
def monitor(request):
    # turn the bytes array into a string
    request_data = request.get_data(as_text=True)
    # get the event in the input
    event = json.loads(request_data)
    message = event['event']['activity'][0]
    print(f'message: {message}')

    # read in the config file
    with open('./config.yml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    rpc = config['network_config']['rpc']
    # the campaign contract address
    to_address = message.get('toAddress')
    if to_address is not None and isinstance(to_address, str):
        this_config = config['oniichan']
        decoded_tx = decode_tx(this_config, message['hash'], rpc)
    return 'ok'



def decode_tx(
        this_config: dict,
        tx_hash: str,
        rpc: str
        )->dict|None:
     contract_address_string = Web3.to_checksum_address(this_config['address'])
     # connect to the blockchain
     w3 = Web3(Web3.HTTPProvider(rpc))

     # get the contract ABI
     with open(this_config['abi']) as f:
          abi = json.load(f)
     tx = w3.eth.get_transaction(tx_hash)
     # get the contract
     contract = w3.eth.contract(address=contract_address_string, abi=abi)

     # decode the transaction data and print the result
     if tx.get('input') is not None:
         decoded_tx = contract.decode_function_input(tx.get('input'))
         print(decoded_tx)
         print('[DECODED]')
         return decoded_tx[1]


if __name__ == '__main__':
    with open('./config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    this_config = config['oniichan']
    rpc = config['network_config']['rpc']
    decoded_tx = decode_tx(this_config, '0x767e339ca0a09224d59c55d66594fb09d612fc959925749419a51a00e04ac4f6', rpc)
    print(decoded_tx)
