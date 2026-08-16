from fastapi import APIRouter

from app.api.routes import auth, course, exercise, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/api/v1")
api_router.include_router(course.router, prefix="/api/v1")
api_router.include_router(exercise.router, prefix="/api/v1")
