from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.auth.validators import clean_name, normalize_phone


class PhoneInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phone: str = Field(max_length=40)
    normalize = field_validator("phone")(normalize_phone)


class VerifyInput(PhoneInput):
    code: str = Field(pattern=r"^[0-9]{6}$")


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=1, max_length=100)

    clean = field_validator("display_name")(clean_name)
