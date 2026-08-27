import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from brasaland_auth_verify.surface import fastapi_docs_kwargs
from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from auth.db import resolve_db_path
from auth.email_sender import send_password_reset_email
from auth.health import auth_ready_reason
from auth.request_log import RequestIdAccessLogMiddleware, disable_uvicorn_access_log
from auth.security import TokenError
from auth.service import (
    authenticate_user,
    build_update_fields,
    can_modify_user,
    delete_user,
    ensure_bootstrap_admin,
    get_user,
    issue_token_pair,
    list_all_users,
    register_user,
    request_password_reset,
    reset_password,
    resolve_active_user,
    revoke_refresh_token,
    rotate_refresh_token,
    self_registration_enabled,
    update_profile,
    update_user,
)
from auth.types import (
    EmailAlreadyExistsError,
    InvalidRefreshTokenError,
    InvalidResetTokenError,
    UserNotFoundError,
    UserRecord,
)
from rate_limit import AUTH_RATE_LIMIT, limiter

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    try:
        resolve_db_path().parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.warning("Could not create TinyDB parent path; /readyz will fail")
    seeded = ensure_bootstrap_admin()
    if seeded is not None:
        logger.info("Bootstrap admin seeded: %s", seeded["email"])
    yield


app = FastAPI(
    title="Brasaland Auth Service",
    lifespan=lifespan,
    **fastapi_docs_kwargs(),
)
disable_uvicorn_access_log()
app.add_middleware(RequestIdAccessLogMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "unhandled_server_error",
        extra={"path": request.url.path, "request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred."},
    )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

FORGOT_PASSWORD_MESSAGE = "If that email is registered, a reset link has been sent."
EMAIL_ALREADY_REGISTERED = "Email already registered"
USER_NOT_FOUND = "User not found"
INVALID_REFRESH_TOKEN = "Invalid or expired refresh token"
SELF_REGISTRATION_DISABLED = "Self-registration is disabled"
ADMIN_REQUIRED = "Admin privileges required"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = ""
    phone: str = ""
    address: str = ""


class UserCreate(UserRegister):
    is_admin: bool = False


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr | None = None
    is_active: bool
    is_admin: bool
    created_at: str
    name: str = ""
    phone: str = ""
    address: str = ""


class ProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    address: str | None = None


class ProfileResponse(BaseModel):
    email: EmailStr
    name: str = ""
    phone: str = ""
    address: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class MessageResponse(BaseModel):
    message: str


def _to_response(user: UserRecord, requester: UserRecord) -> UserResponse:
    show_email = requester["id"] == user["id"] or requester["is_admin"]
    return UserResponse(
        id=user["id"],
        email=user["email"] if show_email else None,
        is_active=user["is_active"],
        is_admin=user["is_admin"],
        created_at=user["created_at"],
        name=user.get("name", ""),
        phone=user.get("phone", ""),
        address=user.get("address", ""),
    )


def _to_profile_response(user: UserRecord) -> ProfileResponse:
    return ProfileResponse(
        email=user["email"],
        name=user.get("name", ""),
        phone=user.get("phone", ""),
        address=user.get("address", ""),
    )


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserRecord:
    user = resolve_active_user(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> UserRecord:
    if not current_user["is_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ADMIN_REQUIRED,
        )
    return current_user


def _token_response(access_token: str, refresh_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(AUTH_RATE_LIMIT)
def auth_register(
    request: Request,
    body: Annotated[UserRegister, Body()],
) -> TokenResponse:
    if not self_registration_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=SELF_REGISTRATION_DISABLED,
        )
    try:
        user = register_user(
            body.email,
            body.password,
            name=body.name,
            phone=body.phone,
            address=body.address,
        )
    except EmailAlreadyExistsError as error:
        raise HTTPException(status_code=400, detail=EMAIL_ALREADY_REGISTERED) from error
    return _token_response(*issue_token_pair(user))


@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
def auth_login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    user = authenticate_user(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _token_response(*issue_token_pair(user))


@app.post("/auth/refresh", response_model=TokenResponse)
@limiter.limit(AUTH_RATE_LIMIT)
def auth_refresh(
    request: Request,
    body: Annotated[RefreshRequest, Body()],
) -> TokenResponse:
    try:
        access_token, refresh_token = rotate_refresh_token(body.refresh_token)
    except InvalidRefreshTokenError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_REFRESH_TOKEN,
        ) from error
    return _token_response(access_token, refresh_token)


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def auth_logout(body: RefreshRequest) -> Response:
    revoke_refresh_token(body.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/auth/forgot-password", response_model=MessageResponse)
def auth_forgot_password(request: Request, body: ForgotPasswordRequest) -> MessageResponse:
    token = request_password_reset(str(body.email))
    if token is not None:
        try:
            send_password_reset_email(str(body.email), token)
        except Exception:
            request_id = getattr(request.state, "request_id", None)
            logger.error(
                "password_reset_email_failed",
                extra={"request_id": request_id},
            )
    return MessageResponse(message=FORGOT_PASSWORD_MESSAGE)


@app.post("/auth/reset-password", response_model=MessageResponse)
def auth_reset_password(body: ResetPasswordRequest) -> MessageResponse:
    try:
        reset_password(body.token, body.new_password)
    except (InvalidResetTokenError, TokenError) as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token",
        ) from error
    return MessageResponse(message="Password has been reset. You can now log in.")


@app.get("/auth/me", response_model=UserResponse)
def auth_me(current_user: Annotated[UserRecord, Depends(get_current_user)]) -> UserResponse:
    return _to_response(current_user, current_user)


@app.get("/auth/profiles/me", response_model=ProfileResponse)
def get_profile_me(
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> ProfileResponse:
    return _to_profile_response(current_user)


@app.put("/auth/profiles/me", response_model=ProfileResponse)
def put_profile_me(
    body: ProfileUpdate,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> ProfileResponse:
    user = update_profile(
        current_user["id"],
        name=body.name,
        phone=body.phone,
        address=body.address,
    )
    return _to_profile_response(user)


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserCreate,
    current_user: Annotated[UserRecord, Depends(require_admin)],
) -> UserResponse:
    try:
        user = register_user(
            body.email,
            body.password,
            is_admin=body.is_admin,
            name=body.name,
            phone=body.phone,
            address=body.address,
        )
    except EmailAlreadyExistsError as error:
        raise HTTPException(status_code=400, detail=EMAIL_ALREADY_REGISTERED) from error
    return _to_response(user, current_user)


@app.get("/users", response_model=list[UserResponse])
def list_users(
    current_user: Annotated[UserRecord, Depends(require_admin)],
) -> list[UserResponse]:
    return [_to_response(user, current_user) for user in list_all_users()]


@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> UserResponse:
    if not can_modify_user(current_user, user_id):
        raise HTTPException(status_code=403, detail="Not allowed to view this user")
    try:
        user = get_user(user_id)
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND) from error
    return _to_response(user, current_user)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user_by_id(
    user_id: int,
    body: UserUpdate,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> UserResponse:
    if not can_modify_user(current_user, user_id):
        raise HTTPException(status_code=403, detail="Not allowed to update this user")

    fields = build_update_fields(body.email, body.password)
    if not fields:
        try:
            user = get_user(user_id)
        except UserNotFoundError as error:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND) from error
        return _to_response(user, current_user)

    try:
        user = update_user(user_id, fields)
    except EmailAlreadyExistsError as error:
        raise HTTPException(status_code=400, detail=EMAIL_ALREADY_REGISTERED) from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND) from error
    return _to_response(user, current_user)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(
    user_id: int,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> Response:
    if not can_modify_user(current_user, user_id):
        raise HTTPException(status_code=403, detail="Not allowed to delete this user")

    try:
        delete_user(user_id)
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=USER_NOT_FOUND) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/livez")
def livez() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> JSONResponse:
    reason = auth_ready_reason()
    if reason is None:
        return JSONResponse({"status": "ok"})
    return JSONResponse(
        {"status": "unavailable", "reason": reason},
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


@app.get("/")
async def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/forgot-password")
async def read_forgot_password() -> FileResponse:
    return FileResponse(STATIC_DIR / "forgot-password.html")


@app.get("/reset-password")
async def read_reset_password() -> FileResponse:
    return FileResponse(STATIC_DIR / "reset-password.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
