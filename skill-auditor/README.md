# Skill Ecosystem Auditor

> Cycle 3 Build-to-Understand | Claude Code Self-Evolution v3.0

Automated conflict detection for Claude Code skill ecosystems.

## Quick Start

```bash
pip install -r requirements.txt
python auditor.py --skills-dir ~/.claude/skills --output report.json
```

## Features

- **4-Axis Audit**: Duplication, Conflict, Dependency Integrity, Coverage Gap
- **Always/Never Contradiction Detection**: Finds conflicting skill instructions
- **Description Similarity Analysis**: Jaccard similarity on skill descriptions
- **Dependency Validation**: Verifies complementary_skills and obsidian_read_paths
- **JSON Export**: Machine-readable audit reports

## First Run Results (2026-08-12)

- Scanned: 61 SKILL.md files
- Conflicts found: 149 (13 critical, 136 warning)
- Critical: 13 always/never instruction contradictions
- Warning: Mostly tool-list overlaps (needs common-tool filter)

## Architecture

```
auditor.py
├── Skill Loader: YAML frontmatter parser
├── Analyzers:
│   ├── check_duplicates() — Jaccard similarity + tool overlap
│   ├── check_dependencies() — complementary_skills integrity
│   └── check_conflicts() — always/never contradiction detection
└── Reporter: Pretty-print + JSON export
```

## Roadmap

- [ ] Semantic similarity via sentence-transformers
- [ ] Common-tool exclusion filter (Read/Write/Edit/Glob/Grep)
- [ ] Auto-generated merge PR templates
- [ ] Continuous monitoring via cron
