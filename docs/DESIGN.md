---
version: alpha
name: AI Intelligence Hub
description: A light, editorial product design system for an AI news digest and retrieval chat experience.
colors:
  background: "#f7f9fb"
  surface: "#f7f9fb"
  surface-bright: "#f7f9fb"
  surface-container-lowest: "#ffffff"
  surface-container-low: "#f2f4f6"
  surface-container: "#eceef0"
  surface-container-high: "#e6e8ea"
  surface-container-highest: "#e0e3e5"
  surface-variant: "#e0e3e5"
  surface-dim: "#d8dadc"
  on-background: "#191c1e"
  on-surface: "#191c1e"
  on-surface-variant: "#434655"
  inverse-surface: "#2d3133"
  inverse-on-surface: "#eff1f3"
  outline: "#737686"
  outline-variant: "#c3c6d7"
  border-subtle: "#e2e8f0"
  text-muted: "#475569"
  text-strong: "#0f172a"
  primary: "#004ac6"
  primary-container: "#2563eb"
  primary-fixed: "#dbe1ff"
  primary-fixed-dim: "#b4c5ff"
  on-primary: "#ffffff"
  on-primary-container: "#eeefff"
  on-primary-fixed: "#00174b"
  on-primary-fixed-variant: "#003ea8"
  inverse-primary: "#b4c5ff"
  secondary: "#505f76"
  secondary-container: "#d0e1fb"
  on-secondary: "#ffffff"
  on-secondary-container: "#54647a"
  secondary-fixed: "#d3e4fe"
  secondary-fixed-dim: "#b7c8e1"
  on-secondary-fixed: "#0b1c30"
  on-secondary-fixed-variant: "#38485d"
  tertiary: "#943700"
  tertiary-container: "#bc4800"
  on-tertiary: "#ffffff"
  on-tertiary-container: "#ffede6"
  tertiary-fixed: "#ffdbcd"
  tertiary-fixed-dim: "#ffb596"
  on-tertiary-fixed: "#360f00"
  on-tertiary-fixed-variant: "#7d2d00"
  research: "#2563eb"
  research-soft: "#eff6ff"
  news: "#059669"
  news-soft: "#ecfdf5"
  error: "#ba1a1a"
  error-soft: "#ffdad6"
  on-error: "#ffffff"
  on-error-container: "#93000a"
  danger: "#dc2626"
  danger-soft: "#fef2f2"
  white: "#ffffff"
typography:
  h1:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: 600
    lineHeight: 38px
    letterSpacing: -0.02em
  h2:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: 600
    lineHeight: 32px
    letterSpacing: -0.01em
  h3:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: 600
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: 400
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 400
    lineHeight: 20px
  button:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 500
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: 500
    lineHeight: 16px
    letterSpacing: 0.02em
  nav-link:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: 500
    lineHeight: 20px
    letterSpacing: -0.01em
  brand:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: 700
    lineHeight: 28px
rounded:
  sm: 2px
  DEFAULT: 2px
  lg: 4px
  xl: 8px
  pill: 12px
  full: 12px
  capsule-max: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 24px
  section-y: 96px
  section-y-lg: 128px
  container-max: 1280px
elevation:
  base: 0
  raised: 1
  sticky: 30
  navigation: 50
shadows:
  none: none
  subtle: "0px 1px 2px rgba(15, 23, 42, 0.06)"
  card: "0px 4px 6px rgba(0, 0, 0, 0.05)"
  focus-ring: "0px 0px 0px 2px rgba(0, 74, 198, 0.10)"
motion:
  duration-fast: 150
  duration-standard: 200
  duration-emphasis: 250
  easing-standard: ease
  easing-emphasis: ease-out
components:
  app-shell:
    backgroundColor: "{colors.background}"
    textColor: "{colors.on-surface}"
  navbar:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.text-strong}"
    borderColor: "{colors.border-subtle}"
    height: 64px
  nav-link:
    textColor: "{colors.text-muted}"
    typography: "{typography.nav-link}"
  nav-link-active:
    textColor: "{colors.research}"
    borderColor: "{colors.research}"
  hero-pill:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.on-secondary-container}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs}"
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.xl}"
    padding: "{spacing.md}"
    shadow: "{shadows.none}"
  button-primary-hover:
    backgroundColor: "{colors.primary-container}"
  button-secondary:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline-variant}"
    typography: "{typography.button}"
    rounded: "{rounded.xl}"
    padding: "{spacing.md}"
  button-icon:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.pill}"
    size: 40px
  filter-chip:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.text-muted}"
    borderColor: "{colors.border-subtle}"
    typography: "{typography.label-md}"
    rounded: "{rounded.xl}"
    padding: "{spacing.xs}"
  filter-chip-active:
    backgroundColor: "{colors.research}"
    textColor: "{colors.white}"
    borderColor: "{colors.research}"
  card-news:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.border-subtle}"
    rounded: "{rounded.DEFAULT}"
    padding: "{spacing.lg}"
    shadow: "{shadows.none}"
  card-auth:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline-variant}"
    rounded: "{rounded.xl}"
    padding: "{spacing.xl}"
    shadow: "{shadows.card}"
  card-chat-assistant:
    backgroundColor: "{colors.surface-container-low}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline-variant}"
    rounded: "{rounded.xl}"
    padding: "{spacing.md}"
    shadow: "{shadows.subtle}"
  card-chat-user:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.xl}"
    padding: "{spacing.md}"
    shadow: "{shadows.subtle}"
  input-field:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline-variant}"
    typography: "{typography.body-md}"
    rounded: "{rounded.xl}"
    padding: "{spacing.sm}"
    shadow: "{shadows.none}"
  input-chat:
    backgroundColor: "{colors.surface-container-lowest}"
    textColor: "{colors.on-surface}"
    borderColor: "{colors.outline-variant}"
    rounded: "{rounded.pill}"
    padding: "{spacing.sm}"
    shadow: "{shadows.subtle}"
  badge-news:
    backgroundColor: "{colors.news-soft}"
    textColor: "{colors.news}"
    typography: "{typography.label-md}"
  badge-research:
    backgroundColor: "{colors.research-soft}"
    textColor: "{colors.research}"
    typography: "{typography.label-md}"
  sidebar-rail:
    backgroundColor: "#f8fafc"
    borderColor: "{colors.border-subtle}"
  sidebar-rail-active:
    backgroundColor: "{colors.research-soft}"
    textColor: "{colors.research}"
    borderColor: "{colors.research}"
  destructive-button:
    backgroundColor: "{colors.danger-soft}"
    textColor: "{colors.danger}"
    rounded: "{rounded.xl}"
---

## Overview

This design system expresses a calm, professional AI product that sits between an editorial briefing and a productivity tool. The visual identity is light-first, structured, and information-dense without feeling cramped. It should feel credible for research and news consumption, but approachable enough for daily use.

The core personality is modern newsroom meets SaaS workspace. The interface relies on cool neutrals, cobalt-blue interaction cues, restrained borders, and disciplined typography rather than decorative effects. Visual confidence comes from clarity and alignment, not ornament.

## Colors

The palette is led by paper-like whites and pale technical grays, with blue reserved for intent and interaction.

- **Background and surfaces:** The main canvas stays in a very light blue-gray range so the product feels fresh and digital rather than warm or print-like.
- **Primary blue:** Use the deep cobalt `primary` for calls to action, login states, send actions, active navigation, and key emphasis.
- **Supportive blue:** Use `primary-container`, `research`, and `secondary-container` for softer emphasis, selected pills, and information framing.
- **Editorial semantics:** Research content reads blue, while news content reads green. These are the only recurring category accents and should stay consistent across labels, chips, and source treatments.
- **Neutrals:** Text and borders should remain cool and slate-based. The product depends on gray hierarchy to preserve its measured, analytical tone.
- **Error and destructive states:** Use red sparingly and only for true failure, error copy, or destructive actions like clearing chat history.

The design is overwhelmingly light. Dark mode tokens may exist in other experiments, but the current product identity is the bright, white-surface presentation described here.

## Typography

Typography uses **Inter** exclusively. The system depends on weight, spacing, and scale rather than font pairing.

- **Headlines:** Semi-bold, compact, and slightly tightened. Headings should feel sharp and product-focused, not editorially dramatic.
- **Body text:** Small-to-medium sizes dominate. This is intentional: the product is optimized for summary reading, scanning metadata, and chat dialogue.
- **Labels and metadata:** Small label styles use mild positive tracking and medium weight. They should feel informational and structured, especially for content type, timestamps, and compact navigation cues.
- **Buttons and nav:** Interactive text should remain crisp and medium-weight, never oversized or overly rounded in tone.

Avoid expressive display typography, serif accents, or playful weight jumps. The interface should always read as precise and current.

## Layout

The layout model is fixed-max-width on desktop with generous horizontal breathing room and a practical mobile collapse. Pages are centered inside a wide content frame, with the largest sections stretching to a comfortable dashboard width rather than a narrow article column.

- **Container width:** Major screens should feel anchored around a broad desktop frame rather than full-bleed edge-to-edge content.
- **Rhythm:** Spacing follows a 4px base with visible use of 8px, 12px, 16px, 24px, and 32px increments.
- **Sections:** Hero and page-level sections use large vertical spacing to create calm pacing before the denser card and feed areas begin.
- **Grids:** News and feature collections should snap into tidy multi-column grids with consistent gutters and equal card padding.
- **Rails and sidebars:** Secondary navigation uses a narrow utility rail with icon-led grouping and clear active markers.

This system should always feel organized and slightly roomy, even when the content is dense.

## Elevation & Depth

Depth is intentionally restrained. Most hierarchy is created through tonal separation and borders rather than dramatic shadow stacks.

- **Primary method:** White cards on a light gray-blue canvas create most of the interface layering.
- **Borders first:** Thin cool-gray borders do more work than shadows across navigation, cards, filters, and inputs.
- **Shadows:** Use shadows only where a small lift improves readability, such as the auth card or chat bubbles. Shadows should be soft, short, and low-opacity.
- **Sticky UI:** The top navigation may remain fixed and feel stable, but it should still read as flat infrastructure rather than a floating glass panel.

If a choice exists between adding more shadow or improving tonal contrast, prefer tonal contrast.

## Shapes

The shape language is crisp with a controlled amount of softness.

- **Default geometry:** Most cards and panels are nearly square with only slight rounding.
- **Interactive controls:** Buttons and inputs move slightly softer, typically into 8px radii.
- **Pills and chat composer:** Compact pill forms use a 12px capsule radius rather than a perfect 9999px circle. They should read as softened utilities, not bubbly candy shapes.
- **No excessive curvature:** The UI should not feel bubbly, cute, or consumer-social. Corners are softened just enough to feel contemporary.

## Components

### Buttons

Primary buttons are saturated blue with white text and minimal decoration. Secondary buttons are white or pale neutral with a border. Hover states should feel like a tonal nudge, not a dramatic transform.

### Navigation

Top navigation is white, slim, and persistent. Active states are communicated with blue text and a bottom border. The left utility rail uses a similar active blue, but its selected item can carry a pale blue background fill for stronger wayfinding.

### Cards

News, digest, and supporting content cards are flat white rectangles with subtle borders and generous internal padding. The lead digest card may become larger and more editorial, but it should still remain within the same visual family rather than turning into a hero banner.

### Forms

Authentication and newsletter inputs are clean white fields with thin borders, medium padding, and blue focus feedback. The chat composer is the most distinctive input treatment: a pill-shaped field with an embedded send button and compact tool affordances.

### Chat

Assistant messages sit on pale neutral containers with a border. User messages invert into solid primary blue. This contrast is one of the strongest visual distinctions in the product and should remain stable.

### Content Labels

Category labels are uppercase, compact, and color-coded: blue for research, green for news. They should remain lightweight and editorial rather than becoming chunky badges.

## Do's and Don'ts

- Do keep the interface light, cool-toned, and highly legible.
- Do use blue as the dominant interaction color across navigation, buttons, and selected states.
- Do preserve the distinction between research blue and news green.
- Do favor borders, whitespace, and alignment over decorative depth.
- Do keep type scales compact enough for dashboard and feed reading.
- Don't introduce warm background tints, gradient-heavy branding, or glassmorphism.
- Don't over-round cards or enlarge controls until the product feels playful.
- Don't use multiple accent colors on the same screen without a semantic reason.
- Don't rely on shadow-heavy depth to create hierarchy.
