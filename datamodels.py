from pydantic import BaseModel


class DbConfig(BaseModel):
    """
       Class for database configuration.
    """
    container_name: str
    db_name: str
    user: str
    password: str
