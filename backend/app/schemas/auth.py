from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    # Demo accounts use the reserved .local TLD, which pydantic's EmailStr
    # rejects; validate the shape instead of the deliverability.
    email: str = Field(min_length=5, max_length=190, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    role: str
    team_id: int | None = None
    team_code: str | None = None
    team_name: str | None = None


class LoginResponse(BaseModel):
    token: str
    user: UserOut
