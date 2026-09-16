from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    password: str = Field(
        min_length=1,
        max_length=200,
    )


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
