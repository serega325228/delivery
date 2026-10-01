from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.customer import Customer


class CustomerReq(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(pattern=r"^\+?[0-9 ()-]{7,20}$")


class CustomerRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    phone: str

    @classmethod
    def from_domain(cls, customer: Customer) -> "CustomerRes":
        return cls.model_validate(customer)
