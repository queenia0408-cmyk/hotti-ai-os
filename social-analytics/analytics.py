#!/usr/bin/env python3
"""
Social Media Analytics — Content Calendar + Engagement Calculator + Optimal Post Timing
Cycle 10 Autonomous Evolution — Marketing Domain Deep-Dive

Features:
- Content calendar with engagement forecasting
- Optimal posting time analysis (engagement heatmap)
- Viral coefficient calculator (K-factor)
- Hashtag performance scoring
- Platform-specific engagement rate benchmarks

Usage:
    python analytics.py calendar --platforms "Twitter, LinkedIn, Instagram" --posts 7
    python analytics.py viral --followers 10000 --avg-likes 250 --avg-shares 45
    python analytics.py hashtags --tags "tech, ai, python, coding, startup, machine-learning"
    python analytics.py benchmark --followers 5000 --likes 200 --comments 35 --shares 25 --platform Twitter
"""

import argparse
import calendar as cal
import json
import math
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


# ─── Data Models ─────────────────────────────────────────────────────────

@dataclass
class ContentPost:
    day: str               # "Mon", "Tue", etc.
    platform: str
    content_type: str      # "educational", "promotional", "engagement", "behind-scenes"
    topic: str
    best_time: str         # "09:00"
    expected_engagement: float  # %
    hashtags: List[str] = field(default_factory=list)


@dataclass
class ViralMetrics:
    followers: int
    avg_likes: int
    avg_comments: int
    avg_shares: int
    avg_impressions: int
    engagement_rate: float
    k_factor: float        # how many new followers each follower brings
    virality_score: float  # 0-100
    quality_score: str     # "Low / Medium / High / Viral"


@dataclass
class HashtagScore:
    tag: str
    popularity: int        # 0-100 (estimated search volume)
    competition: int       # 0-100 (how many posts use it)
    relevance: float       # 0-1
    score: float           # composite
    recommendation: str    # "Use", "Consider", "Avoid"


@dataclass
class PlatformBenchmark:
    platform: str
    followers: int
    engagement_rate: float
    industry_avg: float
    percentile: int        # vs industry
    rating: str            # "Below Avg", "Average", "Above Avg", "Excellent"


# ─── Content Calendar ────────────────────────────────────────────────────

CONTENT_TYPES = {
    "educational": {"weight": 0.4, "emoji": "📚", "desc": "How-to, tutorials, insights"},
    "promotional": {"weight": 0.2, "emoji": "📢", "desc": "Product, offer, launch"},
    "engagement":  {"weight": 0.25, "emoji": "💬", "desc": "Polls, questions, UGC"},
    "behind-scenes": {"weight": 0.15, "emoji": "🎬", "desc": "Team, process, culture"},
}

BEST_TIMES = {
    "Twitter":   {"Mon": "09:00", "Tue": "10:00", "Wed": "09:00", "Thu": "11:00", "Fri": "09:00", "Sat": "10:00", "Sun": "11:00"},
    "LinkedIn":  {"Mon": "10:00", "Tue": "11:00", "Wed": "08:00", "Thu": "10:00", "Fri": "08:00", "Sat": "09:00", "Sun": "10:00"},
    "Instagram": {"Mon": "11:00", "Tue": "09:00", "Wed": "11:00", "Thu": "12:00", "Fri": "09:00", "Sat": "10:00", "Sun": "10:00"},
    "YouTube":   {"Mon": "14:00", "Tue": "12:00", "Wed": "14:00", "Thu": "12:00", "Fri": "14:00", "Sat": "10:00", "Sun": "11:00"},
    "TikTok":    {"Mon": "10:00", "Tue": "16:00", "Wed": "11:00", "Thu": "15:00", "Fri": "10:00", "Sat": "11:00", "Sun": "12:00"},
    "Facebook":  {"Mon": "09:00", "Tue": "11:00", "Wed": "10:00", "Thu": "13:00", "Fri": "09:00", "Sat": "10:00", "Sun": "10:00"},
}

TOPIC_POOLS = {
    "tech": ["AI trends", "coding tips", "system design", "open source", "dev tools"],
    "business": ["growth hacks", "fundraising", "team building", "metrics that matter", "GTM strategy"],
    "creator": ["content tips", "audience building", "monetization", "collaborations", "personal brand"],
    "lifestyle": ["wellness", "productivity", "travel", "food", "fashion"],
}


def generate_calendar(platforms: List[str], num_posts: int, niche: str = "tech") -> List[ContentPost]:
    """Generate optimized content calendar."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    topics = TOPIC_POOLS.get(niche, TOPIC_POOLS["tech"])
    posts = []

    for i in range(num_posts):
        day = days[i % 7]
        platform = platforms[i % len(platforms)]

        # Weighted random content type
        types = list(CONTENT_TYPES.keys())
        weights = [CONTENT_TYPES[t]["weight"] for t in types]
        # Deterministic based on index
        ctype = types[i % len(types)]

        topic = topics[i % len(topics)]
        best_time = BEST_TIMES.get(platform, BEST_TIMES["Twitter"]).get(day, "10:00")

        # Expected engagement varies by platform + content type
        base_engagement = {
            "Twitter": 1.5, "LinkedIn": 2.8, "Instagram": 3.2,
            "YouTube": 4.5, "TikTok": 6.0, "Facebook": 1.2,
        }
        type_multiplier = {
            "educational": 1.4, "promotional": 0.6, "engagement": 2.0, "behind-scenes": 1.2,
        }
        expected = base_engagement.get(platform, 2.0) * type_multiplier.get(ctype, 1.0)
        # Add slight variation
        expected *= 0.9 + (hash(f"{day}{platform}{i}") % 20) / 100

        hashtags = generate_hashtags(topic, 3)

        posts.append(ContentPost(
            day=day,
            platform=platform,
            content_type=ctype,
            topic=topic,
            best_time=best_time,
            expected_engagement=round(expected, 1),
            hashtags=hashtags,
        ))

    return posts


def generate_hashtags(topic: str, count: int) -> List[str]:
    """Generate relevant hashtag suggestions."""
    pools = {
        "AI trends": ["#AI", "#MachineLearning", "#TechTrends", "#FutureOfWork"],
        "coding tips": ["#CodeNewbie", "#100DaysOfCode", "#Programming", "#DevCommunity"],
        "system design": ["#SystemDesign", "#Architecture", "#SoftwareEngineering", "#TechTalks"],
        "open source": ["#OpenSource", "#GitHub", "#FOSS", "#DevCommunity"],
        "dev tools": ["#DevTools", "#Productivity", "#Developer", "#TechStack"],
        "growth hacks": ["#GrowthHacking", "#StartupLife", "#MarketingStrategy", "#BusinessGrowth"],
        "fundraising": ["#VentureCapital", "#Fundraising", "#StartupFunding", "#Entrepreneur"],
        "content tips": ["#ContentCreator", "#CreatorEconomy", "#ContentStrategy", "#SocialMedia"],
    }
    candidates = pools.get(topic, ["#Tech", "#Innovation", "#Digital"])
    return candidates[:count]


# ─── Viral Coefficient ───────────────────────────────────────────────────

def analyze_virality(followers: int, avg_likes: int, avg_comments: int = 0,
                     avg_shares: int = 0, avg_impressions: int = 0) -> ViralMetrics:
    """Calculate viral potential and K-factor."""
    if avg_impressions == 0:
        avg_impressions = followers * 3  # rough estimate

    # Engagement rate = (likes + comments + shares) / impressions
    total_engagements = avg_likes + avg_comments + avg_shares
    engagement_rate = (total_engagements / avg_impressions * 100) if avg_impressions > 0 else 0

    # K-factor = avg shares per post × conversion rate of share viewers → followers
    share_conversion = 0.02  # 2% of share viewers become followers
    k_factor = avg_shares * share_conversion if followers > 0 else 0

    # Virality score (0-100): composite of engagement, share ratio, k-factor
    share_ratio = (avg_shares / avg_likes * 100) if avg_likes > 0 else 0

    viral_base = min(100, engagement_rate * 12)  # engagement scaled
    viral_share = min(100, share_ratio * 5)       # share ratio scaled
    viral_k = min(100, k_factor * 200)            # k-factor scaled

    virality_score = round(viral_base * 0.3 + viral_share * 0.3 + viral_k * 0.4, 1)

    if virality_score >= 80:
        quality = "🚀 Viral — Content has strong viral mechanics"
    elif virality_score >= 60:
        quality = "📈 High — Optimize for shares to reach viral"
    elif virality_score >= 40:
        quality = "📊 Medium — Steady engagement, work on shareability"
    elif virality_score >= 20:
        quality = "📉 Low — Improve content quality and CTA"
    else:
        quality = "⚠️ Very Low — Fundamental content/market fit issue"

    return ViralMetrics(
        followers=followers,
        avg_likes=avg_likes,
        avg_comments=avg_comments,
        avg_shares=avg_shares,
        avg_impressions=avg_impressions,
        engagement_rate=round(engagement_rate, 2),
        k_factor=round(k_factor, 4),
        virality_score=virality_score,
        quality_score=quality,
    )


# ─── Hashtag Scoring ─────────────────────────────────────────────────────

def score_hashtags(tags: List[str]) -> List[HashtagScore]:
    """Score hashtags by popularity, competition, relevance."""
    # Simulated hashtag database
    known_tags = {
        "ai": (95, 90), "tech": (90, 85), "python": (75, 60), "coding": (80, 70),
        "startup": (70, 80), "machine-learning": (60, 55), "programming": (75, 70),
        "developer": (65, 55), "javascript": (70, 65), "react": (60, 55),
        "marketing": (75, 80), "growth": (55, 65), "seo": (50, 60),
        "design": (70, 75), "ui": (55, 65), "ux": (50, 55),
        "business": (80, 90), "entrepreneur": (65, 80), "innovation": (60, 70),
    }

    results = []
    for tag in tags:
        tag_clean = tag.lower().lstrip("#").strip()
        popularity, competition = known_tags.get(tag_clean, (40, 50))

        # Score: high popularity + low competition = best
        relevance = 0.7 + (hash(tag_clean) % 30) / 100  # 0.7-1.0
        score = (popularity * 0.4 + (100 - competition) * 0.4 + relevance * 100 * 0.2)
        score = round(score, 1)

        if score >= 70:
            rec = "✅ Use — High value hashtag"
        elif score >= 50:
            rec = "🤔 Consider — Decent but not outstanding"
        else:
            rec = "❌ Avoid — Too competitive or low relevance"

        results.append(HashtagScore(
            tag=f"#{tag_clean}",
            popularity=popularity,
            competition=competition,
            relevance=round(relevance, 2),
            score=score,
            recommendation=rec,
        ))

    results.sort(key=lambda h: -h.score)
    return results


# ─── Platform Benchmarks ─────────────────────────────────────────────────

INDUSTRY_BENCHMARKS = {
    "Twitter": 0.8, "LinkedIn": 2.5, "Instagram": 3.0,
    "YouTube": 4.0, "TikTok": 5.5, "Facebook": 1.0,
}


def benchmark_engagement(platform: str, followers: int, likes: int,
                         comments: int, shares: int) -> PlatformBenchmark:
    """Benchmark engagement against industry averages."""
    total_engagement = likes + comments + shares
    impressions = likes * 20  # rough: ~5% of impressions → likes
    engagement_rate = (total_engagement / impressions * 100) if impressions > 0 else 0

    industry_avg = INDUSTRY_BENCHMARKS.get(platform, 2.0)
    ratio = engagement_rate / industry_avg if industry_avg > 0 else 1

    # Percentile estimation
    if ratio >= 3.0:
        percentile = 97
        rating = "🏆 Excellent — Top 3%"
    elif ratio >= 2.0:
        percentile = 90
        rating = "📈 Above Average — Top 10%"
    elif ratio >= 1.0:
        percentile = 60
        rating = "📊 Average — Middle of the pack"
    elif ratio >= 0.5:
        percentile = 30
        rating = "📉 Below Average — Bottom 30%"
    else:
        percentile = 10
        rating = "⚠️ Poor — Bottom 10%. Major improvement needed."

    return PlatformBenchmark(
        platform=platform,
        followers=followers,
        engagement_rate=round(engagement_rate, 2),
        industry_avg=industry_avg,
        percentile=percentile,
        rating=rating,
    )


# ─── Reports ─────────────────────────────────────────────────────────────

def format_calendar(posts: List[ContentPost]) -> str:
    bar = "═" * 72
    lines = [f"\n{bar}", f"📅 CONTENT CALENDAR — {len(posts)} posts across {len(set(p.platform for p in posts))} platforms", f"{bar}"]

    for i, p in enumerate(posts, 1):
        ctype_info = CONTENT_TYPES.get(p.content_type, {})
        lines.extend([
            f"",
            f"  #{i:2d} | {p.day:3} {p.best_time} | {p.platform:12} | {ctype_info.get('emoji', '')} {p.content_type:14} | {p.topic}",
            f"       Expected Engagement: {p.expected_engagement}% | {', '.join(p.hashtags)}",
        ])

    lines.extend([f"", f"{bar}", f"✅ Content calendar generated.\n"])
    return "\n".join(lines)


def format_viral(vm: ViralMetrics) -> str:
    bar = "═" * 64
    return f"""
{bar}
🦠 VIRAL POTENTIAL ANALYSIS
{bar}

   Followers:        {vm.followers:,}
   Avg Likes:        {vm.avg_likes:,}
   Avg Comments:     {vm.avg_comments:,}
   Avg Shares:       {vm.avg_shares:,}

   Engagement Rate:  {vm.engagement_rate}%
   K-Factor:         {vm.k_factor:.4f}
   Virality Score:   {vm.virality_score}/100

   {vm.quality_score}

{bar}
✅ Viral analysis complete.
"""


def format_hashtags(scores: List[HashtagScore]) -> str:
    bar = "═" * 64
    lines = [f"\n{bar}", f"#️⃣ HASHTAG PERFORMANCE ANALYSIS", f"{bar}", f""]

    for s in scores:
        lines.append(f"   {s.tag:20} Score: {s.score:5.0f}/100 | Pop: {s.popularity:3} | Comp: {s.competition:3} | {s.recommendation}")

    lines.extend([f"", f"{bar}", f"✅ Hashtag analysis complete.\n"])
    return "\n".join(lines)


def format_benchmark(pb: PlatformBenchmark) -> str:
    bar = "═" * 64
    return f"""
{bar}
📊 PLATFORM BENCHMARK — {pb.platform}
{bar}

   Followers:           {pb.followers:,}
   Engagement Rate:     {pb.engagement_rate}%
   Industry Average:    {pb.industry_avg}%
   Estimated Percentile: Top {100 - pb.percentile}%

   {pb.rating}

{bar}
✅ Benchmark analysis complete.
"""


# ─── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Social Media Analytics — Content Calendar + Viral Calculator + Hashtag Scoring",
        epilog="Cycle 10 Autonomous Evolution | Claude Code Self-Evolution"
    )
    subparsers = parser.add_subparsers(dest="command", help="Analysis type")

    # Calendar
    cal_parser = subparsers.add_parser("calendar", help="Generate content calendar")
    cal_parser.add_argument("--platforms", type=lambda s: [p.strip() for p in s.split(",")],
                            default=["Twitter", "LinkedIn", "Instagram"])
    cal_parser.add_argument("--posts", type=int, default=14, help="Number of posts")
    cal_parser.add_argument("--niche", default="tech", choices=["tech", "business", "creator", "lifestyle"])
    cal_parser.add_argument("--json", default=None)

    # Viral
    viral_parser = subparsers.add_parser("viral", help="Calculate viral potential")
    viral_parser.add_argument("--followers", type=int, required=True)
    viral_parser.add_argument("--likes", dest="avg_likes", type=int, required=True)
    viral_parser.add_argument("--comments", dest="avg_comments", type=int, default=0)
    viral_parser.add_argument("--shares", dest="avg_shares", type=int, default=0)
    viral_parser.add_argument("--json", default=None)

    # Hashtags
    tag_parser = subparsers.add_parser("hashtags", help="Score hashtags")
    tag_parser.add_argument("--tags", type=lambda s: [t.strip() for t in s.split(",")], required=True)
    tag_parser.add_argument("--json", default=None)

    # Benchmark
    bench_parser = subparsers.add_parser("benchmark", help="Platform benchmark")
    bench_parser.add_argument("--platform", required=True)
    bench_parser.add_argument("--followers", type=int, required=True)
    bench_parser.add_argument("--likes", type=int, required=True)
    bench_parser.add_argument("--comments", type=int, default=0)
    bench_parser.add_argument("--shares", type=int, default=0)
    bench_parser.add_argument("--json", default=None)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "calendar":
        posts = generate_calendar(args.platforms, args.posts, args.niche)
        print(format_calendar(posts))
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump([{
                    "day": p.day, "platform": p.platform, "content_type": p.content_type,
                    "topic": p.topic, "best_time": p.best_time,
                    "expected_engagement": p.expected_engagement, "hashtags": p.hashtags,
                } for p in posts], f, indent=2)

    elif args.command == "viral":
        vm = analyze_virality(args.followers, args.avg_likes, args.avg_comments, args.avg_shares)
        print(format_viral(vm))
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({"followers": vm.followers, "avg_likes": vm.avg_likes,
                           "avg_comments": vm.avg_comments, "avg_shares": vm.avg_shares,
                           "engagement_rate": vm.engagement_rate, "k_factor": vm.k_factor,
                           "virality_score": vm.virality_score, "quality": vm.quality_score}, f, indent=2)

    elif args.command == "hashtags":
        scores = score_hashtags(args.tags)
        print(format_hashtags(scores))
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump([{"tag": s.tag, "score": s.score, "popularity": s.popularity,
                            "competition": s.competition, "recommendation": s.recommendation}
                           for s in scores], f, indent=2)

    elif args.command == "benchmark":
        pb = benchmark_engagement(args.platform, args.followers, args.likes, args.comments, args.shares)
        print(format_benchmark(pb))
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump({"platform": pb.platform, "followers": pb.followers,
                           "engagement_rate": pb.engagement_rate, "industry_avg": pb.industry_avg,
                           "percentile": pb.percentile, "rating": pb.rating}, f, indent=2)


if __name__ == "__main__":
    main()
