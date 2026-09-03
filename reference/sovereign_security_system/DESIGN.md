---
name: BorderShield AI
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#45474c'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#75777c'
  outline-variant: '#c4c6cf'
  surface-tint: '#565f6f'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131c2a'
  on-primary-container: '#7b8495'
  inverse-primary: '#bec7d9'
  secondary: '#4f5f78'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fe'
  on-secondary-container: '#53637d'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#261a00'
  on-tertiary-container: '#a87d00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae3f6'
  primary-fixed-dim: '#bec7d9'
  on-primary-fixed: '#131c2a'
  on-primary-fixed-variant: '#3e4756'
  secondary-fixed: '#d4e3ff'
  secondary-fixed-dim: '#b7c7e4'
  on-secondary-fixed: '#0a1c32'
  on-secondary-fixed-variant: '#38485f'
  tertiary-fixed: '#ffdfa0'
  tertiary-fixed-dim: '#fbbc01'
  on-tertiary-fixed: '#261a00'
  on-tertiary-fixed-variant: '#5c4300'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
  success-pulse: '#003366'
  error-alert: '#ba1a1a'
  blueprint-grid: rgba(196, 198, 207, 0.15)
typography:
  display-lg:
    fontFamily: Bricolage Grotesque
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Bricolage Grotesque
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Bricolage Grotesque
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Hanken Grotesk
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Hanken Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  technical-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Hanken Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 48px
  gutter: 24px
  rail-width: 72px
  sidebar-expanded: 260px
  container-max: 1440px
---

## Brand & Style
BorderShield AI is a high-stakes, institutional-grade security platform. The brand personality is authoritative, precise, and uncompromising, designed for intelligence and law enforcement agencies. 

The visual style is **Industrial Brutalism** mixed with **Modern Corporate** reliability. It utilizes sharp grid lines, blueprints, and monospaced technical metadata to evoke a sense of structural integrity and data transparency. The UI prioritizes information density and "evidence-first" clarity over decorative fluff. It feels like a digital tactical command center: clean, cold, and hyper-functional.

## Colors
The palette is dominated by "Deep Space Navy" (Primary) and "Tactical Grey" (Neutral). The background uses a clinical off-white to reduce eye strain during long surveillance sessions. 

- **Primary:** Used for high-contrast text, primary actions, and structural accents like active navigation indicators.
- **Secondary:** Used for auxiliary information and "synthetic" or sandbox environments.
- **Tertiary (Amber):** Reserved for warning states, risk matrices, and high-importance cryptographic status.
- **Surface Tiers:** Uses a subtle progression of greys (`#f8f9fa` to `#e1e3e4`) to create logical grouping without relying on heavy shadows.

## Typography
The system uses a tri-font approach to categorize information types:
1. **Bricolage Grotesque:** Large, impactful, and slightly idiosyncratic. Used for primary headings and hero titles to establish the brand's unique institutional voice.
2. **Hanken Grotesk:** A clean, modern sans-serif for standard body copy and functional labels.
3. **JetBrains Mono:** Used for all "System Data" and status indicators. This monospaced font signals to the user that the information is being pulled directly from the "engine" or "audit trail."

**Note:** Headings should frequently use `uppercase` and tight `letter-spacing` to mimic official documentation.

## Layout & Spacing
The layout follows a **Hybrid Sidebar-Rail** model. On desktop, a persistent navigation drawer provides quick access to high-level modules. The content area utilizes a **12-column fixed grid** with a max-width of 1440px.

- **Vertical Rhythm:** Strict 8px increments. 
- **Hero Section:** Features a blueprint grid background (`24px` square size) to emphasize the "architectural" nature of the screening process.
- **Adaptive Behavior:** 
  - **Desktop:** Sidebar expanded (260px).
  - **Tablet:** Sidebar collapses to a Mini-Rail (72px).
  - **Mobile:** Sidebar hidden; top navigation bar becomes the primary anchor with a hamburger menu trigger.

## Elevation & Depth
This system eschews traditional soft shadows for **Bold Outlines** and **Tonal Layering**. 

Depth is communicated through:
1. **Borders:** 1px solid lines using `outline-variant` define every container.
2. **Surface Insets:** Interactive elements use `surface-container` (a darker grey) to appear "pressed" into the page.
3. **Accent Borders:** Use a 4px left-border of `primary` color to denote active states or "Stage" indicators.
4. **Blueprint Overlays:** The hero section uses a low-opacity grid overlay to create a background layer that feels structural rather than atmospheric.

## Shapes
Shapes are predominantly **Sharp and Technical**. 
- **Default:** 2px (`0.125rem`) for a precise, machine-cut look on buttons and cards.
- **Large Components:** 4px or 8px for containers that need to feel slightly more substantial.
- **Status Pills:** 12px (Full) for success/status indicators to provide high visual contrast against the otherwise rectangular UI.

## Components
- **Buttons:** Sharp corners. Primary buttons are solid `primary` with `on-primary` text. Secondary buttons are outlined with 1px `primary`.
- **Navigation Links:** Use a 4px left-accent border. Active state shifts the background to `surface-container-highest` and the text to bold.
- **Status Chips:** Small, monospaced text within a `surface-container` with a 1px border. Often includes a small dot indicator (e.g., `success-pulse`).
- **Data Nodes:** Used in flow diagrams. White background, 1px border, hover state shifts border to `primary`.
- **System Logs:** Monospaced text blocks inside a `surface-container` with a subtle `outline-variant` border.
- **Emergency Alert:** High-contrast `error-container` (red) with a persistent warning icon, designed to be unavoidable.
- **Input Fields:** 1px border, sharp corners, using `technical-data` font style for the input text.