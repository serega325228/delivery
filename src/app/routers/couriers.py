from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException

from app.dependencies import get_courier_service
from app.exceptions import DomainError, NotFoundError
from app.schemas.courier import CourierReq, CourierRes
from app.services.courier import CourierService

router = APIRouter(prefix="/couriers", tags=["couriers"])
Couriers = Annotated[CourierService, Depends(get_courier_service)]


@router.post("", response_model=CourierRes, status_code=status.HTTP_201_CREATED)
async def create_courier(data: CourierReq, couriers: Couriers) -> CourierRes:
    try:
        courier = couriers.create(data.name, data.phone, data.capacity)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return CourierRes.from_domain(courier)


@router.get("", response_model=list[CourierRes])
async def get_couriers(couriers: Couriers) -> list[CourierRes]:
    try:
        all_couriers = couriers.get_all()
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return [CourierRes.from_domain(courier) for courier in all_couriers]


@router.get("/{courier_id}", response_model=CourierRes)
async def get_courier(courier_id: UUID, couriers: Couriers) -> CourierRes:
    try:
        courier = couriers.get(courier_id)
    except NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return CourierRes.from_domain(courier)
