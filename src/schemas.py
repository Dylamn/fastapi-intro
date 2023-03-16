from pydantic import BaseModel, Field


class Item(BaseModel):
    name: str
    description: str | None = None
    price: int = Field(
        title="The price of the item.",
        description="A positive integer representing how much to charge in the "
                    "smallest currency unit (e.g., 100 cents to charge €1.00 "
                    "or 100 to charge ¥100, a zero-decimal currency)."
                    "The minimum amount is €1.00 and its supports up to eight "
                    "digits (e.g., a value of 99999999 for a EUR charge of "
                    "€999,999.99).",
        gt=100,
        le=99999999
    )
    tax: float | None = None


class ItemOptions(BaseModel):
    promotion: int = Field(
        default=0,
        title="A promotion to apply to the price.",
        description="The promotion value will be substracted to the base price."
                    "e.g. for a price of 1000 -> 1000 - 100 = 900 which is 9€."
    )
    hidden: bool = False
    shipping_available: bool = True
