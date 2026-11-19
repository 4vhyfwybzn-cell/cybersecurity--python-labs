from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Сервіс обліку спрацювань засобів захисту",
    description="Lab 3: FastAPI та SQLite для обліку спрацювань засобів захисту (Варіант 5).",
    version="1.0.0",
    lifespan=lifespan,
)

# Підключаємо роутери
app.include_router(categories.router)
app.include_router(records.router)


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
