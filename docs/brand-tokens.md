# Brasaland Brand Tokens

## Purpose

This document is the single source of truth for Brasaland's visual identity. All brand color, typography, spacing, and tone decisions defined here are consumed by `@brasaland/public-website` (via an inline Tailwind CDN configuration) and `@brasaland/talent-pipeline-tracker` (via Tailwind v4 CSS-first `@theme` in `app/globals.css`). Changes to any token should be reflected across the brand-consuming workspaces.

---

## Color Palette

| Token | Hex | Tailwind name | Usage |
| --- | --- | --- | --- |
| Ember | `#C24A2B` | `brasaland-ember` | Primary brand color — CTAs, active states, key accents |
| Charcoal | `#1C1C1C` | `brasaland-charcoal` | Primary body text — near-black for readability without harshness |
| Cream | `#F5EFE6` | `brasaland-cream` | Warm section backgrounds — story, features, testimonials |
| Ivory | `#FAFAF8` | `brasaland-ivory` | Default page background — clean, warm off-white |
| Success | `#27AE60` | `brasaland-success` | Form success messages, confirmed states |
| Error | `#E74C3C` | `brasaland-error` | Form validation errors — brighter signal red, distinct from Ember |

### Rationale

Ember (`#C24A2B`) evokes live coals and the glow of an open grill — the core sensory experience of the brand. It sits in the warm-red spectrum without reading as a pure alarm red. Cream and Ivory keep the palette grounded in warmth rather than clinical white. Charcoal replaces pure black to soften contrast while maintaining accessibility.

---

## Typography

### Typefaces

| Role | Family | Style | Import weight |
| --- | --- | --- | --- |
| Display (headings) | Playfair Display | Serif — heritage, steakhouse elegance | 400, 600, 700, italic 400 |
| Body | Inter | Sans-serif — modern, highly legible | 400, 500, 600 |

### Google Fonts Import URL

```
https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@400;500;600&display=swap
```

Use two `<link rel="preconnect">` tags (`fonts.googleapis.com` and `fonts.gstatic.com`) before the stylesheet link for performance.

### Type Scale

| Level | Size | Usage |
| --- | --- | --- |
| h1 | 3rem (48px) | Hero headline |
| h2 | 2rem (32px) | Section headings |
| h3 | 1.5rem (24px) | Subsection or card headings |
| body | 1rem (16px) | Paragraph and UI text |
| small | 0.875rem (14px) | Captions, labels, legal copy |

---

## Spacing and Radius

| Context | Tailwind class | Value |
| --- | --- | --- |
| Small rounding (inputs, badges) | `rounded-sm` | 2px |
| Default rounding (cards, buttons) | `rounded-md` | 6px |
| Large rounding (panels, modals) | `rounded-lg` | 8px |
| Section vertical padding | `py-16` | 4rem (64px) |
| Section horizontal padding | `px-6 md:px-8` | 1.5rem / 2rem |
| Container max width | `max-w-6xl mx-auto` | 1152px centered |

---

## Tone of Voice

- **Warm and welcoming** — speak as a family-run restaurant that takes pride in hosting, not a corporate chain.
- **Heritage-aware** — the brand was born in Medellín in 2008; lean into Latin American culinary tradition without being nostalgic to the point of exclusion.
- **Quality-focused** — describe ingredients, technique, and sourcing with specificity. Avoid vague superlatives.
- **Professional without formality** — suitable for both a Colombian family deciding where to dine and a Miami professional looking for an after-work spot.
- **Bilingual-friendly** — copy should feel natural in both English and Spanish; avoid idioms that resist translation.

---

## Usage in M1 — `@brasaland/public-website`

Tokens are applied via an inline `tailwind.config` block immediately after the Tailwind CDN `<script>` tag in `index.html` and `application.html`:

```html
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          'brasaland-ember': '#C24A2B',
          'brasaland-charcoal': '#1C1C1C',
          'brasaland-cream': '#F5EFE6',
          'brasaland-ivory': '#FAFAF8',
          'brasaland-success': '#27AE60',
          'brasaland-error': '#E74C3C',
        },
        fontFamily: {
          display: ['"Playfair Display"', 'Georgia', 'serif'],
          sans: ['Inter', 'system-ui', 'sans-serif'],
        },
      },
    },
  };
</script>
```

This makes utilities such as `bg-brasaland-ember`, `text-brasaland-charcoal`, `font-display`, and `font-sans` available across all HTML pages without a build step.

---

## Usage in M3 — `@brasaland/talent-pipeline-tracker`

Imported via Tailwind v4's CSS-first config in `apps/talent-pipeline-tracker/app/globals.css`. Brand colors are declared as `--color-brasaland-*` custom properties inside a `@theme` block, which Tailwind v4 turns into utility classes (`bg-brasaland-ember`, `text-brasaland-charcoal`, etc.). Fonts are loaded via `next/font/google` in `app/layout.tsx`, exposed as CSS variables (`--font-inter`, `--font-playfair`), and bound to `--font-display` / `--font-sans` inside the same `@theme` block.

---

## Usage in M4 — `@brasaland/website` and `@brasaland/backoffice`

Both M4 workspaces use the same token system as M3, implemented identically via Tailwind v4's
CSS-first config in `uis/website/app/globals.css` and `uis/backoffice/app/globals.css`.

Brand colors are declared as `--color-brasaland-*` custom properties inside a `@theme` block.
Fonts are loaded via `next/font/google` in each workspace's `app/layout.tsx`, exposed as CSS
variables (`--font-inter`, `--font-playfair`), and bound to `--font-display` / `--font-sans`
inside the same `@theme` block.

`uis/backoffice` additionally imports business logic directly from
`@brasaland/operations-toolkit` — the M2 workspace — using npm workspace references. No token
values are redefined or overridden in the backoffice; the same 6-color palette and 2-typeface
system governs all four milestones.
