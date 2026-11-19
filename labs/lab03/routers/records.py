import sqlite3
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from labs.lab03 import repository
from labs.lab03.schemas import RecordCreate, RecordRead, RecordReplace

router = APIRouter(prefix="/records", tags=["Records"])


@router.get("", response_model=list[RecordRead])
def get_records(
    category_id: int | None = Query(None, gt=0),
    status: Literal["new", "in_progress", "done"] | None = None,
    min_value: int | None = Query(None, ge=0),
    q: str | None = Query(None, min_length=1, max_length=120),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    return repository.get_filtered_records(
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=RecordRead)
def get_record(record_id: int):
    record = repository.get_record_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )
    return record


@router.post("", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create_record(record: RecordCreate):
    try:
        return repository.create_record(record.model_dump())
    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if "foreign key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вказана категорія не існує.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Запис із таким кодом (code) вже існує.",
        )


@router.put("/{record_id}", response_model=RecordRead)
def replace_record(record_id: int, record: RecordReplace):
    existing = repository.get_record_by_id(record_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )
    try:
        updated = repository.update_record(record_id, record.model_dump())
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Запис не знайдено.",
            )
        return updated
    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if "foreign key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Вказана категорія не існує.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Конфлікт унікальності (код вже використовується).",
        )


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int):
    deleted = repository.delete_record(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )


@router.post(
    "/bulk", response_model=list[RecordRead], status_code=status.HTTP_201_CREATED
)
def create_records_bulk(records: list[RecordCreate]):
    if not records or len(records) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Кількість елементів у пакеті має бути від 1 до 100.",
        )

    records_data = [r.model_dump() for r in records]
    try:
        return repository.create_records_bulk(records_data)
    except sqlite3.IntegrityError as e:
        error_msg = str(e).lower()
        if "foreign key" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Один із записів посилається на неіснуючу категорію.",
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Конфлікт даних (дублікат коду всередині пакету або в базі).",
        )
