from fastapi import FastAPI
import os
from confluent_kafka import Consumer, KafkaError, Producer
from confluent_kafka.admin import AdminClient, NewTopic
import json
import threading
import time
from httpx import AsyncClient

MONGO_SERVER = os.getenv('MONGO_SERVER','localhost:27017')
KAFKA_SERVER = os.getenv('KAFKA_SERVER', 'localhost:9092')
KAFKA_TOPIC_CONSUMER = 'business_logic'  # Update with your topic name
KAFKA_TOPIC_PRODUCER = 'database'  # Update with your topic name
DATABASE_SERVICE_URL = os.getenv('DATABASE_SERVICE_URL','http://database-service-ip:database-service-port')

# Initialize Kafka producer
try:
    admin_client = AdminClient({'bootstrap.servers': KAFKA_SERVER})

    # Define the topic configuration
    topic_config = {
        'topic_name': KAFKA_TOPIC_PRODUCER,  # Update with your topic name
        'num_partitions': 1,
        'replication_factor': 1
    }

    # Create the NewTopic instance
    new_topic = NewTopic(
        topic_config['topic_name'],
        num_partitions=topic_config['num_partitions'],
        replication_factor=topic_config['replication_factor']
    )

    # Create the topic
    admin_client.create_topics([new_topic])
except Exception as e:
    print(f"Topic creation failed: {e}")

producer = Producer({'bootstrap.servers': KAFKA_SERVER})

app = FastAPI()
# Initialize Kafka consumer
conf = {'bootstrap.servers': KAFKA_SERVER, 'group.id': 'my-group', 'auto.offset.reset': 'earliest'}
consumer = Consumer(conf)
consumer.subscribe([KAFKA_TOPIC_CONSUMER])

def consume_messages():
    print("consume_messages function started")  # Add this line
    while True:
        print("Waiting for message")
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                continue
            else:
                print(msg.error())
                break

        message_value = msg.value().decode('utf-8')
        print(f"Received message: {message_value}")
        
        # Process the message and update the database accordingly
        process_message(message_value)
        time.sleep(0.2)

    consumer.close()

def process_message(message):
    try:
        data = json.loads(message)
        method = data.get('method')

        if method in ['make_order', 'cancel_order']:
            producer.produce(KAFKA_TOPIC_PRODUCER, value=json.dumps(data).encode('utf-8'))
            print("Message sent to database:", data)

    except Exception as e:
        print("Error processing message:", e)

@app.get("/get_all_order")
async def get_all_order():
    async with AsyncClient() as client:
        response = await client.get(f"{DATABASE_SERVICE_URL}/get_all_order")
    return response.json()


if __name__ == "__main__":
    # Start the Kafka consumer thread
    t1 = threading.Thread(target=consume_messages)
    t1.start()

    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)