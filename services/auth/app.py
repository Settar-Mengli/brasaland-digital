from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from auth.security import TokenError, create_access_token, decode_access_token, hash_password
from auth.service import (
    authenticate_user,
    delete_user,
    get_user,
    list_all_users,
    register_user,
    update_user,
)
from auth.types import EmailAlreadyExistsError, UserNotFoundError, UserRecord

app = FastAPI(title="Brasaland Auth Service")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)


class UserResponse(BaseModel):
    id: int
    email: EmailStr | None = None
    is_active: bool
    is_admin: bool
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _to_response(user: UserRecord, requester: UserRecord) -> UserResponse:
    show_email = requester["id"] == user["id"] or requester["is_admin"]
    return UserResponse(
        id=user["id"],
        email=user["email"] if show_email else None,
        is_active=user["is_active"],
        is_admin=user["is_admin"],
        created_at=user["created_at"],
    )


def _issue_token(user: UserRecord) -> TokenResponse:
    token = create_access_token({"sub": str(user["id"]), "user_id": user["id"]})
    return TokenResponse(access_token=token, token_type="bearer")


def _user_id_from_token(payload: dict) -> int | None:
    if "user_id" in payload:
        return int(payload["user_id"])
    subject = payload.get("sub")
    if subject is None:
        return None
    return int(subject)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserRecord:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
    except TokenError as error:
        raise credentials_error from error

    user_id = _user_id_from_token(payload)
    if user_id is None:
        raise credentials_error

    try:
        user = get_user(user_id)
    except UserNotFoundError as error:
        raise credentials_error from error

    if not user["is_active"]:
        raise credentials_error

    return user


def _can_modify_user(requester: UserRecord, target_user_id: int) -> bool:
    return requester["id"] == target_user_id or requester["is_admin"]


def _build_update_fields(body: UserUpdate) -> dict[str, object]:
    fields: dict[str, object] = {}
    if body.email is not None:
        fields["email"] = str(body.email)
    if body.password is not None:
        fields["hashed_password"] = hash_password(body.password)
    return fields


@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def auth_register(body: UserRegister) -> TokenResponse:
    try:
        user = register_user(body.email, body.password)
    except EmailAlreadyExistsError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _issue_token(user)


@app.post("/auth/login", response_model=TokenResponse)
def auth_login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    user = authenticate_user(form.username, form.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_token(user)


@app.get("/auth/me", response_model=UserResponse)
def auth_me(current_user: Annotated[UserRecord, Depends(get_current_user)]) -> UserResponse:
    return _to_response(current_user, current_user)


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserRegister,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> UserResponse:
    try:
        user = register_user(body.email, body.password)
    except EmailAlreadyExistsError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _to_response(user, current_user)


@app.get("/users", response_model=list[UserResponse])
def list_users(
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> list[UserResponse]:
    return [_to_response(user, current_user) for user in list_all_users()]


@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> UserResponse:
    try:
        user = get_user(user_id)
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _to_response(user, current_user)


@app.put("/users/{user_id}", response_model=UserResponse)
def update_user_by_id(
    user_id: int,
    body: UserUpdate,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> UserResponse:
    if not _can_modify_user(current_user, user_id):
        raise HTTPException(status_code=403, detail="Not allowed to update this user")

    fields = _build_update_fields(body)
    if not fields:
        try:
            user = get_user(user_id)
        except UserNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return _to_response(user, current_user)

    try:
        user = update_user(user_id, fields)
    except EmailAlreadyExistsError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return _to_response(user, current_user)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_by_id(
    user_id: int,
    current_user: Annotated[UserRecord, Depends(get_current_user)],
) -> Response:
    if not _can_modify_user(current_user, user_id):
        raise HTTPException(status_code=403, detail="Not allowed to delete this user")

    try:
        delete_user(user_id)
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
