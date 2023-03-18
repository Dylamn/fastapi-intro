from enum import Enum
from typing import Any

from fastapi import (
    FastAPI, Body, Form, Query, Path, Cookie, Header, status, File, UploadFile,
    HTTPException, Request
)
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import Required
from starlette.exceptions import HTTPException as StarletteHTTPException

from .enums import ModelName
from .exceptions import UnicornException
from .functions import fake_save_user
from .schemas import (
    Item, ItemOptions, Offer, Image, UserIn, UserOut, CarVehicle, PlaneVehicle
)

app = FastAPI()


class Tags(Enum):
    items = "items"
    users = "users"


fake_items_db = [{"item_name": "Foo"}, {"item_name": "Bar"}, {"item_name": "Spam"}]

items = {
    "foo": {
        "name": "Foo", "price": 50200
    },
    "bar": {
        "name": "Bar", "description": "The bartenders", "price": 6200, "tax": 20.2
    },
    "baz": {
        "name": "Baz", "description": None, "price": 5020, "tax": 10.5, "tags": []
    },
}

vehicles = {
    "vehicle1": {"description": "All my friends drive a low rider", "type": "car"},
    "vehicle2": {
        "description": "Music is my aeroplane, it's my aeroplane",
        "type": "plane",
        "size": 5,
    },
}


# region Exception Handlers
@app.exception_handler(UnicornException)
async def unicorn_exception_handler(request: Request, exc: UnicornException):
    return JSONResponse(
        status_code=418,
        content={
            "message": f"Oops! {exc.name} did something. There goes a rainbow..."
        }
    )


# Overrides the default exception handler for validation exceptions
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
        request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body})
    )


# When we register an HTTPException handler, we shoul register it for Starlette's
# HTTPException.
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request, exc):
    print(f"An HTTP error: {repr(exc)}")

    # Re-use FastAPI's exception handler
    return await http_exception_handler(request, exc)


# endregion

@app.get("/", summary="Says hello world!")
async def root() -> dict[str, str]:
    return {"message": "Hello, world!"}


# region Path Parameters

@app.get("/cards/{card_id}", tags=["cards"])
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

@app.get("/users/me", tags=[Tags.users])
async def read_user_me(jwt_token: str = Cookie()):
    return {"user_id": f"the current user: {jwt_token}"}


@app.get("/users/{username}/hi", tags=[Tags.users])
async def say_hi_to_user(username: str):
    return {"msg": f"hi {username}"}


@app.get("/models/{model_name}", tags=["models"])
async def get_model(model_name: ModelName):
    if model_name is ModelName.alexnet:
        return {"model_name": model_name, "message": "Deep Learning FTW!"}

    if model_name.value == "lenet":
        return {"model_name": model_name, "message": "LeCNN all the images"}

    return {"model_name": model_name, "message": "Have some residuals"}


# endregion

# region Path Params and Numeric Validations
@app.get("/keyboards/{keyboard_id}/", tags=["keyboard"])
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
@app.get("/users/{user_id}/items/{item_id}", tags=[Tags.users])
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


@app.get("/search", tags=[Tags.items])
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
@app.post(
    "/items/",
    summary="Create an item",
    response_description="The created item",
    tags=[Tags.items]
)
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
    """
    Create an item with all the information:

    - **name**: each item must have a name
    - **description**: a long description
    - **price**: required
    - **tax**: if the item doesn't have tax, you can omit this
    - **tags**: a set of unique tag strings for this item
    """
    item_dict = {**item.dict(), **{"importance": "importance"}}

    if item.tax:
        price_with_tax = item.price + item.tax
        item_dict.update({"price_with_tax": price_with_tax})

    return item_dict


@app.put("/items/{item_id}", tags=[Tags.items])
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


@app.patch("/items/{item_id}", response_model=Item, tags=["items"])
async def update_item(item_id: str, item: Item):
    stored_item_data = items[item_id]
    stored_item_model = Item(**stored_item_data)
    update_data = item.dict(exclude_unset=True)
    updated_item = stored_item_model.copy(update=update_data)
    items[item_id] = jsonable_encoder(updated_item)

    return updated_item


@app.post("/offers/", response_model=Offer, tags=["offers"])
async def create_offer(offer: Offer) -> dict[str, Any]:
    duration = offer.end_datetime - offer.start_datetime
    offer_dict = offer.dict()
    offer_dict.update({"duration": duration})

    return offer_dict


@app.post("/images/", tags=["images"])
async def create_image(images: list[Image]) -> list[Image]:
    for image in images:
        print(image.url)

    return images


@app.post("/index-weights/")
async def create_index_weights(weights: dict[int, float]):
    # Have in mind that JSON only supports str as keys.
    # Pydantic does the automatic data conversion.
    return weights


# endregion


@app.get("/headers/echo/", deprecated=True)
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


@app.post("/user/", status_code=status.HTTP_201_CREATED, tags=[Tags.users])
async def create_user(user: UserIn) -> UserOut:
    user_saved = fake_save_user(user)
    return user_saved


@app.get(
    "/vehicles/{vehicle_id}",
    response_model=PlaneVehicle | CarVehicle,
    tags=["vehicles"]
)
async def read_vehicle(vehicle_id: str):
    vehicle = vehicles.get(f"vehicle{vehicle_id}")

    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found.")

    return vehicle


@app.post("/login", tags=[Tags.users])
async def login(username: str = Form(), password: str = Form()):
    if password == "password123":
        return {"token": "user_token", "username": username}

    raise HTTPException(
        status_code=400,
        detail="Incorrect username and/or password.",
        headers={"X-Error": "There goes my error"}
    )


@app.post("/files/", tags=["files"])
async def create_file(
        token: str = Form(),
        files: list[bytes] = File(
            default=None,
            description="A list of files read as bytes."
        )
):
    if not files:
        return {"message": "No file sent"}

    return {"token": token, "file_sizes": [len(file) for file in files]}


@app.post("/uploadfile/", tags=["files"])
async def create_upload_file(
        file: UploadFile = File(description="A file read as UploadFile.")
):
    if not file:
        return {"message": "No upload file sent"}

    return {"filename": file.filename}


@app.get("/unicorns/{name}", tags=["unicorns"])
async def read_unicorn(name: str):
    if name == "yolo":
        raise UnicornException(name=name)

    return {"unicorn_name": name}


@app.get("/tracks/{track_id}", tags=["tracks"])
async def read_exceptions(track_id: int):
    if track_id == 3:
        raise HTTPException(status_code=418, detail="Nope! I don't like 3.")

    return {"track_id": track_id}
