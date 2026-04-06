"""
Checkpoint 3: retrieval-augmented generation — retrieve courses, build prompts, call OpenAI.
"""
import json
import os
from typing import List, Optional, Tuple

from dotenv import load_dotenv

from . import db
from . import query_parser

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """You are CourseBot, an assistant for a university course catalog (demo data).

Rules (follow strictly):
- Answer ONLY using information in the COURSE DATA block below. It is the only authoritative source for this turn.
- If COURSE DATA is empty or does not contain the answer, say no matching courses were found or that you cannot answer from the catalog. Suggest trying another department, keyword, or filter. Do NOT invent course codes, titles, credits, departments, professors, or prerequisites.
- If the user asks about topics unrelated to this catalog (e.g. weather, jokes, personal advice), say you only help with course information from the provided data.
- Be concise. Use short paragraphs or bullet lists when listing multiple courses.
- When you name a course from COURSE DATA, include its professor field when present (e.g. who teaches the section).
"""


def retrieve_courses(user_message: str) -> List[db.CourseRow]:
    """Parse the message and return matching course rows from SQLite."""
    msg = user_message.strip()
    parsed = query_parser.parse_query(msg)

    if parsed.prerequisite_for_code:
        course = db.get_course_by_code(parsed.prerequisite_for_code)
        if not course:
            return []

        # Include the asked course plus concrete prerequisite course rows
        # so the UI can show what is required, not only the target course.
        rows: List[db.CourseRow] = [course]
        seen_codes = {course["course_code"].strip().upper()}
        for prereq_code in course["prerequisites"]:
            prereq = db.get_course_by_code(prereq_code)
            if not prereq:
                continue
            key = prereq["course_code"].strip().upper()
            if key in seen_codes:
                continue
            seen_codes.add(key)
            rows.append(prereq)
        return rows

    if parsed.search_keywords and not parsed.department and not parsed.credits and parsed.has_prerequisites is None:
        return db.search_courses(parsed.search_keywords)

    return db.get_all_courses_with_prereqs(
        department=parsed.department,
        credits=parsed.credits,
        has_prerequisites=parsed.has_prerequisites,
    )


def format_context_block(rows: List[db.CourseRow]) -> str:
    if not rows:
        return "(no courses matched — COURSE DATA is empty)"
    payload = [
        {
            "course_code": r["course_code"],
            "title": r["title"],
            "description": r["description"],
            "credits": r["credits"],
            "department": r["department"],
            "professor": r["professor"],
            "prerequisites": r["prerequisites"],
        }
        for r in rows
    ]
    return json.dumps(payload, indent=2)


def build_user_prompt(user_message: str, context_block: str) -> str:
    return (
        "COURSE DATA (authoritative; do not contradict or extend beyond this):\n"
        f"{context_block}\n\n"
        f"User question:\n{user_message.strip()}"
    )


def generate_rag_reply(user_message: str, rows: List[db.CourseRow]) -> Tuple[str, Optional[str]]:
    """
    Returns (assistant_text, error_message). error_message is None on success.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return "", "OPENAI_API_KEY is not set"

    context_block = format_context_block(rows)
    user_prompt = build_user_prompt(user_message, context_block)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            return "", "Empty response from model"
        return content.strip(), None
    except Exception as exc:
        return "", str(exc)
