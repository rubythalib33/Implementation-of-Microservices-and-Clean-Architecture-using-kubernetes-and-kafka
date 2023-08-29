from fastapi import FastAPI
import os
import json
import threading
import time
import redis
from httpx import AsyncClient

REDIS_SERVER = os.getenv('REDIS_SERVER', 'localhost:6379')
REDIS_CHANNEL_CONSUMER = 'business_logic'
REDIS_CHANNEL_PRODUCER = 'database'
DATABASE_SERVICE_URL = os.getenv('DATABASE_SERVICE_URL', 'http://database-service-ip:database-service-port')

# Initialize Redis client
redis_client = redis.StrictRedis(host=REDIS_SERVER, port=6379, db=0)
pubsub = redis_client.pubsub()
pubsub.subscribe(REDIS_CHANNEL_CONSUMER)

app = FastAPI()

def consume_messages():
    print("consume_messages function started")
    while True:
        print("Waiting for message")
        message = pubsub.get_message()

        if message and message['type'] == 'message':
            message_value = message['data'].decode('utf-8')
            print(f"Received message: {message_value}")

            # Process the message and update the database accordingly
            process_message(message_value)
        time.sleep(0.2)

def process_message(message):
    try:
        data = json.loads(message)
        method = data.get('method')

        if method in ['make_order', 'cancel_order']:
            redis_client.publish(REDIS_CHANNEL_PRODUCER, json.dumps(data))
            print("Message sent to database:", data)

    except Exception as e:
        print("Error processing message:", e)

@app.get("/get_all_order")
async def get_all_order():
    async with AsyncClient() as client:
        response = await client.get(f"{DATABASE_SERVICE_URL}/get_all_order")
    return response.json()

if __name__ == "__main__":
    # Start the Redis consumer thread
    t1 = threading.Thread(target=consume_messages)
    t1.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
