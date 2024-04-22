from pydantic import BaseModel


class DbConfig(BaseModel):
    container_name: str
    db_name: str
    user: str
    password: str
