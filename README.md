# FastAPI Intro

A project for learning the basics of FastAPI.


## Using python types

All URL parameters are sended as string, neither if they're path nor query params.

To convert them to other type, assign them a python type like so:
````python
from fastapi import FastAPI

app = FastAPI()


@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "query": q}
````

Using python types for parameters in function signature applies the following process:

- Data "parsing"
- Data validation
- Automatic documention
- Editor support (obviously)
