import asyncio
import aiohttp
import json
import redis
import os
import ssl
from web3 import Web3
from datetime import datetime

class GraphEventMonitor:
    def __init__(self):
        self.graph_url = "https://api.studio.thegraph.com/query/12344/onii-chan/version/latest"
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))
        self.w3 = Web3()
        self.blocks_per_query = 2
        self.poll_interval = 5
        
        # Create SSL context
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def make_request(self, query):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graph_url,
                json={
                    "query": query,
                    "operationName": "Subgraphs",
                    "variables": {}
                },
                ssl=self.ssl_context
            ) as response:
                return await response.json()
        
    async def fetch_tips(self, from_block, to_block):
        query = """
        {
            tips(
                first: 10, 
                where: { 
                    blockNumber_gte: "%d", 
                    blockNumber_lte: "%d" 
                }, 
                orderBy: blockNumber
            ) {
                id
                from
                tokenId
                amount
                tokenAddress
                message
                blockNumber
                blockTimestamp
                transactionHash
            }
        }
        """ % (from_block, to_block)

        result = await self.make_request(query)
        return result.get('data', {}).get('tips', [])

    async def get_latest_block(self):
        query = """
        {
            _meta {
                block {
                    number
                }
            }
        }
        """
        
        result = await self.make_request(query)
        return int(result.get('data', {}).get('_meta', {}).get('block', {}).get('number', 0))

    async def monitor_events(self):
        print("Starting Graph event monitor...")
        stored_block = None
        
        while True:
            try:
                # Get current block from The Graph
                latest_block = await self.get_latest_block()
                
                if stored_block is None:
                    stored_block = latest_block - 1
                    print(f"Starting from block {stored_block}")

                # Calculate block range for this query
                from_block = stored_block + 1
                to_block = min(from_block + self.blocks_per_query - 1, latest_block)

                if from_block > latest_block:
                    print("Waiting for new blocks...")
                    await asyncio.sleep(self.poll_interval)
                    continue

                print(f"Checking blocks {from_block} to {to_block}")
                tips = await self.fetch_tips(from_block, to_block)
                
                for tip in tips:
                    try:
                        await self.process_event(tip)
                    except Exception as e:
                        print(f"Error processing tip: {str(e)}")
                        continue

                # Update stored block
                stored_block = to_block

            except Exception as e:
                print(f"Loop error: {str(e)}")
                await asyncio.sleep(self.poll_interval)
                continue

            await asyncio.sleep(self.poll_interval)

    async def process_event(self, tip):
        try:
            # Convert wei to ETH
            amount_wei = int(tip['amount'])
            amount_eth = float(self.w3.from_wei(amount_wei, 'ether'))

            # Convert timestamp to readable format
            timestamp = datetime.fromtimestamp(int(tip['blockTimestamp']))

            # Format event
            tip_event = {
                "type": "tip",
                "session_id": "default",
                "amount": amount_eth,
                "currency": "ETH",
                "token_id": int(tip['tokenId']),
                "message": tip['message'],
                "from_address": get_ens(tip['from'])
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
            print(f"Raw tip data: {tip}")
            raise e

import requests

def get_ens(address):
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
        
        return address
    except requests.RequestException as e:
        print(f"Error during API request: {e}")
        return None


async def main():
    while True:
        try:
            monitor = GraphEventMonitor()
            await monitor.monitor_events()
        except Exception as e:
            print(f"Fatal error, restarting in 5 seconds: {str(e)}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())