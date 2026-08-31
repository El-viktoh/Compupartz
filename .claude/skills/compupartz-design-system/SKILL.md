---
name: compupartz-design-system
description: The approved visual design system for the Compupartz website (a laptop repair business in Ghana) — a dark "glow-podium" aesthetic built on the site's existing brandBlue/brandOrange Tailwind tokens. Use this skill whenever building a new page, restyling an existing template, adding a hero/CTA/card-grid/promo section, or making any visual/UI change to this repo's Django templates (templates/*.html) — even if the user just says "make this page match the new design," "restyle X," "add a hero to Y," or doesn't mention "design system" by name. This is the house style for this codebase; consult it before inventing new colors, fonts, button shapes, or component patterns.
---

# Compupartz design system

This codifies the visual direction approved for the Compupartz home page redesign (built in a Claude Design mockup, dark "glow-podium" aesthetic recolored to the site's own brand). Apply it whenever you touch the visual layer of this repo — new pages, restyled sections, new components — so the site reads as one coherent product instead of a pile of one-off pages.

This is a **starting vocabulary, not a locked template**. Reuse the tokens and the underlying patterns (glow fields behind a focal image, pill CTAs with matching glow, eyebrow labels, dark elevated cards); don't just copy-paste the exact hero markup onto every page. A track-repair page and a product-detail page should both feel like Compupartz without looking identical.

## Before you start

The real tokens already live in code — read them, don't retype them from memory:
- [tailwind.config.js](../../tailwind.config.js) — `brandBlue`, `brandOrange`, animation keyframes
- [static/src/input.css](../../static/src/input.css) — custom scrollbar, `.reveal-element`, navbar-scroll CSS
- [templates/base.html](../../templates/base.html) — Google Fonts link (Inter + Outfit), dark-mode class-strategy toggle, existing navbar/footer chrome

If a value below ever disagrees with those files, the files win — this skill can drift, code doesn't.

## Brand tokens

| Token | Value | Use |
|---|---|---|
| `brandBlue` | `#008BC6` | Primary action color — the "repair" journey (Book a Repair, Track Status, service links) |
| `brandOrange` | `#FF7200` | Secondary/alternate action color — the "parts" journey (Request a Part), eyebrow labels, accent words in headlines |
| Dark background | `#0a0a0c` | Page background in dark mode — matches `base.html`'s `dark:bg-[#0a0a0c]` |
| Card surface | `#12141a` | Elevated surface on the dark background (cards, panels, floating widgets) |
| Heading text | `#ffffff` | On dark backgrounds |
| Body text | `#9a9aa3` | Paragraph copy on dark backgrounds |
| Muted/meta text | `#6b6a72` | Timestamps, subtitles, secondary captions |
| Secondary label | `#c7c7cf` | Badge labels, small supporting text that needs more presence than muted |

**These two dark-mode tokens are canonical — there must be exactly one hex value for "page background" and one for "card surface" across the whole site.** This codebase previously drifted into near-duplicate near-black variants for what was conceptually the same role — `#0a0b0e` alongside `#0a0a0c` for page background; `#161920`, `#111218`, `#0f1015`, `#1a1d24`, `#1a1b23` alongside `#12141a` for card surface — spread across `home.html`, `repair_home.html`, `book_repair.html`, `dashboard.html`, `base.html`, and `contact.html`. All of that was consolidated to the two values above. If you spot a new near-black hex in a template that isn't `#0a0a0c` or `#12141a`, that's drift, not a deliberate design choice — fold it into the matching canonical token rather than adding a third variant. (Deliberately *different* dark blues — e.g. `#005a8d`/`#006a99` used as gradient stops darkening `brandBlue` — are a different thing and are fine; the rule is about near-black surface colors converging to one value each, not about banning all dark colors.)

Fonts: **Outfit** (weights 600–900) for headings, **Inter** (weights 400–700) for body — both already loaded sitewide via the Google Fonts `<link>` in `base.html`. Don't add another font without a real reason; this pairing is the brand now.

Dark mode uses Tailwind's `class` strategy, already wired in `base.html`. This system was designed dark-first — if you need a light-mode equivalent for a section, invert surface/text tones but keep `brandBlue`/`brandOrange` constant; don't invent new accent hues to compensate.

## Component patterns

Each pattern below names the *why*, not just the CSS, so you can adapt it rather than clone it.

**Hero.** Dark background, a large soft `radial-gradient` glow field in `brandBlue` at low opacity (roughly 15–25%) positioned behind the page's focal image, plus optional faint concentric SVG ring accents for depth. The focal image (a product/device photo, or whatever the page's subject is) sits centered with `object-fit: contain` and a soft elliptical glow-shadow beneath it, like it's resting on an invisible podium. This only makes sense when there's a real focal image — don't force the glow-podium treatment onto a page that has no hero visual.

**Eyebrow label.** Small uppercase kicker above a heading: `11px`, `letter-spacing: 0.22em`, `font-weight: 700`, color `brandOrange`, often paired with a short horizontal rule. Use it to name the section's category ("Precision Repair Lab," "Our Capabilities") — not as generic decoration on every heading.

**Headline.** Outfit `800`, large (60–76px desktop, scale down responsibly on mobile), tight `line-height` (~1.04). One phrase gets emphasis — italic, and either a brighter tint of `brandBlue` or `brandOrange` — to give the eye a landing point. One emphasized phrase per headline; more than that and nothing stands out.

**Dual CTA.** Two pill-shaped buttons (`border-radius: 100px`) side by side, each with a soft box-shadow glow matching its own color (`brandBlue` → `0 0 30px rgba(0,139,198,0.4)`, `brandOrange` → `0 0 30px rgba(255,114,0,0.3)`). This pairing exists because Compupartz genuinely has two customer journeys — repair vs. parts-request — not because two buttons look balanced. Only reach for two primary pills when a page actually serves two distinct real actions; a single-purpose page (e.g. a checkout confirmation) gets one pill, not two for symmetry.

**Tertiary action.** A circular icon button (40px, `1px solid rgba(255,255,255,0.1)` border) paired with a two-line label: bold title + small muted subtitle underneath. Use for a real but lower-priority action next to the primary CTAs (e.g. "Track Status / Check repair progress").

**Trust badge row.** Small circular icon chips (34px, `1px solid rgba(0,139,198,0.35)` border) each paired with a short bold label, laid out horizontally with generous gap. Pull the actual claims from the page's real content (original parts, certified technicians, service area) — never invent a badge to fill space.

**Card grid.** Dark cards (`#12141a` background, `1px solid rgba(255,255,255,0.06)` border, `16px` radius), image fills the top at `aspect-ratio: 1/1` with `object-fit: cover`, `18px` padding below holding a bold title and a colored "Action →" link — `brandBlue` for repair/service actions, `brandOrange` for parts/request actions. This color split is load-bearing: it's how a user tells the two journeys apart at a glance across the whole site, so don't swap it per-page for variety.

**Promo band.** A large rounded panel (`24px` radius), subtle diagonal gradient dark background, one soft radial glow blob in a corner for atmosphere (usually the *other* brand color from whatever dominates the section, for contrast). Split into a copy column (eyebrow + headline-with-italic-accent + short paragraph + one pill CTA) and an image column (rounded photo, drop shadow). Good for a single focused pitch mid-page — don't chain more than one or two of these per page or they lose weight.

**Icons.** Always inline stroke-based SVG — `24px` viewBox, `1.5`–`2px` stroke, `currentColor`-style (`stroke="{color}"`, `fill="none"`). Never emoji in new component work, even though some existing templates (toasts, footer) still use emoji — that's legacy, not the pattern to extend. When a concept repeats (checkmark-circle for "verified/original," map-pin for "location/nationwide," etc.), reuse the exact SVG path already in `templates/home.html` rather than redrawing a slightly different version — small path drift between instances reads as sloppy at a glance even if no one can say exactly why.

**Parts are requested, not shopped.** There is deliberately no product grid, shop card, or cart pattern for parts in this system — the business wants parts handled through a request/quote flow (a "Request a Part" pill CTA + a promo band pitching "tell us what you need, we'll source it"), not a storefront. If a task asks you to add a parts *store* or product catalog, that's a scope change from what was approved — flag it rather than building it silently, since the repo already has dormant `store`/`parts`/`cart` Django apps behind `ENABLE_STORE=False` that a real storefront would need to reckon with.

## Content rules

- **Use real copy.** Pull actual service names, trust claims, and copy from the existing templates (`templates/home.html`, `templates/repair/*.html`, etc.) when extending this system to a new page. Never invent placeholder marketing copy ("Lorem ipsum," generic filler stats) — if a real fact is missing, leave a clearly bracketed placeholder like `[TURNAROUND TIME]` rather than fabricating one.
- **Navbar and footer are out of scope for now.** They stay exactly as implemented in `templates/base.html` unless a redesign of that shared chrome is separately requested — don't quietly restyle them while working on a page-level section.
- **Don't force the pattern.** Not every page needs a glow-podium hero, a dual CTA, or a promo band. Use the piece that fits what the page is actually for; a settings page or a plain form page might need none of this beyond the base tokens (colors, fonts, card surface).
