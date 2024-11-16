import redis
import json
import asyncio
from typing import AsyncIterator, Dict, Any
import os

class PubSubClient:
    def __init__(self, redis_url: str = None):
        """Initialize Redis Pub/Sub client"""
        self.redis = redis.Redis.from_url(
            redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        )
        self.pubsub = self.redis.pubsub()

    async def subscribe(self, channel: str) -> AsyncIterator[Dict[str, Any]]:
        """Subscribe to a Redis channel and yield messages"""
        self.pubsub.subscribe(channel)
        
        while True:
            message = self.pubsub.get_message(ignore_subscribe_messages=True)
            if message and message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    yield data
                except Exception as e:
                    print(f"Error processing message: {e}")
            await asyncio.sleep(0.1)

    def close(self):
        """Close the Redis connection"""
        self.pubsub.close()
        self.redis.close() 