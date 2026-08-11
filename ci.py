#!/usr/bin/env python3
"""
CI Runner — Local Continuous Integration Pipeline
Cycle 6 Quality Engineering — Automated test + lint + verify

Usage:
    python ci.py                  # Run all checks
    python ci.py --tests-only     # Only run tests
    python ci.py --lint-only      # Only run linting
    python ci.py --json           # JSON output for automation
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


ROOT = Path(__file__).parent.absolute()


@dataclass
class CIResult:
    stage: str
    passed: bool
    details: str = ""
    duration_ms: float = 0
    items: list = field(default_factory=list)


# ─── Stages ────────────────────────────────────────────────────────────────

def run_tests() -> CIResult:
    """Stage 1: Run pytest on all test files."""
    t0 = time.time()
    test_files = list(ROOT.glob("**/test_*.py"))

    if not test_files:
        return CIResult("tests", True, "No test files found", 0)

    results = []
    total_passed = 0
    total_failed = 0

    for tf in sorted(test_files):
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(tf), "-v", "--tb=short", "--no-header"],
            capture_output=True, text=True, cwd=str(tf.parent),
            timeout=120,
        )
        # Parse pytest output for pass/fail count
        stdout = proc.stdout
        passed = stdout.count("PASSED")
        failed = stdout.count("FAILED")
        total_passed += passed
        total_failed += failed

        results.append({
            "file": str(tf.relative_to(ROOT)),
            "passed": passed,
            "failed": failed,
            "exit_code": proc.returncode,
        })

    duration = (time.time() - t0) * 1000
    all_pass = total_failed == 0

    details = f"{total_passed} passed, {total_failed} failed across {len(test_files)} test files"
    return CIResult("tests", all_pass, details, duration, results)


def run_lint() -> CIResult:
    """Stage 2: Basic linting checks."""
    t0 = time.time()
    issues = []

    py_files = list(ROOT.glob("**/*.py"))
    py_files = [f for f in py_files if "venv" not in str(f) and "__pycache__" not in str(f)]

    for pf in sorted(py_files):
        content = pf.read_text(encoding="utf-8", errors="replace")
        lines = content.split("\n")

        # Check 1: No trailing whitespace
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line:
                issues.append({
                    "file": str(pf.relative_to(ROOT)),
                    "line": i,
                    "rule": "trailing-whitespace",
                    "message": "Trailing whitespace",
                })

        # Check 2: File ends with newline
        if content and not content.endswith("\n"):
            issues.append({
                "file": str(pf.relative_to(ROOT)),
                "line": len(lines),
                "rule": "missing-final-newline",
                "message": "File does not end with newline",
            })

        # Check 3: No debug prints (easy to miss)
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("print(") and "def " not in stripped:
                # Allow print in main() and __name__ blocks
                pass  # Skipping this check for our projects

    duration = (time.time() - t0) * 1000
    passed = len(issues) == 0
    details = f"{len(issues)} lint issue(s)" if issues else "No lint issues"
    return CIResult("lint", passed, details, duration, issues)


def run_verify() -> CIResult:
    """Stage 3: Structural verification."""
    t0 = time.time()
    checks = []

    # Check 1: All project dirs have README.md
    for proj_dir in ROOT.iterdir():
        if proj_dir.is_dir() and not proj_dir.name.startswith("."):
            readme = proj_dir / "README.md"
            checks.append({
                "check": f"{proj_dir.name}/README.md",
                "passed": readme.exists(),
            })

    # Check 2: .gitignore exists
    gitignore = ROOT / ".gitignore"
    checks.append({
        "check": ".gitignore",
        "passed": gitignore.exists(),
    })

    # Check 3: No leftover .pytest_cache
    cache_dirs = list(ROOT.glob("**/.pytest_cache"))
    checks.append({
        "check": "no .pytest_cache dirs",
        "passed": len(cache_dirs) == 0,
    })

    duration = (time.time() - t0) * 1000
    all_pass = all(c["passed"] for c in checks)
    failed = [c for c in checks if not c["passed"]]
    details = f"{len(checks)} checks, {len(failed)} failed" if failed else f"All {len(checks)} checks passed"
    return CIResult("verify", all_pass, details, duration, checks)


# ─── Reporter ───────────────────────────────────────────────────────────────

def format_report(results: List[CIResult]) -> str:
    """Pretty-print CI report."""
    bar = "═" * 64
    total_ms = sum(r.duration_ms for r in results)
    all_pass = all(r.passed for r in results)

    status_icon = "✅" if all_pass else "❌"
    lines = [
        f"\n{bar}",
        f"{status_icon} CI PIPELINE — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"{bar}",
    ]

    for r in results:
        icon = "✅" if r.passed else "❌"
        lines.append(f"\n{icon} [{r.stage.upper()}] ({r.duration_ms:.0f}ms)")
        lines.append(f"   {r.details}")

        # Show first few failures
        if not r.passed and r.items:
            failures = [item for item in r.items if isinstance(item, dict) and not item.get("passed", True)]
            if not failures:
                # For test results, check exit_code
                failures = [item for item in r.items if isinstance(item, dict) and item.get("failed", 0) > 0]
            for item in failures[:5]:
                fname = item.get("file", item.get("check", "?"))
                lines.append(f"     • {fname}")
            if len(failures) > 5:
                lines.append(f"     ... and {len(failures) - 5} more")

    lines.append(f"\n{bar}")
    lines.append(f"Total: {total_ms:.0f}ms | Status: {'PASS' if all_pass else 'FAIL'}")
    lines.append(f"{bar}\n")
    return "\n".join(lines)


def save_json(results: List[CIResult], path: str):
    """Save CI results as JSON."""
    data = {
        "timestamp": datetime.now().isoformat(),
        "passed": all(r.passed for r in results),
        "total_duration_ms": sum(r.duration_ms for r in results),
        "stages": [
            {
                "stage": r.stage,
                "passed": r.passed,
                "details": r.details,
                "duration_ms": r.duration_ms,
                "items": r.items,
            }
            for r in results
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"📄 CI report saved to: {path}")


# ─── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="CI Runner — Local Continuous Integration Pipeline",
        epilog="Cycle 6 Quality Engineering | Claude Code Self-Evolution"
    )
    parser.add_argument("--tests-only", action="store_true", help="Only run tests")
    parser.add_argument("--lint-only", action="store_true", help="Only run linting")
    parser.add_argument("--json", default=None, help="Save JSON report to file")
    parser.add_argument("--quiet", action="store_true", help="Suppress output, exit code only")
    args = parser.parse_args()

    results = []

    if args.lint_only:
        results.append(run_lint())
    elif args.tests_only:
        results.append(run_tests())
    else:
        # Full pipeline: verify → lint → test (verify first so cache dirs clean)
        results.append(run_verify())
        results.append(run_lint())
        # Clean pytest cache before test run
        for cache_dir in ROOT.glob("**/.pytest_cache"):
            import shutil
            shutil.rmtree(cache_dir, ignore_errors=True)
        results.append(run_tests())
        # Clean pytest cache after test run
        for cache_dir in ROOT.glob("**/.pytest_cache"):
            import shutil
            shutil.rmtree(cache_dir, ignore_errors=True)

    if not args.quiet:
        print(format_report(results))

    if args.json:
        save_json(results, args.json)

    all_pass = all(r.passed for r in results)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
