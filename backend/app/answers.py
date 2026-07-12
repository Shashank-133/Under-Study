"""Deprecated thin wrapper — prefer app.ai_bridge.generate_answer."""

from app.ai_bridge import generate_answer as build_answer

__all__ = ["build_answer"]
