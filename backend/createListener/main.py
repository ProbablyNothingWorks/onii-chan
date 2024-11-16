import base64
import functions_framework
import requests
import json
from web3 import Web3
from cryptography.fernet import Fernet
from itsdangerous import URLSafeSerializer
import yaml
from google.cloud import pubsub_v1

# Initialize the Pub/Sub publisher client
publisher = pubsub_v1.PublisherClient()
# Specify your Pub/Sub topic
PUBSUB_TOPIC = "projects/bb-rnd-poc/topics/oniichan"

@functions_framework.http
def monitor(request):
    # Turn the bytes array into a string
    request_data = request.get_data(as_text=True)
    # Parse the event in the input
    event = json.loads(request_data)
    print(event)
    if 'event' not in event or 'activity' not in event['event']:
        print('no event or activity found')
        return 'no event or activity found'
    message = event['event']['activity'][0]
    print(f'message: {message}')
# Read in the config file
    with open('./config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    
    rpc = config['network_config']['rpc']
    # The campaign contract address
    to_address = message.get('toAddress')
    decoded_tx = None
    
    if to_address is not None and isinstance(to_address, str):
        this_config = config['oniichan']
        decoded_tx = decode_tx(this_config, message['hash'], rpc)
    
    if decoded_tx:
        # Prepare the message to be sent to Pub/Sub
        pubsub_message = {
            "toAddress": to_address,
            "decodedTransaction": decoded_tx,
            "originalMessage": message
        }
        
        # Publish the message to Pub/Sub
        publish_to_pubsub(pubsub_message)
    
    return 'ok'


def decode_tx(this_config: dict, tx_hash: str, rpc: str) -> dict | None:
    contract_address_string = Web3.to_checksum_address(this_config['address'])
    # Connect to the blockchain
    w3 = Web3(Web3.HTTPProvider(rpc))

    # Get the contract ABI
    with open(this_config['abi']) as f:
        abi = json.load(f)
    tx = w3.eth.get_transaction(tx_hash)
    # Get the contract
    contract = w3.eth.contract(address=contract_address_string, abi=abi)

    # Decode the transaction data and print the result
    if tx.get('input') is not None:
        decoded_tx = contract.decode_function_input(tx.get('input'))
        print(decoded_tx)
        print('[DECODED]')
        return decoded_tx[1]

def publish_to_pubsub(message: dict):
    """Publishes a message to the Pub/Sub topic."""
    try:
        # Convert the message to JSON and encode it as bytes
        data = json.dumps(message).encode("utf-8")
        # Publish the message
        future = publisher.publish(PUBSUB_TOPIC, data)
        print(f"Message published to Pub/Sub with message ID: {future.result()}")
    except Exception as e:
        print(f"Failed to publish message to Pub/Sub: {e}")

import requests

def get_ens(address):
    """
    Retrieves one ENS name for the given Ethereum address using the MnemonicHQ API.

    Args:
        address (str): Ethereum address to resolve.
        api_key (str): Your MnemonicHQ API key.

    Returns:
        str: The first ENS name associated with the address or None if no valid ENS is found.
    """
    # Define the API URL
    api_url = f"https://ethereum-rest.api.mnemonichq.com/wallets/v1beta2/ens/by_address/{address}"
    
    # Set the headers with the API key
    headers = {
        'X-API-Key': 'IMAbzFuLRsW9GTkBg4LDL0YV5MwAN7mTsXET5PGSL3oYWiMH'
    }
    
    try:
        # Make the GET request
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        
        # Parse the JSON response
        data = response.json()
        
        # Return the 'name' field if it exists
        if 'entities' in data and data['entities']:
            for entity in data['entities']:
                if entity.get('name'):
                    return entity['name']
        
        return None  # No valid ENS name found
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None




if __name__ == '__main__':
    # Example usage
    address = "0xd8da6bf26964af9d7eed9e03e53415d37aa96045"  # Replace with your Ethereum address
    ens_name = get_ens(address)
    if ens_name:
        print(f"The ENS name for address {address} is: {ens_name}")
    else:
        print(f"No ENS name found for address {address}.")

    # with open('./config.yaml') as f:
    #     config = yaml.load(f, Loader=yaml.FullLoader)
    # this_config = config['oniichan']
    # rpc = config['network_config']['rpc']
    # decoded_tx = decode_tx(this_config, '0x767e339ca0a09224d59c55d66594fb09d612fc959925749419a51a00e04ac4f6', rpc)
    # print(decoded_tx)
