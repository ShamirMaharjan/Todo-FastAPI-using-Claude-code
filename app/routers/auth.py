"""Authentication router with registration and login endpoints.

This router is the HTTP layer only: it receives requests, delegates all
business logic to ``AuthService``, and translates domain exceptions into
HTTP responses.  It never imports ``AsyncSession`` or SQLAlchemy query
primitives, enforcing strict layered separation.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from ..core.security import create_access_token
from ..dependencies import get_auth_service
from ..schemas import Token, UserCreate, UserResponse
from ..services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_in: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Register a new user account.

    Args:
        user_in: The user creation data containing email and password.
        auth_service: The injected authentication service.

    Returns:
        The created user serialized as a ``UserResponse``.
    """
    return await auth_service.register_user(user_in)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Authenticate a user and return a bearer access token.

    Args:
        form_data: OAuth2 password request form containing ``username``
            (used as the email) and ``password``.
        auth_service: The injected authentication service.

    Returns:
        A ``Token`` containing the JWT ``access_token`` and ``token_type``.
    """
    user = await auth_service.authenticate_user(
        form_data.username, form_data.password
    )
    access_token = create_access_token(data={"sub": user.email})
    return Token(access_token=access_token, token_type="bearer")
