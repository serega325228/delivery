from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException

from app.exceptions import NotFoundError
from app.main import get_customer_service
from app.schemas.customer import CustomerReq, CustomerRes
from app.services.customer import CustomerService, DomainError

router = APIRouter(prefix="/customers", tags=["customers"])

Customers = Annotated[CustomerService, Depends(get_customer_service)]

@router.post("", response_model=CustomerRes, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CustomerReq,
    customers: Customers,
) -> CustomerRes:
    try:
        customer = customers.create(
            request.name,
            request.phone,
        )
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return CustomerRes.from_domain(customer)


@router.get("", response_model=list[CustomerRes])
async def get_customers(
    customers: Customers,
) -> list[CustomerRes]:
    try:
        all_customers = customers.get_all()
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return [CustomerRes.from_domain(customer) for customer in all_customers]


@router.get("/{customer_id}", response_model=CustomerRes)
async def get_customer(
    customer_id: UUID,
    customers: Customers,
) -> CustomerRes:
    try:
        customer = customers.get(customer_id)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return CustomerRes.from_domain(customer)
