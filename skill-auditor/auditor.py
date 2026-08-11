#!/usr/bin/env python3
"""
Skill Ecosystem Auditor — 스킬 충돌·중복·의존성 감지 시스템
Cycle 3 Build-to-Understand: 실제 실행 가능한 스킬 감사 스크립트

Usage:
    python auditor.py --skills-dir C:/Users/hotti/.claude/skills
    python auditor.py --skills-dir ./skills --output report.json
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class SkillMeta:
    name: str
    path: str
    description: str = ""
    version: str = ""
    level: int = 0
    tools: List[str] = field(default_factory=list)
    complementary_skills: List[str] = field(default_factory=list)
    obsidian_read_paths: List[str] = field(default_factory=list)
    content: str = ""

@dataclass
class Conflict:
    severity: str       # critical | warning | info | notice
    category: str       # duplicate | conflict | dependency | gap
    skill_a: str
    skill_b: str
    detail: str
    recommendation: str = ""

@dataclass
class AuditReport:
    skills_parsed: int
    skills_failed: int
    conflicts: List[Conflict] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

# ---------------------------------------------------------------------------
# YAML Frontmatter Parser (minimal — avoids PyYAML dependency)
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> Dict[str, any]:
    """Parse YAML-like frontmatter from skill markdown."""
    if not content.startswith("---"):
        return {}

    end_idx = content.find("---", 3)
    if end_idx == -1:
        return {}

    frontmatter = content[3:end_idx].strip()
    result = {}

    # Parse simple key: value pairs + list fields
    current_key = None
    in_list = False
    list_values = []

    for line in frontmatter.split("\n"):
        line = line.strip()
        if not line:
            continue

        # List continuation
        if line.startswith("- ") and current_key:
            list_values.append(line[2:].strip())
            in_list = True
            continue

        # Key: Value
        if ":" in line and not line.startswith("- "):
            # Save previous list
            if in_list and current_key:
                result[current_key] = list_values
                list_values = []
                in_list = False

            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if value == "":
                current_key = key
                list_values = []
                continue
            else:
                result[key] = value
                current_key = key

    # Save final list
    if in_list and current_key:
        result[current_key] = list_values

    return result

# ---------------------------------------------------------------------------
# Skill Loader
# ---------------------------------------------------------------------------

def load_skills(skills_dir: str) -> List[SkillMeta]:
    """Load all SKILL.md files from the skills directory."""
    skills = []
    failed = 0

    if not os.path.isdir(skills_dir):
        print(f"❌ Skills directory not found: {skills_dir}")
        return skills

    for root, dirs, files in os.walk(skills_dir):
        for f in files:
            if f == "SKILL.md":
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    fm = parse_frontmatter(content)

                    skill = SkillMeta(
                        name=fm.get("name", os.path.basename(root)),
                        path=path,
                        description=fm.get("description", ""),
                        version=fm.get("version", ""),
                        level=int(fm.get("level", 0)),
                        tools=fm.get("tools", []),
                        complementary_skills=fm.get("complementary_skills", []),
                        obsidian_read_paths=fm.get("obsidian_read_paths", []),
                        content=content,
                    )
                    skills.append(skill)
                except Exception as e:
                    print(f"⚠ Failed to parse {path}: {e}")
                    failed += 1

    return skills, failed

# ---------------------------------------------------------------------------
# Analyzers
# ---------------------------------------------------------------------------

def check_duplicates(skills: List[SkillMeta]) -> List[Conflict]:
    """Axis 1: Detect duplicate/overlapping skills."""
    conflicts = []
    desc_words = {}

    for s in skills:
        words = set(re.findall(r'\w+', s.description.lower()))
        desc_words[s.name] = words

    for i, a in enumerate(skills):
        for b in skills[i + 1:]:
            # Simple Jaccard similarity on description words
            wa = desc_words[a.name]
            wb = desc_words[b.name]
            if not wa or not wb:
                continue

            intersection = wa & wb
            union = wa | wb
            similarity = len(intersection) / len(union) if union else 0

            if similarity > 0.7:
                severity = "critical" if similarity > 0.85 else "warning"
                conflicts.append(Conflict(
                    severity=severity,
                    category="duplicate",
                    skill_a=a.name,
                    skill_b=b.name,
                    detail=f"Description similarity: {similarity:.0%} — overlapping purpose detected",
                    recommendation=f"Consider merging '{a.name}' and '{b.name}' into a single skill"
                ))

            # Check tool overlap
            tools_a = set(a.tools)
            tools_b = set(b.tools)
            tool_overlap = tools_a & tools_b
            if len(tool_overlap) >= 3 and a.name != b.name:
                conflicts.append(Conflict(
                    severity="warning",
                    category="duplicate",
                    skill_a=a.name,
                    skill_b=b.name,
                    detail=f"Shared tools ({len(tool_overlap)}): {', '.join(sorted(tool_overlap)[:5])}",
                    recommendation="Review if these skills serve distinct purposes"
                ))

    return conflicts


def check_dependencies(skills: List[SkillMeta]) -> List[Conflict]:
    """Axis 3: Verify skill dependency integrity."""
    conflicts = []
    skill_names = {s.name for s in skills}

    for s in skills:
        for dep in s.complementary_skills:
            if dep not in skill_names:
                conflicts.append(Conflict(
                    severity="warning",
                    category="dependency",
                    skill_a=s.name,
                    skill_b=dep,
                    detail=f"'{s.name}' references '{dep}' in complementary_skills, but '{dep}' does not exist",
                    recommendation=f"Create '{dep}' skill or remove it from '{s.name}'"
                ))

        # Check obsidian paths
        vault = r"C:\Users\hotti\OneDrive\문서\Obsidian Vault"
        for obs_path in s.obsidian_read_paths:
            md_path = os.path.join(vault, obs_path + ".md")
            if not os.path.exists(md_path):
                conflicts.append(Conflict(
                    severity="info",
                    category="dependency",
                    skill_a=s.name,
                    skill_b=obs_path,
                    detail=f"Obsidian path '{obs_path}.md' not found in vault",
                    recommendation=f"Verify the node exists or update obsidian_read_paths in '{s.name}'"
                ))

    return conflicts


def check_conflicts(skills: List[SkillMeta]) -> List[Conflict]:
    """Axis 2: Detect conflicting instructions between skills."""
    conflicts = []

    # Heuristic: search for opposing directives
    for i, a in enumerate(skills):
        for b in skills[i + 1:]:
            content_a = a.content.lower()
            content_b = b.content.lower()

            # Check for conflicting "always/never" patterns
            always_a = set(re.findall(r'always\s+(\w+)', content_a))
            never_a = set(re.findall(r'never\s+(\w+)', content_a))
            always_b = set(re.findall(r'always\s+(\w+)', content_b))
            never_b = set(re.findall(r'never\s+(\w+)', content_b))

            for word in always_a & never_b:
                conflicts.append(Conflict(
                    severity="critical",
                    category="conflict",
                    skill_a=a.name,
                    skill_b=b.name,
                    detail=f"'{a.name}' says always '{word}', but '{b.name}' says never '{word}'",
                    recommendation=f"Resolve the contradiction between '{a.name}' and '{b.name}'"
                ))

            for word in always_b & never_a:
                conflicts.append(Conflict(
                    severity="critical",
                    category="conflict",
                    skill_a=a.name,
                    skill_b=b.name,
                    detail=f"'{b.name}' says always '{word}', but '{a.name}' says never '{word}'",
                    recommendation=f"Resolve the contradiction between '{a.name}' and '{b.name}'"
                ))

    return conflicts


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------

def format_audit_report(report: AuditReport) -> str:
    """Pretty-print audit report."""
    bar = "═" * 64
    lines = [f"\n{bar}",
             f"🔍 SKILL ECOSYSTEM AUDIT REPORT",
             f"{bar}",
             f"  Skills Parsed:  {report.skills_parsed}",
             f"  Parse Failures: {report.skills_failed}",
             f"  Conflicts Found: {len(report.conflicts)}",
             f""]

    by_severity = {"critical": [], "warning": [], "info": [], "notice": []}
    for c in report.conflicts:
        by_severity.get(c.severity, []).append(c)

    for sev in ["critical", "warning", "info", "notice"]:
        items = by_severity[sev]
        if not items:
            continue
        emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵", "notice": "⚪"}[sev]
        lines.append(f"\n{emoji} {sev.upper()} ({len(items)})")
        for item in items:
            lines.append(f"  [{item.category}] {item.skill_a} ↔ {item.skill_b}")
            lines.append(f"    {item.detail}")
            if item.recommendation:
                lines.append(f"    💡 {item.recommendation}")

    lines.append(f"\n{bar}")
    lines.append("✅ Audit complete. Cycle 3 — Build to Understand.\n")
    return "\n".join(lines)


def save_json_report(report: AuditReport, path: str):
    """Save audit report as JSON."""
    data = {
        "skills_parsed": report.skills_parsed,
        "skills_failed": report.skills_failed,
        "total_conflicts": len(report.conflicts),
        "conflicts": [
            {
                "severity": c.severity,
                "category": c.category,
                "skill_a": c.skill_a,
                "skill_b": c.skill_b,
                "detail": c.detail,
                "recommendation": c.recommendation,
            }
            for c in report.conflicts
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"📄 JSON report saved to: {path}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Skill Ecosystem Auditor — Detect conflicts in Claude Code skills",
        epilog="Cycle 3 Build-to-Understand | Claude Code Self-Evolution"
    )
    parser.add_argument("--skills-dir", required=True,
                        help="Path to .claude/skills directory")
    parser.add_argument("--output", default=None,
                        help="Save JSON report to file")
    parser.add_argument("--min-severity", default="info",
                        choices=["critical", "warning", "info", "notice"],
                        help="Minimum severity to report")
    args = parser.parse_args()

    print(f"\n🔍 Scanning skills in: {args.skills_dir}")

    skills, failed = load_skills(args.skills_dir)
    print(f"   Parsed {len(skills)} skills ({failed} failed)")

    sev_order = {"critical": 0, "warning": 1, "info": 2, "notice": 3}
    min_sev = sev_order[args.min_severity]

    all_conflicts = (
        check_duplicates(skills) +
        check_dependencies(skills) +
        check_conflicts(skills)
    )

    # Filter by severity
    all_conflicts = [c for c in all_conflicts if sev_order.get(c.severity, 99) <= min_sev]

    report = AuditReport(
        skills_parsed=len(skills),
        skills_failed=failed,
        conflicts=sorted(all_conflicts, key=lambda c: sev_order.get(c.severity, 99)),
        summary={
            "critical": sum(1 for c in all_conflicts if c.severity == "critical"),
            "warning": sum(1 for c in all_conflicts if c.severity == "warning"),
            "info": sum(1 for c in all_conflicts if c.severity == "info"),
            "notice": sum(1 for c in all_conflicts if c.severity == "notice"),
        }
    )

    print(format_audit_report(report))

    if args.output:
        save_json_report(report, args.output)


if __name__ == "__main__":
    main()
