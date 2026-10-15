"""Split summary overflow without changing facts or making another model call."""
import re

# Common in medical correspondence; preserve their internal punctuation.
_ABBREVIATION = re.compile(r"\b(?:Dr|Mr|Mrs|Ms|Prof|Sr|Jr|St|No|Fig|Dept|vs|approx|e\.g|i\.e)\.$", re.I)
_INITIAL = re.compile(r"\b[A-Z]\.$")
_MONTH = re.compile(r"^(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", re.I)


def split_summary(text: str) -> tuple[str, str]:
    """Return the first sentence and the unchanged remaining text.

    This is a conservative English heuristic, not a full grammar parser. Common
    titles, initials, decimals, dotted dates and abbreviations stay intact.
    """
    for boundary in re.finditer(r'''[.!?]+["'”’)]*(?=\s+\S)''', text):
        prefix = text[:boundary.end()]
        remaining = text[boundary.end():].strip()
        punctuation = boundary.group().rstrip('"\'”’)')
        if punctuation == ".":
            before_closing = prefix.rstrip('"\'”’)')
            if _ABBREVIATION.search(before_closing) or _INITIAL.search(before_closing):
                continue
            # A German-style day followed by an English month, or spaced date.
            if re.search(r"\d\.$", before_closing) and (_MONTH.match(remaining) or re.match(r"\d+[.]", remaining)):
                continue
        return prefix.strip(), remaining
    return text.strip(), ""
