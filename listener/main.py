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


if __name__ == '__main__':
    with open('./config.yaml') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    this_config = config['oniichan']
    rpc = config['network_config']['rpc']
    decoded_tx = decode_tx(this_config, '0x767e339ca0a09224d59c55d66594fb09d612fc959925749419a51a00e04ac4f6', rpc)
    print(decoded_tx)
