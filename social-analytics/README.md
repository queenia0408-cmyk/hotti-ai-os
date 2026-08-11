# Social Media Analytics Suite

Content Calendar + Viral Coefficient + Hashtag Scoring + Platform Benchmarks.

## Quick Start

```bash
python analytics.py calendar --platforms "Twitter, LinkedIn, Instagram" --posts 14
python analytics.py viral --followers 10000 --likes 250 --shares 45 --comments 35
python analytics.py hashtags --tags "tech, ai, python, coding, startup"
python analytics.py benchmark --platform Twitter --followers 5000 --likes 200 --comments 35 --shares 25
```

## Features

- **Content Calendar** — Optimized posting schedule with engagement forecasts per platform/type
- **Viral Calculator** — K-factor, virality score (0-100), engagement rate analysis
- **Hashtag Scorer** — Popularity × Competition × Relevance composite scoring
- **Platform Benchmarks** — Industry percentile comparison (Twitter, LinkedIn, Instagram, etc.)

## Platforms Supported

Twitter, LinkedIn, Instagram, YouTube, TikTok, Facebook — with platform-specific best posting times and industry benchmarks.

## Tech

Python, argparse, dataclasses, engagement rate formulas, K-factor
