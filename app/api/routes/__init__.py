from fastapi import APIRouter

from app.api.routes import (
    ai,
    auth,
    conversation,
    course,
    course_exam,
    exercise,
    health,
    homework,
    level_exam,
    mistake,
    placement,
    review,
    speaking,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/api/v1")
api_router.include_router(course.router, prefix="/api/v1")
api_router.include_router(exercise.router, prefix="/api/v1")
api_router.include_router(level_exam.router, prefix="/api/v1")
api_router.include_router(course_exam.router, prefix="/api/v1")
api_router.include_router(placement.router, prefix="/api/v1")
api_router.include_router(mistake.router, prefix="/api/v1")
api_router.include_router(review.router, prefix="/api/v1")
api_router.include_router(ai.router, prefix="/api/v1")
api_router.include_router(homework.router, prefix="/api/v1")
api_router.include_router(conversation.router, prefix="/api/v1")
api_router.include_router(speaking.router, prefix="/api/v1")
