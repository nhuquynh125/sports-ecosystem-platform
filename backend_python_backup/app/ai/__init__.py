"""AI engine placeholder (ARCH §4.2, ADR-09).

Intentionally empty in Step 2. SportScout AI (Step 3+) will implement a thin interface here,
e.g. ``AIEngine.score(features) -> ScoreResult``, so the engine can later be moved out of
process without touching callers. Nothing in the core backend imports this package yet.
"""
