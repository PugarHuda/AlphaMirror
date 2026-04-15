"""
Client factory — returns either real AveClient or MockAveClient based on env.

Usage:
    from alphamirror.client_factory import make_client
    with make_client() as ave:
        ...

Set DEMO_MODE=1 to force offline fixture mode (for demo video).
"""

from __future__ import annotations

import os
from typing import Union

from .ave_client import AveClient
from .mock_client import MockAveClient


def make_client() -> Union[AveClient, MockAveClient]:
    """
    Return a live client or a mock client based on DEMO_MODE env var.
    Both share the same duck-typed interface.
    """
    if os.environ.get("DEMO_MODE", "").lower() in ("1", "true", "yes"):
        return MockAveClient()
    return AveClient()
