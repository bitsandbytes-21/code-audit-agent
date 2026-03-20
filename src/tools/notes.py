"""
Note-taking tools for the audit agent.
Allows saving and retrieving findings during an audit session.
"""

from datetime import datetime
from langchain_core.tools import tool

_notes: list[dict] = []


@tool
def save_note(note: str) -> str:
    """
    Save an important audit finding or note.
    Use this to record critical security issues, action items, or key observations.
    """
    entry = {
        "id": len(_notes) + 1,
        "note": note,
        "timestamp": datetime.now().isoformat(),
    }
    _notes.append(entry)
    return f"Note #{entry['id']} saved."


@tool
def get_notes(query: str = "") -> str:
    """
    Retrieve all saved audit notes. Optionally filter by keyword.
    """
    if not _notes:
        return "No notes saved yet."

    filtered = _notes
    if query:
        filtered = [n for n in _notes if query.lower() in n["note"].lower()]

    if not filtered:
        return f"No notes matching '{query}'."

    lines = [f"--- Audit Notes ({len(filtered)}) ---"]
    for n in filtered:
        lines.append(f"#{n['id']} [{n['timestamp'][:16]}]: {n['note']}")

    return "\n".join(lines)


def clear_notes():
    """Clear all notes (called when loading a new repo)."""
    _notes.clear()
