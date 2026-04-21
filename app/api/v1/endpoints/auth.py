from fastapi import APIRouter, HTTPException, status, Depends, Form
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from app.models.schemas import UserCreate, UserLogin, TokenPair, MessageResponse
from app.services import user_service
from app.core.security import create_access_token, create_refresh_token
from app.core.dependencies import get_current_user_id

router = APIRouter(prefix="/auth", tags=["Auth"])


class RefreshRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: UserCreate):
    """Create a new user account."""
    user, error = user_service.register_user(data)
    if error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=error)
    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id)
    user_service.save_refresh_token(user.id, refresh)
    return {
        "success": True,
        "message": "Account created successfully",
        "user": {
            "id": user.id, "name": user.name,
            "email": user.email, "loyalty_tier": user.loyalty_tier,
        },
        "tokens": TokenPair(access_token=access, refresh_token=refresh, expires_in=3600),
    }


# ── This handles Swagger UI's OAuth2 form ─────────────────────────────────────
@router.post("/login/form", include_in_schema=False)
def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 password flow for Swagger UI.
    Swagger sends 'username' field — we treat it as email.
    """
    user, error = user_service.authenticate_user(form_data.username, form_data.password)
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id)
    user_service.save_refresh_token(user.id, refresh)
    # OAuth2 spec requires exactly this shape
    return {"access_token": access, "token_type": "bearer"}


# ── This handles normal JSON login from your frontend/app ─────────────────────
@router.post("/login")
def login(data: UserLogin):
    """Login with JSON body — use this from your frontend."""
    user, error = user_service.authenticate_user(data.email, data.password)
    if error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=error)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    access  = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id)
    user_service.save_refresh_token(user.id, refresh)
    return {
        "success": True,
        "message": "Login successful",
        "user": {
            "id": user.id, "name": user.name, "email": user.email,
            "loyalty_tier": user.loyalty_tier,
            "loyalty_points": user.loyalty_points,
            "is_premium": user.is_premium,
        },
        "tokens": TokenPair(access_token=access, refresh_token=refresh, expires_in=3600),
    }


@router.post("/refresh")
def refresh_token(body: RefreshRequest):
    uid = user_service.verify_refresh_token(body.refresh_token)
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
    user = user_service.get_user(uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user_service.invalidate_refresh_token(body.refresh_token)
    new_access  = create_access_token(user.id, user.email)
    new_refresh = create_refresh_token(user.id)
    user_service.save_refresh_token(user.id, new_refresh)
    return {
        "success": True,
        "tokens": TokenPair(access_token=new_access, refresh_token=new_refresh, expires_in=3600),
    }


@router.post("/logout", response_model=MessageResponse)
def logout(body: RefreshRequest, user_id: str = Depends(get_current_user_id)):
    user_service.invalidate_refresh_token(body.refresh_token)
    return MessageResponse(success=True, message="Logged out successfully")


@router.post("/change-password", response_model=MessageResponse)
def change_password(body: ChangePasswordRequest, user_id: str = Depends(get_current_user_id)):
    ok, msg = user_service.change_password(user_id, body.current_password, body.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return MessageResponse(success=True, message=msg)