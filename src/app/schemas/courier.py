from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.courier import Courier


class CourierReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(pattern=r"^\+?[0-9 ()-]{7,20}$")


class CourierRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str
    available: bool

    @classmethod
    def from_domain(cls, courier: Courier) -> "CourierRes":
        return cls.model_validate(courier)
