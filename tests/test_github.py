"""
Tests for the GitHub service module.
Run with: pytest tests/ -v
"""

import pytest
from src.services.github import parse_repo_url


class TestParseRepoUrl:
    def test_owner_repo_format(self):
        owner, repo = parse_repo_url("techwithtim/Flask-Web-App-Tutorial")
        assert owner == "techwithtim"
        assert repo == "Flask-Web-App-Tutorial"

    def test_full_url(self):
        owner, repo = parse_repo_url("https://github.com/pallets/flask")
        assert owner == "pallets"
        assert repo == "flask"

    def test_full_url_with_trailing_slash(self):
        owner, repo = parse_repo_url("https://github.com/pallets/flask/")
        assert owner == "pallets"
        assert repo == "flask"

    def test_full_url_with_subpath(self):
        owner, repo = parse_repo_url("https://github.com/pallets/flask/tree/main")
        assert owner == "pallets"
        assert repo == "flask"

    def test_whitespace_stripped(self):
        owner, repo = parse_repo_url("  pallets/flask  ")
        assert owner == "pallets"
        assert repo == "flask"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_repo_url("not-a-valid-input")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            parse_repo_url("")


class TestParseRepoUrlEdgeCases:
    def test_http_url(self):
        owner, repo = parse_repo_url("http://github.com/user/repo")
        assert owner == "user"
        assert repo == "repo"

    def test_repo_with_dots(self):
        owner, repo = parse_repo_url("user/my.repo.name")
        assert owner == "user"
        assert repo == "my.repo.name"

    def test_repo_with_hyphens(self):
        owner, repo = parse_repo_url("my-org/my-repo-name")
        assert owner == "my-org"
        assert repo == "my-repo-name"
