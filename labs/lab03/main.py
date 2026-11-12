import sqlite3
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, status

from labs.lab03 import repository
from labs.lab03.database import initialize_database
from labs.lab03.schemas import (
    CategoryCreate,
    CategoryRead,
    RecordCreate,
    RecordRead,
    RecordReplace,
)
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Сервіс обліку спрацювань засобів захисту",
    description="Lab 3: FastAPI та SQLite для обліку спрацювань засобів захисту (Варіант 5). Одиниця вимірювання: events.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/ping", tags=["System"])
def ping():
    return {"status": "ok"}


@app.get("/student", tags=["System"])
def get_student_info():
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }


@app.get("/categories", response_model=list[CategoryRead], tags=["Categories"])
def get_categories():
    return repository.get_all_categories()


@app.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Categories"],
)
def create_category(category: CategoryCreate):
    try:
        return repository.create_category(category.name)
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Категорія з такою назвою вже існує.",
        )


@app.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Categories"],
)
def delete_category(category_id: int):
    try:
        deleted = repository.delete_category(category_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Категорію не знайдено.",
            )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Неможливо видалити категорію, яка містить записи.",
        )


@app.get("/records", response_model=list[RecordRead], tags=["Records"])
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


@app.get("/records/{record_id}", response_model=RecordRead, tags=["Records"])
def get_record(record_id: int):
    record = repository.get_record_by_id(record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )
    return record


@app.post(
    "/records",
    response_model=RecordRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Records"],
)
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


@app.put("/records/{record_id}", response_model=RecordRead, tags=["Records"])
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


@app.delete(
    "/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Records"]
)
def delete_record(record_id: int):
    deleted = repository.delete_record(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запис не знайдено.",
        )


@app.post(
    "/records/bulk",
    response_model=list[RecordRead],
    status_code=status.HTTP_201_CREATED,
    tags=["Records"],
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
