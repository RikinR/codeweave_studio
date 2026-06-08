PLACEHOLDER_DIFF_MARKERS = (
    "not provided",
    "assuming ",
    "placeholder",
    "tbd",
    "todo:",
    "lorem ipsum",
)


def is_placeholder_diff(diff: str) -> bool:
    normalized = diff.strip().lower()
    if not normalized:
        return True
    return any(marker in normalized for marker in PLACEHOLDER_DIFF_MARKERS)


def is_valid_unified_diff(diff: str) -> bool:
    if is_placeholder_diff(diff):
        return False
    has_header = diff.startswith("---") or "diff --git" in diff
    has_hunk = "@@" in diff
    has_add_or_remove = "\n+" in diff or "\n-" in diff
    return has_header and has_hunk and has_add_or_remove


def patch_quality_score(diff: str) -> int:
    if not is_valid_unified_diff(diff):
        return -1
    return len(diff) + diff.count("\n+") * 20 + diff.count("@@") * 50
