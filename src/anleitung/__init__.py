"""
Anleitung (Protocol Instructions)
==================================

The protocol that guides external LLMs on how to use IRIS.

This is NOT code that runs — it's instructions that get injected into
the LLM's context (via MCP resources/prompts).

Main export:
- get_anleitung(): Returns the full protocol as a string
"""

from src.anleitung.protocol import get_anleitung

__all__ = ["get_anleitung"]
