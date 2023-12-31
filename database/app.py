from fastapi import FastAPI
from pymongo import MongoClient
import os
import json
import threading
import time
import redis

MONGO_SERVER = os.getenv('MONGO_SERVER', 'localhost:27017')
REDIS_SERVER = os.getenv('REDIS_SERVER', 'localhost:6379')
REDIS_CHANNEL = 'database'

app = FastAPI()
db = MongoClient(f'mongodb://{MONGO_SERVER}/')
db = db['restaurant']

# Initialize Redis client and subscribe to a channel
redis_client = redis.StrictRedis(host=REDIS_SERVER, port=6379, db=0)
pubsub = redis_client.pubsub()
pubsub.subscribe(REDIS_CHANNEL)

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
        
        elif method == 'food_is_done_cooked':
            order_id = data.get('order_id')
            if order_id:
                db.orders.update_one({'order_id': order_id}, {'$set': {'is_cooked': True}})

        elif method == 'order_is_done_delivered':
            order_id = data.get('order_id')
            if order_id:
                db.orders.update_one({'order_id': order_id}, {'$set': {'is_delivered': True}})

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