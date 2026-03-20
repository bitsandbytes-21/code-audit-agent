"""
Agent construction and management.
"""

import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_core.tools import create_retriever_tool
from langchain_astradb import AstraDBVectorStore

from src.config import settings
from src.services import vectorstore
from src.tools.analyzer import static_analysis, code_quality_check
from src.tools.notes import save_note, get_notes

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior security engineer and code auditor with expertise in:
- Application security (OWASP Top 10)
- Python, JavaScript, and web framework best practices
- Code review and architecture assessment

When auditing, check for:
1. SECURITY: Hardcoded secrets, SQL injection, XSS, CSRF, auth flaws, insecure deserialization
2. RELIABILITY: Error handling, edge cases, null checks, race conditions
3. QUALITY: Code duplication, function complexity, test coverage, documentation
4. DEPENDENCIES: Known vulnerabilities, outdated packages

Format findings with severity levels:
- CRITICAL: Exploitable security vulnerabilities, data exposure
- WARNING: Bad practices that could lead to issues
- INFO: Suggestions for improvement

Use repo_search to find context. Use static_analysis and code_quality_check for automated scanning.
Use save_note to record critical findings and get_notes to review them.
"""

_graph = None


def build(vstore: AstraDBVectorStore):
    """Build a LangGraph agent with all audit tools."""
    global _graph

    retriever = vectorstore.get_retriever(vstore)
    retriever_tool = create_retriever_tool(
        retriever,
        "repo_search",
        "Search repository issues, pull requests, and source code.",
    )

    tools = [retriever_tool, static_analysis, code_quality_check, save_note, get_notes]

    _graph = create_agent(
        model=ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, temperature=0),
        tools=tools,
        prompt=SYSTEM_PROMPT,
    )

    return _graph


def invoke(message: str, repo_info: str) -> str:
    """Send a message to the agent and return the response."""
    if not _graph:
        raise RuntimeError("Agent not built. Load a repo first.")

    inputs = {
        "messages": [
            {"role": "user", "content": f"[Auditing: {repo_info}]\n\n{message}"}
        ]
    }

    result = _graph.invoke(inputs)

    # Extract the last AI message
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and msg.content:
            return msg.content

    return "No response from agent."