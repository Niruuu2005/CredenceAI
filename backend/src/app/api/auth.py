from typing import List, Optional
import httpx
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.api_key_service import create_api_key, validate_api_key
from app.models import ApiKey, User
from app.schemas import ApiKeyCreateRequest, ApiKeyCreateResponse, ApiKeyResponse
from app.services.security import create_access_token, get_current_user
from app.services.quota_service import count_user_jobs_in_period
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

class GoogleCallbackRequest(BaseModel):
    code: str

class GitHubCallbackRequest(BaseModel):
    code: str

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Validates developer admin credentials and issues a JWT token (local dev only)."""
    if settings.APP_ENV != "local":
        raise HTTPException(status_code=503, detail="Developer login is disabled outside local environment.")
    if not settings.DEV_LOGIN_USERNAME or not settings.DEV_LOGIN_PASSWORD:
        raise HTTPException(status_code=503, detail="Developer login is not configured. Set DEV_LOGIN_USERNAME and DEV_LOGIN_PASSWORD.")
    if request.username == settings.DEV_LOGIN_USERNAME and request.password == settings.DEV_LOGIN_PASSWORD:
        user_id = settings.DEV_LOGIN_USERNAME
        email = f"{settings.DEV_LOGIN_USERNAME}@localhost"
        name = settings.DEV_LOGIN_USERNAME
        picture = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?auto=format&fit=crop&w=150&h=150"
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=email,
                name=name,
                picture=picture
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.name = name
            user.picture = picture
            db.commit()
            db.refresh(user)
            
        token_payload = {
            "sub": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture
        }
        jwt_token = create_access_token(token_payload)
        
        return {
            "token": jwt_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "plan": user.plan,
                "search_quota_limit": user.search_quota_limit
            }
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid developer credentials.")

@router.post("/keys", response_model=ApiKeyCreateResponse, status_code=201)
def issue_api_key(
    request: ApiKeyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = create_api_key(
        db,
        owner=current_user.id,
        label=request.label,
        user_id=current_user.id,
    )
    return key

@router.get("/keys", response_model=List[ApiKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    keys = (
        db.query(ApiKey)
        .filter(ApiKey.revoked == False, ApiKey.user_id == current_user.id)
        .all()
    )
    return keys

@router.delete("/keys/{key_id}")
def revoke_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = (
        db.query(ApiKey)
        .filter(ApiKey.id == key_id, ApiKey.user_id == current_user.id)
        .first()
    )
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.revoked = True
    db.commit()
    return {"message": "API key successfully revoked"}

@router.get("/validate")
def validate_key(x_api_key: str = Header(None, alias="X-API-Key"), db: Session = Depends(get_db)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header is required.")
    result = validate_api_key(db, x_api_key)
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key.")
    return {"valid": True, "owner": result.owner}


# --- Google OAuth2 & Session Authentication Endpoints ---

@router.get("/google/url")
def get_google_auth_url():
    """Generates Google login URL or mock callback url for offline testing."""
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_REDIRECT_URI:
        # Production auth URL
        url = (
            f"https://accounts.google.com/o/oauth2/v2/auth?"
            f"response_type=code&"
            f"client_id={settings.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
            f"scope=openid%20email%20profile&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        return {"url": url, "mock": False}
    elif settings.APP_ENV == "local":
        logger.info("Auth settings for Google are missing. Activating offline development mock login.")
        return {"url": "/auth/google/callback?code=mock_dev_code", "mock": True}
    else:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI.",
        )


def _issue_session_for_user(db: Session, user_id: str, email: str, name: str, picture: str | None):
    """Create or update user record and return JWT + user payload."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()
        if user:
            if name:
                user.name = name
            if picture:
                user.picture = picture
            db.commit()
            db.refresh(user)
    if not user:
        user = User(id=user_id, email=email, name=name, picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if user.id == user_id:
            user.name = name
            user.picture = picture
            db.commit()
            db.refresh(user)

    token_payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
    jwt_token = create_access_token(token_payload)
    return {
        "token": jwt_token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "plan": user.plan,
            "search_quota_limit": user.search_quota_limit,
        },
    }


@router.post("/google/callback")
async def google_callback(request: GoogleCallbackRequest, db: Session = Depends(get_db)):
    """Exchanges auth code with Google API for profile details or performs local dev bypass."""
    user_id = ""
    email = ""
    name = ""
    picture = None

    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET and settings.GOOGLE_REDIRECT_URI:
        # Perform real Google OAuth2 code exchange
        try:
            async with httpx.AsyncClient() as client:
                # 1. Exchange authorization code for token
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code",
                        "code": request.code
                    }
                )
                if token_res.status_code != 200:
                    logger.error(f"Google token exchange failed: {token_res.text}")
                    raise HTTPException(status_code=400, detail="Token exchange with Google failed.")
                
                token_data = token_res.json()
                access_token = token_data.get("access_token")
                
                # 2. Retrieve user info using token
                user_res = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if user_res.status_code != 200:
                    logger.error(f"Google user info fetch failed: {user_res.text}")
                    raise HTTPException(status_code=400, detail="Failed to fetch user profile from Google.")
                
                user_info = user_res.json()
                user_id = user_info.get("sub")
                email = user_info.get("email")
                name = user_info.get("name")
                picture = user_info.get("picture")
        except HTTPException:
            raise
        except Exception:
            logger.exception("Unexpected error in real Google OAuth exchange")
            raise HTTPException(status_code=500, detail="Authentication server error during Google OAuth.")
    elif settings.APP_ENV == "local":
        if request.code == "mock_dev_code":
            user_id = "mock_jane_doe"
            email = "jane.doe@example.com"
            name = "Jane Doe"
            picture = "https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&h=150"
        else:
            raise HTTPException(status_code=400, detail="Invalid code supplied in offline testing mode.")
    else:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI.",
        )

    if not user_id or not email:
        raise HTTPException(status_code=400, detail="Missing required user identity properties.")

    return _issue_session_for_user(db, user_id, email, name, picture)


# --- GitHub OAuth2 Endpoints ---

@router.get("/github/url")
def get_github_auth_url():
    """Generates GitHub login URL or mock callback url for offline testing."""
    if settings.GITHUB_CLIENT_ID and settings.GITHUB_REDIRECT_URI:
        from urllib.parse import urlencode
        params = urlencode({
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "read:user user:email",
        })
        url = f"https://github.com/login/oauth/authorize?{params}"
        return {"url": url, "mock": False}
    elif settings.APP_ENV == "local":
        logger.info("GitHub auth settings missing. Activating offline development mock login.")
        return {"url": "/auth/github/callback?code=mock_github_code", "mock": True}
    else:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, and GITHUB_REDIRECT_URI.",
        )


@router.post("/github/callback")
async def github_callback(request: GitHubCallbackRequest, db: Session = Depends(get_db)):
    """Exchanges auth code with GitHub API for profile details or performs local dev bypass."""
    user_id = ""
    email = ""
    name = ""
    picture = None

    if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET and settings.GITHUB_REDIRECT_URI:
        try:
            async with httpx.AsyncClient() as client:
                token_res = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": settings.GITHUB_CLIENT_ID,
                        "client_secret": settings.GITHUB_CLIENT_SECRET,
                        "redirect_uri": settings.GITHUB_REDIRECT_URI,
                        "code": request.code,
                    },
                )
                if token_res.status_code != 200:
                    logger.error("GitHub token exchange failed: %s", token_res.text)
                    raise HTTPException(status_code=400, detail="Token exchange with GitHub failed.")

                token_data = token_res.json()
                if "error" in token_data:
                    logger.error("GitHub token error: %s", token_data)
                    raise HTTPException(status_code=400, detail=token_data.get("error_description", "GitHub OAuth failed."))

                access_token = token_data.get("access_token")
                if not access_token:
                    raise HTTPException(status_code=400, detail="GitHub did not return an access token.")

                user_res = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github+json",
                    },
                )
                if user_res.status_code != 200:
                    logger.error("GitHub user info fetch failed: %s", user_res.text)
                    raise HTTPException(status_code=400, detail="Failed to fetch user profile from GitHub.")

                user_info = user_res.json()
                github_id = user_info.get("id")
                user_id = f"gh_{github_id}"
                name = user_info.get("name") or user_info.get("login", "")
                picture = user_info.get("avatar_url")
                email = user_info.get("email")

                if not email:
                    emails_res = await client.get(
                        "https://api.github.com/user/emails",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/vnd.github+json",
                        },
                    )
                    if emails_res.status_code == 200:
                        emails = emails_res.json()
                        primary = next((e for e in emails if e.get("primary")), None)
                        if primary:
                            email = primary.get("email")
                        elif emails:
                            email = emails[0].get("email")
        except HTTPException:
            raise
        except Exception:
            logger.exception("Unexpected error in GitHub OAuth exchange")
            raise HTTPException(status_code=500, detail="Authentication server error during GitHub OAuth.")
    elif settings.APP_ENV == "local":
        if request.code == "mock_github_code":
            user_id = "gh_mock_dev"
            email = "dev@github.local"
            name = "GitHub Dev User"
            picture = "https://avatars.githubusercontent.com/u/0?v=4"
        else:
            raise HTTPException(status_code=400, detail="Invalid code supplied in offline testing mode.")
    else:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth is not configured. Set GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, and GITHUB_REDIRECT_URI.",
        )

    if not user_id or not email:
        raise HTTPException(status_code=400, detail="Missing required user identity properties.")

    return _issue_session_for_user(db, user_id, email, name, picture)


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns profile for currently authenticated user session."""
    search_used = count_user_jobs_in_period(db, current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "plan": current_user.plan,
        "search_quota_limit": current_user.search_quota_limit,
        "search_used": search_used,
    }

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None

@router.patch("/me")
def update_me(
    body: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.name is not None:
        current_user.name = body.name
    db.commit()
    db.refresh(current_user)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "plan": current_user.plan,
        "search_quota_limit": current_user.search_quota_limit,
    }

class UpgradeRequest(BaseModel):
    plan: str

@router.post("/upgrade")
def upgrade_plan(request: UpgradeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Local-only mock upgrade. Production must use Stripe checkout."""
    if settings.APP_ENV == "production":
        raise HTTPException(
            status_code=410,
            detail="Direct plan upgrades are disabled. Use POST /api/billing/checkout-session.",
        )
    if request.plan not in ["Free", "Pro", "Enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid plan selected.")
    
    current_user.plan = request.plan
    if request.plan == "Free":
        current_user.search_quota_limit = 50
    elif request.plan == "Pro":
        current_user.search_quota_limit = 500
    elif request.plan == "Enterprise":
        current_user.search_quota_limit = 5000
        
    db.commit()
    db.refresh(current_user)
    return {
        "message": f"Successfully upgraded to {request.plan} plan.",
        "plan": current_user.plan,
        "search_quota_limit": current_user.search_quota_limit
    }


