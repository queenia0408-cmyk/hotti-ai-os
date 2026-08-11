# Design System Component Library

Reusable CSS component library with design tokens, 10+ components, and responsive utilities.

## Quick Start

```html
<link rel="stylesheet" href="components.css">
<div class="ds">
  <button class="ds-btn ds-btn--primary">Click Me</button>
  <button class="ds-btn ds-btn--secondary ds-btn--lg">Large Secondary</button>
  <div class="ds-card">
    <div class="ds-card__header"><h3 class="ds-h3">Card Title</h3></div>
    <div class="ds-card__body">Card content here.</div>
    <div class="ds-card__footer">
      <button class="ds-btn ds-btn--primary">Save</button>
      <button class="ds-btn ds-btn--ghost">Cancel</button>
    </div>
  </div>
</div>
```

## Components

- **Buttons** — 5 variants (primary, secondary, danger, ghost, success), 3 sizes (sm, md, lg), pill variant
- **Cards** — Default + elevated, with header/body/footer slots
- **Badges** — 4 semantic variants (success, warning, danger, info)
- **Forms** — Inputs, textareas, labels, helper text, error states, form layouts
- **Navbar** — Brand + navigation links with active states
- **Alerts** — 4 variants (info, success, warning, danger) with icon + title + description
- **Tables** — Default + striped variants with hover states
- **Modals** — Overlay + animated dialog with header/body/footer
- **Tooltips** — Hover-activated, auto-positioning
- **Skeleton Loaders** — Shimmer animation, text/title/avatar/card variants
- **Layout Utilities** — Container, stack, row, grid (2/3/4 columns), divider

## Design Tokens

3-layer architecture: Primitives → Semantic → Component. 60+ CSS Custom Properties.

## Tech

CSS Custom Properties, BEM methodology, Fluid typography (clamp), CSS animations, Responsive (mobile-first)
