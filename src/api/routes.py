"""
API route definitions.
Separates routing logic from business logic.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from src.config import settings
from src.api.middleware import verify_session, create_session
from src.services import github, vectorstore
from src.agent import builder
from src.tools.notes import clear_notes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")

# ─── App State ────────────────────────────────────────────────────────────────

_state = {
    "owner": None,
    "repo": None,
    "agent": None,
}


# ─── Routes ───────────────────────────────────────────────────────────────────


@router.get("/health")
async def health():
    repo = f"{_state['owner']}/{_state['repo']}" if _state["owner"] else None
    return {
        "status": "ok",
        "repo": repo,
        "auth_enabled": settings.auth_enabled,
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/auth")
async def authenticate(request: Request):
    if not settings.auth_enabled:
        return JSONResponse({"success": True, "message": "Auth disabled"})

    body = await request.json()
    password = body.get("password", "")

    if password == settings.APP_PASSWORD:
        token = create_session()
        response = JSONResponse({"success": True})
        response.set_cookie("session_token", token, httponly=True, max_age=86400)
        return response

    return JSONResponse({"success": False, "error": "Invalid password"}, status_code=401)


@router.post("/load-repo")
async def load_repo(request: Request):
    if not verify_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    body = await request.json()
    repo_input = body.get("repo", "").strip()

    if not repo_input:
        return JSONResponse({"error": "No repository provided"})

    try:
        owner, repo = github.parse_repo_url(repo_input)
    except ValueError as e:
        return JSONResponse({"error": str(e)})

    try:
        docs = github.fetch_all(repo_input)
        if not docs:
            return JSONResponse({
                "error": f"No data found for {owner}/{repo}. Check it exists and is public."
            })

        vstore = vectorstore.load_documents(docs)
        builder.build(vstore)
        _state["agent"] = True
        _state["owner"] = owner
        _state["repo"] = repo
        clear_notes()

        stats = {
            "issues": sum(1 for d in docs if d.metadata.get("type") == "issue"),
            "pull_requests": sum(1 for d in docs if d.metadata.get("type") == "pull_request"),
            "code_files": sum(1 for d in docs if d.metadata.get("type") == "code_file"),
            "total": len(docs),
        }

        logger.info(f"Loaded {owner}/{repo}: {stats}")
        return JSONResponse({
            "success": True,
            "message": f"Loaded {owner}/{repo}",
            "stats": stats,
        })

    except Exception as e:
        logger.exception(f"Failed to load repo: {e}")
        return JSONResponse({"error": f"Failed to load repository: {e}"}, status_code=500)


@router.post("/chat")
async def chat(request: Request):
    if not verify_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not _state["agent"]:
        return JSONResponse({"error": "No repository loaded. Load a repo first."})

    body = await request.json()
    message = body.get("message", "").strip()
    if not message:
        return JSONResponse({"error": "No message provided"})

    try:
        repo_info = f"{_state['owner']}/{_state['repo']}"
        from src.agent import builder
        response = builder.invoke(message, repo_info)
        return JSONResponse({"response": response})
    except Exception as e:
        logger.exception(f"Agent error: {e}")
        return JSONResponse({"error": f"Agent error: {e}"}, status_code=500)
