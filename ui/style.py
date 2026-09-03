"""One CSS injection, applied once at app startup.

AESTHETIC DIRECTION -- "Sovereign": an institutional, industrial-brutalist
console, not a web dashboard. Built against the Stitch "Sovereign" design
system (reference/sovereign_security_system/), light and clinical rather
than the dark instrument-panel look this file carried before.

  * Clinical off-white surfaces (#f8f9fa), never pure white -- pure white
    has no atmosphere and shows every rendering artefact.
  * A faint 24px blueprint grid behind the whole app: the "architectural"
    read the reference calls for, low enough contrast to never compete
    with content.
  * Depth from 1px outlines and tonal surface steps, never shadows.
    `--shadow: none` is a real constraint, not a placeholder.
  * Sharp, machine-cut corners: 2px by default, 4-8px only for the
    largest containers. Nothing rounds enough to feel soft.
  * --primary is BLACK (#000000), not a hue. It is structural -- text,
    active nav accents, primary buttons -- never decorative.

COLOUR DISCIPLINE -- unchanged from the previous direction and still the
central decision: GREEN / AMBER / RED are the only SATURATED colours
anywhere in the interface, reserved for verdicts. Black/white/grey are
neutrals, not brand colours, so they never compete with a verdict for
attention. The exact green/amber values are a documented gap-fill: the
Sovereign reference has no green in its palette (its "success" colour is
a navy), so those two come from the companion "Sentinel Prime" reference,
chosen for the same light institutional surface and matching 6:1 contrast.
Red is Sovereign's own.

A second, separate pair of bright green/amber/red variants
(--green-on-dark etc.) exists ONLY for text inside the dark terminal-log
panel (see PIPELINE LOG below) -- the primary-container background there
is dark navy, and the light-mode verdict colours would be unreadably low
contrast on it. This is the same kind of documented, narrow exception as
the green/amber gap-fill above: a real rendering need, not decoration.

MOTION -- unchanged from the previous direction; every curve and duration
below still comes from a published table (emilkowalski/skills `animate`):
    --ease-out     cubic-bezier(0.23, 1, 0.32, 1)     entrances, UI
    --ease-in-out  cubic-bezier(0.77, 0, 0.175, 1)    on-screen movement
UI durations stay in the 150-260ms band. Only `transform` and `opacity`
are animated, hover motion is gated behind a real pointer, and
prefers-reduced-motion gets a GENTLER variant -- opacity without
translation -- rather than motion switched off entirely. Page navigation
carries a single flat ~110ms fade and nothing else: a per-block entrance
stagger was measured to stack past 275ms of perceived lag on every nav
click, and the published guidance is explicit that a frequently-repeated
action should not carry animation at all.

TYPE -- Bricolage Grotesque (display), Hanken Grotesk (body/labels),
JetBrains Mono for every technical readout (MRZ lines, hashes, case IDs,
scores -- anything scanned character-by-character). Unchanged from the
previous direction; these three faces are also what the Sovereign
reference itself specifies, so no font migration was needed.
"""

CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap">

<style>
:root{
  /* clinical off-white surfaces -- Sovereign reference, verbatim */
  --bg:#f8f9fa;
  --surface-lowest:#ffffff;
  --surface-low:#f3f4f5;
  --surface:#edeeef;
  --surface-high:#e7e8e9;
  --surface-highest:#e1e3e4;
  --line:#c4c6cf;
  --line-soft:#e1e3e4;
  --outline:#75777c;
  --text:#191c1d;
  --text-2:#45474c;
  --text-3:#75777c;
  /* structural -- black is not a hue here, it's ink. Interactive/primary
     actions, active nav accents, and the focus ring all key off this. */
  --primary:#000000;
  --on-primary:#ffffff;
  --primary-container:#131c2a;
  --on-primary-container:#dfe3ea;
  --secondary:#4f5f78;
  --secondary-container:#d0e1fe;
  --on-secondary-container:#38485f;
  /* the only saturated hues in the entire interface. Green/amber are a
     documented gap-fill from the Sentinel Prime reference (see module
     docstring); red is Sovereign's own. */
  --green:#166534;  --green-line:rgba(22,101,52,.28);  --green-bg:rgba(22,101,52,.08);
  --amber:#92400e;  --amber-line:rgba(146,64,14,.28);  --amber-bg:rgba(146,64,14,.08);
  --red:#ba1a1a;    --red-line:rgba(186,26,26,.30);    --red-bg:#ffdad6;
  --on-red-container:#93000a;
  /* decorative-only accent, added for the premium polish pass. Pulled from
     the user's own reference set (MEA India navy+saffron, Embassy of India
     terracotta) -- never applied to anything a risk verdict renders, so it
     cannot be mistaken for --amber. */
  --accent:#c2410c; --accent-line:rgba(194,65,12,.28); --accent-bg:rgba(194,65,12,.08);
  /* terminal-only bright variants -- see module docstring. Used exclusively
     inside .bsx-pipeline-log, never on the light surface. */
  --green-on-dark:#4ade80; --amber-on-dark:#fbbf24; --red-on-dark:#f87171;
  --text-on-dark:#dfe3ea; --text-on-dark-3:#8a93a3;
  --radius-sm:2px;
  --radius:2px;
  --radius-lg:4px;
  --radius-xl:8px;
  --container-max:1440px;
  --grid-blueprint:rgba(196,198,207,.4);
  --grid-size:24px;
  --font-head:'Bricolage Grotesque', system-ui, sans-serif;
  --font-body:'Hanken Grotesk', system-ui, sans-serif;
  --font-mono:'JetBrains Mono', ui-monospace, monospace;
  --shadow:none;
  /* motion tokens -- published values, never approximated */
  --ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-in-out: cubic-bezier(0.77, 0, 0.175, 1);
  --dur-fast: 150ms;
  --dur: 200ms;
  --dur-slow: 260ms;
  --stagger: 55ms;
}

/* ---- Streamlit chrome ----------------------------------------------
   The header is NOT hidden with visibility:hidden. It used to be, and
   that removed the only control that re-opens a collapsed sidebar --
   collapsing it stranded you with no way back. The header is kept
   visible and zero-height; only the individual controls we don't want
   (Deploy, main menu, toolbar) are removed, so whichever element this
   Streamlit version uses to re-expand the sidebar survives. Both known
   testids for that control are force-shown and restyled below.        */
header[data-testid="stHeader"] { background: transparent !important; height: 0 !important;
  visibility: visible !important; pointer-events: none; }
header[data-testid="stHeader"] * { pointer-events: auto; }
/* stToolbar is NOT display:none -- the re-open control is a DESCENDANT of
   it, and display:none on an ancestor removes the whole subtree from
   rendering no matter what position/visibility the child declares. That
   exact mistake is what stranded a collapsed sidebar with no way back.
   Hide the toolbar's own unwanted children individually instead. */
[data-testid="stToolbar"] { display: flex !important; background: transparent !important;
  height: 0 !important; padding: 0 !important; }
[data-testid="stMainMenuButton"], [data-testid="stBaseButton-header"],
[data-testid="stBaseButton-headerNoPadding"], [data-testid="stStatusWidget"],
[data-testid="stToolbarActions"], [data-testid="stDecoration"], #MainMenu, footer { display: none !important; }

/* the re-open control: always reachable, never chrome-coloured. Styled on
   the element itself AND on a nested button, because the control is a
   <button> directly in some Streamlit versions and a wrapper in others. */
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] {
  display: flex !important; visibility: visible !important; opacity: 1 !important;
  pointer-events: auto !important; align-items: center !important; justify-content: center !important;
  position: fixed !important; top: 14px !important; left: 14px !important; z-index: 999999 !important;
  width: 40px !important; height: 40px !important; min-width: 40px !important;
  background: var(--surface-lowest) !important; border: 1px solid var(--outline) !important;
  border-radius: var(--radius) !important; color: var(--text) !important;
  transition: border-color var(--dur-fast) var(--ease-out), background-color var(--dur-fast) var(--ease-out);
}
[data-testid="stExpandSidebarButton"] button, [data-testid="stSidebarCollapsedControl"] button {
  background: transparent !important; border: none !important; color: var(--text) !important;
  width: 100% !important; height: 100% !important;
}
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],
[data-testid="stSidebarCollapsedControl"] [data-testid="stIconMaterial"] {
  font-size: 22px !important; width: 22px !important; height: 22px !important; color: var(--text) !important; }
@media (hover: hover) and (pointer: fine) {
  [data-testid="stExpandSidebarButton"]:hover, [data-testid="stSidebarCollapsedControl"]:hover {
    background: var(--surface-low) !important; border-color: var(--primary) !important; }
}

.block-container { padding-top:2.4rem !important; padding-bottom:5rem !important;
  padding-left:3rem !important; padding-right:3rem !important; max-width:var(--container-max) !important; }

/* ---- base ----
   The ground is a faint 24px blueprint grid, not a flat fill -- the
   "architectural" read the Sovereign reference specifies for an
   evidence-first, structural-integrity product. It sits far below text
   contrast and covers the whole app, not just the hero: that matches
   what the reference screens actually show (the grid is visible behind
   the Command Center's cards too, not just Overview). No glow, no light
   pool -- this direction is flat and clinical, depth comes from outlines
   and tonal steps only. */
html, body, [class*="css"] { font-family: var(--font-body); }
.stApp { background: var(--bg); color: var(--text); }
.stApp::before {
  content: ""; position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    linear-gradient(to right, var(--grid-blueprint) 1px, transparent 1px),
    linear-gradient(to bottom, var(--grid-blueprint) 1px, transparent 1px);
  background-size: var(--grid-size) var(--grid-size);
}
section[data-testid="stSidebar"], .block-container, header[data-testid="stHeader"] { position: relative; z-index: 1; }
h1, h2, h3, h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: var(--font-head) !important; letter-spacing: -0.02em; color: var(--text) !important;
}
p, span, div, label { color: var(--text); }
/* every st.button wraps its label in its own <p>/<div> -- without this,
   the rule above reaches straight past a button's own `color` (even
   !important) and paints every button label near-black, regardless of
   background. One rule here fixes the whole class, not just the primary
   button where it was actually caught (see the button[kind="primary"]
   comment below for the full explanation). Plain inherit, no !important
   needed: `button p` beats a bare `p` on specificity alone. */
button p, button span, button div, button label { color: inherit; }
code, .stCode, .stJson, pre { font-family: var(--font-mono) !important; }
[data-testid="stCaptionContainer"] { color: var(--text-3) !important; font-size:0.94rem; max-width:76ch; line-height:1.6; }
hr { border-color: var(--line-soft) !important; }

/* THE core structural override: st.container(border=True) paints a full
   rounded card, and under Sovereign a container genuinely IS a 1px
   bordered card (the reference calls this "Bold Outlines" -- every
   container defined by a 1px solid line, no shadows). This is simpler
   than the previous hairline-only treatment, not more complex. */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid var(--line) !important; border-radius: var(--radius-lg) !important;
  background: var(--surface-lowest) !important; padding: 1.3rem 1.5rem 1.5rem 1.5rem !important;
}
[data-testid="stExpander"] { border: 1px solid var(--line) !important;
  border-radius: var(--radius-lg) !important; background: var(--surface-lowest); }
[data-testid="stExpander"] summary { font-family: var(--font-body); font-size: 0.82rem; color: var(--text-2); }

/* ====================== MOTION ======================================
   Entrances only: transform + opacity, 150-260ms, published curves.
   Nothing loops, nothing autoplays, nothing blocks input. */
@keyframes bsx-rise { from { opacity:0; transform: translate3d(0,10px,0); } to { opacity:1; transform:none; } }
@keyframes bsx-fade { from { opacity:0; } to { opacity:1; } }
@keyframes bsx-land { from { opacity:0; transform: translate3d(0,14px,0) scale(.985); } to { opacity:1; transform:none; } }
@keyframes bsx-slide-in { from { opacity:0; transform: translate3d(-10px,0,0); } to { opacity:1; transform:none; } }
@keyframes bsx-draw { to { stroke-dashoffset: var(--dash-end, 0); } }
@keyframes bsx-pulse-once { 0%,100% { opacity:1; } 45% { opacity:.35; } }
@keyframes bsx-grow-x { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes bsx-type-in { from { opacity:0; } to { opacity:1; } }

/* PAGE-LEVEL: deliberately NOT a stagger.
   Switching pages is a constant action during operation, and Streamlit
   already costs a server round-trip per nav click. A per-block cascade
   ran up to 275ms of delay on top of that, so every navigation felt
   laggy and the content appeared to dribble in. The published guidance is
   explicit that a frequently-repeated action should not carry animation
   at all -- so navigation gets one 110ms opacity fade on the whole page
   and nothing else. Choreography is spent only where it is seen once
   per case (the verdict reveal), never on the path between screens. */
.block-container > div > div > div[data-testid="stVerticalBlock"] {
  animation: bsx-fade 110ms linear;
}

/* Gentler, not absent: keep the fade, drop the translation. */
@media (prefers-reduced-motion: reduce) {
  .block-container > div > div > div[data-testid="stVerticalBlock"] > div,
  .bsx-verdict, .bsx-verdict-num, .bsx-spine-row, .bsx-metric, .bsx-finding,
  .bsx-status-card, .bsx-audit-card, .bsx-ladder-row,
  .st-key-scn_genuine, .st-key-scn_dob, .st-key-scn_photo, .st-key-scn_recapture,
  .st-key-scn_face, .st-key-scn_sig {
    animation-name: bsx-fade !important;
  }
  .bsx-ring svg .bsx-arc { animation: none !important; stroke-dashoffset: var(--dash-end, 0) !important; }
  .bsx-decided { animation: none !important; }
  .bsx-meter-fill { animation: none !important; transform: scaleX(1) !important; }
  .bsx-pipeline-log .ln { animation: none !important; opacity: 1 !important; }
}

/* ---- sidebar: a quiet rail. Navigation, not a feature. ---- */
section[data-testid="stSidebar"] {
  width: 260px !important; min-width: 260px !important; max-width: 260px !important;
  background: var(--surface-lowest); border-right: 1px solid var(--line);
}
section[data-testid="stSidebar"] > div { width: 260px; padding-top: 1.4rem; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: 0.15rem; }
section[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] { border: none !important; padding: 0 !important; background: transparent !important; }
/* Streamlit's own collapse chevron is hover-only and zero-sized by
   default, so the control that hides the rail is itself undiscoverable.
   Forced to a permanent 32px target: a control with a destructive-feeling
   outcome (the whole nav disappears) should never be a hidden affordance. */
[data-testid="stSidebarCollapseButton"] {
  display: flex !important; align-items: center; justify-content: center;
  visibility: visible !important; opacity: 1 !important;
  width: 32px !important; height: 32px !important; }
[data-testid="stSidebarCollapseButton"] button {
  display: flex !important; align-items: center; justify-content: center;
  visibility: visible !important; opacity: 1 !important;
  width: 32px !important; height: 32px !important; min-height: 32px !important;
  color: var(--text-3) !important; background: transparent !important; border: none !important;
  transition: color var(--dur-fast) var(--ease-out); }
@media (hover: hover) and (pointer: fine) {
  [data-testid="stSidebarCollapseButton"] button:hover { color: var(--text) !important; }
}
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"] {
  font-size: 20px !important; width: 20px !important; height: 20px !important; }

.bsx-sidebar-brand { padding: 0 1.1rem 1.1rem 1.1rem; margin-bottom: 0.9rem; border-bottom: 1px solid var(--line); }
.bsx-sidebar-brand .name { font-family: var(--font-head); font-weight: 800; font-size: 1.3rem;
  color: var(--text); letter-spacing: -0.02em; line-height:1.15; }
.bsx-sidebar-brand .sub { font-family: var(--font-mono); font-size: 0.76rem; color: var(--text-3);
  text-transform: uppercase; letter-spacing: 0.14em; margin-top: 0.4rem; }

/* the identity block: an honest label, not an operator persona. Same
   bordered-card visual weight the reference gives its (fabricated)
   operator card, filled with a real statement about what you're
   looking at instead. */
.bsx-sidebar-identity { margin: 0 1.1rem 1.1rem 1.1rem; padding: 0.7rem 0.8rem;
  border: 1px solid var(--line); border-radius: var(--radius); background: var(--surface-low);
  display: flex; align-items: flex-start; gap: 0.6rem; }
.bsx-sidebar-identity .dot { width: 7px; height: 7px; border-radius: 50%; background: var(--secondary);
  margin-top: 0.35rem; flex-shrink: 0; }
.bsx-sidebar-identity .l1 { font-family: var(--font-mono); font-size: 0.76rem; font-weight: 600;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--text); }
.bsx-sidebar-identity .l2 { font-family: var(--font-mono); font-size: 0.76rem; color: var(--text-3);
  letter-spacing: 0.04em; margin-top: 0.25rem; }

section[data-testid="stSidebar"] .stButton > button {
  width: 100%; display: flex !important; justify-content: flex-start !important; align-items: center;
  gap: 0.7rem; text-align: left;
  background: transparent; border: none; border-left: 4px solid transparent; color: var(--text-2);
  font-family: var(--font-body); font-size: 1rem; font-weight: 500;
  padding: 0.72rem 1rem; border-radius: 0; min-height: 0;
  transition: color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out),
              background-color var(--dur-fast) var(--ease-out);
}
section[data-testid="stSidebar"] .stButton > button [data-testid="stIconMaterial"] {
  font-size: 21px !important; width: 21px !important; height: 21px !important;
}
section[data-testid="stSidebar"] .stButton > button p { font-family: inherit !important; font-size: inherit !important; text-align: left; }
@media (hover: hover) and (pointer: fine) {
  section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--surface-low); color: var(--text); border-left-color: var(--outline); }
}
.bsx-nav-note { font-size: 0.84rem; line-height:1.5; color: var(--text-3); padding: 0.95rem 1.1rem 0 1.1rem;
  margin-top: 1rem; border-top: 1px solid var(--line-soft); }

/* Below ~640px the sidebar and the main content area both render at
   flex-basis 100% -- Streamlit's own responsive layout expects the
   sidebar to go off-canvas at this width, but the unconditional
   `!important` width above overrides that instead of replacing it, so
   the two panes end up painted on top of each other. Turning the
   sidebar into an explicit fixed overlay when expanded restores a
   correct single-pane-at-a-time layout without touching Streamlit's own
   open/close mechanism (still the same aria-expanded toggle). */
@media (max-width: 640px) {
  section[data-testid="stSidebar"][aria-expanded="true"] {
    position: fixed !important; inset: 0 auto 0 0 !important; height: 100dvh !important;
    z-index: 999997 !important; box-shadow: 2px 0 24px rgba(25,28,29,.18);
  }
  /* scrim behind the drawer: a fixed pseudo-element escapes the sidebar's
     own box regardless of its 260px width, since fixed positioning is
     relative to the viewport, not the ancestor. */
  section[data-testid="stSidebar"][aria-expanded="true"]::after {
    content: ""; position: fixed; inset: 0; z-index: -1;
    background: rgba(25,28,29,.32);
  }
  section[data-testid="stSidebar"][aria-expanded="false"] { display: none !important; }
  .bsx-status-grid { grid-template-columns: 1fr !important; }
  /* the 3.2rem clamp floor is wider than "BorderShield" fits on a 375px
     viewport, so the browser force-wraps mid-word ("BorderShiel" / "d AI")
     -- pre-existing, not introduced by this pass, fixed while touching
     mobile CSS here anyway. */
  .bsx-hero h1.bsx-hero-title { font-size: clamp(2.3rem, 10.5vw, 6rem) !important; }
}

:focus-visible { outline: none !important; box-shadow: 0 0 0 2px var(--bg), 0 0 0 3px var(--primary) !important; }

/* ---- page head ---- */
.bsx-topbar { display: flex; justify-content: space-between; align-items: flex-end; gap: 1rem;
  padding-bottom: 1.5rem; margin-bottom: 0.4rem; flex-wrap: wrap; position: relative; }
.bsx-topbar .eyebrow { font-family: var(--font-mono); font-size: 0.79rem; text-transform: uppercase;
  letter-spacing: 0.18em; color: var(--text-3); margin-bottom: 0.6rem; }
.bsx-topbar .title { font-family: var(--font-head); font-weight: 700; font-size: 2.5rem;
  color: var(--text); letter-spacing: -0.035em; line-height: 1; text-wrap: balance; }
.bsx-topbar .sub { font-family: var(--font-body); font-size: 1.05rem; color: var(--text-3);
  margin-top: 0.7rem; max-width: 62ch; line-height: 1.5; }
.bsx-topbar .case-chip { font-family: var(--font-mono); font-size: 0.82rem; color: var(--text-2);
  letter-spacing: 0.04em; border: 1px solid var(--line); border-radius: var(--radius); padding: 0.28rem 0.6rem; }
.bsx-topbar .meta { display:flex; align-items:center; gap:0.5rem; padding-bottom: 0.3rem; }
.bsx-chain-pill { font-family: var(--font-mono); font-size: 0.79rem; font-weight: 600; letter-spacing: 0.1em;
  text-transform: uppercase; border-radius: var(--radius-sm); padding: 0.3rem 0.6rem; border: 1px solid; }
.bsx-chain-pill.ok { color: var(--green); border-color: var(--green-line); background: var(--green-bg); }
.bsx-chain-pill.broken { color: var(--red); border-color: var(--red-line); background: var(--red-bg); }

/* ---- section label: the only divider this design uses outside of
   bordered cards ---- */
.bsx-tier-head {
  font-family: var(--font-mono); font-size: 0.79rem; font-weight: 600; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--text-3); margin: 0 0 1rem 0; padding: 0; border: none;
  display: flex; align-items: center; gap: 0.7rem;
}
.bsx-tier-head::after { content:""; flex:1; height:1px; background: var(--line-soft); }

/* ---- registration-mark corner ticks: a forensic/blueprint signature
   detail on the elements that anchor a screen (hero, the Command Center
   status row). Diagonal pair, not all four corners -- reads as a
   crop/registration mark without needing four pseudo-els. Not applied to
   .bsx-ladder: that element already owns ::before for its spine line, and
   a second ::before rule on the same class would just lose the cascade. */
.bsx-ticks { position: relative; }
.bsx-ticks::before, .bsx-ticks::after {
  content: ""; position: absolute; width: 14px; height: 14px; pointer-events: none; opacity: 0.55;
  border: 1px solid var(--accent);
}
.bsx-ticks::before { top: -1px; left: -1px; border-right: none; border-bottom: none; }
.bsx-ticks::after { bottom: -1px; right: -1px; border-left: none; border-top: none; }

/* ===================== COMMAND: the metric strip =====================
   One ruled strip, not N cards. Cells power up left-to-right. */
.bsx-metric-strip { display:grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 0; border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.bsx-metric { padding: 1.3rem 1.6rem 1.35rem 0; border-right: 1px solid var(--line-soft);
  animation: bsx-rise var(--dur) var(--ease-out) backwards; }
.bsx-metric:nth-child(1) { animation-delay: 0ms; }
.bsx-metric:nth-child(2) { animation-delay: 40ms; }
.bsx-metric:nth-child(3) { animation-delay: 80ms; }
.bsx-metric:last-child { border-right: none; }
.bsx-metric .label { font-family: var(--font-mono); font-size: 0.78rem; letter-spacing: 0.16em;
  text-transform: uppercase; color: var(--text-3); }
.bsx-metric .value { font-family: var(--font-mono); font-weight: 600; font-size: 2.5rem; color: var(--text);
  line-height: 1; margin-top: 0.65rem; font-variant-numeric: tabular-nums; letter-spacing:-0.03em; }
.bsx-metric .value.tone-red { color: var(--red); }
.bsx-metric .sub { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-3);
  text-transform: uppercase; letter-spacing:0.1em; margin-left: 0.5rem; }

.bsx-pill-row { display:flex; gap:0.45rem; flex-wrap:wrap; margin-top:0.6rem; }
.bsx-status-dot { display:inline-flex; align-items:center; gap:0.45rem; font-family: var(--font-mono);
  font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-2);
  background: var(--surface-low); border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 0.25rem 0.55rem; }
.bsx-status-dot .dot { width: 6px; height: 6px; border-radius: 50%; }
.bsx-status-dot .dot.ok { background: var(--green); }
.bsx-status-dot .dot.bad { background: var(--red); }
.bsx-status-dot .dot.na { background: var(--text-3); }

/* ===================== system status cards (4-across) ================
   Bordered boxes, not a hairline strip -- Sovereign's "Bold Outlines"
   language. Each card states one real, checkable fact. */
/* asymmetric, not four equal cells -- the last card (Cases logged, the
   most narratively important number) runs wider so the row reads as one
   composition instead of four interchangeable tiles. Fixed columns need
   an explicit mobile stack since they lose auto-fit's intrinsic reflow --
   see the 640px override below. */
.bsx-status-grid { display:grid; grid-template-columns: 1fr 1fr 1fr 1.6fr; gap: 1px;
  background: var(--line); border: 1px solid var(--line); border-radius: var(--radius-lg); overflow: hidden; }
.bsx-status-card { background: var(--surface-lowest); padding: 1.2rem 1.3rem;
  animation: bsx-rise var(--dur) var(--ease-out) backwards; }
.bsx-status-card:nth-child(1) { animation-delay: 0ms; }
.bsx-status-card:nth-child(2) { animation-delay: 40ms; }
.bsx-status-card:nth-child(3) { animation-delay: 80ms; }
.bsx-status-card:nth-child(4) { animation-delay: 120ms; }
.bsx-status-card .head { display:flex; justify-content:space-between; align-items:flex-start; gap:0.6rem; }
.bsx-status-card .label { font-family: var(--font-mono); font-size: 0.78rem; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-3); line-height: 1.4; }
.bsx-status-card .value { font-family: var(--font-head); font-weight: 700; font-size: 1.35rem;
  color: var(--text); margin-top: 0.6rem; letter-spacing: -0.01em; }
.bsx-status-card .sub { font-family: var(--font-mono); font-size: 0.76rem; color: var(--text-3);
  margin-top: 0.35rem; }
.bsx-status-pill { display:inline-flex; align-items:center; gap: 0.35rem; font-family: var(--font-mono);
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
  padding: 0.2rem 0.5rem; border-radius: var(--radius-sm); border: 1px solid; white-space: nowrap; }
.bsx-status-pill .dot { width: 6px; height: 6px; border-radius: 50%; }
.bsx-status-pill.ok { color: var(--green); border-color: var(--green-line); background: var(--green-bg); }
.bsx-status-pill.ok .dot { background: var(--green); }
.bsx-status-pill.bad { color: var(--red); border-color: var(--red-line); background: var(--red-bg); }
.bsx-status-pill.bad .dot { background: var(--red); }
.bsx-status-pill.neutral { color: var(--text-2); border-color: var(--line); background: var(--surface-low); }
.bsx-status-pill.neutral .dot { background: var(--text-3); }

/* ===================== scenario cards (attack wall) ===================
   Bordered cards with a real button as their action row, not a bare
   uppercase button standing in for a card. See ui/screens.py
   scenario_card_head_html for why the button is split from the markup.

   Laid out via st.columns(6) in ui/pages.py, not a CSS grid parent: a
   plain st.container() -- with or without key= -- does not emit the
   stVerticalBlockBorderWrapper testid in this Streamlit version (checked
   directly against the running app: zero instances anywhere), so there
   is no single wrapping element these six containers could share a grid
   parent through. Each card is self-sufficient instead -- its own
   border, radius and background declared directly on the .st-key-scn_*
   selector -- rather than depending on Streamlit's border argument or a
   shared grid ancestor that doesn't exist. */
.st-key-scn_genuine, .st-key-scn_dob, .st-key-scn_photo, .st-key-scn_recapture,
.st-key-scn_face, .st-key-scn_sig {
  background: var(--surface-lowest) !important; border: 1px solid var(--line) !important;
  border-radius: var(--radius-lg) !important; padding: 1.1rem 1.2rem 0.9rem 1.2rem !important;
  transition: background-color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out),
              border-left-width var(--dur-fast) var(--ease-out);
  animation: bsx-rise var(--dur) var(--ease-out) backwards;
}
/* entrance stagger -- these six were firing simultaneously (no delay), the
   one motion gap this pass found: every other card grid in the app
   staggers, this one didn't. Explicit per-selector delay, not nth-child:
   each card is its own uniquely-keyed .st-key-scn_* class (see the
   comment above), not siblings a structural selector can index. */
.st-key-scn_genuine { animation-delay: 0ms; }
.st-key-scn_dob { animation-delay: 40ms; }
.st-key-scn_photo { animation-delay: 80ms; }
.st-key-scn_recapture { animation-delay: 120ms; }
.st-key-scn_face { animation-delay: 160ms; }
.st-key-scn_sig { animation-delay: 200ms; }
/* Stacked, NOT a space-between row. These six cards sit in st.columns(6),
   so each is ~200px wide; a side-by-side numeral + layer badge overflowed
   the card outright once the numeral grew to 1.6rem -- "T0 CRYPTO / T2
   FORENSICS" alone needs more width than the badge had left. Stacking is
   the fix that holds at every column width instead of only wide ones. */
.bsx-scenario-head { display:flex; flex-direction: column; align-items: flex-start;
  gap: 0.45rem; margin-bottom: 0.7rem; }
/* index-numeral treatment: the real scenario id (SCN_01..SCN_06, already
   passed in -- not a fabricated counter) rendered as a small ghost mark
   instead of ordinary label text, so each card reads as a numbered
   position in a sequence rather than one of six interchangeable boxes. */
.bsx-scenario-id { font-family: var(--font-mono); font-size: 1.6rem; font-weight: 700;
  color: var(--accent); opacity: 0.28; letter-spacing: -0.02em; line-height: 1; }
/* white-space:normal so a two-tier label wraps INSIDE its border instead
   of running past it; max-width caps it to the card. */
.bsx-scenario-layer { font-family: var(--font-mono); font-size: 0.72rem; font-weight: 600;
  letter-spacing: 0.05em; text-transform: uppercase; color: var(--secondary);
  border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 0.2rem 0.45rem;
  white-space: normal; line-height: 1.35; max-width: 100%; }
.bsx-scenario-title { font-family: var(--font-head); font-weight: 700; font-size: 1.08rem;
  color: var(--text); letter-spacing: -0.01em; line-height: 1.25; }
.bsx-scenario-desc { font-size: 0.88rem; line-height: 1.5; color: var(--text-3); margin-top: 0.5rem; }
/* Equal-height cards with bottom-aligned buttons. The six descriptions are
   genuinely different lengths, so a min-height fudge can't align them --
   stretching each card to its column and pushing the button down with
   margin-top:auto does, at any width. */
/* The testid is stColumn, not "column" (checked against the running app;
   an earlier guess at "column" silently matched nothing). Streamlit
   stretches the columns themselves, but height:100% on the card alone
   resolves against auto-height intermediate wrappers and collapses back
   to content height -- so the whole chain
   stColumn > stVerticalBlock > stLayoutWrapper > card needs stretching.
   Scoped by :has(.st-key-scn_genuine) to the scenario row only, so no
   other st.columns layout in the app is affected.

   The column itself must NOT get height:100%: the row's height is
   content-derived, so a percentage resolves against auto and collapses --
   and worse, declaring any explicit height cancels the align-items:stretch
   that was already going to size it correctly. Let the column stretch,
   then fill inward from it, where the height IS definite. */
div[data-testid="stHorizontalBlock"]:has(.st-key-scn_genuine) div[data-testid="stColumn"] {
  align-self: stretch;
}
div[data-testid="stHorizontalBlock"]:has(.st-key-scn_genuine) div[data-testid="stColumn"] > div[data-testid="stVerticalBlock"],
div[data-testid="stHorizontalBlock"]:has(.st-key-scn_genuine) div[data-testid="stLayoutWrapper"] {
  height: 100%;
}
.st-key-scn_genuine, .st-key-scn_dob, .st-key-scn_photo, .st-key-scn_recapture,
.st-key-scn_face, .st-key-scn_sig {
  height: 100%; display: flex !important; flex-direction: column !important;
}
/* margin-top:auto has to sit on the card's DIRECT flex child, and that is
   the stElementContainer wrapping the button -- not .stButton itself,
   which is a grandchild and so has no auto-margin effect in the card's
   flex context. Verified against the running DOM, not assumed. */
.st-key-scn_genuine > [data-testid="stElementContainer"]:has(.stButton),
.st-key-scn_dob > [data-testid="stElementContainer"]:has(.stButton),
.st-key-scn_photo > [data-testid="stElementContainer"]:has(.stButton),
.st-key-scn_recapture > [data-testid="stElementContainer"]:has(.stButton),
.st-key-scn_face > [data-testid="stElementContainer"]:has(.stButton),
.st-key-scn_sig > [data-testid="stElementContainer"]:has(.stButton) {
  margin-top: auto !important;
}
/* Descendant selectors, not .stButton > button: a disabled button with a
   `help=` tooltip gets wrapped by Streamlit in an extra
   .stTooltipHoverTarget div, so the actual <button> is a GRANDCHILD of
   .stButton for that one case, not a direct child. A `>` combinator here
   silently failed to match the disabled Face Mismatch button only,
   leaving it un-styled (default text-transform, wrong colour) while
   every enabled sibling matched fine -- caught by comparing computed
   styles between an enabled and the disabled card, not by inspection. */
.st-key-scn_genuine .stButton button, .st-key-scn_dob .stButton button,
.st-key-scn_photo .stButton button, .st-key-scn_recapture .stButton button,
.st-key-scn_face .stButton button, .st-key-scn_sig .stButton button {
  width: 100% !important; background: transparent !important; color: var(--text-2) !important;
  border: none !important; border-top: 1px solid var(--line-soft) !important; border-radius: 0 !important;
  font-family: var(--font-mono) !important; font-weight: 600 !important; font-size: 0.78rem !important;
  letter-spacing: 0.08em !important; text-transform: uppercase !important; padding: 0.8rem 0 0.1rem 0 !important;
  min-height: 0 !important; height: auto !important; text-align: left !important;
  justify-content: flex-start !important; margin-top: 0.7rem !important; box-shadow: none !important;
}
.st-key-scn_genuine .stButton button:disabled, .st-key-scn_dob .stButton button:disabled,
.st-key-scn_photo .stButton button:disabled, .st-key-scn_recapture .stButton button:disabled,
.st-key-scn_face .stButton button:disabled, .st-key-scn_sig .stButton button:disabled {
  color: var(--text-3) !important; opacity: 1 !important;
}
@media (hover: hover) and (pointer: fine) {
  .st-key-scn_dob:hover, .st-key-scn_photo:hover, .st-key-scn_sig:hover {
    background: var(--amber-bg) !important; border-color: var(--amber) !important; border-left-width: 4px !important; }
  .st-key-scn_dob:hover .bsx-scenario-layer, .st-key-scn_photo:hover .bsx-scenario-layer,
  .st-key-scn_sig:hover .bsx-scenario-layer { color: var(--amber); border-color: var(--amber-line); }
  .st-key-scn_recapture:hover, .st-key-scn_face:hover {
    background: var(--red-bg) !important; border-color: var(--red) !important; border-left-width: 4px !important; }
  .st-key-scn_recapture:hover .bsx-scenario-layer, .st-key-scn_face:hover .bsx-scenario-layer {
    color: var(--red); border-color: var(--red-line); }
  .st-key-scn_genuine:hover {
    background: var(--green-bg) !important; border-color: var(--green) !important; border-left-width: 4px !important; }
  .st-key-scn_genuine:hover .bsx-scenario-layer { color: var(--green); border-color: var(--green-line); }
  .st-key-scn_genuine .stButton button:hover, .st-key-scn_dob .stButton button:hover,
  .st-key-scn_photo .stButton button:hover, .st-key-scn_recapture .stButton button:hover,
  .st-key-scn_face .stButton button:hover, .st-key-scn_sig .stButton button:hover {
    color: var(--text) !important; }
}

div[data-testid="column"] .stButton > button, div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button {
  width: 100%; background: var(--surface-lowest) !important; color: var(--text-2) !important;
  border: 1px solid var(--line) !important; border-radius: var(--radius) !important;
  font-family: var(--font-mono) !important; font-weight: 600 !important; font-size: 0.82rem !important;
  letter-spacing: 0.1em; text-transform: uppercase; padding: 0.9rem 0.7rem !important;
  min-height: 54px !important; height: auto !important; line-height: 1.35 !important;
  transition: border-color var(--dur-fast) var(--ease-out), background-color var(--dur-fast) var(--ease-out),
              color var(--dur-fast) var(--ease-out); box-shadow: none;
}
div[data-testid="column"] .stButton > button [data-testid="stIconMaterial"] { font-size: 19px !important; }
@media (hover: hover) and (pointer: fine) {
  div[data-testid="column"] .stButton > button:hover,
  div[data-testid="stVerticalBlockBorderWrapper"] .stButton > button:hover {
    border-color: var(--primary) !important; color: var(--text) !important; }
}
div[data-testid="column"] .stButton > button p { font-family: inherit !important; font-weight: inherit !important; letter-spacing: inherit; }
/* --accent, not --primary: black-on-black-adjacent CTAs read as "part of
   the chrome", and this was the site's one real colour opportunity --
   the button everyone's eye lands on first. --primary (pure black) stays
   untouched everywhere else; this is a button-background-only change. */
button[kind="primary"] { background: var(--accent) !important; color: var(--on-primary) !important;
  border: 1px solid var(--accent) !important; font-weight: 600 !important; }
/* REAL BUG, not just a colour choice: Streamlit wraps a button's label in
   its own <p>/<div data-testid="stMarkdownContainer">, and the earlier
   `p, span, div, label { color: var(--text) }` base rule (line ~188)
   targets that inner <p> DIRECTLY -- inheritance from the button's own
   `color` never gets a chance to apply, because a direct rule on an
   element always wins over an inherited value regardless of !important
   on the ancestor. Result: every type="primary" button's dark-grey label
   was rendering the base near-black --text colour on top of a dark
   button fill -- unreadable. `!important` here (unlike the ancestor's)
   DOES win, because it's now competing against another declaration on
   the SAME element, where !important legitimately outranks specificity
   and source order. Confirmed via getComputedStyle on the actual <p>,
   not just the <button>, which is what hid this the first time. */
button[kind="primary"] * { color: inherit !important; }
button[kind="primary"]:hover { opacity: 0.85; }

/* ============ NEW SCREENING: an explicit stepped flow ================ */
.bsx-step-bar { display:flex; gap:2.2rem; margin-bottom: 1.6rem; padding-bottom: 1.2rem;
  border-bottom: 1px solid var(--line); }
.bsx-step-bar .bsx-step { flex: 1; margin-bottom: 0; }
.bsx-step { display:flex; align-items:center; gap:0.85rem; margin-bottom: 0.9rem; }
.bsx-step-num { width:26px; height:26px; border-radius:50%; border:1px solid var(--line); flex-shrink:0;
  display:flex; align-items:center; justify-content:center; font-family: var(--font-mono);
  font-size:0.7rem; color: var(--text-3); background: var(--surface);
  transition: color var(--dur) var(--ease-out), border-color var(--dur) var(--ease-out); }
.bsx-step.done .bsx-step-num { color: var(--green); border-color: var(--green-line); background: var(--green-bg); }
.bsx-step.active .bsx-step-num { color: var(--on-primary); border-color: var(--primary); background: var(--primary); }
.bsx-step-label { font-family: var(--font-mono); font-size: 0.79rem; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--text-3); }
.bsx-step.active .bsx-step-label, .bsx-step.done .bsx-step-label { color: var(--text); font-weight: 600; }
.bsx-step-rule { flex:1; height:1px; background: var(--line-soft); }

/* ================ CASE FILE: the verdict block ======================
   The one element allowed to dominate a screen. It lands as a unit, then
   the numeral settles a beat later -- the score is the payload. */
.bsx-verdict { position: relative; padding: 2rem 2.2rem 1.7rem 2.4rem; border: 1px solid var(--line);
  border-radius: var(--radius-lg); background: var(--surface-lowest); overflow: hidden;
  animation: bsx-land var(--dur) var(--ease-out) backwards; }
.bsx-verdict::before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background: var(--vc, var(--text-3)); }
.bsx-verdict-grid { display:flex; align-items:flex-start; gap:2.6rem; flex-wrap:wrap; }
.bsx-verdict-num { font-family: var(--font-mono); font-weight: 700; font-size: 5.5rem; line-height: .82;
  color: var(--vc, var(--text)); font-variant-numeric: tabular-nums; letter-spacing: -0.05em;
  animation: bsx-rise var(--dur) var(--ease-out) 70ms backwards; }
.bsx-verdict-den { font-family: var(--font-mono); font-size: 0.82rem; color: var(--text-3);
  letter-spacing: 0.16em; text-transform: uppercase; margin-top: 0.7rem; }
.bsx-verdict-body { flex:1; min-width: 260px; }
.bsx-verdict-band { display:inline-block; font-family: var(--font-mono); font-size: 0.79rem; font-weight: 700;
  letter-spacing: 0.16em; text-transform: uppercase; color: var(--vc); border:1px solid var(--vc);
  border-radius: var(--radius-sm); padding: 0.22rem 0.55rem; margin-bottom: 0.85rem; }
.bsx-verdict-action { font-family: var(--font-head); font-weight: 700; font-size: 1.9rem; line-height: 1.08;
  letter-spacing: -0.03em; color: var(--text); text-wrap: balance; }
.bsx-verdict-why { font-size: 1.02rem; color: var(--text-2); margin-top: 0.75rem; line-height: 1.55; max-width: 58ch; }
.bsx-verdict-why b { color: var(--text); font-weight: 600; }

/* risk scale rail */
.bsx-scale-track { position: relative; width:100%; height:2px; background: var(--line); margin: 1.9rem 0 0.7rem 0; }
.bsx-scale-tick { position:absolute; top:-3px; width:1px; height:8px; background: var(--line); }
.bsx-scale-marker { position:absolute; top:-5px; width:2px; height:12px; transform: translateX(-50%);
  animation: bsx-fade var(--dur) var(--ease-out) 150ms backwards; }
.bsx-scale-marker::after { content:""; position:absolute; left:50%; top:-5px; transform:translateX(-50%);
  border-left:4px solid transparent; border-right:4px solid transparent; border-top:5px solid currentColor; }
.bsx-scale-labels { display: grid; grid-template-columns: repeat(4, 1fr); font-family: var(--font-mono); font-size: 0.77rem;
  color: var(--text-3); letter-spacing: 0.08em; text-transform: uppercase; margin-top: 0.4rem; }
.bsx-scale-labels span { text-align: center; }
.bsx-scale-labels span:first-child { text-align: left; }
.bsx-scale-labels span:last-child { text-align: right; }
.bsx-scale-labels .on { color: var(--text); font-weight: 600; }

/* ---- the Trust Ladder spine: the project's thesis, drawn. Tiers
   resolve top-down in ladder order -- the order they actually run. ---- */
.bsx-spine { position: relative; }
.bsx-spine-row { position: relative; display: grid; grid-template-columns: 34px 26px 1fr auto;
  gap: 0 0.85rem; align-items: start; padding: 0.75rem 0;
  animation: bsx-slide-in var(--dur-fast) var(--ease-out) backwards; }
.bsx-spine-row:nth-child(1) { animation-delay: 90ms; }
.bsx-spine-row:nth-child(2) { animation-delay: 130ms; }
.bsx-spine-row:nth-child(3) { animation-delay: 170ms; }
.bsx-spine-row:nth-child(4) { animation-delay: 210ms; }
.bsx-spine-row::before { content:""; position:absolute; left:46px; top:26px; bottom:-8px; width:1px; background: var(--line); }
.bsx-spine-row:last-child::before { display:none; }
.bsx-spine-tier { font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-3);
  letter-spacing: 0.1em; padding-top: 0.32rem; }
.bsx-spine-dot { width: 21px; height: 21px; border-radius: 50%; border: 1px solid var(--line);
  background: var(--surface-lowest); display:flex; align-items:center; justify-content:center;
  font-family: var(--font-mono); font-size: 0.66rem; color: var(--text-3); position: relative; z-index:1; }
.bsx-spine-dot.pass { color: var(--green); border-color: var(--green-line); background: var(--green-bg); }
.bsx-spine-dot.fail { color: var(--red); border-color: var(--red); background: var(--red-bg); }
.bsx-spine-dot.review { color: var(--amber); border-color: var(--amber-line); background: var(--amber-bg); }
.bsx-spine-dot.na { color: var(--text-3); border-color: var(--line-soft); background: transparent; }
.bsx-spine-name { font-family: var(--font-body); font-size: 1.05rem; font-weight: 500; color: var(--text); line-height:1.35; }
.bsx-spine-row.na .bsx-spine-name { color: var(--text-3); font-weight: 400; }
.bsx-spine-row.fail .bsx-spine-name { color: var(--red); font-weight: 600; }
/* "Checks:" -- the constant plain-English question this tier answers.
   Set quieter and italic so it reads as a standing description, never as
   a finding about the document on screen. The pair of lines (question,
   then "This case:") is the whole fix for the case file being
   unreadable -- see _TIER_QUESTION in ui/screens.py. */
.bsx-spine-asks { font-size: 0.86rem; color: var(--text-3); font-style: italic; margin-top: 0.25rem;
  line-height: 1.45; max-width: 54ch; }
.bsx-spine-detail { font-size: 0.92rem; color: var(--text-2); margin-top: 0.35rem; line-height:1.45; max-width: 52ch; }
.bsx-spine-detail b { color: var(--text); font-weight: 600; }
.bsx-spine-status { font-family: var(--font-mono); font-size: 0.79rem; letter-spacing: 0.12em;
  color: var(--text-3); padding-top: 0.3rem; }
.bsx-spine-row.fail .bsx-spine-status { color: var(--red); }
.bsx-spine-row.pass .bsx-spine-status { color: var(--green); }
.bsx-spine-row.review .bsx-spine-status { color: var(--amber); }
/* fires once, after its row has landed: this is the answer to "which
   layer decided?", so it earns exactly one blink and never repeats */
.bsx-decided { display:inline-block; font-family: var(--font-mono); font-size: 0.73rem; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--red); border:1px solid var(--red-line); background: var(--red-bg);
  border-radius: var(--radius-sm); padding: 0.1rem 0.4rem; margin-left: 0.5rem; vertical-align: 2px;
  animation: bsx-pulse-once 460ms var(--ease-in-out) 300ms 1 backwards; }

/* ---- hairline data list: replaces every boxed key/value table ---- */
.bsx-datalist { display:flex; flex-direction: column; }
.bsx-field-row, .bsx-datarow { display:flex; justify-content:space-between; align-items:baseline; gap:1rem;
  padding: 0.62rem 0; border-bottom: 1px solid var(--line-soft); }
.bsx-field-row:last-child, .bsx-datarow:last-child { border-bottom: none; }
.bsx-field-name { font-family: var(--font-mono); color: var(--text-3); font-size:0.78rem;
  text-transform:uppercase; letter-spacing:0.12em; white-space: nowrap; }
.bsx-field-value { font-family: var(--font-mono); color: var(--text); font-size: 0.96rem; text-align: right;
  font-variant-numeric: tabular-nums; }

/* ---- finding cards: bordered, the "Evidence Inspector" language ---- */
.bsx-finding { border: 1px solid var(--line); border-left: 4px solid var(--red);
  background: var(--surface-lowest); border-radius: 0 var(--radius) var(--radius) 0;
  overflow: hidden; margin-bottom: 0.7rem;
  animation: bsx-rise var(--dur-fast) var(--ease-out) 120ms backwards; }
.bsx-finding-head { padding: 0.8rem 1.1rem 0.55rem 1.1rem; font-family: var(--font-body); font-size: 0.98rem;
  font-weight: 700; letter-spacing: -0.01em; color: var(--red); }
.bsx-finding-body { padding: 0 1rem 0.9rem 1rem; }
.bsx-finding-body p { color: var(--text-2); font-size: 0.95rem; margin: 0 0 0.7rem 0; line-height:1.55; }
/* Technical wording, kept but demoted. Native <details> so it needs no
   JS and stays keyboard-operable; closed by default so the plain-English
   answer is what an officer reads first. */
.bsx-tech { margin-top: 0.2rem; border-top: 1px solid var(--line-soft); padding-top: 0.5rem; }
.bsx-tech summary { font-family: var(--font-mono); font-size: 0.74rem; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--text-3); cursor: pointer; list-style: none; }
.bsx-tech summary::-webkit-details-marker { display: none; }
.bsx-tech summary::before { content: "▸ "; color: var(--accent); }
.bsx-tech[open] summary::before { content: "▾ "; }
.bsx-tech summary:hover { color: var(--text-2); }
.bsx-tech p { font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-3) !important;
  margin: 0.5rem 0 0 0 !important; line-height: 1.5; }

/* "Not established by this check" -- the honest counterpart to a score.
   Deliberately neutral, never a severity colour: an unassessed layer is
   an absence of evidence, not evidence against the document. */
.bsx-limits { border: 1px solid var(--line); border-left: 3px solid var(--outline);
  border-radius: var(--radius-lg); background: var(--surface-low); padding: 1rem 1.2rem; margin-top: 1rem; }
.bsx-limits .k { font-family: var(--font-mono); font-size: 0.74rem; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-3); margin-bottom: 0.6rem; }
.bsx-limits ul { margin: 0 0 0.7rem 0; padding-left: 1.1rem; }
.bsx-limits li { font-size: 0.88rem; color: var(--text-2); line-height: 1.5; margin-bottom: 0.25rem; }
.bsx-limits p { font-size: 0.88rem; color: var(--text-3); margin: 0; line-height: 1.55; }
.bsx-limits p b { color: var(--text); }

/* The two-column honest answer: what WAS established beside what was not.
   Side by side on purpose -- these are equal-weight halves of one result,
   and stacking them made the second read as a footnote to the first. */
.bsx-split { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1px;
  background: var(--line); border: 1px solid var(--line); border-radius: var(--radius-lg);
  overflow: hidden; margin-top: 1rem; }
.bsx-split-col { background: var(--surface-lowest); padding: 1rem 1.2rem; }
.bsx-split-col .k { font-family: var(--font-mono); font-size: 0.72rem; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--text-3); margin-bottom: 0.7rem; }
.bsx-split-col .k.ok { color: var(--green); }
.bsx-split-col ul { margin: 0; padding: 0; list-style: none; }
.bsx-split-col li { font-size: 0.87rem; line-height: 1.5; margin-bottom: 0.4rem; padding-left: 1.4rem;
  position: relative; color: var(--text-2); }
.bsx-split-col li::before { position: absolute; left: 0; font-family: var(--font-mono); font-weight: 700; }
/* Three distinct marks for three distinct claims -- a tick is not the
   same statement as "advisory only", and neither is "does not apply". */
.bsx-split-col li.yes::before { content: "\\2713"; color: var(--green); }
.bsx-split-col li.review::before { content: "!"; color: var(--amber); }
.bsx-split-col li.na::before { content: "\\25CB"; color: var(--text-3); }
.bsx-split-col li.none::before { content: "\\25CB"; color: var(--text-3); }
.bsx-split-col li.none { color: var(--text-3); font-style: italic; }
.bsx-finding.advisory { border-left-color: var(--amber); }
.bsx-finding.advisory .bsx-finding-head { color: var(--amber); }
.bsx-compare-grid { display:grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;
  font-family: var(--font-mono); font-size: 0.9rem; }
.bsx-compare-cell { border: 1px solid var(--line); border-radius: var(--radius-sm); padding: 0.5rem 0.65rem;
  background: var(--surface-low); color: var(--text); }
.bsx-compare-cell.bad { border-color: var(--red-line); background: var(--red-bg); color: var(--on-red-container); }
.bsx-compare-cell .k { font-family: var(--font-mono); font-size: 0.72rem; color: var(--text-3);
  letter-spacing:0.12em; text-transform:uppercase; margin-bottom: 0.3rem; }

/* ---- verification sequence (Mode B's dynamic ladder) ---- */
.bsx-vseq-row { display:flex; align-items:center; gap:0.8rem; padding: 0.55rem 0;
  border-bottom: 1px solid var(--line-soft); }
.bsx-vseq-row:last-child { border-bottom:none; }
.bsx-vseq-dot { width:21px; height:21px; border-radius:50%; border:1px solid var(--line); display:flex;
  align-items:center; justify-content:center; font-family: var(--font-mono); font-size:0.66rem; flex-shrink:0;
  background: var(--surface-lowest); }
.bsx-vseq-dot.pass { color: var(--green); border-color: var(--green-line); }
.bsx-vseq-dot.fail { color: var(--red); border-color: var(--red); background: var(--red-bg); }
.bsx-vseq-dot.na { color: var(--text-3); border-color: var(--line-soft); background: transparent; }
.bsx-vseq-dot.review { color: var(--amber); border-color: var(--amber-line); background: var(--amber-bg); }
.bsx-vseq-label { flex:1; display:flex; justify-content:space-between; align-items:center;
  font-family: var(--font-body); font-size: 0.9rem; }
.bsx-vseq-label .status { font-family: var(--font-mono); font-size: 0.65rem; letter-spacing:0.12em;
  text-transform:uppercase; color: var(--text-3); }
.bsx-vseq-row.fail .bsx-vseq-label { color: var(--red); font-weight:600; }
.bsx-vseq-row.fail .status { color: var(--red); }
.bsx-vseq-row.na .bsx-vseq-label { color: var(--text-3); }
.bsx-vseq-row.review .bsx-vseq-label { color: var(--amber); font-weight:600; }
.bsx-vseq-row.review .status { color: var(--amber); }

/* ---- instrument dial: the arc DRAWS to the score, so the number is
   arrived at rather than asserted ---- */
.bsx-ring-wrap { display:flex; flex-direction:column; align-items:center; gap:0.9rem; }
.bsx-ring { position:relative; width:210px; height:210px; }
.bsx-ring svg { width:100%; height:100%; }
.bsx-ring .bsx-arc { animation: bsx-draw 460ms var(--ease-out) 60ms backwards; }
.bsx-ring-score { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.bsx-ring-score .n { font-family: var(--font-mono); font-size: 3.4rem; font-weight:700; color: var(--text);
  line-height:1; font-variant-numeric: tabular-nums; letter-spacing:-0.04em; }
.bsx-ring-score .d { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-3);
  text-transform:uppercase; letter-spacing:0.16em; margin-top:0.5rem; }

/* ---- risk contribution meters: real bars, widths from real weights --- */
.bsx-meter-row { padding: 0.65rem 0; border-bottom: 1px solid var(--line-soft); }
.bsx-meter-row:last-child { border-bottom: none; }
.bsx-meter-row .top { display:flex; justify-content:space-between; align-items:baseline; margin-bottom: 0.4rem; }
.bsx-meter-row .lbl { font-size: 0.94rem; color: var(--text-2); }
.bsx-meter-row .amt { font-family: var(--font-mono); font-weight:700; font-size: 0.85rem;
  font-variant-numeric: tabular-nums; }
.bsx-meter-row.red .amt { color: var(--red); }
.bsx-meter-row.amber .amt { color: var(--amber); }
.bsx-meter-track { width: 100%; height: 5px; background: var(--line-soft); border-radius: 3px; overflow: hidden; }
.bsx-meter-fill { height: 100%; border-radius: 3px; transform-origin: left; transform: scaleX(0);
  animation: bsx-grow-x var(--dur-slow) var(--ease-out) 100ms forwards; }
.bsx-meter-fill.red { background: var(--red); }
.bsx-meter-fill.amber { background: var(--amber); }
.bsx-contrib-total { display:flex; justify-content:space-between; align-items:baseline; margin-top:0.8rem;
  padding-top:0.8rem; border-top: 1px solid var(--line); font-family: var(--font-mono); font-size: 0.77rem;
  text-transform:uppercase; letter-spacing:0.16em; color: var(--text-3); }
.bsx-contrib-total .amt { font-family: var(--font-mono); font-size: 1.5rem; font-weight:700; color: var(--text);
  letter-spacing:-0.02em; font-variant-numeric: tabular-nums; }

/* ---- the pipeline log: an honest terminal. Every line is a real
   signal from verdict.signals, closing on the real fusion line from
   core/risk.py. Dark inset by design -- the one deliberately dark panel
   in an otherwise light interface, because a terminal reads as a
   terminal only on a dark ground. See module docstring for the
   on-dark colour variants this requires. ---- */
.bsx-pipeline-log { background: var(--primary-container); border-radius: var(--radius);
  padding: 1.1rem 1.3rem; font-family: var(--font-mono); font-size: 0.83rem; line-height: 1.85;
  overflow-x: auto; }
.bsx-pipeline-log .ln { white-space: pre; opacity: 0; animation: bsx-type-in var(--dur-fast) linear forwards; }
.bsx-pipeline-log .ln:nth-child(1) { animation-delay: 0ms; }
.bsx-pipeline-log .ln:nth-child(2) { animation-delay: 35ms; }
.bsx-pipeline-log .ln:nth-child(3) { animation-delay: 70ms; }
.bsx-pipeline-log .ln:nth-child(4) { animation-delay: 105ms; }
.bsx-pipeline-log .ln:nth-child(5) { animation-delay: 140ms; }
.bsx-pipeline-log .ln:nth-child(6) { animation-delay: 175ms; }
.bsx-pipeline-log .ln:nth-child(7) { animation-delay: 210ms; }
.bsx-pipeline-log .ln:nth-child(n+8) { animation-delay: 245ms; }
.bsx-pipeline-log .tag { color: var(--text-on-dark-3); }
.bsx-pipeline-log .pass { color: var(--green-on-dark); }
.bsx-pipeline-log .fail { color: var(--red-on-dark); }
.bsx-pipeline-log .weak { color: var(--amber-on-dark); }
.bsx-pipeline-log .txt { color: var(--text-on-dark); }
.bsx-pipeline-log .fuse { color: var(--text-on-dark); font-weight: 600; border-top: 1px solid rgba(255,255,255,.14);
  display: block; margin-top: 0.5rem; padding-top: 0.6rem; }

/* ---- case table ---- */
.bsx-table { width: 100%; border-collapse: collapse; font-family: var(--font-body); font-size: 0.95rem; }
.bsx-table th { text-align:left; font-family: var(--font-mono); font-size: 0.76rem; font-weight:600;
  text-transform:uppercase; letter-spacing: 0.16em; color: var(--text-3); padding: 0 0.9rem 0.7rem 0;
  border-bottom: 1px solid var(--line); background: transparent; }
.bsx-table td { padding: 0.85rem 0.9rem 0.85rem 0; border-bottom: 1px solid var(--line-soft);
  vertical-align: middle; color: var(--text-2); }
.bsx-table tr:last-child td { border-bottom: none; }
.bsx-table tr.case-row td:first-child { border-left: 3px solid var(--row-accent, var(--line)); padding-left: 0.9rem; }
.bsx-table tr.case-row { transition: background-color var(--dur-fast) var(--ease-out); }
@media (hover: hover) and (pointer: fine) { .bsx-table tr.case-row:hover { background: var(--surface-low); } }
.bsx-table .case-id { color: var(--text); font-family: var(--font-mono); font-size:0.9rem; }
.bsx-table .finding-txt { color: var(--text-3); font-size: 0.9rem; line-height:1.45; }
.bsx-risk-bar-track { width: 100%; max-width: 90px; height: 4px; background: var(--line-soft); margin-bottom: 0.4rem; border-radius: 2px; }
.bsx-risk-bar-fill { height: 4px; border-radius: 2px; }
.bsx-pill { display:inline-block; font-family: var(--font-mono); font-size: 0.75rem; font-weight:600;
  text-transform:uppercase; letter-spacing: 0.1em; padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm); border: 1px solid; }
.bsx-pill.green { color: var(--green); border-color: var(--green-line); background: var(--green-bg); }
.bsx-pill.amber { color: var(--amber); border-color: var(--amber-line); background: var(--amber-bg); }
.bsx-pill.red   { color: var(--on-red-container); border-color: var(--red-line);   background: var(--red-bg); }

/* ============ AUDIT: hash-chained record cards ======================= */
.bsx-audit-card { border: 1px solid var(--line); border-left: 4px solid var(--card-border, var(--line)); border-radius: var(--radius-lg);
  background: var(--surface-lowest); padding: 1.1rem 1.3rem 1.2rem 1.3rem; margin-bottom: 0.9rem;
  animation: bsx-rise var(--dur-fast) var(--ease-out) backwards; }
.bsx-audit-card:nth-child(1) { animation-delay: 0ms; }
.bsx-audit-card:nth-child(2) { animation-delay: 30ms; }
.bsx-audit-card:nth-child(3) { animation-delay: 60ms; }
.bsx-audit-card:nth-child(4) { animation-delay: 90ms; }
.bsx-audit-card:nth-child(n+5) { animation-delay: 120ms; }
.bsx-audit-card .top { display:flex; justify-content:space-between; align-items:baseline; gap: 0.8rem;
  font-family: var(--font-mono); font-size: 0.76rem; color: var(--text-3); letter-spacing: 0.06em;
  padding-bottom: 0.6rem; border-bottom: 1px solid var(--line-soft); margin-bottom: 0.6rem; }
.bsx-audit-card .rec { color: var(--text); font-weight: 600; }
.bsx-audit-card .title { font-family: var(--font-head); font-weight: 700; font-size: 1.05rem;
  color: var(--text); letter-spacing: -0.01em; margin-bottom: 0.35rem; }
.bsx-audit-card .body { font-size: 0.92rem; color: var(--text-2); line-height: 1.55; margin-bottom: 0.8rem; }
.bsx-audit-card .hashes { display: grid; gap: 0.5rem; background: var(--surface-low);
  border: 1px solid var(--line-soft); border-radius: var(--radius-sm); padding: 0.6rem 0.75rem; }
.bsx-audit-card .hrow { display: flex; flex-direction: column; gap: 0.15rem; font-family: var(--font-mono); font-size: 0.78rem; }
.bsx-audit-card .hrow .k { color: var(--text-3); letter-spacing: 0.06em; text-transform: uppercase; font-size: 0.7rem; font-weight: 600; width: auto; }
.bsx-audit-card .hrow .v { color: var(--text-2); word-break: break-all; font-size: 0.78rem; }

/* ---- misc ---- */
.bsx-crypto-note { border: 1px solid var(--line); border-left: 4px solid var(--primary);
  background: var(--surface-low); border-radius: var(--radius); padding: 0.9rem 1.1rem;
  font-size: 0.98rem; color: var(--text-2); margin-top: 1rem; line-height:1.6; }
.bsx-crypto-note b { color: var(--text); }

/* ===================== OVERVIEW: the front page =====================
   The only screen in the product that is READ rather than operated, so
   it is the only one allowed editorial scale. No decorative graphic --
   the blueprint grid behind the whole app already carries the visual
   interest; this page earns its whitespace instead of filling it. */
.bsx-hero { position: relative; padding: 3.4rem 0 3rem 0; }
.bsx-hero-eyebrow { font-family: var(--font-mono); font-size: 0.82rem; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--text-3); margin-bottom: 1.6rem;
  animation: bsx-rise var(--dur-slow) var(--ease-out) backwards; }
/* h1.bsx-hero-title, not .bsx-hero-title: Streamlit ships its own
   `h1 { font-size: 2.75rem }` which outranks a bare class selector and
   was flattening the display line to 44px. */
.bsx-hero h1.bsx-hero-title { font-family: var(--font-head) !important; font-weight: 800;
  font-size: clamp(3.2rem, 6.6vw, 6rem) !important; line-height: 0.94; letter-spacing: -0.045em;
  color: var(--text); margin: 0; padding: 0; text-wrap: balance;
  animation: bsx-rise var(--dur) var(--ease-out) 40ms backwards; }
.bsx-hero-title .dim { color: var(--text-3); }
.bsx-hero-subtitle { font-family: var(--font-mono); font-size: 0.85rem; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--text-3); margin-top: 0.5rem; }
.bsx-hero-thesis { font-family: var(--font-head); font-weight: 600;
  font-size: clamp(1.3rem, 2.3vw, 1.95rem); line-height: 1.28; letter-spacing: -0.02em;
  color: var(--text-2); max-width: 34ch; margin: 2rem 0 0 0; text-wrap: balance;
  animation: bsx-rise var(--dur) var(--ease-out) 80ms backwards; }
.bsx-hero-thesis em { font-style: normal; color: var(--text); }
.bsx-hero-lede { font-size: 1.12rem; line-height: 1.68; color: var(--text-3);
  max-width: 62ch; margin-top: 1.5rem;
  animation: bsx-rise var(--dur) var(--ease-out) 120ms backwards; }
.bsx-hero-rule { height: 1px; background: var(--line); margin: 3rem 0 0 0; }

/* the four tiers, stated as the architecture rather than a live result --
   a connected ladder diagram, not four interchangeable cards. A rail on
   the left (node + spine) mirrors the audit-trail's hash-chain visual
   language: this hierarchy IS a chain of authority, so it reads as one.
   Built in CSS (row height derives from real, variable description text)
   rather than raw SVG coordinates, which would need the two to agree on
   pixel-exact row heights independently of content length. */
.bsx-ladder { border: 1px solid var(--line); border-radius: var(--radius-lg); background: var(--surface-lowest);
  padding: 0.4rem 1.8rem 0.4rem 1.6rem; }
.bsx-ladder-row { display:grid; grid-template-columns: 54px 1fr; column-gap: 1.5rem; position: relative;
  padding: 1.5rem 0; animation: bsx-rise var(--dur) var(--ease-out) backwards; }
.bsx-ladder-row:not(:last-child) { border-bottom: 1px solid var(--line-soft); }
.bsx-ladder-row:nth-child(1){animation-delay:0ms;} .bsx-ladder-row:nth-child(2){animation-delay:40ms;}
.bsx-ladder-row:nth-child(3){animation-delay:80ms;} .bsx-ladder-row:nth-child(4){animation-delay:120ms;}
/* the spine: one continuous line behind every node, drawn on the wrapper
   so it never has to resync with each row's independently-variable height. */
.bsx-ladder { position: relative; }
/* centered through the node column: padding-left + half the 54px node
   width - half the line's own width, so the line threads through every
   node's true center regardless of root font-size. */
.bsx-ladder::before { content:""; position:absolute; left: calc(1.6rem + 27px - 0.5px);
  top: 1.9rem; bottom: 1.9rem; width: 1px; background: var(--line); z-index: 0; }
.bsx-ladder-node { width: 54px; height: 54px; border-radius: 50%; border: 1.5px solid var(--tc, var(--outline));
  background: var(--surface-lowest); display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-weight: 700; font-size: 0.86rem; color: var(--tc, var(--text-3));
  position: relative; z-index: 1; align-self: start; }
.bsx-ladder-body .name { font-family: var(--font-head); font-weight: 700; font-size: 1.24rem;
  letter-spacing: -0.02em; color: var(--text); line-height: 1.2; }
.bsx-ladder-body .role { display: inline-block; font-family: var(--font-mono); font-size: 0.74rem;
  font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--tc, var(--text-3));
  border: 1px solid var(--tc, var(--line)); border-radius: var(--radius-sm); padding: 0.18rem 0.5rem;
  margin-top: 0.5rem; }
.bsx-ladder-body .desc { font-size: 0.98rem; line-height: 1.6; color: var(--text-3); margin-top: 0.7rem; max-width: 62ch; }

/* honest limitations, stated on the front page rather than discovered in Q&A */
.bsx-honesty { display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 2rem 2.5rem; }
.bsx-honesty-item .k { font-family: var(--font-mono); font-size: 0.78rem; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--amber); margin-bottom: 0.6rem; }
.bsx-honesty-item .v { font-size: 1rem; line-height: 1.65; color: var(--text-3); max-width: 44ch; }
.bsx-honesty-item .v b { color: var(--text-2); font-weight: 600; }

/* wide content never scrolls the page body sideways */
.bsx-scroll-x { overflow-x: auto; }
[data-testid="stImage"] img { border-radius: var(--radius); }
</style>
"""


def inject() -> None:
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
