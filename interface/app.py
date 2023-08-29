from fastapi import FastAPI
from pydantic import BaseModel
from confluent_kafka import Producer
from httpx import AsyncClient
from uuid import uuid4
import json
import os
from confluent_kafka.admin import AdminClient, NewTopic

KAFKA_SERVER = os.getenv('KAFKA_SERVER', 'localhost:9092')
KAFKA_TOPIC = 'business_logic'  # Update with your topic name
try:
    admin_client = AdminClient({'bootstrap.servers': KAFKA_SERVER})

    # Define the topic configuration
    topic_config = {
        'topic_name': KAFKA_TOPIC,  # Update with your topic name
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

app = FastAPI()

producer = Producer({'bootstrap.servers': KAFKA_SERVER})
RESTAURANT_SERVICE_URL = os.getenv('RESTAURANT_SERVICE_URL','http://restaurant-service-ip:restaurant-service-port')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL','http://order-service-ip:order-service-port')

# Pydantic model for order data
class Order(BaseModel):
    order_id: str = str(uuid4())
    product_names: list
    is_paid: bool = False
    is_cooked: bool = False
    is_delivered: bool = False

# Pydantic model for product data
class Product(BaseModel):
    name: str 
    price: float

# API endpoint to get all products
@app.get("/get_all_product")
async def get_all_product():
    async with AsyncClient() as client:
        response = await client.get(f"{RESTAURANT_SERVICE_URL}/get_all_product")
    return response.json()

# API endpoint to make an order
@app.post("/make_order")
def make_order(order: Order):
    # Process order logic
    # ...
    order = order.dict()
    order['method'] = 'make_order'
    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(order).encode('utf-8'))
    producer.flush()  # Wait for the message to be sent
    return {"message": "Order placed successfully"}

# API endpoint to cancel an order
@app.post("/cancel_order")
def cancel_order(order_id: str):
    # Cancel order logic
    # ...
    order = {
        'method': 'cancel_order',
        'order_id': order_id
    }
    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(order).encode('utf-8'))
    producer.flush()  # Wait for the message to be sent
    return {"message": f"Order {order_id} canceled"}

# API endpoint to make a payment
@app.post("/make_payment")
def make_payment(order_id: str):
    # Payment logic
    # ...
    order = {
        'method': 'make_payment',
        'order_id': order_id
    }
    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(order).encode('utf-8'))
    producer.flush()
    return {"message": f"Payment for order {order_id} processed"}

# API endpoint to add a product
@app.post("/add_product")
def add_product(product: Product):
    # Add product logic
    # ...
    product = product.dict()
    product['method'] = 'add_product'
    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(product).encode('utf-8'))
    producer.flush()
    return {"message": f"Product {product['name']} added"}

# API endpoint to remove a product
@app.post("/remove_product")
def remove_product(product_name: str):
    # Remove product logic
    # ...
    product = {
        'method': 'remove_product',
        'product_name': product_name
    }
    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(product).encode('utf-8'))
    producer.flush()
    return {"message": f"Product {product_name} removed"}

# API endpoint to update a product
@app.post("/update_product")
def update_product(product: Product):
    # Update product logic
    # ...
    product = product.dict()
    product['method'] = 'update_product'

    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(product).encode('utf-8'))
    producer.flush()
    return {"message": f"Product {product.name} updated"}

# API endpoint for notifying food is done cooked
@app.post("/food_is_done_cooked")
def food_is_done_cooked(order_id: str):
    # Food cooked logic
    # ...
    order = {
        'method': 'food_is_done_cooked',
        'order_id': order_id
    }
    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(order).encode('utf-8'))
    producer.flush()
    return {"message": f"Food for order {order_id} is cooked"}

# API endpoint to get all orders by making a request to OrderService
@app.get("/get_all_order")
async def get_all_order():
    async with AsyncClient() as client:
        response = await client.get(f"{ORDER_SERVICE_URL}/get_all_order")
    return response.json()


# API endpoint for notifying order is done delivered
@app.post("/order_is_done_delivered")
def order_is_done_delivered(order_id: str):
    # Order delivered logic
    # ...
    order = {
        'method': 'order_is_done_delivered',
        'order_id': order_id
    }
    # Publish message to Kafka for further processing
    producer.produce(KAFKA_TOPIC, value=json.dumps(order).encode('utf-8'))
    producer.flush()
    return {"message": f"Order {order_id} is delivered"}

# ... similar implementations for other actions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
