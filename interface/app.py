from fastapi import FastAPI
from pydantic import BaseModel
from kafka import KafkaProducer
from httpx import AsyncClient
from uuid import uuid4
import json

app = FastAPI()

# Initialize Kafka producer
producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda x: json.dumps(x).encode('utf-8'))

RESTAURANT_SERVICE_URL = "http://product-service-ip:product-service-port"
ORDER_SERVICE_URL = "http://order-service-ip:order-service-port"

# Pydantic model for order data
class Order(BaseModel):
    order_id: str = str(uuid4())
    product_ids: list
    is_paid: bool = False
    is_cooked: bool = False
    is_delivered: bool = False

# Pydantic model for product data
class Product(BaseModel):
    name: str = str(uuid4())
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
    producer.send('business_logic', value=order)
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
    producer.send('business_logic', value=order)
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
    producer.send('business_logic', value=order)
    return {"message": f"Payment for order {order_id} processed"}

# API endpoint to add a product
@app.post("/add_product")
def add_product(product: Product):
    # Add product logic
    # ...
    product = product.dict()
    product['method'] = 'add_product'
    # Publish message to Kafka for further processing
    producer.send('business_logic', value=product)
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
    producer.send('business_logic', value=product)
    return {"message": f"Product {product_name} removed"}

# API endpoint to update a product
@app.post("/update_product")
def update_product(product: Product):
    # Update product logic
    # ...
    product = product.dict()
    product['method'] = 'update_product'

    # Publish message to Kafka for further processing
    producer.send('business_logic', value=product)
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
    producer.send('business_logic', value=order)
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
    producer.send('business_logic', value=order)
    return {"message": f"Order {order_id} is delivered"}

# ... similar implementations for other actions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
