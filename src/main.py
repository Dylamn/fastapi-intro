from fastapi import FastAPI, Body, Query, Path, Cookie, Header
from pydantic import Required

from .enums import ModelName
from .schemas import Item, ItemOptions, Offer, Image

app = FastAPI()

fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Spam"}]


@app.get("/")
async def root():
    return {"message": "Hello, world!"}


# region Path Parameters

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
async def read_user_me(jwt_token: str = Cookie()):
    return {"user_id": f"the current user: {jwt_token}"}


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

# region Path Params and Numeric Validations
@app.get("/keyboards/{keyboard_id}/")
async def read_keyboard(
        q: str | None = Query(default=None, alias="keyboard-query"),
        keyboard_id: int = Path(title="The ID of the keyboard to get", ge=1, le=999)
):
    results = {"keyboard_id": keyboard_id}
    if q:
        results.update({"q": q})

    return results


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


# To declare a query parameter with a type of `list`, we need to explicitly use
# `Query`, otherwise it would be interpreted as a request body.
@app.get("/echo/items/")
async def echo_items(
        q: list[str] | None = Query(default=[], alias="list-query"),
        hidden_query: str | None = Query(default=None, include_in_schema=False)
):
    if hidden_query:
        return {"hidden_query": hidden_query}

    query_items = {"q": q}

    return query_items


@app.get("/search")
async def search_items(
        q: str | None = Query(
            default=None,
            title="Query string",
            description="Query string for the items to search in the db.",
            min_length=3,
            max_length=50,
        )
):
    results = []
    if not q:
        results = fake_items_db
    else:
        for item in fake_items_db:
            if q.lower() == item["item_name"].lower():
                results.append(item)

    return {"results": results}


# endregion

# region Request Body
@app.post("/items/")
async def create_item(item: Item = Body(
    examples={
        "normal": {
            "summary": "A normal example",
            "description": "A **normal** item works correctly.",
            "value": {
                "name": "Foo",
                "description": "A very nice Item",
                "price": 35.4,
                "tax": 3.2,
            },
        },
        "converted": {
            "summary": "An example with converted data",
            "description": "FastAPI can convert price `strings` to actual "
                           "`numbers` automatically",
            "value": {
                "name": "Bar",
                "price": "35.4",
            },
        },
        "invalid": {
            "summary": "Invalid data is rejected with an error",
            "value": {
                "name": "Baz",
                "price": "thirty five point four",
            },
        },
    },
)):
    item_dict = {**item.dict(), **{"importance": "importance"}}

    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})

    return item_dict


@app.put("/items/{item_id}")
async def update_item(
        item_id: int,
        item: Item,
        options: ItemOptions = Body(default=None, embed=True),
        q: str = Query(
            default=Required,
            min_length=3,
            max_length=50,
            regex="^[a-zA-Z0-9 ]+"),
        optional_query: str | None = Query(
            default=None,
            max_length=3,
            deprecated=True
        )
):
    if options.hidden:
        return {
            "query": q,
            "opt_query": optional_query
        }

    return {
        "query": q,
        "opt_query": optional_query,
        "item": {
            **{"item_id": item_id, **item.dict()},
            **{k: v for k, v in options.dict().items() if k != 'hidden'}
        }
    }


@app.post("/offers/")
async def create_offer(offer: Offer):
    duration = offer.end_datetime - offer.start_datetime
    offer_dict = offer.dict()
    offer_dict.update({"duration": duration})

    return offer_dict


@app.post("/images/")
async def create_image(images: list[Image]):
    for image in images:
        print(image.url)

    return images


@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    # Have in mind that JSON only supports str as keys.
    # Pydantic does the automatic data conversion.
    return weights


# endregion


@app.get("/headers/echo/")
async def echo_user_agent(
        user_agent: str | None = Header(default=None),
        strange_header: str | None = Header(default=None, convert_underscores=False),
        x_token: list[str] | None = Header(default=None)
):
    return {
        "User-Agent": user_agent,
        "strange_header": strange_header,
        "X-Token values": x_token
    }
