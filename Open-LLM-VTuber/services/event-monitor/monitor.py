import asyncio
from web3 import Web3
import os
import json
import redis
from hexbytes import HexBytes

class EventMonitor:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(
            os.getenv('WEB3_RPC_URL', 'https://base-sepolia.g.alchemy.com/v2/jRDWgvakZFvscXO7eOIZKItOQ_FpnfKd'),
            request_kwargs={'timeout': 30}
        ))
        self.contract_address = Web3.to_checksum_address('0x9fa0da29b88cc1479d28cead5a12ff498528a9d0')
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

        if not self.w3.is_connected():
            raise Exception("Failed to connect to RPC endpoint")

        try:
            current_block = self.w3.eth.block_number
            print(f"Successfully connected. Current block: {current_block}")
        except Exception as e:
            raise Exception(f"Failed to get current block: {str(e)}")

    async def monitor_events(self):
        print("Starting event monitor...")
        stored_block = None
        
        while True:
            try:
                try:
                    current_block = self.w3.eth.block_number
                except Exception as e:
                    print(f"Error getting block number: {str(e)}")
                    await asyncio.sleep(5)
                    continue

                if stored_block is None:
                    stored_block = current_block - 1
                    print(f"Starting from block {stored_block}")

                if stored_block >= current_block:
                    await asyncio.sleep(5)
                    continue

                target_block = stored_block + 1
                print(f"Checking block {target_block}")

                try:
                    logs = self.w3.eth.get_logs({
                        'fromBlock': target_block,
                        'toBlock': target_block,
                        'address': self.contract_address
                    })
                except Exception as e:
                    print(f"Error getting logs for block {target_block}: {str(e)}")
                    await asyncio.sleep(5)
                    continue

                for log in logs:
                    try:
                        await self.process_event(log)
                    except Exception as e:
                        print(f"Error processing event: {str(e)}")
                        continue

                stored_block = target_block

            except Exception as e:
                print(f"Loop error: {str(e)}")
                await asyncio.sleep(5)
                continue

            await asyncio.sleep(2)

    def hex_to_address(self, hex_data):
        """Safely convert hex data to address."""
        if isinstance(hex_data, HexBytes):
            hex_str = hex_data.hex()
        else:
            hex_str = str(hex_data)
        
        # Take the last 40 characters (20 bytes) of the hex string
        address = '0x' + hex_str[-40:]
        return Web3.to_checksum_address(address)

    async def process_event(self, event):
        try:
            # Print raw event for debugging
            print("\nProcessing event:")
            print(f"Topics: {[t.hex() if isinstance(t, HexBytes) else t for t in event['topics']]}")
            print(f"Data: {event['data'].hex() if isinstance(event['data'], HexBytes) else event['data']}")
            
            # Extract indexed parameters from topics
            from_address = self.hex_to_address(event['topics'][1])
            token_id = int(event['topics'][2].hex(), 16)
            
            # Decode data field
            data = event['data'].hex() if isinstance(event['data'], HexBytes) else event['data']
            if data.startswith('0x'):
                data = data[2:]
            
            # Extract amount (first 32 bytes)
            amount = int(data[:64], 16)
            
            # Extract message from the remaining data
            try:
                # Skip token address (32 bytes) and get to string data
                string_offset = int(data[128:192], 16)  # Get string offset
                string_start = string_offset * 2  # Convert to hex string position
                string_length = int(data[string_start:string_start+64], 16)  # Get string length
                message_start = string_start + 64
                message = bytes.fromhex(data[message_start:message_start+string_length*2]).decode('utf-8')
            except Exception as e:
                print(f"Error decoding message: {e}")
                message = ""

            # Format event
            tip_event = {
                "type": "tip",
                "session_id": "default",
                "amount": float(self.w3.from_wei(amount, 'ether')),
                "currency": "ETH",
                "token_id": token_id,
                "message": message
            }

            print(f"Formatted event: {tip_event}")

            # Publish to Redis
            self.redis_client.publish(
                'vtuber_events',
                json.dumps(tip_event)
            )
            
            print(f"Published event successfully")

        except Exception as e:
            print(f"Error in process_event: {str(e)}")
            print(f"Raw event data: {event}")
            raise e

async def main():
    while True:
        try:
            monitor = EventMonitor()
            await monitor.monitor_events()
        except Exception as e:
            print(f"Fatal error, restarting in 5 seconds: {str(e)}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
