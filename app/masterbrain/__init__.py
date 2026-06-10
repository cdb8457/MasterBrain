"""MasterBrain — Shared External Agent Brain memory layer (MVP).

A small, dependency-light, provenance-aware memory store for a multi-agent
external brain. Durable state is append-only JSONL under the *sacred* vault
(``/data`` in the container, the ``MasterBrain`` folder in local dev).

Design rules baked in here:
- The container is replaceable; the mounted vault is sacred.
- Memory is append-only events (claims + reviews + edges + sources), so history
  and provenance are never silently overwritten.
- No cloud services are required for basic operation.
"""

__version__ = "0.1.0"
