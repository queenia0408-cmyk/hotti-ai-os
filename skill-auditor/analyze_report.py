#!/usr/bin/env python3
"""Analyze audit-report.json — categorize and rank findings."""
import json
from collections import Counter
import re

with open("C:/Users/hotti/projects/skill-auditor/audit-report.json", encoding="utf-8") as f:
    data = json.load(f)

print(f"Skills parsed: {data['skills_parsed']}")
print(f"Total conflicts: {data['total_conflicts']}")
print()

# By severity
sev = Counter(c['severity'] for c in data['conflicts'])
print("By Severity:")
for s in ['critical','warning','info','notice']:
    print(f"  {s}: {sev.get(s,0)}")
print()

# By category
cat = Counter(c['category'] for c in data['conflicts'])
print("By Category:")
for k, v in cat.most_common():
    print(f"  {k}: {v}")
print()

# Critical trigger words
critical_words = Counter()
for c in data['conflicts']:
    if c['severity'] == 'critical':
        detail = c['detail']
        words = re.findall(r"always '(\w+)'", detail)
        words2 = re.findall(r"never '(\w+)'", detail)
        for w in words + words2:
            critical_words[w] += 1
print("Critical trigger words (top 15):")
for w, cnt in critical_words.most_common(15):
    print(f"  '{w}': {cnt}")
print()

# Most conflicted skills
skill_conflicts = Counter()
for c in data['conflicts']:
    skill_conflicts[c['skill_a']] += 1
    skill_conflicts[c['skill_b']] += 1
print("Top 10 most conflicted skills:")
for s, cnt in skill_conflicts.most_common(10):
    print(f"  {s}: {cnt} conflicts")
print()

# Dependency issues
dep_issues = [c for c in data['conflicts'] if c['category'] == 'dependency']
print(f"Dependency issues: {len(dep_issues)}")
for c in dep_issues[:10]:
    print(f"  [{c['severity']}] {c['skill_a']} -> {c['skill_b']}: {c['detail'][:150]}")
print()

# True duplicates (>85% similarity)
dupes = [c for c in data['conflicts'] if c['category'] == 'duplicate' and c['severity'] in ('critical', 'warning')]
print(f"Duplicate risks: {len(dupes)}")
for c in dupes[:15]:
    print(f"  [{c['severity']}] {c['skill_a']} <-> {c['skill_b']}: {c['detail'][:150]}")
