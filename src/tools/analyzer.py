"""
Static analysis tools for automated code scanning.
Includes Bandit security analysis and custom quality checks.
"""

import json
import os
import subprocess
import tempfile
from langchain_core.tools import tool


@tool
def static_analysis(code: str, filename: str = "code.py") -> str:
    """
    Run Bandit security analysis on Python code.
    Pass in Python source code as a string.
    Returns a security report with findings and severity levels.
    """
    if not filename.endswith(".py"):
        return "Static analysis currently supports Python files only (.py)."

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = subprocess.run(
            ["bandit", "-f", "json", "-ll", tmp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        os.unlink(tmp_path)

        if result.stdout:
            report = json.loads(result.stdout)
            return _format_bandit_report(report)
        elif result.returncode == 0:
            return "No security issues found. Code passed all Bandit checks."
        else:
            return f"Analysis completed with warnings:\n{result.stderr}"

    except FileNotFoundError:
        return "Bandit is not installed. Install with: pip install bandit"
    except subprocess.TimeoutExpired:
        return "Analysis timed out — code may be too large."
    except Exception as e:
        return f"Static analysis error: {e}"


def _format_bandit_report(report: dict) -> str:
    results = report.get("results", [])
    metrics = report.get("metrics", {}).get("_totals", {})

    if not results:
        return f"No issues detected. Lines analyzed: {metrics.get('loc', '?')}"

    severity_map = {"HIGH": "CRITICAL", "MEDIUM": "WARNING", "LOW": "INFO"}
    lines = [f"Found {len(results)} security issue(s):\n"]

    for i, finding in enumerate(results, 1):
        sev = severity_map.get(finding.get("issue_severity", ""), "INFO")
        lines.append(
            f"{i}. [{sev}] {finding.get('issue_text', 'Unknown')}\n"
            f"   Test: {finding.get('test_id', '?')} ({finding.get('test_name', '?')})\n"
            f"   Line {finding.get('line_number', '?')}\n"
            f"   Confidence: {finding.get('issue_confidence', '?')}\n"
        )

    return "\n".join(lines)


@tool
def code_quality_check(code: str) -> str:
    """
    Run code quality checks on Python code.
    Detects hardcoded secrets, long functions, bare excepts, and missing error handling.
    """
    issues = []
    lines = code.split("\n")

    # Hardcoded secrets
    secret_patterns = [
        "password", "api_key", "apikey", "secret", "token",
        "private_key", "access_key", "auth_token",
    ]
    for i, line in enumerate(lines, 1):
        stripped = line.strip().lower()
        if stripped.startswith("#"):
            continue
        for pattern in secret_patterns:
            if pattern in stripped and "=" in stripped:
                if "os.getenv" not in stripped and "os.environ" not in stripped:
                    issues.append(
                        f"[CRITICAL] Line {i}: Possible hardcoded secret "
                        f"('{pattern}'). Use environment variables."
                    )

    # Long functions
    current_func = None
    func_start = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("def "):
            if current_func and (i - func_start) > 50:
                issues.append(
                    f"[WARNING] Function '{current_func}' is {i - func_start} "
                    f"lines long (line {func_start}). Consider splitting."
                )
            current_func = stripped.split("(")[0].replace("def ", "")
            func_start = i

    # Bare excepts
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped in ("except:", "except Exception:"):
            issues.append(f"[WARNING] Line {i}: Broad except clause. Catch specific exceptions.")

    # TODO/FIXME
    for i, line in enumerate(lines, 1):
        for tag in ["TODO", "FIXME", "HACK", "XXX"]:
            if tag in line.upper():
                issues.append(f"[INFO] Line {i}: '{tag}' comment needs attention.")

    # Missing error handling on network calls
    has_requests = any("requests." in line for line in lines)
    has_try = any("try:" in line.strip() for line in lines)
    if has_requests and not has_try:
        issues.append("[WARNING] Uses 'requests' without try/except. Add error handling.")

    if not issues:
        return "No code quality issues detected."

    return f"Found {len(issues)} issue(s):\n\n" + "\n".join(issues)
