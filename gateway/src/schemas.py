from pydantic import BaseModel


class AuthConfigurations(BaseModel):
    server_url: str
    realm: str
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str


class UserPayload(BaseModel):
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    realm_roles: list
