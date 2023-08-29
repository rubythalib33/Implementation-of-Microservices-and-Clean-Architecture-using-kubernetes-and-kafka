from fastapi import FastAPI
from pydantic import BaseModel
import redis
from httpx import AsyncClient
from uuid import uuid4
import json
import os

REDIS_SERVER = os.getenv('REDIS_SERVER', 'localhost:6379')
CHANNEL = 'business_logic'

app = FastAPI()

# Redis publisher setup
redis_client = redis.StrictRedis(host=REDIS_SERVER, port=6379, db=0)

RESTAURANT_SERVICE_URL = os.getenv('RESTAURANT_SERVICE_URL','http://restaurant-service-ip:restaurant-service-port')
ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL','http://order-service-ip:order-service-port')

class Order(BaseModel):
    order_id: str = str(uuid4())
    product_names: list
    is_paid: bool = False
    is_cooked: bool = False
    is_delivered: bool = False

class Product(BaseModel):
    name: str 
    price: float

@app.get("/get_all_product")
async def get_all_product():
    async with AsyncClient() as client:
        response = await client.get(f"{RESTAURANT_SERVICE_URL}/get_all_product")
    return response.json()

@app.post("/make_order")
def make_order(order: Order):
    order = order.dict()
    order['method'] = 'make_order'
    redis_client.publish(CHANNEL, json.dumps(order))
    return {"message": "Order placed successfully"}

@app.post("/cancel_order")
def cancel_order(order_id: str):
    order = {
        'method': 'cancel_order',
        'order_id': order_id
    }
    redis_client.publish(CHANNEL, json.dumps(order))
    return {"message": f"Order {order_id} canceled"}

@app.post("/make_payment")
def make_payment(order_id: str):
    order = {
        'method': 'make_payment',
        'order_id': order_id
    }
    redis_client.publish(CHANNEL, json.dumps(order))
    return {"message": f"Payment for order {order_id} processed"}

@app.post("/add_product")
def add_product(product: Product):
    product = product.dict()
    product['method'] = 'add_product'
    redis_client.publish(CHANNEL, json.dumps(product))
    return {"message": f"Product {product['name']} added"}

@app.post("/remove_product")
def remove_product(product_name: str):
    product = {
        'method': 'remove_product',
        'product_name': product_name
    }
    redis_client.publish(CHANNEL, json.dumps(product))
    return {"message": f"Product {product_name} removed"}

@app.post("/update_product")
def update_product(product: Product):
    product = product.dict()
    product['method'] = 'update_product'
    redis_client.publish(CHANNEL, json.dumps(product))
    return {"message": f"Product {product['name']} updated"}

@app.post("/food_is_done_cooked")
def food_is_done_cooked(order_id: str):
    order = {
        'method': 'food_is_done_cooked',
        'order_id': order_id
    }
    redis_client.publish(CHANNEL, json.dumps(order))
    return {"message": f"Food for order {order_id} is cooked"}

@app.get("/get_all_order")
async def get_all_order():
    async with AsyncClient() as client:
        response = await client.get(f"{ORDER_SERVICE_URL}/get_all_order")
    return response.json()

@app.post("/order_is_done_delivered")
def order_is_done_delivered(order_id: str):
    order = {
        'method': 'order_is_done_delivered',
        'order_id': order_id
    }
    redis_client.publish(CHANNEL, json.dumps(order))
    return {"message": f"Order {order_id} is delivered"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
