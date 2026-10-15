"""Server-owned source passages: models select IDs instead of copying quotes."""


def source_passages(source: str, target_size: int = 800) -> dict[str, str]:
    """Preserve original substrings and avoid cutting words, numbers or references."""
    passages = {}
    start = 0
    while start < len(source):
        end = min(start + target_size, len(source))
        if end < len(source):
            boundary = max(source.rfind("\n", start + target_size // 4, end),
                           source.rfind(" ", start + target_size // 4, end))
            if boundary >= start:
                end = boundary + 1
            else:
                # A long unbroken token is kept whole, never silently truncated.
                while end < len(source) and not source[end].isspace():
                    end += 1
        passage = source[start:end].strip()
        if passage:
            passages[f"S{len(passages) + 1:04d}"] = passage
        start = end
    return passages
