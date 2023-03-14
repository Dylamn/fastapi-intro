from fastapi import FastAPI

from .enums import ModelName
from .schemas import Item

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Spam"}]


@app.get("/")
async def root():
    return {"message": "Hello, world!"}


# region Path parameters

@app.get("/cards/{card_id}")
async def read_card(card_id: int, short: bool = False, q: str | None = None):
    card = {"card_id": card_id}
    if q:
        card.update({"q": q})
    if not short:
        card.update({
            "description": "An amazing card with an extra long description"
        })

    return card


# Order matters for route definition.

@app.get("/users/me")
async def read_user_me():
    return {"user_id": "the current user"}


@app.get("/users/{username}/hi")
async def say_hi_to_user(username: str):
    return {"msg": f"hi {username}"}


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


# endregion

# region Query Parameters
@app.get("/items/")
async def read_item(skip: int = 0, limit: int = 10):
    return fake_items_db[skip:skip + limit]


# Required query parameter (`needy`)
@app.get("/users/{user_id}/items/{item_id}")
async def read_user_item(user_id: int, item_id: str, needy: str):
    item = {"user_id": user_id, "item_id": item_id, "needy": needy}

    return item

# endregion


# region Request Body
@app.post("/items/")
async def create_item(item: Item):
    item_dict = item.dict()

    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})

    return item


@app.put("/items/{item_id}")
async def update_item(item_id: int, item: Item):
    return {"item_id": item_id, **item.dict()}


# endregion
