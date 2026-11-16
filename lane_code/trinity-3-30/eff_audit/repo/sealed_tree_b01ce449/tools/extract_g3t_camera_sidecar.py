#!/usr/bin/env python3
"""Alias entry point for tools.g3t_camera_sidecar_store."""
from tools.g3t_camera_sidecar_store import (  # noqa: F401
    SIDECAR_KEYS,
    SIDECAR_ROW_KEYS,
    SIDECAR_SCHEMA,
    build,
    extract,
    main,
    prior_from_g3t_extri_intri,
    seal,
)

if __name__ == "__main__":
    main()
