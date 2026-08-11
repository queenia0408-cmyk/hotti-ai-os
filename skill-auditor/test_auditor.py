#!/usr/bin/env python3
"""
Unit tests for Skill Ecosystem Auditor
Cycle 5 Quality Engineering — pytest 기반 테스트 스위트

Usage:
    pytest test_auditor.py -v
"""

import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auditor import (
    parse_frontmatter,
    SkillMeta,
    Conflict,
    check_duplicates,
    check_dependencies,
    check_conflicts,
)


# ─── YAML Parser Tests ─────────────────────────────────────────────────────

class TestParseFrontmatter:
    def test_empty_content(self):
        assert parse_frontmatter("") == {}

    def test_no_frontmatter(self):
        content = "# Just a heading\n\nSome text here."
        assert parse_frontmatter(content) == {}

    def test_simple_key_value(self):
        content = "---\nname: test-skill\ndescription: A test skill\n---\n\n# Body"
        result = parse_frontmatter(content)
        assert result["name"] == "test-skill"
        assert result["description"] == "A test skill"

    def test_list_field(self):
        content = "---\ntools:\n  - tool-a\n  - tool-b\n  - tool-c\n---\n\nBody"
        result = parse_frontmatter(content)
        assert result["tools"] == ["tool-a", "tool-b", "tool-c"]

    def test_mixed_fields(self):
        content = """---
name: autopilot
level: 4
tools:
  - Read
  - Write
  - Edit
complementary_skills:
  - ralph
  - ultrawork
  - ultraqa
---
"""
        result = parse_frontmatter(content)
        assert result["name"] == "autopilot"
        assert result["level"] == "4"
        assert result["tools"] == ["Read", "Write", "Edit"]
        assert result["complementary_skills"] == ["ralph", "ultrawork", "ultraqa"]

    def test_quoted_values(self):
        content = '---\nname: "my skill"\ndescription: "hello world"\n---\n'
        result = parse_frontmatter(content)
        assert result["name"] == "my skill"
        assert result["description"] == "hello world"

    def test_list_then_scalar(self):
        """List followed by another key should reset list parsing."""
        content = """---
tools:
  - read
  - write
level: 3
---
"""
        result = parse_frontmatter(content)
        assert result["tools"] == ["read", "write"]
        assert result["level"] == "3"


# ─── Duplicate Detection Tests ─────────────────────────────────────────────

class TestCheckDuplicates:
    def test_no_duplicates_different_domains(self):
        skills = [
            SkillMeta(path="", name="stock-analysis", description="Analyze stocks using technical indicators",
                      tools=["Read", "Write", "Glob"]),
            SkillMeta(path="", name="seo-optimizer", description="Optimize content for search engines",
                      tools=["Read", "Write", "Glob"]),
        ]
        conflicts = check_duplicates(skills)
        # Low description similarity, tool overlap < 3
        assert len([c for c in conflicts if c.severity == "critical"]) == 0

    def test_high_similarity_detected(self):
        skills = [
            SkillMeta(path="", name="skill-a", description="analyze stock market data with technical indicators for trading",
                      tools=[]),
            SkillMeta(path="", name="skill-b", description="analyze stock market data with technical indicators for investing",
                      tools=[]),
        ]
        conflicts = check_duplicates(skills)
        assert any(c.category == "duplicate" for c in conflicts)

    def test_tool_overlap_detected(self):
        skills = [
            SkillMeta(path="", name="skill-x", description="Does X", tools=["Read", "Write", "Edit", "Glob"]),
            SkillMeta(path="", name="skill-y", description="Does Y", tools=["Read", "Write", "Edit"]),
        ]
        conflicts = check_duplicates(skills)
        assert any(c.severity == "warning" and c.category == "duplicate" for c in conflicts)

    def test_no_false_positive_for_distinct_skills(self):
        skills = [
            SkillMeta(path="", name="brainstorming", description="Generate creative ideas and explore possibilities",
                      tools=["Read"]),
            SkillMeta(path="", name="test-driven-development", description="Write failing tests first, then implement",
                      tools=["Write", "Edit"]),
        ]
        conflicts = check_duplicates(skills)
        # Low similarity, no tool overlap → no duplicate flags
        dups = [c for c in conflicts if c.severity in ("critical", "warning")]
        assert len(dups) == 0


# ─── Dependency Check Tests ────────────────────────────────────────────────

class TestCheckDependencies:
    def test_broken_complementary_skill(self):
        skills = [
            SkillMeta(path="", name="autopilot", complementary_skills=["ralph", "ultrawork"]),
        ]
        conflicts = check_dependencies(skills)
        assert len(conflicts) == 2  # both missing

    def test_valid_dependencies(self):
        skills = [
            SkillMeta(path="", name="autopilot", complementary_skills=["ralph"]),
            SkillMeta(path="", name="ralph", complementary_skills=[]),
        ]
        conflicts = check_dependencies(skills)
        assert len(conflicts) == 0

    def test_empty_complementary(self):
        skills = [
            SkillMeta(path="", name="standalone", complementary_skills=[]),
        ]
        conflicts = check_dependencies(skills)
        assert len(conflicts) == 0

    def test_obsidian_path_missing(self):
        skills = [
            SkillMeta(path="", name="test-skill", obsidian_read_paths=["nonexistent/path/here"]),
        ]
        conflicts = check_dependencies(skills)
        # Should report info about missing obsidian path
        assert any(c.category == "dependency" for c in conflicts)


# ─── Conflict Detection Tests ──────────────────────────────────────────────

class TestCheckConflicts:
    def test_no_conflict_different_terms(self):
        skills = [
            SkillMeta(path="", name="skill-a", content="Always use Read tool. Never skip planning."),
            SkillMeta(path="", name="skill-b", content="Always test your code. Never deploy on Friday."),
        ]
        conflicts = check_conflicts(skills)
        assert len(conflicts) == 0

    def test_always_never_conflict_detected(self):
        skills = [
            SkillMeta(path="", name="skill-a", content="Always use Read before writing. This is critical."),
            SkillMeta(path="", name="skill-b", content="Never use Read before writing. It wastes time."),
        ]
        conflicts = check_conflicts(skills)
        assert any(c.severity == "critical" and c.category == "conflict" for c in conflicts)

    def test_case_insensitive_matching(self):
        skills = [
            SkillMeta(path="", name="upper", content="ALWAYS RUN tests first"),
            SkillMeta(path="", name="lower", content="never run tests"),
        ]
        conflicts = check_conflicts(skills)
        assert any(c.category == "conflict" for c in conflicts)


# ─── Data Model Tests ──────────────────────────────────────────────────────

class TestSkillMeta:
    def test_default_values(self):
        skill = SkillMeta(path="/tmp/test/SKILL.md", name="test")
        assert skill.description == ""
        assert skill.version == ""
        assert skill.level == 0
        assert skill.tools == []
        assert skill.complementary_skills == []


class TestConflict:
    def test_conflict_creation(self):
        c = Conflict(
            severity="critical",
            category="conflict",
            skill_a="a",
            skill_b="b",
            detail="A says always X, B says never X",
            recommendation="Resolve contradiction"
        )
        assert c.severity == "critical"
        assert c.skill_a == "a"
        assert c.recommendation != ""


# ─── Integration Tests ─────────────────────────────────────────────────────

class TestEndToEnd:
    def test_real_skill_content(self):
        """Parse a realistic SKILL.md frontmatter."""
        content = """---
name: obsidian-claude-hermes-evolution
description: Obsidian, Claude Code, and Hermes evidence-based evolution workflow
version: 1.0.0
level: 4
tools:
  - Read
  - Write
  - Edit
  - mcp__obsidian-mcp-rs__*
  - mcp__obsidian-local-rest-api__*
obsidian_read_paths:
  - Claude Code/system/ai-os-integration
  - wiki/index
complementary_skills:
  - knowledge-sync
  - auto-ingest
  - wiki
  - deep-dive
---
"""
        result = parse_frontmatter(content)
        assert result["name"] == "obsidian-claude-hermes-evolution"
        assert result["level"] == "4"
        assert len(result["tools"]) == 5
        assert len(result["complementary_skills"]) == 4

    def test_full_audit_pipeline_on_tmp_skills(self):
        """Create temp skill files, run full audit pipeline."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two skills with a conflict
            os.makedirs(os.path.join(tmpdir, "skill-a"))
            os.makedirs(os.path.join(tmpdir, "skill-b"))

            with open(os.path.join(tmpdir, "skill-a", "SKILL.md"), "w") as f:
                f.write("---\nname: skill-a\ndescription: always use Read first\n---\n\nAlways use Read first.")

            with open(os.path.join(tmpdir, "skill-b", "SKILL.md"), "w") as f:
                f.write("---\nname: skill-b\ndescription: never use Read\n---\n\nNever use Read. Use Write directly.")

            from auditor import load_skills
            skills, failed = load_skills(tmpdir)
            assert len(skills) == 2
            assert failed == 0

            conflicts = check_conflicts(skills)
            assert len(conflicts) >= 1


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
