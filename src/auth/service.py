import httpx
from fastapi import Request
from fastapi.responses import RedirectResponse
from src.auth import config
from sqlalchemy.orm import Session
from src.auth.models import User
from src.auth import schemas

GITHUB_OAUTH_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_OAUTH_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_API_USER_URL = "https://api.github.com/user"
GITHUB_API_REPO_URL = "https://api.github.com/user/repos"

def login_with_github():
    github_url = (
        f"{GITHUB_OAUTH_AUTHORIZE_URL}"
        f"?client_id={config.GITHUB_CLIENT_ID}"
        f"&redirect_uri={config.REDIRECT_URI}"
        "&scope=repo user"
    )
    return RedirectResponse(github_url)

async def exchange_code_for_token(code: str) -> str | None:
    async with httpx.AsyncClient() as client:
        res = await client.post(
            GITHUB_OAUTH_ACCESS_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id": config.GITHUB_CLIENT_ID,
                "client_secret": config.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": config.REDIRECT_URI,
            }
        )
        return res.json().get("access_token")

async def github_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}

    access_token = await exchange_code_for_token(code)
    if not access_token:
        return {"error": "Failed to get access token"}

    user = await get_github_user(access_token)
    repos = await get_user_repos(access_token)

    return schemas.GitHubAuthResponse(
        user=user,
        repositories=[
            schemas.RepoInfo(
                name=repo["name"],
                private=repo["private"],
                url=repo["html_url"],
                description=repo.get("description"),
            )
            for repo in repos
        ]
    )

async def get_github_user(access_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            GITHUB_API_USER_URL,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return res.json()

async def get_user_repos(access_token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        res = await client.get(
            GITHUB_API_REPO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"visibility": "all"}  # public + private repos
        )
        return res.json()

def get_or_create_user(db: Session, github_user: dict, access_token: str) -> User:
    user = db.query(User).filter(User.github_id == github_user["id"]).first()
    
    if user:
        user.github_access_token = access_token
    else:
        user = User(
            github_id=github_user["id"],
            github_login=github_user["login"],
            avatar_url=github_user.get("avatar_url", ""),
            github_access_token=access_token
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    return user