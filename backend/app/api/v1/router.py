from fastapi import APIRouter

from app.api.v1 import (
    account,
    activity,
    admin_users,
    auth,
    cases,
    invites,
    members,
    recovery,
    transitions,
)

router = APIRouter(prefix="/api/v1")

# Auth + identity (no RLS needed — pre-auth or own account)
router.include_router(auth.router)
router.include_router(recovery.router)
router.include_router(invites.router)
router.include_router(account.router)
router.include_router(admin_users.router)

# Case management (RLS-protected)
router.include_router(cases.router)
router.include_router(transitions.router)
router.include_router(members.router)
router.include_router(activity.router)
