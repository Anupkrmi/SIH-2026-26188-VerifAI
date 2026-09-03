---
name: Sentinel Prime
colors:
  surface: '#f8f9ff'
  surface-dim: '#ccdbf3'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e6eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d5e3fc'
  on-surface: '#0d1c2e'
  on-surface-variant: '#44474e'
  inverse-surface: '#233144'
  inverse-on-surface: '#eaf1ff'
  outline: '#75777f'
  outline-variant: '#c5c6cf'
  surface-tint: '#4a5e88'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#001a41'
  on-primary-container: '#6f84b0'
  inverse-primary: '#b2c6f7'
  secondary: '#115cb9'
  on-secondary: '#ffffff'
  secondary-container: '#659dfe'
  on-secondary-container: '#003370'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#360f00'
  on-tertiary-container: '#b47458'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d8e2ff'
  primary-fixed-dim: '#b2c6f7'
  on-primary-fixed: '#001a41'
  on-primary-fixed-variant: '#32466f'
  secondary-fixed: '#d7e2ff'
  secondary-fixed-dim: '#acc7ff'
  on-secondary-fixed: '#001a40'
  on-secondary-fixed-variant: '#004491'
  tertiary-fixed: '#ffdbcd'
  tertiary-fixed-dim: '#ffb596'
  on-tertiary-fixed: '#360f00'
  on-tertiary-fixed-variant: '#6c3921'
  background: '#f8f9ff'
  on-background: '#0d1c2e'
  surface-variant: '#d5e3fc'
  surface-base: '#FDFCFB'
  verification-green: '#166534'
  review-amber: '#92400E'
  integrity-red: '#991B1B'
  border-slate: '#CBD5E1'
typography:
  display-title:
    fontFamily: Barlow Condensed
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: 0.02em
  headline-lg:
    fontFamily: Barlow Condensed
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: 0.01em
  headline-lg-mobile:
    fontFamily: Barlow Condensed
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-md:
    fontFamily: Barlow
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Barlow
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.03em
  label-caps:
    fontFamily: Barlow Condensed
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.06em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  spine-width: 4px
---

## Brand & Style

The design system establishes a high-stakes, institutional identity for national border security. It is engineered to evoke feelings of absolute precision, unyielding authority, and forensic clarity. The brand personality is formal and vigilant, targeting intelligence officers and border personnel who require rapid, error-free data interpretation.

The design style is a sophisticated blend of **Institutional Minimalism** and **Technical Brutalism**. It draws inspiration from the Government Digital Service (GDS) ethos of clarity and accessibility, fused with the dense, diagnostic aesthetic of a forensic workstation. The interface avoids all decorative trends—such as neons or soft gradients—in favor of functional structural elements: crisp 1px borders, a "Verification Spine" visual motif to track screening progress, and a clinical warm-white environment that ensures maximum legibility during high-pressure screening cycles.

## Colors

The palette is anchored in a professional, government-grade spectrum that prioritizes contrast and semantic meaning. The background uses a warm white base to prevent the clinical coldness of pure white while maintaining high contrast against the primary colors.

- **Primary (Deep Navy):** Utilized for structural framing, core navigation, and high-authority headers. It signals stability and institutional power.
- **Secondary (Government Blue):** Used for primary actions, progress indicators, and interactive focus states.
- **Neutrals (Slate Gray):** Provides the framework for borders, metadata labels, and secondary UI controls.
- **Semantic Status:** 
    - **Green:** Reserved strictly for successful identity verification and cleared status.
    - **Amber:** Indicates manual review requirements or non-critical anomalies.
    - **Red:** Signals integrity failure, biometric mismatch, or security alerts.

## Typography

This system uses a tiered typographic strategy to separate administrative narrative from technical data.

- **Authority Titles (Barlow Condensed):** Headlines and section titles use this condensed face to mimic official government ledgers and passport documents. It allows for high information density without sacrificing legibility. Titles should frequently use `uppercase` for an added sense of formality.
- **UI & Body (Barlow):** A versatile sans-serif used for all functional instructions, descriptive text, and standard interface labels. It provides a human, readable balance to the sharper display face.
- **Technical Readouts (JetBrains Mono):** All system-generated data—Machine Readable Zones (MRZ), Case IDs, cryptographic hashes, and biometric scores—must be rendered in this monospaced font. This creates a clear visual distinction between human-authored text and raw machine data.

## Layout & Spacing

The layout is built on a **12-column fixed grid** for desktop, ensuring that complex screening dashboards remain consistent across high-resolution duty monitors. 

A central feature is the **Verification Spine**: a vertical 4px structural line that runs down the left side of the main screening area. This spine acts as a visual timeline, changing color (Primary to Green/Amber/Red) as the officer progresses through biometric, document, and background check stages.

- **Desktop (1280px+):** Fixed grid with 32px margins. Two-pane layout with a persistent technical sidebar for data logs.
- **Tablet (768px - 1279px):** Content reflows to a single column for the main screening flow, with the technical sidebar moving to a collapsible tray.
- **Mobile (Below 768px):** Strict single-column layout. Spacing units are compressed to 16px margins to maximize screen real estate for high-priority biometric alerts.

## Elevation & Depth

To maintain an institutional and "flat" document feel, the system avoids heavy shadows. Depth is achieved through **Tonal Layers** and **Crisp Outlines**.

- **Surface Tiers:** Backgrounds use the warm white base, while "containers" (screening cards) use a slightly lifted white with a 1px Slate Gray border.
- **Subtle Depth:** When a shadow is necessary to denote a floating element (like a modal), use a very low-opacity, zero-blur shadow: `0px 2px 0px rgba(0, 26, 65, 0.1)`. This creates a "stacked paper" effect rather than an atmospheric glow.
- **Active States:** Active inputs or cards do not glow; instead, they receive a 2px interior border of Government Blue and a slight tonal shift to a cooler white.

## Shapes

The shape language is **Soft (0.25rem)**, providing a precise, machine-cut appearance. This subtle rounding suggests modern technology without the casual friendliness of highly rounded UI.

- **Standard Elements:** Buttons, input fields, and small cards use 4px (`rounded-md`).
- **Data Containers:** Large screening modules use 8px (`rounded-lg`) to provide a clear structural boundary.
- **System Indicators:** Small status dots and tags for Case Status use 2px corners to maintain a "stamp" or "tag" aesthetic consistent with physical identification papers.

## Components

- **Buttons:** Primary buttons are solid Deep Navy with white Barlow Condensed (Caps) text. Secondary buttons are 1px Slate Gray outlines. No rounded-pill shapes; all buttons must use the Soft (4px) corner radius.
- **Identity Cards:** High-density containers with 1px borders. The header of the card should include the `data-mono` Case ID in the top right corner.
- **Input Fields:** 1px borders with a background shift to a cooler gray on focus. Use JetBrains Mono for the input text to signal data entry precision.
- **The Verification Spine:** A persistent vertical element that connects screening phases. It must be 4px wide and use semantic coloring to indicate the "health" of the screening process.
- **Status Chips:** Small, rectangular tags with 1px borders. Background colors should be low-opacity versions of the semantic colors (e.g., 10% Green) with high-contrast text for accessibility.
- **Data Readouts:** Technical tables using 1px horizontal dividers only. Column headers must be Barlow Condensed (Caps) in Slate Gray.