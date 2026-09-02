"""Guided F-16 HTS + HARM SEAD training mission.

Deprecated entry point — use :mod:`dcsintel.training` instead.
Kept so ``type: sead_training`` specs and older imports keep working.
"""

from __future__ import annotations

from ..training.sead_viper import build_sead_viper as build_training

__all__ = ["build_training"]
