import asyncio
import json
import os
from web3 import Web3
import redis
from eth_abi import decode_abi
import time

class EventMonitor:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('WEB3_RPC_URL')))
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        
        # Example event signature for a tip event
        self.tip_event_signature = self.w3.keccak(
            text="TipReceived(address,uint256,string)"
        ).hex()

    async def monitor_events(self):
        print("Starting event monitor...")
        last_block = None

        while True:
            try:
                current_block = self.w3.eth.block_number
                
                if last_block is None:
                    last_block = current_block - 1

                # Get new events
                events = self.w3.eth.get_logs({
                    'fromBlock': last_block + 1,
                    'toBlock': current_block,
                    'address': self.contract_address,
                    'topics': [self.tip_event_signature]
                })

                for event in events:
                    await self.process_event(event)

                last_block = current_block
                
                # Sleep for a bit before next check
                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                print(f"Error monitoring events: {e}")
                await asyncio.sleep(10)  # Wait longer on error

    async def process_event(self, event):
        try:
            # Decode the event data
            data = event['data']
            topics = event['topics']
            
            # Example decoding (adjust based on your event structure)
            decoded_data = decode_abi(
                ['address', 'uint256', 'string'],
                bytes.fromhex(data[2:])  # Remove '0x' prefix
            )
            
            tipper_address = decoded_data[0]
            amount = decoded_data[1]
            username = decoded_data[2]

            # Create message for VTuber
            message = {
                "type": "tip",
                "session_id": "default",  # You might want to handle this differently
                "amount": self.w3.from_wei(amount, 'ether'),
                "currency": "ETH",
                "username": username,
                "wallet_address": tipper_address
            }

            # Publish to Redis
            self.redis_client.publish(
                'vtuber_events',
                json.dumps(message)
            )
            
            print(f"Published tip event: {message}")

        except Exception as e:
            print(f"Error processing event: {e}")

async def main():
    monitor = EventMonitor()
    await monitor.monitor_events()

if __name__ == "__main__":
    asyncio.run(main()) 