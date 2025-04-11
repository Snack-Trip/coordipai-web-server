import exceptions.definitions as definitions
from fastapi import APIRouter, Request
from src.auth import service, schemas

router = APIRouter(prefix="/auth", tags=["GitHub OAuth"])

@router.get("/login", summary="Redirect to GitHub login page")
def login_with_github():
   return service.login_with_github()

@router.get("/github/callback", response_model=schemas.GitHubAuthResponse, summary="Callback for GitHub login")
async def github_callback(request: Request):
   return await service.github_callback(request)

@router.get("/err")
def test():
   raise definitions.TestException("Oh no")
    

# @router.get("/repos/{owner}/{repo}/issues")
# async def get_repo_issues(owner: str, repo: str, user: User = Depends(get_current_user)):
#     if not user.github_access_token:
#         raise HTTPException(status_code=401, detail="No GitHub access token")
    
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             f"https://api.github.com/repos/{owner}/{repo}/issues",
#             headers={"Authorization": f"Bearer {user.github_access_token}"}
#         )
#         if response.status_code != 200:
#             raise HTTPException(status_code=response.status_code, detail=response.text)
#         return response.json()