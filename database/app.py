from fastapi import FastAPI
from pymongo import MongoClient
import os
from confluent_kafka import Consumer, KafkaError
import json
import threading
import time

MONGO_SERVER = os.getenv('MONGO_SERVER','localhost:27017')
KAFKA_SERVER = os.getenv('KAFKA_SERVER', 'localhost:9092')
KAFKA_TOPIC = 'business_logic'  # Update with your topic name


app = FastAPI()
db = MongoClient(f'mongodb://{MONGO_SERVER}/')
db = db['restaurant']

# Initialize Kafka consumer
conf = {'bootstrap.servers': KAFKA_SERVER, 'group.id': 'my-group', 'auto.offset.reset': 'earliest'}
consumer = Consumer(conf)
consumer.subscribe([KAFKA_TOPIC])

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

        if method == 'make_order':
            # Process the make_order message
            order_data = data
            del order_data['method']
            if order_data:
                db.orders.insert_one(order_data)
                print("Order inserted:", order_data)

        elif method == 'cancel_order':
            # Process the cancel_order message
            order_id = data.get('order_id')
            if order_id:
                db.orders.delete_one({'order_id': order_id})
                print("Order deleted:", order_id)

        elif method == 'make_payment':
            # Process the make_payment message
            order_id = data.get('order_id')
            if order_id:
                db.orders.update_one({'order_id': order_id}, {'$set': {'is_paid': True}})
                print("Order payment updated:", order_id)

        elif method == 'add_product':
            # Process the add_product message
            product_data = data
            del product_data['method']
            if product_data:
                db.products.insert_one(product_data)
                print("Product inserted:", product_data)

        elif method == 'remove_product':
            # Process the remove_product message
            product_name = data.get('product_name')
            if product_name:
                db.products.delete_one({'name': product_name})
                print("Product deleted:", product_name)

        elif method == 'update_product':
            # Process the update_product message
            product_data = data
            del product_data['method']
            if product_data:
                db.products.update_one({'name': product_data['name']}, {'$set': product_data})
                print("Product updated:", product_data['name'])

        # Add more cases for other methods as needed

        else:
            print("Unknown method:", method)

    except Exception as e:
        print("Error processing message:", e)

@app.get("/get_all_product")
async def get_all_product():
    products = db.products.find()
    products = [product for product in products]
    products_temp = []
    for product in products:
        product['_id'] = str(product['_id'])
        products_temp.append(product)

    return products_temp

@app.get("/get_all_order")
async def get_all_order():
    orders = db.orders.find()
    orders = [order for order in orders]
    orders_temp = []
    for order in orders:
        order['_id'] = str(order['_id'])
        orders_temp.append(order)

    return orders_temp

if __name__ == "__main__":
    import uvicorn
    # Start the Kafka consumer thread
    t = threading.Thread(target=consume_messages)
    t.daemon = True
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=7000)