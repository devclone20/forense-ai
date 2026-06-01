from fastapi import APIRouter

from app.api.v1 import activity, cases, members, transitions

router = APIRouter(prefix="/api/v1")

router.include_router(cases.router)
router.include_router(transitions.router)
router.include_router(members.router)
router.include_router(activity.router)
