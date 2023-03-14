from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: int
    tax: float | None = None
