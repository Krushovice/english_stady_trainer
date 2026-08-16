from fastapi import APIRouter

from app.api.routes import auth, course, exercise, health, mistake, placement, review

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/api/v1")
api_router.include_router(course.router, prefix="/api/v1")
api_router.include_router(exercise.router, prefix="/api/v1")
api_router.include_router(placement.router, prefix="/api/v1")
api_router.include_router(mistake.router, prefix="/api/v1")
api_router.include_router(review.router, prefix="/api/v1")
