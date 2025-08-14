from fastapi import APIRouter, Depends
from app.dependencies.auth import get_current_active_user
from app.models.schemas import UserResponse
from app.db.models import User

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user