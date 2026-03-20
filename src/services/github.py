"""
GitHub API client for fetching repository data.
Handles issues, pull requests, and source code retrieval.
"""

import os
import re
import base64
import logging
import requests
from langchain_core.documents import Document
from src.config import settings

logger = logging.getLogger(__name__)

HEADERS = {"Authorization": f"Bearer {settings.GITHUB_TOKEN}"} if settings.GITHUB_TOKEN else {}

CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php"}
SKIP_DIRS = {"node_modules", "venv", ".git", "__pycache__", "dist", "build", ".next"}


def parse_repo_url(repo_input: str) -> tuple[str, str]:
    """
    Parse GitHub repo from 'owner/repo' or full URL.
    Returns (owner, repo) or raises ValueError.
    """
    repo_input = repo_input.strip().rstrip("/")

    match = re.match(r"https?://github\.com/([^/]+)/([^/]+)", repo_input)
    if match:
        return match.group(1), match.group(2)

    match = re.match(r"^([^/]+)/([^/]+)$", repo_input)
    if match:
        return match.group(1), match.group(2)

    raise ValueError(
        f"Invalid repo format: '{repo_input}'. Use 'owner/repo' or 'https://github.com/owner/repo'"
    )


# ─── Internal Helpers ─────────────────────────────────────────────────────────


def _api_get(url: str, params: dict = None) -> dict | list | None:
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 403:
            logger.warning(f"Rate limited: {url}")
        elif response.status_code == 404:
            logger.warning(f"Not found: {url}")
        else:
            logger.error(f"GitHub API {response.status_code}: {url}")
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
    return None


def _paginate(url: str, params: dict = None, max_pages: int = 3) -> list:
    all_results = []
    params = params or {}
    params.setdefault("per_page", 30)

    for page in range(1, max_pages + 1):
        params["page"] = page
        data = _api_get(url, params)
        if not data:
            break
        all_results.extend(data)
        if len(data) < params["per_page"]:
            break

    return all_results


# ─── Public API ───────────────────────────────────────────────────────────────


def fetch_issues(owner: str, repo: str) -> list[Document]:
    """Fetch open issues as LangChain Documents."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    issues = _paginate(url, params={"state": "open"})

    docs = []
    for entry in issues:
        if "pull_request" in entry:
            continue

        metadata = {
            "type": "issue",
            "author": entry["user"]["login"],
            "comments": entry["comments"],
            "labels": [l["name"] for l in entry.get("labels", [])],
            "created_at": entry["created_at"],
            "url": entry["html_url"],
            "number": entry["number"],
        }

        content = f"[Issue #{entry['number']}] {entry['title']}"
        if entry.get("body"):
            content += f"\n\n{entry['body']}"

        docs.append(Document(page_content=content, metadata=metadata))

    return docs


def fetch_pull_requests(owner: str, repo: str) -> list[Document]:
    """Fetch recent PRs with diffs as LangChain Documents."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    prs = _paginate(url, params={"state": "all", "sort": "updated"}, max_pages=2)

    docs = []
    for pr in prs:
        metadata = {
            "type": "pull_request",
            "author": pr["user"]["login"],
            "state": pr["state"],
            "merged": pr.get("merged_at") is not None,
            "created_at": pr["created_at"],
            "url": pr["html_url"],
            "number": pr["number"],
        }

        content = f"[PR #{pr['number']}] {pr['title']}"
        if pr.get("body"):
            content += f"\n\n{pr['body']}"

        files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr['number']}/files"
        files = _api_get(files_url) or []
        if files:
            changed = [f["filename"] for f in files[:20]]
            content += f"\n\nChanged files: {', '.join(changed)}"
            for f in files[:5]:
                patch = f.get("patch", "")
                if patch and len(patch) < 2000:
                    content += f"\n\n--- {f['filename']} ---\n{patch}"

        docs.append(Document(page_content=content, metadata=metadata))

    return docs


def fetch_code_files(owner: str, repo: str, path: str = "") -> list[Document]:
    """Recursively fetch source code files as LangChain Documents."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    items = _api_get(url)
    if not items:
        return []
    if isinstance(items, dict):
        items = [items]

    docs = []
    for item in items:
        name = item.get("name", "")

        if item["type"] == "dir" and name not in SKIP_DIRS:
            docs.extend(fetch_code_files(owner, repo, item["path"]))
        elif item["type"] == "file":
            _, ext = os.path.splitext(name)
            if ext in CODE_EXTENSIONS and item.get("size", 0) < 50_000:
                file_content = _download_file(item)
                if file_content:
                    metadata = {
                        "type": "code_file",
                        "path": item["path"],
                        "size": item["size"],
                        "url": item["html_url"],
                    }
                    content = f"[File: {item['path']}]\n\n{file_content}"
                    docs.append(Document(page_content=content, metadata=metadata))

    return docs


def _download_file(item: dict) -> str | None:
    if item.get("content"):
        try:
            return base64.b64decode(item["content"]).decode("utf-8", errors="replace")
        except Exception:
            pass

    download_url = item.get("download_url")
    if download_url:
        try:
            resp = requests.get(download_url, timeout=10)
            if resp.status_code == 200:
                return resp.text
        except requests.RequestException:
            pass

    return None


def fetch_all(repo_input: str) -> list[Document]:
    """
    Fetch all data from a GitHub repo.
    Accepts 'owner/repo' or full URL.
    Returns list of LangChain Documents.
    """
    owner, repo = parse_repo_url(repo_input)
    logger.info(f"Fetching data from {owner}/{repo}")

    all_docs = []

    logger.info("Fetching issues...")
    issues = fetch_issues(owner, repo)
    all_docs.extend(issues)
    logger.info(f"Found {len(issues)} issues")

    logger.info("Fetching pull requests...")
    prs = fetch_pull_requests(owner, repo)
    all_docs.extend(prs)
    logger.info(f"Found {len(prs)} PRs")

    logger.info("Fetching code files...")
    code = fetch_code_files(owner, repo)
    all_docs.extend(code)
    logger.info(f"Found {len(code)} code files")

    logger.info(f"Total: {len(all_docs)} documents")
    return all_docs
