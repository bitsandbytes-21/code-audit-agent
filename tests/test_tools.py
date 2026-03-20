"""
Tests for audit tools.
Run with: pytest tests/ -v
"""

from src.tools.notes import save_note, get_notes, clear_notes


class TestNotes:
    def setup_method(self):
        clear_notes()

    def test_save_and_retrieve(self):
        result = save_note.invoke({"note": "Found SQL injection in login.py"})
        assert "saved" in result.lower()

        notes = get_notes.invoke({"query": ""})
        assert "SQL injection" in notes

    def test_filter_notes(self):
        save_note.invoke({"note": "XSS vulnerability in templates"})
        save_note.invoke({"note": "Hardcoded API key in config"})

        xss_notes = get_notes.invoke({"query": "XSS"})
        assert "XSS" in xss_notes
        assert "API key" not in xss_notes

    def test_empty_notes(self):
        result = get_notes.invoke({"query": ""})
        assert "No notes" in result

    def test_clear_notes(self):
        save_note.invoke({"note": "test note"})
        clear_notes()
        result = get_notes.invoke({"query": ""})
        assert "No notes" in result

    def test_no_match(self):
        save_note.invoke({"note": "something unrelated"})
        result = get_notes.invoke({"query": "nonexistent"})
        assert "No notes matching" in result
