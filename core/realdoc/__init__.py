"""Real Document Screening mode (Mode B): arbitrary uploaded documents +
an optional person photo, screened with a capability-aware Trust Ladder.

Completely separate from the top-level core/ modules that run Mode A (the
fixed 1000x700 synthetic UTO template + Attack Wall) -- nothing here is
imported by core/pipeline.py, core/risk.py, or core/types.py, and nothing
in this package modifies them. See PLAN_realdoc.md for the reasoning.
"""
