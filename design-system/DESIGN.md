---
title: "Design System Specification (DESIGN.md)"
version: "1.0.0"
protocol: "google-labs-design-md"
generator_target: "AI agent UI component generation"
domains: ["web", "react", "css"]
language: "markdown"
token_namespace: "ds"
css_variable_prefix: "--ds"
status: "active"
created: "2026-08-12"
updated: "2026-08-12"
---

# DESIGN.md — Design System Specification

> Machine-readable design system specification. An AI agent that parses this document MUST be able to
> generate consistent UI components (Button, Input, Card, Badge, Alert) with correct tokens, states,
> variants, sizes, and accessibility behavior.
>
> Every token and component contract below is normalized into tables so they can be extracted by regex,
> and exported as JSON in the final section. Section markers `<!-- @section: ... -->` delimit parsable blocks.

## Document Control

| Field | Value |
|---|---|
| Document | Design System Specification |
| Version | 1.0.0 |
| Protocol | Google Labs DESIGN.md |
| Token namespace | `ds` (CSS custom property prefix: `--ds-`) |
| Naming convention | `layer.category.property` → kebab-case CSS var, e.g. `color.blue.500` → `--ds-color-blue-500` |
| Methodology | 3-tier tokens → base styles → components → utilities |
| CSS architecture | Custom Properties + BEM (`ds-btn`, `ds-btn--primary`, `ds-btn__icon`) |
| Baseline | Aligned with `components.css` in this directory |

---

## 1. Design Principles

1. **Token-first.** Every visual decision is a token. No hard-coded hex, rem, or px inside component rules.
2. **3-tier abstraction.** Components reference **component tokens** → component tokens reference **semantic tokens** → semantic tokens reference **primitives**. A component never references a primitive directly.
3. **Accessible by default.** All interactive elements meet WCAG 2.1 AA (see `<!-- @section: accessibility -->`).
4. **CJK + Latin parity.** The type system is designed so Korean (CJK) and English render with equal rhythm and legibility.
5. **Responsive rhythm.** Spacing, type, and layout scale on a 4px grid across 5 breakpoints.
6. **Machine-generatable.** Every contract in this document is a table an agent can parse into props, CSS, and test fixtures.

### 1.1 Tier Rules (enforced)

| Rule | Contract |
|---|---|
| T1 | Primitives hold raw values only (`#3B82F6`). They carry no meaning. |
| T2 | Semantic tokens hold purpose, not raw values (`color-primary`). They map to primitives. |
| T3 | Component tokens are scoped to a component part (`button-primary-bg`). They map to semantic tokens. |
| T4 | Dark mode is a mapping override at the semantic tier (component tokens resolve through it). Primitives are shared. |
| T5 | Any agent-generated component MUST resolve T3 → T2 → T1 before emitting CSS custom properties. |

---

<!-- @section: colors -->

## 2. Color System (3-Tier Token Architecture)

### 2.1 Tier 1 — Primitive Tokens

Raw color values. Shared across light/dark. Prefix: `--ds-color-`.

#### Neutral (Slate)

| Token | CSS Variable | Hex | Usage |
|---|---|---|---|
| color.gray.50 | `--ds-color-gray-50` | `#F8FAFC` | Subtle surface tint, hover wash |
| color.gray.100 | `--ds-color-gray-100` | `#F1F5F9` | Hover background, disabled fill |
| color.gray.200 | `--ds-color-gray-200` | `#E2E8F0` | Borders, skeleton base |
| color.gray.300 | `--ds-color-gray-300` | `#CBD5E1` | Strong border, placeholder glyph |
| color.gray.400 | `--ds-color-gray-400` | `#94A3B8` | Tertiary text, disabled text |
| color.gray.500 | `--ds-color-gray-500` | `#64748B` | Secondary text |
| color.gray.600 | `--ds-color-gray-600` | `#475569` | Muted interactive, secondary icons |
| color.gray.700 | `--ds-color-gray-700` | `#334155` | Emphasis text on tinted bg |
| color.gray.800 | `--ds-color-gray-800` | `#1E293B` | Tooltip bg, dark surface |
| color.gray.900 | `--ds-color-gray-900` | `#0F172A` | Primary text (light), dark surface |
| color.gray.950 | `--ds-color-gray-950` | `#020617` | Dark canvas background |
| color.white | `--ds-color-white` | `#FFFFFF` | Surface, inverse text |
| color.black | `--ds-color-black` | `#0F172A` | Neutral black (slate-900) |

#### Brand — Blue (primary)

| Token | CSS Variable | Hex | Usage |
|---|---|---|---|
| color.blue.50 | `--ds-color-blue-50` | `#EFF6FF` | Info alert bg, primary tint |
| color.blue.100 | `--ds-color-blue-100` | `#DBEAFE` | Info badge bg |
| color.blue.200 | `--ds-color-blue-200` | `#BFDBFE` | Selected/ring tint |
| color.blue.300 | `--ds-color-blue-300` | `#93C5FD` | Disabled brand accent |
| color.blue.400 | `--ds-color-blue-400` | `#60A5FA` | Dark-mode primary hover |
| color.blue.500 | `--ds-color-blue-500` | `#3B82F6` | Primary (dark), focus border |
| color.blue.600 | `--ds-color-blue-600` | `#2563EB` | Primary (light), link |
| color.blue.700 | `--ds-color-blue-700` | `#1D4ED8` | Primary hover (light) |
| color.blue.800 | `--ds-color-blue-800` | `#1E40AF` | Primary active, info text |
| color.blue.900 | `--ds-color-blue-900` | `#1E3A8A` | Dark-mode primary tint |

#### Status — Green (success)

| Token | CSS Variable | Hex | Usage |
|---|---|---|---|
| color.green.50 | `--ds-color-green-50` | `#F0FDF4` | Success alert bg |
| color.green.100 | `--ds-color-green-100` | `#DCFCE7` | Success badge bg |
| color.green.500 | `--ds-color-green-500` | `#22C55E` | Success accent (dark) |
| color.green.600 | `--ds-color-green-600` | `#16A34A` | Success accent (large/decorative) |
| color.green.700 | `--ds-color-green-700` | `#15803D` | Success text on tint, success button |
| color.green.800 | `--ds-color-green-800` | `#166534` | Success badge text |

#### Status — Red (danger/error)

| Token | CSS Variable | Hex | Usage |
|---|---|---|---|
| color.red.50 | `--ds-color-red-50` | `#FEF2F2` | Danger alert bg |
| color.red.100 | `--ds-color-red-100` | `#FEE2E2` | Danger badge bg |
| color.red.400 | `--ds-color-red-400` | `#F87171` | Dark-mode danger hover |
| color.red.500 | `--ds-color-red-500` | `#EF4444` | Danger accent, error border |
| color.red.600 | `--ds-color-red-600` | `#DC2626` | Danger button (light) |
| color.red.700 | `--ds-color-red-700` | `#B91C1C` | Danger hover, danger text |

#### Status — Yellow (warning)

| Token | CSS Variable | Hex | Usage |
|---|---|---|---|
| color.yellow.50 | `--ds-color-yellow-50` | `#FEFCE8` | Warning alert bg |
| color.yellow.100 | `--ds-color-yellow-100` | `#FEF9C3` | Warning badge bg |
| color.yellow.500 | `--ds-color-yellow-500` | `#EAB308` | Warning accent |
| color.yellow.600 | `--ds-color-yellow-600` | `#CA8A04` | Warning icon on tint |
| color.yellow.700 | `--ds-color-yellow-700` | `#A16207` | Warning text on tint |

#### Accent — Purple

| Token | CSS Variable | Hex | Usage |
|---|---|---|---|
| color.purple.50 | `--ds-color-purple-50` | `#FAF5FF` | Purple tint bg |
| color.purple.100 | `--ds-color-purple-100` | `#F3E8FF` | Purple badge bg |
| color.purple.500 | `--ds-color-purple-500` | `#8B5CF6` | Purple accent |
| color.purple.600 | `--ds-color-purple-600` | `#7C3AED` | Purple accent strong |
| color.purple.700 | `--ds-color-purple-700` | `#6D28D9` | Purple text on tint |

**Primitive count: 47.** Primitives do NOT change between light and dark mode; they are the shared source of truth.

### 2.2 Tier 2 — Semantic Tokens

Purpose-mapped. These are the ONLY tokens that flip between light and dark. Prefix: `--ds-` (e.g. `--ds-bg-surface`).

| Token | CSS Variable | Light | Dark |
|---|---|---|---|
| color.primary | `--ds-color-primary` | `color.blue.600` | `color.blue.500` |
| color.primary-hover | `--ds-color-primary-hover` | `color.blue.700` | `color.blue.400` |
| color.primary-active | `--ds-color-primary-active` | `color.blue.800` | `color.blue.600` |
| color.primary-subtle | `--ds-color-primary-subtle` | `color.blue.50` | `color.blue.900` |
| color.secondary | `--ds-color-secondary` | `color.gray.600` | `color.gray.400` |
| color.danger | `--ds-color-danger` | `color.red.600` | `color.red.500` |
| color.danger-hover | `--ds-color-danger-hover` | `color.red.700` | `color.red.400` |
| color.danger-subtle | `--ds-color-danger-subtle` | `color.red.50` | `color.red.900`* |
| color.success | `--ds-color-success` | `color.green.700` | `color.green.500` |
| color.warning | `--ds-color-warning` | `color.yellow.600` | `color.yellow.500` |
| color.info | `--ds-color-info` | `color.blue.600` | `color.blue.500` |
| bg.canvas | `--ds-bg` | `color.gray.50` | `color.gray.950` |
| bg.surface | `--ds-bg-surface` | `color.white` | `color.gray.900` |
| bg.surface-hover | `--ds-bg-surface-hover` | `color.gray.100` | `color.gray.800` |
| bg.elevated | `--ds-bg-elevated` | `color.white` | `color.gray.800` |
| bg.overlay | `--ds-bg-overlay` | `rgba(15, 23, 42, 0.6)` | `rgba(2, 6, 23, 0.7)` |
| text.primary | `--ds-text-primary` | `color.gray.900` | `color.gray.50` |
| text.secondary | `--ds-text-secondary` | `color.gray.500` | `color.gray.400` |
| text.tertiary | `--ds-text-tertiary` | `color.gray.400` | `color.gray.500` |
| text.inverse | `--ds-text-inverse` | `color.white` | `color.gray.900` |
| text.disabled | `--ds-text-disabled` | `color.gray.400` | `color.gray.500` |
| border.default | `--ds-border` | `color.gray.200` | `color.gray.700` |
| border.subtle | `--ds-border-subtle` | `color.gray.100` | `color.gray.800` |
| border.strong | `--ds-border-strong` | `color.gray.300` | `color.gray.600` |
| border.focus | `--ds-border-focus` | `color.blue.500` | `color.blue.400` |
| ring.focus | `--ds-ring-focus` | `0 0 0 3px rgba(59,130,246,0.20)` | `0 0 0 3px rgba(96,165,250,0.25)` |
| ring.error | `--ds-ring-error` | `0 0 0 3px rgba(239,68,68,0.20)` | `0 0 0 3px rgba(248,113,113,0.25)` |

\* `color.red.900` = `#7F1D1D` (dark-mode danger tint; add to primitives when implementing dark theme).

**Semantic count: 28 (each with a dark variant).**

### 2.3 Tier 3 — Component Tokens

Component-scoped tokens. Prefix: `--ds-` + component (e.g. `--ds-button-primary-bg`). These resolve through semantic tokens, so dark mode propagates automatically.

| Token | CSS Variable | Value (light) | Applies to |
|---|---|---|---|
| button.primary-bg | `--ds-button-primary-bg` | `color.primary` | `.ds-btn--primary` |
| button.primary-text | `--ds-button-primary-text` | `text.inverse` | `.ds-btn--primary` |
| button.primary-hover-bg | `--ds-button-primary-hover-bg` | `color.primary-hover` | `:hover` |
| button.primary-active-bg | `--ds-button-primary-active-bg` | `color.primary-active` | `:active` |
| button.secondary-bg | `--ds-button-secondary-bg` | `bg.surface` | `.ds-btn--secondary` |
| button.secondary-text | `--ds-button-secondary-text` | `text.primary` | `.ds-btn--secondary` |
| button.secondary-border | `--ds-button-secondary-border` | `border.default` | `.ds-btn--secondary` |
| button.secondary-hover-bg | `--ds-button-secondary-hover-bg` | `bg.surface-hover` | `:hover` |
| button.danger-bg | `--ds-button-danger-bg` | `color.danger` | `.ds-btn--danger` |
| button.danger-text | `--ds-button-danger-text` | `text.inverse` | `.ds-btn--danger` |
| button.danger-hover-bg | `--ds-button-danger-hover-bg` | `color.danger-hover` | `:hover` |
| button.ghost-text | `--ds-button-ghost-text` | `text.secondary` | `.ds-btn--ghost` |
| button.ghost-hover-bg | `--ds-button-ghost-hover-bg` | `bg.surface-hover` | `:hover` |
| button.ghost-hover-text | `--ds-button-ghost-hover-text` | `text.primary` | `:hover` |
| button.disabled-opacity | `--ds-button-disabled-opacity` | `0.5` | `:disabled` |
| button.border-width | `--ds-button-border-width` | `2px` | all variants |
| button.focus-ring | `--ds-button-focus-ring` | `ring.focus` | `:focus-visible` |
| input.bg | `--ds-input-bg` | `bg.surface` | `.ds-input` |
| input.border | `--ds-input-border` | `border.default` | `.ds-input` |
| input.text | `--ds-input-text` | `text.primary` | `.ds-input` |
| input.placeholder | `--ds-input-placeholder` | `text.tertiary` | `::placeholder` |
| input.focus-border | `--ds-input-focus-border` | `border.focus` | `:focus` |
| input.focus-ring | `--ds-input-focus-ring` | `ring.focus` | `:focus` |
| input.error-border | `--ds-input-error-border` | `color.danger` | `[aria-invalid="true"]` |
| input.error-ring | `--ds-input-error-ring` | `ring.error` | `[aria-invalid="true"]:focus` |
| input.disabled-bg | `--ds-input-disabled-bg` | `bg.surface-hover` | `:disabled` |
| input.disabled-text | `--ds-input-disabled-text` | `text.disabled` | `:disabled` |
| card.bg | `--ds-card-bg` | `bg.surface` | `.ds-card` |
| card.border | `--ds-card-border` | `border.default` | `.ds-card` |
| card.shadow-hover | `--ds-card-shadow-hover` | `shadow.md` | `.ds-card:hover` |
| card.shadow-elevated | `--ds-card-shadow-elevated` | `shadow.lg` | `.ds-card--elevated` |
| badge.default-bg | `--ds-badge-default-bg` | `color.gray.100` | `.ds-badge--default` |
| badge.default-text | `--ds-badge-default-text` | `color.gray.700` | `.ds-badge--default` |
| badge.success-bg | `--ds-badge-success-bg` | `color.green.100` | `.ds-badge--success` |
| badge.success-text | `--ds-badge-success-text` | `color.green.800` | `.ds-badge--success` |
| badge.warning-bg | `--ds-badge-warning-bg` | `color.yellow.50` | `.ds-badge--warning` |
| badge.warning-text | `--ds-badge-warning-text` | `color.yellow.700` | `.ds-badge--warning` |
| badge.danger-bg | `--ds-badge-danger-bg` | `color.red.100` | `.ds-badge--danger` |
| badge.danger-text | `--ds-badge-danger-text` | `color.red.700` | `.ds-badge--danger` |
| badge.info-bg | `--ds-badge-info-bg` | `color.blue.100` | `.ds-badge--info` |
| badge.info-text | `--ds-badge-info-text` | `color.blue.800` | `.ds-badge--info` |
| alert.info-bg | `--ds-alert-info-bg` | `color.blue.50` | `.ds-alert--info` |
| alert.info-border | `--ds-alert-info-border` | `color.blue.500` | `.ds-alert--info` |
| alert.info-text | `--ds-alert-info-text` | `color.blue.800` | `.ds-alert--info` |
| alert.success-bg | `--ds-alert-success-bg` | `color.green.50` | `.ds-alert--success` |
| alert.success-border | `--ds-alert-success-border` | `color.green.500` | `.ds-alert--success` |
| alert.success-text | `--ds-alert-success-text` | `color.green.800` | `.ds-alert--success` |
| alert.warning-bg | `--ds-alert-warning-bg` | `color.yellow.50` | `.ds-alert--warning` |
| alert.warning-border | `--ds-alert-warning-border` | `color.yellow.500` | `.ds-alert--warning` |
| alert.warning-text | `--ds-alert-warning-text` | `color.yellow.700` | `.ds-alert--warning` |
| alert.danger-bg | `--ds-alert-danger-bg` | `color.red.50` | `.ds-alert--danger` |
| alert.danger-border | `--ds-alert-danger-border` | `color.red.500` | `.ds-alert--danger` |
| alert.danger-text | `--ds-alert-danger-text` | `color.red.700` | `.ds-alert--danger` |
| focus.ring-width | `--ds-focus-ring-width` | `2px` | all focus rings |
| focus.ring-offset | `--ds-focus-ring-offset` | `2px` | all focus rings |

**Component token count: 53.** Total color-system tokens across all tiers: **47 + 28 + 53 = 128.**

### 2.4 Dark Mode Strategy

Dark mode is applied by overriding ONLY the semantic tier inside a `[data-theme="dark"]` (or `.ds-dark`) selector. Primitives and component tokens are untouched.

```css
:root { /* light — semantic tokens resolve to light primitives */ }
[data-theme="dark"] {
  --ds-color-primary: var(--ds-color-blue-500);
  --ds-bg: var(--ds-color-gray-950);
  --ds-bg-surface: var(--ds-color-gray-900);
  --ds-text-primary: var(--ds-color-gray-50);
  /* ...all semantic tokens remapped... */
}
```

Rules:
- Dark surfaces come from `gray.950` (canvas), `gray.900` (surface), `gray.800` (elevated/hover).
- Primary accent shifts one step lighter (`blue.600 → blue.500`) to hold luminance on dark surfaces.
- Focus ring on dark uses `blue.400` with higher alpha.
- Elevation in dark mode is expressed through **surface lightness**, not shadow (shadows are near-invisible on dark).

### 2.5 WCAG 2.1 AA Contrast Compliance

Documented ratios for every sanctioned text-on-bg pairing. AA = ≥ 4.5:1 normal text / ≥ 3.0:1 large text (≥ 24px or ≥ 18.66px bold). AAA = ≥ 7:1.

| Pairing (light) | Foreground | Background | Ratio | Level |
|---|---|---|---|---|
| text.primary on surface | `gray.900` | `white` | 17.9 : 1 | AAA |
| text.secondary on surface | `gray.500` | `white` | 4.8 : 1 | AA |
| text.tertiary on surface | `gray.400` | `white` | 2.6 : 1 | ❌ decorative/placeholder only |
| button.primary-text on primary-bg | `white` | `blue.600` | 5.2 : 1 | AA |
| button.primary-text on primary-hover-bg | `white` | `blue.700` | 6.7 : 1 | AA (AAA large) |
| button.danger-text on danger-bg | `white` | `red.600` | 4.8 : 1 | AA |
| button.success-text on success-bg | `white` | `green.700` | 5.0 : 1 | AA |
| ~~button.success on `green.600`~~ | `white` | `green.600` | 3.3 : 1 | ❌ DO NOT USE for text — use `green.700` |
| badge.success-text on badge-success-bg | `green.800` | `green.100` | 4.6 : 1 | AA |
| badge.danger-text on badge-danger-bg | `red.700` | `red.100` | 5.9 : 1 | AA |
| badge.info-text on badge-info-bg | `blue.800` | `blue.100` | 6.2 : 1 | AA |
| badge.warning-text on badge-warning-bg | `yellow.700` | `yellow.50` | 6.4 : 1 | AA |
| alert text on alert bg (all variants) | `*-800/700` | `*-50` | ≥ 4.6 : 1 | AA |

| Pairing (dark) | Foreground | Background | Ratio | Level |
|---|---|---|---|---|
| text.primary on surface | `gray.50` | `gray.900` | 17.1 : 1 | AAA |
| text.secondary on surface | `gray.400` | `gray.900` | 7.0 : 1 | AAA |
| text.tertiary on surface | `gray.500` | `gray.900` | 4.8 : 1 | AA |
| primary text on primary-bg (dark) | `gray.900` | `blue.500` | 6.0 : 1 | AA |
| danger text on danger-bg (dark) | `gray.900` | `red.500` | 5.5 : 1 | AA |

Generation rule: an agent MUST NOT emit a color pairing whose ratio falls below AA for normal text. If a design demands it, elevate to `large` size (≥ 24px / ≥ 18.66px bold) or swap to a compliant primitive.

---

<!-- @section: typography -->

## 3. Typography System

### 3.1 Font Family Stacks (CJK + Latin)

| Token | CSS Variable | Stack | Purpose |
|---|---|---|---|
| font.sans | `--ds-font-sans` | `'Pretendard', 'Inter', 'Noto Sans KR', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', 'Helvetica Neue', Arial, sans-serif` | UI + body text. Pretendard first: harmonized Korean glyphs with metric-compatible Latin. |
| font.mono | `--ds-font-mono` | `'JetBrains Mono', 'D2Coding', 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` | Code, numbers, tabular data. D2Coding provides Korean monospace coverage. |

Rules:
- **Latin** sets `Inter`; **Korean/CJK** sets `Pretendard`. Both are in one stack so mixed text (very common in Korean products) renders consistently.
- Always end with `system-ui`/`Segoe UI`/`Malgun Gothic` fallbacks for OS-native rendering.
- `font.sans` is the default for every component unless overridden by `font.mono`.
- Do not add a font `font-weight` to the stack; weights are declared separately (see 3.4).

### 3.2 Type Scale (Static)

Base root = `16px` (`html { font-size: 100% }`). All sizes in `rem`. Prefixed `--ds-text-*`.

| Token | CSS Variable | Size (rem) | Size (px) | Line-height | Letter-spacing | Weight | Use |
|---|---|---|---|---|---|---|---|
| text.xs | `--ds-text-xs` | 0.75rem | 12px | 1.5 (18px) | 0 | 400 | captions, helper text, badge, tooltip |
| text.sm | `--ds-text-sm` | 0.875rem | 14px | 1.5 (21px) | 0 | 400 | secondary text, input md, buttons |
| text.base | `--ds-text-base` | 1rem | 16px | 1.6 (26px) | 0 | 400 | body copy (relaxed for CJK) |
| text.lg | `--ds-text-lg` | 1.125rem | 18px | 1.5 (27px) | -0.01em | 500 | lead paragraph, large input |
| text.xl | `--ds-text-xl` | 1.25rem | 20px | 1.4 (28px) | -0.01em | 600 | card title, navbar brand |
| text.2xl | `--ds-text-2xl` | 1.5rem | 24px | 1.3 (31px) | -0.02em | 700 | section heading (h2) |
| text.3xl | `--ds-text-3xl` | 1.875rem | 30px | 1.25 (37px) | -0.02em | 700 | page heading (h1) |
| text.4xl | `--ds-text-4xl` | 2.25rem | 36px | 1.2 (43px) | -0.03em | 800 | hero / display |

Line-height rule: **tighter for headings (1.2–1.4), looser for body (1.5–1.6)**. CJK text needs extra leading vs. Latin at equal size — body line-height is 1.6, never below 1.5 when the text may contain Korean.

### 3.3 Fluid Type (clamp)

Headings use fluid `clamp(min, preferred, max)` so type scales continuously between breakpoints. Convention: `clamp(min, [vw-based preferred], max)` where the preferred value is derived from viewport width.

| Token | CSS Variable | clamp() rule | 640px | 1024px | 1536px |
|---|---|---|---|---|---|
| text.fluid.display | `--ds-text-fluid-display` | `clamp(2.5rem, 5vw + 0.5rem, 4rem)` | 2.82rem | 3.12rem | 4rem |
| text.fluid.h1 | `--ds-text-fluid-h1` | `clamp(1.75rem, 4vw, 2.5rem)` | 1.75rem | 2.16rem | 2.5rem |
| text.fluid.h2 | `--ds-text-fluid-h2` | `clamp(1.5rem, 3vw, 2rem)` | 1.5rem | 1.81rem | 2rem |
| text.fluid.h3 | `--ds-text-fluid-h3` | `clamp(1.25rem, 2vw, 1.5rem)` | 1.25rem | 1.45rem | 1.5rem |
| text.fluid.h4 | `--ds-text-fluid-h4` | `clamp(1.125rem, 1.5vw, 1.25rem)` | 1.125rem | 1.28rem | 1.25rem |
| text.fluid.body | `--ds-text-fluid-body` | `clamp(0.9375rem, 0.5vw + 0.875rem, 1.0625rem)` | 0.99rem | 1.0rem | 1.06rem |

Notes for agents:
- Only headings and hero copy are fluid. `text.xs`–`text.base` stay static to preserve legibility and alignment.
- Use the `clamp()` function directly in CSS; do not replace it with media-query font sizes.
- The preferred (`vw`) term must keep `min ≤ value ≤ max` across the supported range (sm=640 → 2xl=1536). The table above shows the evaluated sizes; a generator may derive them from `min + (max - min) * (100vw - 640px) / (1536px - 640px)`.

### 3.4 Font Weights

| Weight | Token | Usage |
|---|---|---|
| 400 Regular | `--ds-font-weight-regular` | Body, input text, descriptions |
| 500 Medium | `--ds-font-weight-medium` | Nav links, labels, lead text, emphasis |
| 600 Semibold | `--ds-font-weight-semibold` | Buttons, badges, table headers, card titles |
| 700 Bold | `--ds-font-weight-bold` | Alert/Modal titles, section headings |
| 900 Black | `--ds-font-weight-black` | Brand wordmark, display numerals |

### 3.5 Numerals & Tabular Data

- Prices, counts, and tables use `font.mono` at `text.sm` when alignment of digits matters, OR `font-variant-numeric: tabular-nums` on `font.sans`.
- Korean numerals render via Pretendard by default; no special handling required.

---

<!-- @section: spacing -->

## 4. Spacing System

### 4.1 Base Scale (4px Grid)

All spacing is a multiple of 4px. Prefix `--ds-space-*`. Stored in `rem` (÷ 16).

| Token | CSS Variable | px | rem |
|---|---|---|---|
| space.1 | `--ds-space-1` | 4px | 0.25rem |
| space.2 | `--ds-space-2` | 8px | 0.5rem |
| space.3 | `--ds-space-3` | 12px | 0.75rem |
| space.4 | `--ds-space-4` | 16px | 1rem |
| space.5 | `--ds-space-5` | 20px | 1.25rem |
| space.6 | `--ds-space-6` | 24px | 1.5rem |
| space.8 | `--ds-space-8` | 32px | 2rem |
| space.10 | `--ds-space-10` | 40px | 2.5rem |
| space.12 | `--ds-space-12` | 48px | 3rem |
| space.16 | `--ds-space-16` | 64px | 4rem |
| space.20 | `--ds-space-20` | 80px | 5rem |
| space.24 | `--ds-space-24` | 96px | 6rem |

Rule: an agent MUST NOT emit a spacing value absent from this scale. `2px` (hairline) and `1px` (borders) are the only sanctioned fractional values.

### 4.2 Semantic Spacing

Purpose-mapped spacing so layout intent survives change.

| Token | CSS Variable | Value | Intent |
|---|---|---|---|
| inset.xs | `--ds-inset-xs` | `space.1` | Dense internal padding (badge, tooltip) |
| inset.sm | `--ds-inset-sm` | `space.2` | Compact control padding (button sm) |
| inset.md | `--ds-inset-md` | `space.3` + `space.4` | Default control padding (input md, button md) |
| inset.lg | `--ds-inset-lg` | `space.4` | Alert, form row, card gutter |
| inset.xl | `--ds-inset-xl` | `space.6` | Card padding, modal padding |
| stack.xs | `--ds-stack-xs` | `space.1` | Label → error text gap |
| stack.sm | `--ds-stack-sm` | `space.2` | Icon → text, list density |
| stack.md | `--ds-stack-md` | `space.4` | Title → body, input → helper |
| stack.lg | `--ds-stack-lg` | `space.6` | Card header → body, form field gap |
| stack.xl | `--ds-stack-xl` | `space.8` | Section-to-section rhythm |
| inline.xs | `--ds-inline-xs` | `space.1` | Icon inside button |
| inline.sm | `--ds-inline-sm` | `space.2` | Button icon gap, nav links |
| inline.md | `--ds-inline-md` | `space.3` | Alert icon gap, footer actions |
| inline.lg | `--ds-inline-lg` | `space.4` | Form row columns, button groups |
| gap.component | `--ds-gap-component` | `space.6` | Component stack (form, list) |
| gap.section | `--ds-gap-section` | `space.12` | Major page sections |

Mapping contract: `inset` = padding, `stack` = margin-bottom / flex column gap, `inline` = gap between inline items.

### 4.3 Radius & Shadow Scales

| Token | CSS Variable | Value |
|---|---|---|
| radius.sm | `--ds-radius-sm` | 0.25rem (4px) |
| radius.md | `--ds-radius-md` | 0.5rem (8px) |
| radius.lg | `--ds-radius-lg` | 0.75rem (12px) |
| radius.xl | `--ds-radius-xl` | 1rem (16px) |
| radius.full | `--ds-radius-full` | 9999px |
| shadow.sm | `--ds-shadow-sm` | `0 1px 2px rgba(0,0,0,0.05)` |
| shadow.md | `--ds-shadow-md` | `0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)` |
| shadow.lg | `--ds-shadow-lg` | `0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1)` |
| shadow.xl | `--ds-shadow-xl` | `0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)` |

### 4.4 Responsive Breakpoints

Mobile-first. Container gutter: `space.4` on < md, `space.6` on ≥ md.

| Name | Token | Min-width | Container max | Behavior |
|---|---|---|---|---|
| sm | `--ds-bp-sm` | 640px | 640px | Single-column forms collapse to stack |
| md | `--ds-bp-md` | 768px | 720px | Two-column forms, navbar condenses |
| lg | `--ds-bp-lg` | 1024px | 960px | Grids unlock 2–3 columns |
| xl | `--ds-bp-xl` | 1280px | 1140px | 3–4 column grids |
| 2xl | `--ds-bp-2xl` | 1536px | 1320px | Max content width |

Implementation contract:

```css
.ds-container { width: 100%; max-width: 1200px; margin-inline: auto; padding-inline: var(--ds-space-6); }
@media (max-width: 767.98px) { .ds-container { padding-inline: var(--ds-space-4); } }
```

Agents generate responsive rules from these breakpoints only — do not invent breakpoints.

---

<!-- @section: components -->

## 5. Component API Specification

Conventions shared by all components:
- Class naming: **BEM** — `ds-<component>`, modifier `--<modifier>`, element `__<element>`.
- All colors/padding/fonts MUST reference component tokens (Tier 3), never raw hex.
- Focus visibility: `:focus-visible` shows the focus ring; `:focus` alone does not (see Accessibility).
- Every interactive element ships an accessible name: visible text, `aria-label`, or `aria-labelledby`.

### 5.1 Button

Root class: `ds-btn`. Modifiers: `--primary`, `--secondary`, `--outline`, `--ghost`, `--danger`, `--success`, `--sm`, `--md`, `--lg`, `--pill`, `--icon`, `--full`.

#### Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `variant` | `'primary' \| 'secondary' \| 'outline' \| 'ghost' \| 'danger' \| 'success'` | `'primary'` | Visual style; maps to a modifier + token set |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Density; maps to padding/font tokens |
| `type` | `'button' \| 'submit' \| 'reset'` | `'button'` | Native button type |
| `disabled` | `boolean` | `false` | Disables interaction; sets `:disabled` styles |
| `loading` | `boolean` | `false` | Shows spinner, prevents clicks, sets `aria-busy="true"` |
| `fullWidth` | `boolean` | `false` | `width: 100%` |
| `leftIcon` | `ReactNode` | — | Icon before label; gets `aria-hidden="true"` |
| `rightIcon` | `ReactNode` | — | Icon after label; gets `aria-hidden="true"` |
| `ariaLabel` | `string` | — | Accessible name when icon-only |
| `onClick` | `(e: MouseEvent) => void` | — | Click handler |
| `as` | `'button' \| 'a'` | `'button'` | Render element; `a` for links |

#### States

| State | Trigger | Behavior |
|---|---|---|
| default | — | Token variant colors |
| hover | `:hover:not(:disabled)` | `*-hover-bg` swap; `transform: translateY(-1px)` on primary only |
| active | `:active:not(:disabled)` | `*-active-bg`; `transform: translateY(0)` |
| focus | `:focus-visible` | `outline: 2px solid var(--ds-focus-ring-color); outline-offset: 2px` (or `ring.focus`) |
| disabled | `:disabled` | `opacity: var(--ds-button-disabled-opacity)`, `cursor: not-allowed`, no hover/active |
| loading | `aria-busy="true"` | Replace label with spinner; keep width to prevent layout shift |

#### Variants

| Variant | bg | text | border | hover bg | hover text |
|---|---|---|---|---|---|
| primary | `button.primary-bg` | `button.primary-text` | transparent | `button.primary-hover-bg` | `button.primary-text` |
| secondary | `button.secondary-bg` | `button.secondary-text` | `button.secondary-border` | `button.secondary-hover-bg` | `button.secondary-text` |
| outline | transparent | `color.primary` | `color.primary` | `color.primary-subtle` | `color.primary` |
| ghost | transparent | `button.ghost-text` | transparent | `button.ghost-hover-bg` | `button.ghost-hover-text` |
| danger | `button.danger-bg` | `button.danger-text` | transparent | `button.danger-hover-bg` | `button.danger-text` |
| success | `color.green.700` | `text.inverse` | transparent | `color.green.800` | `text.inverse` |

#### Sizes

| Size | Padding | Font size | Radius | Min-height |
|---|---|---|---|---|
| sm | `space.1` `space.3` (4px 12px) | `text.sm` 0.75rem | `radius.sm` | 32px |
| md | `space.2` `space.4` (8px 16px) | `text.sm` 0.875rem | `radius.md` | 40px |
| lg | `space.3` `space.6` (12px 24px) | `text.base` 1rem | `radius.lg` | 48px |

Touch-target rule: never render an interactive Button below 32×32px effective hit area.

### 5.2 Input

Root class: `ds-input`. Form group: `ds-input-group` (label + control + helper/error). Textarea: `.ds-input` + `.ds-textarea`.

#### Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `type` | `'text' \| 'email' \| 'password' \| 'number' \| 'search' \| 'tel' \| 'url' \| 'date'` | `'text'` | Native input type |
| `value` / `defaultValue` | `string` | — | Controlled / uncontrolled value |
| `name` | `string` | — | Form field name |
| `placeholder` | `string` | — | Example text (`input.placeholder`) |
| `label` | `string` | — | Visible label (rendered as `.ds-label`) |
| `id` | `string` | auto | Links label via `for`/`htmlFor` |
| `disabled` | `boolean` | `false` | `input.disabled-*` styles; removed from tab order |
| `readOnly` | `boolean` | `false` | Non-editable but focusable |
| `required` | `boolean` | `false` | Adds `required` + `aria-required="true"` |
| `invalid` | `boolean` | `false` | Applies error border + `aria-invalid="true"` |
| `errorText` | `string` | — | `.ds-error-text` below; `aria-describedby` wired |
| `helperText` | `string` | — | `.ds-helper-text` below |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Padding/font density |
| `leadingIcon` / `trailingIcon` | `ReactNode` | — | Icon slot; `aria-hidden="true"` |
| `onChange` / `onFocus` / `onBlur` | `fn` | — | Handlers |

#### States

| State | Trigger | Behavior |
|---|---|---|
| default | — | `input.bg`, `input.border`, `input.text` |
| hover | `:hover:not(:disabled)` | `border.default → border.strong` |
| focus | `:focus` | `input.focus-border` + `input.focus-ring`; `outline: none` |
| disabled | `:disabled` | `input.disabled-bg`, `input.disabled-text`, `cursor: not-allowed` |
| readonly | `:read-only` | default border, no focus ring emphasis |
| error | `[aria-invalid="true"]` | `input.error-border`; on focus `input.error-ring` |
| filled | `:not(:placeholder-shown)` | no visual change (JS reads value) |

#### Variants & Sizes

| Variant | Style |
|---|---|
| outlined (default) | `1px solid input.border`, `radius.md`, `bg surface` |
| filled | `border-color: transparent`, `bg.surface-hover` |

| Size | Padding | Font size | Radius |
|---|---|---|---|
| sm | `space.1` `space.3` | `text.sm` 0.875rem | `radius.sm` |
| md | `space.2` `space.3` (8px 12px) | `text.base` 0.9375rem | `radius.md` |
| lg | `space.3` `space.4` (12px 16px) | `text.base` 1rem | `radius.md` |

### 5.3 Card

Root class: `ds-card`. Elements: `__header`, `__body`, `__footer`, `__title`, `__media`. Modifiers: `--elevated`, `--interactive`, `--flat`, `--padding-*`.

#### Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `as` | `'div' \| 'article' \| 'section'` | `'div'` | Semantic element |
| `variant` | `'default' \| 'elevated' \| 'outlined' \| 'flat'` | `'default'` | Border + shadow treatment |
| `padding` | `'none' \| 'sm' \| 'md' \| 'lg' \| 'xl'` | `'lg'` (`space.6`) | Internal inset |
| `interactive` | `boolean` | `false` | Adds `tabindex="0"`, hover shadow, focus ring, `role="button"` |
| `onClick` | `fn` | — | Only valid when `interactive` |
| `header` / `footer` | `ReactNode` | — | Slot content |
| `title` | `string` | — | Renders `__title`; h3 by default |

#### States

| State | Trigger | Behavior |
|---|---|---|
| default | — | `card.bg`, `card.border`, `radius.lg`, padding token |
| hover | `.ds-card:hover` (always) | `card.shadow-hover` (default variant) |
| hover (interactive) | `:hover` / `:focus-visible` | Lift: `card.shadow-hover` + `transform: translateY(-2px)`; `card.focus-ring` on focus |
| active (interactive) | `:active` | `transform: translateY(0)` |
| disabled (interactive) | `aria-disabled="true"` | `opacity: 0.5`, no lift |

#### Variants

| Variant | bg | border | shadow |
|---|---|---|---|
| default | `card.bg` | `card.border` | none → `card.shadow-hover` on hover |
| elevated | `card.bg` | transparent | `card.shadow-elevated` |
| outlined | `card.bg` | `border.strong` | none |
| flat | `bg.surface-hover` | transparent | none |

### 5.4 Badge

Root class: `ds-badge`. Modifiers: `--default`, `--success`, `--warning`, `--danger`, `--info`, `--primary`, `--sm`, `--md`, `--dot`.

#### Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `variant` | `'default' \| 'success' \| 'warning' \| 'danger' \| 'info' \| 'primary'` | `'default'` | Color mapping |
| `size` | `'sm' \| 'md'` | `'md'` | Padding + font |
| `dot` | `boolean` | `false` | Prepend 6px status dot (non-text indication of state) |
| `removable` | `boolean` | `false` | Render `×` button; `aria-label="Remove {label}"` |
| `onRemove` | `fn` | — | Fires on remove; only when `removable` |
| `children` | `ReactNode` | — | Badge content (text or icon) |

#### States

| State | Trigger | Behavior |
|---|---|---|
| default | — | Variant bg/text tokens, `radius.full` |
| hover | `:hover` | Darken bg one step (`gray.100 → gray.200`, `blue.100 → blue.200`, etc.) |
| focus (removable) | `:focus-visible` | Standard focus ring on the remove button |
| removed | unmount | `onRemove` fires; parent controls visibility |

#### Sizes

| Size | Padding | Font size | Weight |
|---|---|---|---|
| sm | 2px 8px | `text.xs` 0.75rem | 600 |
| md | 2px 10px | `text.xs` 0.75rem | 600 |

Badges are non-interactive by default; they are NOT in the tab order unless `removable` or given a role.

### 5.5 Alert

Root class: `ds-alert`. Elements: `__icon`, `__body`, `__title`, `__desc`. Modifiers: `--info`, `--success`, `--warning`, `--danger`, `--dismissible`.

#### Props

| Prop | Type | Default | Description |
|---|---|---|---|
| `variant` | `'info' \| 'success' \| 'warning' \| 'danger'` | `'info'` | Color mapping |
| `title` | `string` | — | Bold title (`__title`) |
| `children` | `ReactNode` | — | Description content (`__desc`) |
| `dismissible` | `boolean` | `false` | Render close button |
| `onDismiss` | `fn` | — | Fires on close; parent controls unmount |
| `role` | `'alert' \| 'status' \| 'none'` | by variant | `danger` → `role="alert"`, `info/success/warning` → `role="status"` |
| `showIcon` | `boolean` | `true` | Toggle leading icon |

#### States

| State | Trigger | Behavior |
|---|---|---|
| default | — | Variant bg/border/text tokens; 4px left accent border |
| focus (dismissible) | `:focus-visible` on close button | Standard focus ring |
| dismissed | close clicked | `onDismiss` fires; animate `max-height → 0` then unmount |

#### Variants

| Variant | bg | left border | text | icon |
|---|---|---|---|---|
| info | `alert.info-bg` | `alert.info-border` | `alert.info-text` | ℹ |
| success | `alert.success-bg` | `alert.success-border` | `alert.success-text` | ✓ |
| warning | `alert.warning-bg` | `alert.warning-border` | `alert.warning-text` | ⚠ |
| danger | `alert.danger-bg` | `alert.danger-border` | `alert.danger-text` | ✕ |

Layout: `display: flex; gap: space.3; padding: space.4; border-left: 4px solid`. Title: `text.sm`, weight 700. Description: `text.sm`, `text.secondary`-equivalent (alert text token).

---

<!-- @section: accessibility -->

## 6. Accessibility Requirements

### 6.1 WCAG Conformance

- **Minimum:** WCAG 2.1 AA for all interactive elements and readable text.
- **Target:** AAA for body text on surface (already met: 17:1).
- Contrast matrix in §2.5 is normative — any generated pairing must satisfy it.

### 6.2 Focus Indicators

| Rule | Value |
|---|---|
| Indicator | `2px` solid `focus.ring-color` (`blue.500` light / `blue.400` dark) |
| Offset | `2px` from the element edge |
| Implementation | `outline: 2px solid var(--ds-focus-ring-color); outline-offset: 2px;` OR `box-shadow: var(--ds-ring-focus)` (box-shadow variant must be full 3px spread) |
| Trigger | `:focus-visible` only — mouse clicks must NOT show the ring |
| Never | Remove the focus outline without providing an equivalent visible indicator |
| Interactive cards | Same ring on the whole card |

### 6.3 Screen Reader Contract

- **Icon-only buttons:** `aria-label` required; inner icon `aria-hidden="true"` (`focusable="false"` for SVG).
- **Buttons with icon + text:** icon `aria-hidden="true"`; the visible text is the accessible name.
- **Inputs:** `label` via `<label for>`; `errorText`/`helperText` referenced with `aria-describedby`; error state sets `aria-invalid="true"`.
- **Alerts:** `role="alert"` (danger) announces immediately; `role="status"` (info/success/warning) announces politely; dismissible alert close button has `aria-label="Close alert"`.
- **Badges:** decorative by default (`aria-hidden` acceptable when redundant to adjacent text); removable badge remove button has `aria-label="Remove {label}"`.
- **Loading buttons:** `aria-busy="true"` and disable pointer events.
- **Modal (reference):** focus trap, `role="dialog"` + `aria-modal="true"`, `aria-labelledby` → title id.

### 6.4 Keyboard Navigation

| Element | Behavior |
|---|---|
| Tab order | Matches DOM order; no `tabindex > 0` |
| Button / Badge-remove | `Enter`/`Space` activates (native) |
| Input | Standard: text entry, `Tab` in/out, `Esc` clears search type |
| Interactive Card | `tabindex="0"`, `Enter`/`Space` activates, `role="button"` |
| Modal | `Esc` closes; focus moves to dialog on open, returns to trigger on close |
| Skip link | Optional but recommended: `.ds-skip-link` jumps to `#main` |

### 6.5 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

Component rules under reduced motion:
- Hover lifts and card `translateY` are removed (color change only).
- Modal fade/scale animations become instant (opacity toggles).
- Skeleton shimmer must be disabled (static gradient).
- Any element whose motion conveys state (spinners) may keep a slow, subtle animation — confirm it is non-essential.

### 6.6 Additional Requirements

- **Color-only indicators:** never communicate state with color alone — pair with icon, text, or pattern (badge `dot` + label, alert icon + text).
- **Target size:** interactive targets ≥ 44×44px (WCAG 2.2 SC 2.5.8) for pointer; keyboard targets ≥ 32×32px minimum.
- **Text resizing:** all type is `rem`-based so browser zoom and 200% text scaling do not clip; fluid type caps at `max` to avoid overflow.
- **Contrast on disabled:** disabled text (`text.disabled`) is exempt from contrast requirements but MUST remain distinguishable from the background.

---

<!-- @section: tokens -->

## 7. Machine-Readable Token Export (JSON)

This block is normative. An agent may consume it directly instead of parsing the tables above. All tokens are emitted with a canonical `ds.*` key, their resolved value, tier, and dark-mode override.

```json
{
  "meta": {
    "protocol": "google-labs-design-md",
    "namespace": "ds",
    "cssPrefix": "--ds",
    "version": "1.0.0",
    "generatorTarget": "AI agent UI component generation"
  },
  "tokens": {
    "color.gray.50":    { "value": "#F8FAFC", "type": "color", "tier": "primitive", "dark": "#F8FAFC", "usage": "surface tint" },
    "color.gray.100":   { "value": "#F1F5F9", "type": "color", "tier": "primitive", "dark": "#F1F5F9", "usage": "hover bg" },
    "color.gray.200":   { "value": "#E2E8F0", "type": "color", "tier": "primitive", "dark": "#E2E8F0", "usage": "border" },
    "color.gray.300":   { "value": "#CBD5E1", "type": "color", "tier": "primitive", "dark": "#CBD5E1", "usage": "strong border" },
    "color.gray.400":   { "value": "#94A3B8", "type": "color", "tier": "primitive", "dark": "#94A3B8", "usage": "tertiary/disabled text" },
    "color.gray.500":   { "value": "#64748B", "type": "color", "tier": "primitive", "dark": "#64748B", "usage": "secondary text" },
    "color.gray.600":   { "value": "#475569", "type": "color", "tier": "primitive", "dark": "#475569", "usage": "secondary icon" },
    "color.gray.700":   { "value": "#334155", "type": "color", "tier": "primitive", "dark": "#334155", "usage": "emphasis on tint" },
    "color.gray.800":   { "value": "#1E293B", "type": "color", "tier": "primitive", "dark": "#1E293B", "usage": "tooltip/dark surface" },
    "color.gray.900":   { "value": "#0F172A", "type": "color", "tier": "primitive", "dark": "#0F172A", "usage": "primary text light" },
    "color.gray.950":   { "value": "#020617", "type": "color", "tier": "primitive", "dark": "#020617", "usage": "dark canvas" },
    "color.white":      { "value": "#FFFFFF", "type": "color", "tier": "primitive", "dark": "#FFFFFF", "usage": "surface/inverse" },
    "color.blue.50":    { "value": "#EFF6FF", "type": "color", "tier": "primitive", "dark": "#EFF6FF", "usage": "info alert bg" },
    "color.blue.100":   { "value": "#DBEAFE", "type": "color", "tier": "primitive", "dark": "#DBEAFE", "usage": "info badge bg" },
    "color.blue.500":   { "value": "#3B82F6", "type": "color", "tier": "primitive", "dark": "#3B82F6", "usage": "primary dark/focus" },
    "color.blue.600":   { "value": "#2563EB", "type": "color", "tier": "primitive", "dark": "#2563EB", "usage": "primary light" },
    "color.blue.700":   { "value": "#1D4ED8", "type": "color", "tier": "primitive", "dark": "#1D4ED8", "usage": "primary hover" },
    "color.blue.800":   { "value": "#1E40AF", "type": "color", "tier": "primitive", "dark": "#1E40AF", "usage": "primary active/info text" },
    "color.green.100":  { "value": "#DCFCE7", "type": "color", "tier": "primitive", "dark": "#DCFCE7", "usage": "success badge bg" },
    "color.green.700":  { "value": "#15803D", "type": "color", "tier": "primitive", "dark": "#15803D", "usage": "success button" },
    "color.green.800":  { "value": "#166534", "type": "color", "tier": "primitive", "dark": "#166534", "usage": "success badge text" },
    "color.red.100":    { "value": "#FEE2E2", "type": "color", "tier": "primitive", "dark": "#FEE2E2", "usage": "danger badge bg" },
    "color.red.500":    { "value": "#EF4444", "type": "color", "tier": "primitive", "dark": "#EF4444", "usage": "danger accent/error border" },
    "color.red.600":    { "value": "#DC2626", "type": "color", "tier": "primitive", "dark": "#DC2626", "usage": "danger button light" },
    "color.red.700":    { "value": "#B91C1C", "type": "color", "tier": "primitive", "dark": "#B91C1C", "usage": "danger text/hover" },
    "color.yellow.50":  { "value": "#FEFCE8", "type": "color", "tier": "primitive", "dark": "#FEFCE8", "usage": "warning alert bg" },
    "color.yellow.700": { "value": "#A16207", "type": "color", "tier": "primitive", "dark": "#A16207", "usage": "warning text" },
    "color.purple.500": { "value": "#8B5CF6", "type": "color", "tier": "primitive", "dark": "#8B5CF6", "usage": "purple accent" },

    "color.primary":        { "value": "color.blue.600", "type": "color", "tier": "semantic", "dark": "color.blue.500", "usage": "brand primary" },
    "color.primary-hover":  { "value": "color.blue.700", "type": "color", "tier": "semantic", "dark": "color.blue.400", "usage": "primary hover" },
    "color.primary-active": { "value": "color.blue.800", "type": "color", "tier": "semantic", "dark": "color.blue.600", "usage": "primary active" },
    "color.danger":         { "value": "color.red.600",  "type": "color", "tier": "semantic", "dark": "color.red.500",  "usage": "danger" },
    "color.danger-hover":   { "value": "color.red.700",  "type": "color", "tier": "semantic", "dark": "color.red.400",  "usage": "danger hover" },
    "color.success":        { "value": "color.green.700","type": "color", "tier": "semantic", "dark": "color.green.500","usage": "success" },
    "color.warning":        { "value": "color.yellow.600","type": "color", "tier": "semantic", "dark": "color.yellow.500","usage": "warning" },
    "bg.canvas":            { "value": "color.gray.50",  "type": "color", "tier": "semantic", "dark": "color.gray.950", "usage": "page bg" },
    "bg.surface":           { "value": "color.white",    "type": "color", "tier": "semantic", "dark": "color.gray.900", "usage": "component bg" },
    "bg.surface-hover":     { "value": "color.gray.100", "type": "color", "tier": "semantic", "dark": "color.gray.800", "usage": "hover fill" },
    "bg.elevated":          { "value": "color.white",    "type": "color", "tier": "semantic", "dark": "color.gray.800", "usage": "popovers/modal" },
    "bg.overlay":           { "value": "rgba(15,23,42,0.6)", "type": "color", "tier": "semantic", "dark": "rgba(2,6,23,0.7)", "usage": "modal scrim" },
    "text.primary":         { "value": "color.gray.900", "type": "color", "tier": "semantic", "dark": "color.gray.50",  "usage": "primary text" },
    "text.secondary":       { "value": "color.gray.500", "type": "color", "tier": "semantic", "dark": "color.gray.400", "usage": "secondary text" },
    "text.tertiary":        { "value": "color.gray.400", "type": "color", "tier": "semantic", "dark": "color.gray.500", "usage": "tertiary text" },
    "text.inverse":         { "value": "color.white",    "type": "color", "tier": "semantic", "dark": "color.gray.900", "usage": "text on brand" },
    "border.default":       { "value": "color.gray.200", "type": "color", "tier": "semantic", "dark": "color.gray.700", "usage": "default border" },
    "border.strong":        { "value": "color.gray.300", "type": "color", "tier": "semantic", "dark": "color.gray.600", "usage": "strong border" },
    "border.focus":         { "value": "color.blue.500", "type": "color", "tier": "semantic", "dark": "color.blue.400", "usage": "focus border" },
    "ring.focus":           { "value": "0 0 0 3px rgba(59,130,246,0.20)", "type": "shadow", "tier": "semantic", "dark": "0 0 0 3px rgba(96,165,250,0.25)", "usage": "focus ring" },
    "ring.error":           { "value": "0 0 0 3px rgba(239,68,68,0.20)", "type": "shadow", "tier": "semantic", "dark": "0 0 0 3px rgba(248,113,113,0.25)", "usage": "error ring" },

    "button.primary-bg":        { "value": "color.primary",      "type": "color", "tier": "component", "dark": "auto", "usage": "primary button bg" },
    "button.primary-text":       { "value": "text.inverse",       "type": "color", "tier": "component", "dark": "auto", "usage": "primary button text" },
    "button.primary-hover-bg":   { "value": "color.primary-hover","type": "color", "tier": "component", "dark": "auto", "usage": "primary button hover" },
    "button.primary-active-bg":  { "value": "color.primary-active","type": "color","tier": "component", "dark": "auto", "usage": "primary button active" },
    "button.secondary-bg":       { "value": "bg.surface",         "type": "color", "tier": "component", "dark": "auto", "usage": "secondary button bg" },
    "button.secondary-border":   { "value": "border.default",     "type": "color", "tier": "component", "dark": "auto", "usage": "secondary button border" },
    "button.danger-bg":          { "value": "color.danger",       "type": "color", "tier": "component", "dark": "auto", "usage": "danger button bg" },
    "button.danger-hover-bg":    { "value": "color.danger-hover", "type": "color", "tier": "component", "dark": "auto", "usage": "danger button hover" },
    "button.ghost-text":         { "value": "text.secondary",     "type": "color", "tier": "component", "dark": "auto", "usage": "ghost button text" },
    "button.ghost-hover-bg":     { "value": "bg.surface-hover",   "type": "color", "tier": "component", "dark": "auto", "usage": "ghost button hover" },
    "button.disabled-opacity":   { "value": "0.5",                "type": "opacity", "tier": "component", "dark": "auto", "usage": "disabled button" },
    "input.bg":                  { "value": "bg.surface",         "type": "color", "tier": "component", "dark": "auto", "usage": "input bg" },
    "input.border":              { "value": "border.default",     "type": "color", "tier": "component", "dark": "auto", "usage": "input border" },
    "input.focus-border":        { "value": "border.focus",       "type": "color", "tier": "component", "dark": "auto", "usage": "input focus border" },
    "input.error-border":        { "value": "color.danger",       "type": "color", "tier": "component", "dark": "auto", "usage": "input error border" },
    "input.placeholder":         { "value": "text.tertiary",      "type": "color", "tier": "component", "dark": "auto", "usage": "input placeholder" },
    "card.bg":                   { "value": "bg.surface",         "type": "color", "tier": "component", "dark": "auto", "usage": "card bg" },
    "card.border":               { "value": "border.default",     "type": "color", "tier": "component", "dark": "auto", "usage": "card border" },
    "card.shadow-hover":         { "value": "shadow.md",          "type": "shadow", "tier": "component", "dark": "auto", "usage": "card hover shadow" },
    "badge.default-bg":          { "value": "color.gray.100",     "type": "color", "tier": "component", "dark": "auto", "usage": "badge default bg" },
    "badge.success-bg":          { "value": "color.green.100",    "type": "color", "tier": "component", "dark": "auto", "usage": "badge success bg" },
    "badge.success-text":        { "value": "color.green.800",    "type": "color", "tier": "component", "dark": "auto", "usage": "badge success text" },
    "badge.danger-bg":           { "value": "color.red.100",      "type": "color", "tier": "component", "dark": "auto", "usage": "badge danger bg" },
    "badge.danger-text":         { "value": "color.red.700",      "type": "color", "tier": "component", "dark": "auto", "usage": "badge danger text" },
    "badge.info-bg":             { "value": "color.blue.100",     "type": "color", "tier": "component", "dark": "auto", "usage": "badge info bg" },
    "badge.info-text":           { "value": "color.blue.800",     "type": "color", "tier": "component", "dark": "auto", "usage": "badge info text" },
    "alert.info-bg":             { "value": "color.blue.50",      "type": "color", "tier": "component", "dark": "auto", "usage": "alert info bg" },
    "alert.info-border":         { "value": "color.blue.500",     "type": "color", "tier": "component", "dark": "auto", "usage": "alert info border" },
    "alert.danger-bg":           { "value": "color.red.50",       "type": "color", "tier": "component", "dark": "auto", "usage": "alert danger bg" },
    "alert.danger-border":       { "value": "color.red.500",      "type": "color", "tier": "component", "dark": "auto", "usage": "alert danger border" },
    "focus.ring-width":          { "value": "2px",                "type": "dimension", "tier": "component", "dark": "auto", "usage": "focus ring width" },
    "focus.ring-offset":         { "value": "2px",                "type": "dimension", "tier": "component", "dark": "auto", "usage": "focus ring offset" },

    "font.sans": { "value": "'Pretendard','Inter','Noto Sans KR',system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI','Apple SD Gothic Neo','Malgun Gothic',sans-serif", "type": "font-family", "tier": "primitive", "dark": "same" },
    "font.mono": { "value": "'JetBrains Mono','D2Coding','Fira Code',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace", "type": "font-family", "tier": "primitive", "dark": "same" },
    "text.xs":    { "value": "0.75rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.5" },
    "text.sm":    { "value": "0.875rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.5" },
    "text.base":  { "value": "1rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.6" },
    "text.lg":    { "value": "1.125rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.5" },
    "text.xl":    { "value": "1.25rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.4" },
    "text.2xl":   { "value": "1.5rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.3" },
    "text.3xl":   { "value": "1.875rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.25" },
    "text.4xl":   { "value": "2.25rem", "type": "font-size", "tier": "primitive", "dark": "same", "lineHeight": "1.2" },
    "text.fluid.h1": { "value": "clamp(1.75rem, 4vw, 2.5rem)", "type": "font-size", "tier": "primitive", "dark": "same" },
    "text.fluid.h2": { "value": "clamp(1.5rem, 3vw, 2rem)", "type": "font-size", "tier": "primitive", "dark": "same" },
    "text.fluid.h3": { "value": "clamp(1.25rem, 2vw, 1.5rem)", "type": "font-size", "tier": "primitive", "dark": "same" },

    "space.1": { "value": "0.25rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 4 },
    "space.2": { "value": "0.5rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 8 },
    "space.3": { "value": "0.75rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 12 },
    "space.4": { "value": "1rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 16 },
    "space.5": { "value": "1.25rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 20 },
    "space.6": { "value": "1.5rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 24 },
    "space.8": { "value": "2rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 32 },
    "space.10": { "value": "2.5rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 40 },
    "space.12": { "value": "3rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 48 },
    "space.16": { "value": "4rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 64 },
    "space.20": { "value": "5rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 80 },
    "space.24": { "value": "6rem", "type": "spacing", "tier": "primitive", "dark": "same", "px": 96 },

    "radius.sm": { "value": "0.25rem", "type": "radius", "tier": "primitive", "dark": "same" },
    "radius.md": { "value": "0.5rem", "type": "radius", "tier": "primitive", "dark": "same" },
    "radius.lg": { "value": "0.75rem", "type": "radius", "tier": "primitive", "dark": "same" },
    "radius.xl": { "value": "1rem", "type": "radius", "tier": "primitive", "dark": "same" },
    "radius.full": { "value": "9999px", "type": "radius", "tier": "primitive", "dark": "same" },

    "shadow.sm": { "value": "0 1px 2px rgba(0,0,0,0.05)", "type": "shadow", "tier": "primitive", "dark": "same" },
    "shadow.md": { "value": "0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)", "type": "shadow", "tier": "primitive", "dark": "same" },
    "shadow.lg": { "value": "0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1)", "type": "shadow", "tier": "primitive", "dark": "same" },
    "shadow.xl": { "value": "0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.1)", "type": "shadow", "tier": "primitive", "dark": "same" },

    "bp.sm":  { "value": "640px", "type": "breakpoint", "tier": "primitive", "dark": "same" },
    "bp.md":  { "value": "768px", "type": "breakpoint", "tier": "primitive", "dark": "same" },
    "bp.lg":  { "value": "1024px", "type": "breakpoint", "tier": "primitive", "dark": "same" },
    "bp.xl":  { "value": "1280px", "type": "breakpoint", "tier": "primitive", "dark": "same" },
    "bp.2xl": { "value": "1536px", "type": "breakpoint", "tier": "primitive", "dark": "same" }
  }
}
```

---

## 8. Generation Rules for AI Agents

When generating a component from this spec, an agent MUST:

1. **Resolve the token chain** — every emitted value is `T3 → T2 → T1` resolved; never emit a semantic reference where a computed value is required, and never emit a raw hex inside a component rule.
2. **Use only sanctioned scales** — spacing (§4.1), type (§3.2/3.3), radius/shadow (§4.3), breakpoints (§4.4).
3. **Emit BEM classes** — `ds-<component>` / `--<modifier>` / `__<element>`, matching §5.
4. **Implement every state** in §5 — default, hover, active, focus-visible, disabled, error/loading as applicable.
5. **Wire the accessibility contract** — focus ring on `:focus-visible`, `aria-label` for icon-only, `aria-describedby`/`aria-invalid` for form errors, `role` per §6.3.
6. **Add reduced-motion guards** — §6.5 block verbatim for any animated component.
7. **Verify contrast** — run each emitted text-on-bg pairing against §2.5; fail the build on AA violations for normal text.
8. **Dark mode** — remap the semantic tier under `[data-theme="dark"]`; component tokens propagate automatically.
9. **Name CSS variables** — `--ds-` + kebab-case of the `ds.*` token key (`ds.color.primary` → `--ds-color-primary`).
10. **Do not invent** — any prop, token, size, or state not present in this document is out of scope for a first pass; flag it for review instead.

---

## Appendix A — Reference: Existing Implementation

| Artifact | Path | Coverage |
|---|---|---|
| Component CSS | `C:\Users\hotti\projects\design-system\components.css` | Tokens, Button, Card, Badge, Input, Navbar, Alert, Table, Modal, Tooltip, Skeleton, Layout utils |
| Demo page | `C:\Users\hotti\projects\design-system\index.html` | Live preview of all components |
| README | `C:\Users\hotti\projects\design-system\README.md` | Quick-start + component list |

Known deltas between this spec and the existing CSS (to reconcile in a future cycle):

| Delta | Location | Resolution |
|---|---|---|
| Success button uses `green.600` + white text (3.3:1) | `components.css` `.ds-btn--success` | Switch to `green.700` (`color.success`) to meet AA |
| Secondary text is `gray.500` (AA 4.8:1) — already compliant | `components.css` `--ds-text-secondary` | Keep; matches spec |
| Focus ring uses `box-shadow` only | `components.css` `.ds-btn:focus-visible` | Spec standardizes `outline` + `outline-offset`; either accepted, but `outline` variant is preferred |
| Dark mode not yet implemented | `components.css` | Add `[data-theme="dark"]` semantic remap per §2.4 |
