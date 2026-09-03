---
name: BorderShield AI Screening Console
colors:
  surface: '#0b141c'
  surface-dim: '#0b141c'
  surface-bright: '#313a43'
  surface-container-lowest: '#060f16'
  surface-container-low: '#141c24'
  surface-container: '#182028'
  surface-container-high: '#222b33'
  surface-container-highest: '#2d363e'
  on-surface: '#dae3ee'
  on-surface-variant: '#c6c6ca'
  inverse-surface: '#dae3ee'
  inverse-on-surface: '#29313a'
  outline: '#909094'
  outline-variant: '#45474a'
  surface-tint: '#c7c6c9'
  primary: '#c7c6c9'
  on-primary: '#303033'
  primary-container: '#0b0c0e'
  on-primary-container: '#7a7a7c'
  inverse-primary: '#5e5e61'
  secondary: '#c2c7d0'
  on-secondary: '#2c3138'
  secondary-container: '#42474f'
  on-secondary-container: '#b1b5bf'
  tertiary: '#cec4c1'
  on-tertiary: '#352f2d'
  tertiary-container: '#0f0b09'
  on-tertiary-container: '#807975'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e3e2e5'
  primary-fixed-dim: '#c7c6c9'
  on-primary-fixed: '#1b1c1e'
  on-primary-fixed-variant: '#464749'
  secondary-fixed: '#dee2ec'
  secondary-fixed-dim: '#c2c7d0'
  on-secondary-fixed: '#171c23'
  on-secondary-fixed-variant: '#42474f'
  tertiary-fixed: '#ebe0dc'
  tertiary-fixed-dim: '#cec4c1'
  on-tertiary-fixed: '#1f1b18'
  on-tertiary-fixed-variant: '#4c4543'
  background: '#0b141c'
  on-background: '#dae3ee'
  surface-variant: '#2d363e'
typography:
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: IBM Plex Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.06em
  technical-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  status-pill:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  sidebar-width: 240px
  gutter: 16px
  margin-page: 24px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style
The design system for this product is rooted in an **Institutional Tech** aesthetic—a fusion of government-grade authority and high-performance computation. The interface prioritizes speed of cognition and absolute clarity over decorative flair.

The style is defined by **High-Density Minimalism**. It utilizes a structured, dark-mode foundation to reduce eye strain during extended operational shifts while maintaining a "mission-critical" atmosphere. Visual hierarchy is established through precise tonal shifts and semantic color application rather than depth or shadows. The emotional response is one of calm, disciplined control and technical reliability.

## Colors
The palette is engineered for professional screening environments. 

- **Foundation**: The background uses a deep Charcoal (`#0B0C0E`) to ground the interface. 
- **Surface**: The secondary Navy-Graphite (`#161B22`) defines containers and active workspaces, providing a subtle but clear distinction from the base.
- **Semantic Accents**: Colors are reserved strictly for operational status. Green signifies "Verified/Clear," Amber signifies "Review Required/Uncertainty," and Red signifies "High-Risk/Integrity Failure."
- **Borders**: Subtle Slate (`#30363D`) is used to define structural boundaries without creating visual noise.

## Typography
The typographic system utilizes a dual-font strategy to separate intent:

1.  **System Interface (IBM Plex Sans / Inter)**: Used for all primary navigation, headers, and descriptive text. It conveys a neutral, professional tone.
2.  **Technical Data (JetBrains Mono)**: Essential for MRZ (Machine Readable Zone) data, hashes, passport IDs, and coordinate data. The monospaced nature ensures character alignment for quick scanning of alphanumeric strings.

Use **Label-Caps** for section headers within sidebars or small utility descriptions to provide a distinct visual anchor.

## Layout & Spacing
The layout adheres to a **Strict Fixed-Fluid Grid**. 

- **Sidebar**: A fixed 240px sidebar on the left persists across all screens, housing primary navigation and high-level system health metrics.
- **Main Console**: Utilizes a 12-column grid with 16px gutters. In data-heavy screening views, utilize a "split-pane" layout where the left 8 columns display the primary subject data and the right 4 columns show the AI decision-log.
- **Density**: Spacing is disciplined. While the data is dense, use generous 24px outer margins to ensure the interface doesn't feel claustrophobic during high-stress operations.

## Elevation & Depth
This design system avoids traditional shadows to maintain a flat, high-performance look. Depth is conveyed exclusively through **Tonal Layering** and **Borders**:

- **Level 0 (Base)**: `#0B0C0E` — The primary background.
- **Level 1 (Surface)**: `#161B22` — Cards, containers, and data blocks.
- **Level 2 (Active/Hover)**: `#1C2128` — Subtle lightening of the surface to indicate interactivity.
- **Outlines**: Every container must have a 1px solid border of `#30363D`. This "ghost border" technique provides structure without the weight of a shadow.

## Shapes
The shape language is "Soft-Technical." Elements use a **0.25rem (4px) base radius** to appear modern and refined while remaining sharp enough to feel institutional. Large radiuses or pill shapes (except for specific status indicators) are discouraged to maintain a serious, military-spec appearance.

## Components

- **Buttons**: Primary buttons are high-contrast with white text on a subtle slate background. Secondary buttons use a transparent background with a `#30363D` border. High-risk actions (e.g., "Deny Entry") use a solid `#DA3633` fill.
- **Status Pills**: Compact containers with a 1px border matching the semantic color (Green/Amber/Red). Use a 10% opacity background fill of the semantic color to provide a "glow" effect that draws the eye without overwhelming the text.
- **Input Fields**: Dark backgrounds (`#0B0C0E`) with a 1px border. Focus states use a subtle blue-gray border, never a vibrant color unless it's a validation error.
- **Data Tables**: Zebra-striping is avoided. Use 1px horizontal dividers only. Header rows use `label-caps` typography with a slightly darker background than the body rows.
- **AI Confidence Meters**: Use thin horizontal bars rather than circular gauges to preserve vertical space and allow for easier comparison between multiple data points.
- **Cards**: Use for grouping subject information (Biometrics, Travel History). Each card must have a clear title in `headline-md`.