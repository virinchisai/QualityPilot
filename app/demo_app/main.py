"""Enterprise-style demo system under test."""

import asyncio
import random
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.demo_app.rate_limit import login_limiter
from app.demo_app.schemas import (
    LoginRequest,
    LogoutRequest,
    ProfileUpdate,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from qualitypilot.config import Settings, get_settings
from qualitypilot.database import RefreshToken, User, get_db, init_db
from qualitypilot.observability.middleware import ObservabilityMiddleware
from qualitypilot.security.auth import (
    create_token,
    decode_token,
    hash_jti,
    hash_password,
    validate_password,
    verify_password,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="QualityPilot Demo Enterprise App",
    version="0.1.0",
    description="System under test for authentication, authorization, API, and UI quality flows.",
    lifespan=lifespan,
)
app.add_middleware(ObservabilityMiddleware, app_name="demo_app")
STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC), name="static")


async def inject_faults(settings: Settings = Depends(get_settings)) -> None:
    if settings.defect_delay_ms:
        await asyncio.sleep(settings.defect_delay_ms / 1000)
    if settings.defect_random_failure and random.random() < 0.25:  # noqa: S311 - deliberate demo
        raise HTTPException(503, "intentional intermittent failure")


def issue_token_pair(user: User, db: Session, settings: Settings, family_id: str | None = None):
    family = family_id or str(uuid.uuid4())
    access, _ = create_token(
        subject=str(user.id),
        role=user.role,
        secret=settings.jwt_secret,
        minutes=settings.access_token_minutes,
        token_type="access",
    )
    refresh, claims = create_token(
        subject=str(user.id),
        role=user.role,
        secret=settings.jwt_secret,
        minutes=settings.refresh_token_minutes,
        token_type="refresh",
        family_id=family,
    )
    db.add(
        RefreshToken(
            jti_hash=hash_jti(claims["jti"]),
            family_id=family,
            user_id=user.id,
            expires_at=claims["exp"].replace(tzinfo=None),
        )
    )
    db.commit()
    return TokenResponse(
        access_token=access, refresh_token=refresh, expires_in=settings.access_token_minutes * 60
    )


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing bearer token")
    try:
        claims = decode_token(
            authorization[7:],
            settings.jwt_secret,
            verify_exp=not settings.defect_allow_expired_tokens,
        )
        if claims.get("type") != "access" or not claims.get("sub"):
            raise jwt.InvalidTokenError("invalid token type or subject")
        user = db.get(User, int(claims["sub"]))
        if not user or not user.active:
            raise jwt.InvalidTokenError("unknown or inactive user")
        return user
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid or expired token") from exc


def admin_user(
    user: User = Depends(current_user), settings: Settings = Depends(get_settings)
) -> User:
    if user.role != "admin" and not settings.defect_break_admin_auth:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "admin role required")
    return user


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC / "dashboard.html")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "demo-app"}


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post(
    "/api/register",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(inject_faults)],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(409, "email already registered")
    errors = validate_password(payload.password)
    if errors:
        raise HTTPException(422, {"password": errors})
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/api/login", response_model=TokenResponse, dependencies=[Depends(inject_faults)])
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    client = request.client.host if request.client else "unknown"
    if not login_limiter.allowed(
        f"{client}:{payload.email.lower()}",
        settings.login_rate_limit,
        settings.login_rate_window_seconds,
    ):
        raise HTTPException(
            429,
            "too many login attempts",
            headers={"Retry-After": str(settings.login_rate_window_seconds)},
        )
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    return issue_token_pair(user, db, settings)


@app.post("/api/token/refresh", response_model=TokenResponse, dependencies=[Depends(inject_faults)])
def refresh(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        claims = decode_token(payload.refresh_token, settings.jwt_secret)
        if claims.get("type") != "refresh":
            raise jwt.InvalidTokenError("wrong token type")
        stored = (
            db.query(RefreshToken).filter(RefreshToken.jti_hash == hash_jti(claims["jti"])).first()
        )
        now = datetime.now(UTC).replace(tzinfo=None)
        if not stored or stored.revoked or stored.expires_at <= now:
            raise jwt.InvalidTokenError("refresh token revoked or unknown")
        user = db.get(User, int(claims["sub"]))
        if not user:
            raise jwt.InvalidTokenError("unknown user")
        if settings.defect_disable_refresh_rotation:
            access, _ = create_token(
                subject=str(user.id),
                role=user.role,
                secret=settings.jwt_secret,
                minutes=settings.access_token_minutes,
                token_type="access",
            )
            return TokenResponse(
                access_token=access,
                refresh_token=payload.refresh_token,
                expires_in=settings.access_token_minutes * 60,
            )
        replacement = issue_token_pair(user, db, settings, stored.family_id)
        replacement_claims = decode_token(replacement.refresh_token, settings.jwt_secret)
        stored.revoked = True
        stored.replaced_by_hash = hash_jti(replacement_claims["jti"])
        db.commit()
        return replacement
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(401, "invalid or revoked refresh token") from exc


@app.post("/api/logout", status_code=204)
def logout(
    payload: LogoutRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    try:
        claims = decode_token(payload.refresh_token, settings.jwt_secret, verify_exp=False)
        family = claims.get("family_id")
        if family:
            db.execute(
                update(RefreshToken).where(RefreshToken.family_id == family).values(revoked=True)
            )
            db.commit()
    except jwt.InvalidTokenError:
        pass
    return Response(status_code=204)


@app.get("/api/me", response_model=UserResponse, dependencies=[Depends(inject_faults)])
def me(user: User = Depends(current_user)):
    return user


@app.patch("/api/me", response_model=UserResponse)
def update_profile(
    payload: ProfileUpdate, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    user.display_name = payload.display_name
    db.commit()
    db.refresh(user)
    return user


@app.get("/api/admin/audit")
def admin_audit(user: User = Depends(admin_user)):
    return {"message": "admin audit access granted", "actor": user.email, "events": []}


@app.get("/api/defect-demo")
def defect_demo(settings: Settings = Depends(get_settings)):
    if settings.defect_malformed_json:
        return PlainTextResponse('{"result": broken', media_type="application/json")
    code = 202 if settings.defect_incorrect_status else 200
    return JSONResponse({"result": "ok", "defects_enabled": False}, status_code=code)
