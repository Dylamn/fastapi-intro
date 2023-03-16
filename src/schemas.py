from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str | None = None
    price: int
    tax: float | None = None


class ItemOptions(BaseModel):
    promotion: int = 0
    hidden: bool = False
    shipping_available: bool = True
