# SEO Content Analyzer

Keyword density + readability scores + meta tag audit + structure validation.

## Quick Start

```bash
python analyzer.py --url https://example.com
python analyzer.py --file page.html --keyword "SEO optimization"
python analyzer.py --text "Your content here..." --keyword "target phrase"
python analyzer.py --url https://example.com --json report.json
```

## Features

- **Keyword Analysis** — density %, prominence, bigram/trigram extraction
- **Readability Scores** — Flesch-Kincaid Grade, Reading Ease, ARI, Coleman-Liau
- **Meta Tag Audit** — title length, description, H1 count validation
- **Structure Check** — heading hierarchy, link density, image alt text coverage
- **Scoring** — 0-100 composite SEO score with actionable recommendations

## Scoring Dimensions

| Dimension | Points | Checks |
|-----------|--------|--------|
| Keywords | 30 | Density 1-3%, Prominence, Length 300+ words |
| Readability | 25 | Reading Ease 60-70, Sentence <25 words, Complex <15% |
| Meta Tags | 25 | Title 30-60c, Description 120-160c, Exactly 1 H1 |
| Structure | 20 | Heading hierarchy, Link density 2-8%, Alt text 90%+ |

## Tech

Python, regex, syllable counting, Flesch-Kincaid, Coleman-Liau, ARI
