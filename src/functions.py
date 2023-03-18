from .schemas import UserIn, UserInDB


def fake_hash_pwd(raw_password: str) -> str:
    return "hashed" + raw_password


def fake_save_user(user_input: UserIn):
    hashed_password = fake_hash_pwd(user_input.raw_password)
    user_in_db = UserInDB(**user_input.dict(), hashed_password=hashed_password)
    print("User saved!")

    return user_in_db
