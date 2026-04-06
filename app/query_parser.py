"""
Simple natural-language-style query parsing for the chatbot.
Maps user messages to API filters (department, credits, has_prerequisites, search keywords).
"""
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ParsedQuery:
    department: Optional[str] = None
    credits: Optional[float] = None
    has_prerequisites: Optional[bool] = None
    search_keywords: Optional[str] = None
    prerequisite_for_code: Optional[str] = None  # e.g. "CS102" for "prerequisites for CS102"


# Common department codes to detect in text
DEPARTMENT_ALIASES = {
    "cs": "CS",
    "computer science": "CS",
    "math": "MATH",
    "mathematics": "MATH",
    "ee": "EE",
    "electrical": "EE",
    "physics": "PHYS",
    "phys": "PHYS",
    "chem": "CHEM",
    "chemistry": "CHEM",
    "bio": "BIO",
    "biology": "BIO",
    "econ": "ECON",
    "economics": "ECON",
    "psych": "PSYCH",
    "psychology": "PSYCH",
    "engl": "ENGL",
    "english": "ENGL",
    "hist": "HIST",
    "history": "HIST",
    "phil": "PHIL",
    "philosophy": "PHIL",
    "stat": "STAT",
    "statistics": "STAT",
    "art": "ART",
    "mus": "MUS",
    "music": "MUS",
}


def parse_query(text: str) -> ParsedQuery:
    """Extract filters and intent from a natural language query."""
    t = text.strip().lower()
    out = ParsedQuery()

    # "prereq(s) / prerequisite(s) for CS102" / "what are the prerequisites for MATH101"
    prereq_match = re.search(
        r"prereq(?:s|uisite|uisites)?\s+for\s+([A-Za-z]+\s*\d+)",
        text,
        re.IGNORECASE,
    )
    if not prereq_match:
        prereq_match = re.search(
            r"(?:what\s+are\s+)?(?:the\s+)?prereq(?:s|uisite|uisites)?\s+(?:of|for)\s*([A-Za-z]+\s*\d+)",
            text,
            re.IGNORECASE,
        )
    if prereq_match:
        out.prerequisite_for_code = prereq_match.group(1).strip().upper().replace(" ", "")
        return out  # Single intent: return prereqs for this course

    # N credit(s) — e.g. "3 credit", "0.5-credit", "3-credit"
    credit_match = re.search(r"(\d+(?:\.\d+)?)\s*\-?\s*credit[s]?", t)
    if credit_match:
        out.credits = float(credit_match.group(1))
        if out.credits > 30 or out.credits < 0:
            out.credits = None

    # No prerequisites / without prerequisites / courses with no prereqs
    if re.search(r"\bno\s+prerequisite|\bwithout\s+prerequisite|\bwith\s+no\s+prerequisite|no\s+prereq", t):
        out.has_prerequisites = False
    if re.search(r"\bcourses?\s+with\s+no\s+prerequisite|courses?\s+that\s+have\s+no\s+prerequisite", t):
        out.has_prerequisites = False

    # Department: "CS courses", "computer science", "math department", "show me EE"
    for alias, code in DEPARTMENT_ALIASES.items():
        # Prefer whole-word or followed by "course(s)" or "department"
        if re.search(rf"\b{re.escape(alias)}\b", t):
            out.department = code
            break

    # If no structured filters were found, treat the whole query as keyword search
    if out.department is None and out.credits is None and out.has_prerequisites is None:
        if len(t) >= 2:
            out.search_keywords = text.strip()

    return out
