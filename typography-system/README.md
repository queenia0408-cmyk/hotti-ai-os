# Typography Design Token System

> Cycle 3 Build-to-Understand | Claude Code Self-Evolution v3.0

Production-ready CSS Custom Properties typography system with fluid scaling, dark mode, and CJK+Latin support.

## Quick Start

```bash
open index.html
```

Or include in your project:

```html
<link rel="stylesheet" href="tokens.css">
```

## Features

- **60+ Design Tokens**: CSS Custom Properties at primitive, semantic, and utility layers
- **Fluid Type Scale**: `clamp()`-based 1.25 Major Third scale (xs → 4xl)
- **Dark Mode**: Automatic `prefers-color-scheme: dark` support
- **CJK + Latin**: Pretendard + Inter, Noto Serif KR + Merriweather pairings
- **Print Styles**: Automatic serif switch for print media
- **Accessibility**: `prefers-reduced-motion` support
- **Component Tokens**: Card, Navigation, Article semantic layers

## Token Architecture

```
Layer 1 — Primitives:  font-size-*, font-family-*, font-weight-*
Layer 2 — Semantic:    --heading-*, --body-*, --link-*, --card-*
Layer 3 — Utilities:   .text-*, .font-*, .leading-*, .measure-*
```

## Preview

Open `index.html` for interactive specimen, pairings, and token reference.
