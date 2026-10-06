"""CM-7 / F1.8 list-unwrap normalization reused for AK batch edges."""

from __future__ import annotations

from typing import Any, cast

_MAX_UNWRAP_DEPTH = 16


def unwrap_item_wraps(obj: object) -> object:
    """Recursively strip ``{"item": X}`` and single-element list wraps."""
    if isinstance(obj, dict):
        mapping: dict[Any, Any] = cast(dict[Any, Any], obj)
        keys = list(mapping.keys())
        if keys == ["item"]:
            return unwrap_item_wraps(mapping["item"])
        return {key: unwrap_item_wraps(value) for key, value in mapping.items()}
    if isinstance(obj, list):
        current_typed: list[Any] = cast(list[Any], obj)
        for _ in range(_MAX_UNWRAP_DEPTH):
            if len(current_typed) == 1 and isinstance(current_typed[0], list):
                current_typed = cast(list[Any], current_typed[0])
            else:
                break
        out: list[object] = []
        for item in current_typed:
            out.append(unwrap_item_wraps(item))
        return out
    return obj


def normalize_str_list_arg(value: object) -> object:
    """Undo the gateway CM-7 wrap on a single ``list[str]`` argument."""
    if value is None:
        return None
    unwrapped = unwrap_item_wraps(value)
    if isinstance(unwrapped, str):
        return [unwrapped]
    if unwrapped == [""]:
        return []
    return unwrapped


__all__ = ["normalize_str_list_arg", "unwrap_item_wraps"]
