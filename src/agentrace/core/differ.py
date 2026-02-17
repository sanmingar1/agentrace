"""State diffing between graph execution steps."""

from typing import Any, Optional

from deepdiff import DeepDiff


def compute_state_diff(before: dict[str, Any], after: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Compute the diff between two state dicts.

    Returns a dict with keys "added", "changed", "removed", or None if
    the states are identical.
    """
    diff = DeepDiff(before, after, verbose_level=2)

    if not diff:
        return None

    result: dict[str, Any] = {}

    # Keys added to the dict
    if "dictionary_item_added" in diff:
        added = {}
        for path, value in diff["dictionary_item_added"].items():
            key = _extract_key(path)
            added[key] = value
        if added:
            result["added"] = added

    # Values that changed
    if "values_changed" in diff:
        changed = {}
        for path, change in diff["values_changed"].items():
            key = _extract_key(path)
            changed[key] = {"old": change["old_value"], "new": change["new_value"]}
        if changed:
            result["changed"] = changed

    # Type changes
    if "type_changes" in diff:
        changed = result.get("changed", {})
        for path, change in diff["type_changes"].items():
            key = _extract_key(path)
            changed[key] = {"old": change["old_value"], "new": change["new_value"]}
        if changed:
            result["changed"] = changed

    # Keys removed from the dict
    if "dictionary_item_removed" in diff:
        removed = {}
        for path, value in diff["dictionary_item_removed"].items():
            key = _extract_key(path)
            removed[key] = value
        if removed:
            result["removed"] = removed

    # Iterable item changes (e.g. list items added/removed)
    if "iterable_item_added" in diff:
        added = result.get("added", {})
        for path, value in diff["iterable_item_added"].items():
            key = _extract_key(path)
            added[key] = value
        if added:
            result["added"] = added

    if "iterable_item_removed" in diff:
        removed = result.get("removed", {})
        for path, value in diff["iterable_item_removed"].items():
            key = _extract_key(path)
            removed[key] = value
        if removed:
            result["removed"] = removed

    return result if result else None


def _extract_key(path: str) -> str:
    """Extract a readable key from a DeepDiff path like \"root['key']\"."""
    # Remove "root" prefix and clean up brackets
    cleaned = path.replace("root", "", 1)
    # Convert ['key'] to .key notation
    cleaned = cleaned.replace("['", ".").replace("']", "")
    # Remove leading dot
    if cleaned.startswith("."):
        cleaned = cleaned[1:]
    return cleaned
