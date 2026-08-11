#!/usr/bin/env python3
"""
SEO Content Analyzer — Keyword Density, Readability, Meta Tags, Structure Audit
Cycle 8 Autonomous Evolution — Marketing Domain Deep-Dive

Analyzes HTML/text content for SEO quality across 4 dimensions:
1. Keywords — density, prominence, n-grams
2. Readability — Flesch-Kincaid, automated readability index
3. Meta — title/description length, H1 structure
4. Structure — heading hierarchy, link density, image alt text

Usage:
    python analyzer.py --url https://example.com
    python analyzer.py --file page.html
    python analyzer.py --text "content" --keyword "SEO optimization"
"""

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from urllib.parse import urlparse


# ─── Data Models ─────────────────────────────────────────────────────────

@dataclass
class KeywordAnalysis:
    total_words: int
    unique_words: int
    keyword: str
    keyword_count: int
    density_pct: float
    prominence_score: float  # 0-100, early + frequent = higher
    top_bigrams: List[Tuple[str, int]] = field(default_factory=list)
    top_trigrams: List[Tuple[str, int]] = field(default_factory=list)


@dataclass
class ReadabilityScores:
    flesch_kincaid_grade: float  # US school grade level
    flesch_reading_ease: float   # 0-100 (higher = easier)
    automated_readability_index: float
    coleman_liau_index: float
    avg_sentence_length: float
    avg_word_length: float
    complex_word_pct: float  # words with 3+ syllables


@dataclass
class MetaAudit:
    title: str
    title_length: int
    title_ok: bool           # 30-60 chars
    description: str
    description_length: int
    description_ok: bool     # 120-160 chars
    h1_count: int
    h1_texts: List[str]
    h1_ok: bool              # exactly 1


@dataclass
class StructureAudit:
    heading_hierarchy_valid: bool
    heading_issues: List[str]
    internal_links: int
    external_links: int
    link_density_pct: float
    images_total: int
    images_missing_alt: int
    images_alt_ok_pct: float


@dataclass
class SEOReport:
    url_or_file: str
    keyword: KeywordAnalysis
    readability: ReadabilityScores
    meta: MetaAudit
    structure: StructureAudit
    overall_score: int       # 0-100
    recommendations: List[str]


# ─── Text Extraction ─────────────────────────────────────────────────────

def extract_text_from_html(html: str) -> Tuple[str, dict]:
    """Extract visible text and meta info from HTML using regex."""
    meta = {}

    # Title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    meta["title"] = title_match.group(1).strip() if title_match else ""

    # Meta description
    desc_match = re.search(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
        html, re.IGNORECASE
    )
    if not desc_match:
        desc_match = re.search(
            r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
            html, re.IGNORECASE
        )
    meta["description"] = desc_match.group(1).strip() if desc_match else ""

    # H1s
    meta["h1"] = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    meta["h1"] = [re.sub(r'<[^>]+>', '', h).strip() for h in meta["h1"]]

    # Links
    all_links = re.findall(r'<a[^>]+href=["\']([^"\']*)["\']', html, re.IGNORECASE)
    meta["internal_links"] = sum(1 for l in all_links if not l.startswith(('http://', 'https://')))
    meta["external_links"] = sum(1 for l in all_links if l.startswith(('http://', 'https://')))

    # Images
    all_imgs = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
    meta["images_total"] = len(all_imgs)
    meta["images_missing_alt"] = sum(1 for img in all_imgs if 'alt=' not in img and 'alt =' not in img)

    # Remove scripts, styles, HTML tags
    text = re.sub(r'<(script|style|noscript|iframe|svg)[^>]*>.*?</\1>', '', html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-z]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    return text, meta


# ─── Keyword Analysis ─────────────────────────────────────────────────────

def analyze_keywords(text: str, target_keyword: str = "") -> KeywordAnalysis:
    """Compute keyword density, prominence, and top n-grams."""
    words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
    total = len(words)
    unique = len(set(words))

    if not target_keyword:
        # Default: most frequent meaningful word
        stopwords = {'the','be','to','of','and','a','in','that','have','i','it','for',
                     'not','on','with','he','as','you','do','at','this','but','his',
                     'by','from','they','we','her','she','or','an','will','my','one',
                     'all','would','there','their','what','so','up','out','if','about',
                     'who','get','which','go','me','when','make','can','like','time',
                     'no','just','him','know','take','people','into','year','your',
                     'good','some','could','them','see','other','than','then','now',
                     'look','only','come','its','over','think','also','back','after',
                     'use','two','how','our','work','first','well','way','even','new',
                     'want','because','any','these','give','day','most','us','is'}
        word_counts = Counter(w for w in words if w not in stopwords)
        target_keyword = word_counts.most_common(1)[0][0] if word_counts else ""

    kw_count = words.count(target_keyword.lower())
    density = (kw_count / total * 100) if total > 0 else 0

    # Prominence: first 100 words weighted 3x, rest 1x
    first_100 = words[:100]
    kw_in_first = sum(1 for w in first_100 if w == target_keyword.lower())
    prominence = (kw_in_first * 3 + max(0, kw_count - kw_in_first)) / max(1, total) * 1000
    prominence = min(100, round(prominence, 1))

    # Bigrams
    bigrams = Counter(zip(words, words[1:]))
    top_bigrams = [(" ".join(bg), c) for bg, c in bigrams.most_common(10)]

    # Trigrams
    trigrams = Counter(zip(words, words[1:], words[2:]))
    top_trigrams = [(" ".join(tg), c) for tg, c in trigrams.most_common(5)]

    return KeywordAnalysis(
        total_words=total,
        unique_words=unique,
        keyword=target_keyword,
        keyword_count=kw_count,
        density_pct=round(density, 2),
        prominence_score=prominence,
        top_bigrams=top_bigrams,
        top_trigrams=top_trigrams,
    )


# ─── Readability ─────────────────────────────────────────────────────────

def count_syllables(word: str) -> int:
    """Approximate syllable count for English words."""
    word = word.lower().strip(".:;?!")
    if len(word) <= 3:
        return 1
    # Count vowel groups
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for ch in word:
        is_vowel = ch in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel
    # Adjust for silent e
    if word.endswith('e') and count > 1:
        count -= 1
    return max(1, count)


def analyze_readability(text: str) -> ReadabilityScores:
    """Compute Flesch-Kincaid and other readability scores."""
    # Split into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip().split()) > 2]

    words_all = re.findall(r'\b[a-zA-Z]+\b', text)
    total_words = len(words_all)
    total_sentences = len(sentences)

    if total_words == 0 or total_sentences == 0:
        return ReadabilityScores(0, 0, 0, 0, 0, 0, 0)

    total_syllables = sum(count_syllables(w) for w in words_all)
    complex_words = sum(1 for w in words_all if count_syllables(w) >= 3)

    avg_words_per_sentence = total_words / total_sentences
    avg_syllables_per_word = total_syllables / total_words

    # Flesch-Kincaid Grade Level
    fk_grade = 0.39 * avg_words_per_sentence + 11.8 * avg_syllables_per_word - 15.59

    # Flesch Reading Ease (0-100, higher = easier)
    fk_ease = 206.835 - 1.015 * avg_words_per_sentence - 84.6 * avg_syllables_per_word

    # Automated Readability Index
    chars = sum(len(w) for w in words_all)
    ari = 4.71 * (chars / total_words) + 0.5 * (total_words / total_sentences) - 21.43

    # Coleman-Liau Index
    L = (chars / total_words) * 100  # letters per 100 words
    S_cl = (total_sentences / total_words) * 100  # sentences per 100 words
    cli = 0.0588 * L - 0.296 * S_cl - 15.8

    return ReadabilityScores(
        flesch_kincaid_grade=round(max(0, fk_grade), 1),
        flesch_reading_ease=round(max(0, min(100, fk_ease)), 1),
        automated_readability_index=round(max(0, ari), 1),
        coleman_liau_index=round(max(0, cli), 1),
        avg_sentence_length=round(avg_words_per_sentence, 1),
        avg_word_length=round(chars / total_words, 1),
        complex_word_pct=round(complex_words / total_words * 100, 1),
    )


# ─── Meta Audit ──────────────────────────────────────────────────────────

def audit_meta(meta: dict) -> MetaAudit:
    """Check title, description, H1 structure."""
    title = meta.get("title", "")
    desc = meta.get("description", "")
    h1s = meta.get("h1", [])

    return MetaAudit(
        title=title,
        title_length=len(title),
        title_ok=30 <= len(title) <= 60,
        description=desc,
        description_length=len(desc),
        description_ok=120 <= len(desc) <= 160,
        h1_count=len(h1s),
        h1_texts=h1s,
        h1_ok=len(h1s) == 1,
    )


# ─── Structure Audit ─────────────────────────────────────────────────────

def audit_structure(text: str, meta: dict, total_words: int) -> StructureAudit:
    """Check heading hierarchy, link density, image alt text."""
    issues = []

    # Simple heading hierarchy check (h1→h2→h3 in the source)
    h_tags = re.findall(r'<(h[1-6])[^>]*>', text, re.IGNORECASE)
    if h_tags:
        levels = {'h1': 1, 'h2': 2, 'h3': 3, 'h4': 4, 'h5': 5, 'h6': 6}
        prev_level = 0
        for tag in h_tags:
            curr = levels.get(tag, 0)
            if curr > prev_level + 1 and prev_level > 0:
                issues.append(f"Heading skip: {tag} after h{prev_level} (no h{prev_level+1})")
            prev_level = curr

    internal = meta.get("internal_links", 0)
    external = meta.get("external_links", 0)
    total_links = internal + external
    link_density = (total_links / total_words * 100) if total_words > 0 else 0

    images_total = meta.get("images_total", 0)
    images_missing = meta.get("images_missing_alt", 0)
    alt_ok = ((images_total - images_missing) / images_total * 100) if images_total > 0 else 100

    return StructureAudit(
        heading_hierarchy_valid=len(issues) == 0,
        heading_issues=issues,
        internal_links=internal,
        external_links=external,
        link_density_pct=round(link_density, 2),
        images_total=images_total,
        images_missing_alt=images_missing,
        images_alt_ok_pct=round(alt_ok, 1),
    )


# ─── Score + Recommendations ─────────────────────────────────────────────

def compute_score(kw: KeywordAnalysis, read: ReadabilityScores,
                  meta: MetaAudit, struct: StructureAudit) -> Tuple[int, List[str]]:
    """Compute 0-100 SEO score and generate recommendations."""
    score = 0
    recs = []

    # Keyword (30 points)
    if 1.0 <= kw.density_pct <= 3.0:
        score += 15
    elif 0.5 <= kw.density_pct <= 4.0:
        score += 10
        recs.append(f"Keyword density {kw.density_pct}% — ideal is 1-3%")
    else:
        score += 5
        recs.append(f"Keyword density {kw.density_pct}% is outside normal range (1-3%)")

    if kw.prominence_score >= 50:
        score += 10
    else:
        recs.append("Use target keyword earlier in content for better prominence")

    if kw.total_words >= 300:
        score += 5
    else:
        recs.append(f"Content too short ({kw.total_words} words). Aim for 300+ words.")

    # Readability (25 points)
    if 60 <= read.flesch_reading_ease <= 70:
        score += 15
    elif 50 <= read.flesch_reading_ease <= 80:
        score += 10
    else:
        recs.append(f"Reading ease {read.flesch_reading_ease} — target 60-70 for general audience")

    if read.avg_sentence_length <= 25:
        score += 5
    else:
        recs.append(f"Sentences too long (avg {read.avg_sentence_length} words). Keep under 25.")

    if read.complex_word_pct <= 15:
        score += 5
    else:
        recs.append(f"{read.complex_word_pct}% complex words. Simplify vocabulary.")

    # Meta (25 points)
    if meta.title_ok:
        score += 10
    else:
        recs.append(f"Title length {meta.title_length} chars — ideal is 30-60 chars")

    if meta.description_ok:
        score += 10
    else:
        recs.append(f"Meta description length {meta.description_length} chars — ideal is 120-160 chars")

    if meta.h1_ok:
        score += 5
    else:
        recs.append(f"Found {meta.h1_count} H1 tags. Use exactly one H1 per page.")

    # Structure (20 points)
    if struct.heading_hierarchy_valid:
        score += 5
    else:
        for issue in struct.heading_issues:
            recs.append(issue)

    if 2 <= struct.link_density_pct <= 8:
        score += 5
    else:
        recs.append(f"Link density {struct.link_density_pct}% — ideal is 2-8%")

    if struct.images_alt_ok_pct >= 90:
        score += 5
    else:
        recs.append(f"{struct.images_missing_alt}/{struct.images_total} images missing alt text")

    if struct.internal_links >= 2:
        score += 5
    else:
        recs.append("Add more internal links for better site structure")

    return min(100, score), recs


# ─── Reports ─────────────────────────────────────────────────────────────

def format_report(report: SEOReport) -> str:
    bar = "═" * 64
    grade = "🟢" if report.overall_score >= 80 else ("🟡" if report.overall_score >= 50 else "🔴")

    lines = [
        f"\n{bar}",
        f"🔍 SEO CONTENT ANALYZER — {report.url_or_file}",
        f"{bar}",
        f"",
        f"{grade} OVERALL SCORE: {report.overall_score}/100",
        f"",
        f"📝 KEYWORD: \"{report.keyword.keyword}\"",
        f"   Density: {report.keyword.density_pct}% | Count: {report.keyword.keyword_count}/{report.keyword.total_words}",
        f"   Prominence: {report.keyword.prominence_score}/100 | Unique words: {report.keyword.unique_words}",
    ]

    if report.keyword.top_bigrams:
        bigrams = ", ".join(f"{bg}({c})" for bg, c in report.keyword.top_bigrams[:5])
        lines.append(f"   Top bigrams: {bigrams}")

    lines.extend([
        f"",
        f"📖 READABILITY",
        f"   Flesch-Kincaid Grade: {report.readability.flesch_kincaid_grade}",
        f"   Reading Ease: {report.readability.flesch_reading_ease}/100",
        f"   ARI: {report.readability.automated_readability_index} | Coleman-Liau: {report.readability.coleman_liau_index}",
        f"   Avg sentence: {report.readability.avg_sentence_length} words | Complex: {report.readability.complex_word_pct}%",
        f"",
        f"🏷️ META TAGS",
        f"   Title ({report.meta.title_length}c): \"{report.meta.title[:80]}{'…' if len(report.meta.title) > 80 else ''}\" {'✅' if report.meta.title_ok else '⚠️'}",
        f"   Description ({report.meta.description_length}c): {'✅' if report.meta.description_ok else '⚠️'}",
        f"   H1 tags: {report.meta.h1_count} {'✅' if report.meta.h1_ok else '⚠️'}",
    ])

    if report.meta.h1_texts:
        for h in report.meta.h1_texts:
            lines.append(f"     → {h[:80]}")

    lines.extend([
        f"",
        f"🏗️ STRUCTURE",
        f"   Heading hierarchy: {'✅ Valid' if report.structure.heading_hierarchy_valid else '⚠️ Issues'}",
        f"   Links: {report.structure.internal_links} internal, {report.structure.external_links} external ({report.structure.link_density_pct}% density)",
        f"   Images: {report.structure.images_total} total, {report.structure.images_missing_alt} missing alt ({report.structure.images_alt_ok_pct}% OK)",
    ])

    if report.recommendations:
        lines.append(f"")
        lines.append(f"💡 RECOMMENDATIONS")
        for i, rec in enumerate(report.recommendations, 1):
            lines.append(f"   {i}. {rec}")

    lines.extend([
        f"",
        f"{bar}",
        f"✅ SEO analysis complete. Cycle 8 — Autonomous Evolution.",
        f"{bar}\n",
    ])

    return "\n".join(lines)


# ─── CLI ─────────────────────────────────────────────────────────────────

def fetch_url(url: str) -> Optional[str]:
    """Fetch HTML content from a URL."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (SEO Analyzer Bot)'
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_type = resp.headers.get('Content-Type', '')
            data = resp.read()
            # Try UTF-8 first, fall back to latin-1
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    continue
            return data.decode('utf-8', errors='replace')
    except Exception as e:
        print(f"❌ Failed to fetch URL: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(
        description="SEO Content Analyzer — Keyword Density + Readability + Meta Audit",
        epilog="Cycle 8 Autonomous Evolution | Claude Code Self-Evolution"
    )
    parser.add_argument("--url", default=None, help="URL to analyze")
    parser.add_argument("--file", default=None, help="Local HTML/text file to analyze")
    parser.add_argument("--text", default=None, help="Raw text content to analyze")
    parser.add_argument("--keyword", default=None, help="Target keyword (auto-detected if omitted)")
    parser.add_argument("--json", default=None, help="Save JSON output")
    args = parser.parse_args()

    # Fetch content
    html = None
    source_label = ""

    if args.url:
        source_label = args.url
        html = fetch_url(args.url)
        if not html:
            sys.exit(1)
    elif args.file:
        source_label = args.file
        try:
            with open(args.file, 'r', encoding='utf-8', errors='replace') as f:
                html = f.read()
        except FileNotFoundError:
            print(f"❌ File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        source_label = "<text>"
        html = args.text
    else:
        print("❌ Provide --url, --file, or --text", file=sys.stderr)
        sys.exit(1)

    # Determine if HTML or plain text
    if html and re.search(r'</?[a-z][^>]*>', html[:500], re.IGNORECASE):
        text, meta = extract_text_from_html(html)
    else:
        text = html or ""
        meta = {}

    if not text.strip():
        print("❌ No readable text content found.", file=sys.stderr)
        sys.exit(1)

    # Analysis
    kw = analyze_keywords(text, args.keyword or "")
    readability = analyze_readability(text)
    meta_audit = audit_meta(meta)
    struct = audit_structure(text, meta, kw.total_words)
    score, recs = compute_score(kw, readability, meta_audit, struct)

    report = SEOReport(
        url_or_file=source_label,
        keyword=kw,
        readability=readability,
        meta=meta_audit,
        structure=struct,
        overall_score=score,
        recommendations=recs,
    )

    print(format_report(report))

    if args.json:
        output = {
            "source": source_label,
            "overall_score": score,
            "keyword": {
                "keyword": kw.keyword,
                "density_pct": kw.density_pct,
                "count": kw.keyword_count,
                "total_words": kw.total_words,
                "prominence_score": kw.prominence_score,
                "top_bigrams": kw.top_bigrams[:5],
            },
            "readability": {
                "flesch_kincaid_grade": readability.flesch_kincaid_grade,
                "flesch_reading_ease": readability.flesch_reading_ease,
                "ari": readability.automated_readability_index,
                "coleman_liau": readability.coleman_liau_index,
            },
            "meta": {
                "title": meta_audit.title,
                "title_length": meta_audit.title_length,
                "title_ok": meta_audit.title_ok,
                "description_ok": meta_audit.description_ok,
                "h1_count": meta_audit.h1_count,
                "h1_ok": meta_audit.h1_ok,
            },
            "structure": {
                "heading_valid": struct.heading_hierarchy_valid,
                "internal_links": struct.internal_links,
                "external_links": struct.external_links,
                "link_density_pct": struct.link_density_pct,
                "images_missing_alt": struct.images_missing_alt,
            },
            "recommendations": recs,
        }
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON saved to: {args.json}")


if __name__ == "__main__":
    main()
