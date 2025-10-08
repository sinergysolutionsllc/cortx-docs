from __future__ import annotations

from typing import Any, Tuple


def normalize_model_metadata(data: dict[str, Any]) -> Tuple[str | None, str | None]:
    """Extract model and version fields from heterogeneous provider responses.

    Tries common keys used across providers, falling back to None.
    """
    # Model name/id keys seen in the wild
    model_keys = [
        "model",
        "model_name",
        "modelId",
        "model_id",
        "id",
    ]
    # Version keys
    version_keys = [
        "model_version",
        "version",
        "modelVersion",
        "release",
        "ver",
    ]
    model = None
    version = None

    for k in model_keys:
        if isinstance(data.get(k), str) and data.get(k):
            model = str(data[k])
            break
    for k in version_keys:
        if isinstance(data.get(k), str) and data.get(k):
            version = str(data[k])
            break

    # Sometimes metadata is nested
    meta = data.get("meta") or data.get("metadata") or {}
    if isinstance(meta, dict):
        if model is None:
            for k in model_keys:
                if isinstance(meta.get(k), str) and meta.get(k):
                    model = str(meta[k])
                    break
        if version is None:
            for k in version_keys:
                if isinstance(meta.get(k), str) and meta.get(k):
                    version = str(meta[k])
                    break

    return model, version
