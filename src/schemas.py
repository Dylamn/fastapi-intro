from datetime import datetime, time
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, HttpUrl, EmailStr


class Image(BaseModel):
    name: str
    url: HttpUrl


class ItemOptions(BaseModel):
    promotion: int = Field(
        default=0,
        title="A promotion to apply to the price.",
        description="The promotion value will be substracted to the base price."
                    "e.g. for a price of 1000 -> 1000 - 100 = 900 which is 9€.",
        example="200"
    )
    hidden: bool = False
    shipping_available: bool = True


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
    tags: set[str] = set()
    images: list[Image] | None = None

    class Config:
        schema_extra = {
            "example": {
                "name": "keyboard",
                "description": "A very nice keyboard.",
                "price": 7900,
                "tax": 0.2,
                "tags": ["Cherry MX Red", "RGB", "Mechanical"],
                "images": [
                    {
                        "name": "Front view",
                        "url": "https://via.placeholder.com/640x360"
                    },
                    {
                        "name": "Switch",
                        "url": "https://via.placeholder.com/640x360"
                    }
                ]
            }
        }


class ItemPartialUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = Field(
        default=None,
        title="The price of the item.",
        gt=100,
        le=99999999
    )
    tax: float | None = None
    tags: set[str] | None = None
    images: list[Image] | None = None


class BaseVehicle(BaseModel):
    description: str
    type: str


class CarVehicle(BaseVehicle):
    type = "car"


class PlaneVehicle(BaseVehicle):
    type = "plane"
    size: int


class Offer(BaseModel):
    id: UUID = Field(example=uuid4())
    name: str = Field(example="Keyboard, mouse pack")
    description: str | None = Field(default=None, example="This pack includes...")
    price: float = Field(example=35000)
    items: list[Item]
    start_datetime: datetime | None = None
    end_datetime: datetime | None = None
    repeat_at: time | None = None


class BaseUser(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None


class UserIn(BaseUser):
    raw_password: str


class UserOut(BaseUser):
    ...


class UserInDB(BaseUser):
    hashed_password: str
