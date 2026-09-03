# VerifAI Rebrand & UI Polish Changelog

Running source of truth for the VerifAI rebrand and UI polish pass (SIH 2026 PS 26188).

## Phase 1 — Core Rebrand & Audit Trail Foundation
- **Brand name**: Renamed application from "BorderShield AI" to "VerifAI" in `app.py` (`page_title`), `ui/screens.py` (sidebar wordmark & hero `<h1>`).
- **Hero subtitle**: Added `.bsx-hero-subtitle` CSS rule and hero subtitle line ("AI-Assisted Identity & Document Screening") under the display wordmark.
- **Audit record card polish**: Updated `audit_record_card_html()` in `ui/screens.py` to color-code each ledger card's left border by its risk band using `traffic_light(Band(band_string))` wrapped in `try/except ValueError` for safe fallback. Rendered risk band as an inline `.bsx-pill {cls}` component in the card body. Fixed punctuation bug where finding text ran into "Risk band:" without a period. Replaced `head_cls` border-color hack with an explicit "Latest" badge (`.bsx-status-pill.ok`). Restacked hash rows label-above-value to prevent 64-char hex overflow misalignment.
- **Color mapping consolidation**: Refactored `recent_cases_table_html()` to remove local `{"LOW": "GREEN", ...}` mapping dict, delegating directly to `traffic_light()` with safe exception fallback. Single source of truth for band colors app-wide.

## Phase 2 — Command Dashboard & Case File Alignment
- **Scenario card layer pills**: Updated `scenario_card_head_html()` in `ui/screens.py` to render layer tags ("T0 CRYPTO", "T1 RULES", "T2 FORENSICS") as `.bsx-pill` badges (`green`, `amber`, `red`) matching the console's existing component tokens.
- **Risk scale rail geometry**: Updated `.bsx-scale-labels` CSS in `ui/style.py` from `justify-content: space-between` to a 4-column equal grid (`repeat(4, 1fr)`). Aligning each risk band label (LOW 0–25, MEDIUM 26–50, HIGH 51–75, CRITICAL 76–100) to its exact 25% track segment ensures tick boundaries and marker position (`left: score%`) line up precisely at the DOM/CSS level.
- **Verdict hero & real document card robustness**: Wrapped `traffic_light()` calls in `verdict_hero_html()` and `realdoc_verdict_card_html()` in `try/except (ValueError, KeyError, AttributeError)` blocks with neutral fallback (`"AMBER"` / `"neutral"`) so unrecognized band strings degrade gracefully without throwing runtime exceptions.
- **Verification**: Verified compilation via `python -m py_compile`, verified real data rendering against live ledger records and fake band fallback data, and verified headless server boot on localhost returning HTTP 200 with zero log tracebacks.
