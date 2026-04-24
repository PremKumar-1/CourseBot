import os
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Optional

from . import db
from . import query_parser
from . import rag

APP_BUILD_ID = os.environ.get("APP_BUILD_ID", "local-dev-2026-04-24")


class CourseCreate(BaseModel):
    course_code: str = Field(..., example="CS101")
    title: str = Field(..., example="Introduction to Computer Science")
    description: str = Field(..., example="Fundamentals of programming and computer science.")
    credits: float = Field(..., ge=0, le=30, example=3.0)
    department: str = Field(..., example="CS")
    prerequisites: Optional[List[str]] = Field(
        default=None,
        description="List of prerequisite course codes, e.g. ['MATH101']",
    )
    professor_id: Optional[int] = Field(
        default=None,
        description="Optional FK to professors.id",
    )


class Course(BaseModel):
    id: int
    course_code: str
    title: str
    description: str
    credits: float
    department: str
    prerequisites: List[str]
    professor: Optional[str] = None


app = FastAPI(title="CourseBot Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    try:
        db.init_db()
    except sqlite3.OperationalError:
        # Serverless safety net: if initial DB path is not writable/openable,
        # retry with /tmp which is writable on Vercel.
        os.environ["COURSEBOT_SQLITE_PATH"] = "/tmp/coursebot.db"
        db.DB_PATH = db._resolve_db_path()  # type: ignore[attr-defined]
        db.init_db()


@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok", "build_id": APP_BUILD_ID, "db_path": str(db.DB_PATH)}


@app.post("/courses", response_model=Course, tags=["courses"])
def create_course(payload: CourseCreate) -> Course:
    try:
        course_id = db.insert_course(
            course_code=payload.course_code.strip(),
            title=payload.title.strip(),
            description=payload.description.strip(),
            credits=payload.credits,
            department=payload.department.strip(),
            prerequisites=payload.prerequisites or [],
            professor_id=payload.professor_id,
        )
    except db.CourseAlreadyExistsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    row = db.get_course_with_prereqs(course_id)
    if row is None:
        raise HTTPException(status_code=500, detail="Failed to load created course")

    return Course(**row)


@app.get("/courses", response_model=List[Course], tags=["courses"])
def list_courses(
    department: Optional[str] = Query(
        default=None,
        description="Filter by department (case-insensitive), e.g. 'CS' for 3-credit CS courses combine with credits=3.",
    ),
    credits: Optional[float] = Query(
        default=None,
        ge=0,
        le=30,
        description="Filter by credit value (supports 0.5, 3, etc.).",
    ),
    has_prerequisites: Optional[bool] = Query(
        default=None,
        description="True = only courses that have prerequisites; False = only courses with no prerequisites.",
    ),
) -> List[Course]:
    """List courses with optional filters. Supports complex queries like 3-credit CS courses (department=CS&credits=3) or courses with no prerequisites (has_prerequisites=false)."""
    rows = db.get_all_courses_with_prereqs(
        department=department,
        credits=credits,
        has_prerequisites=has_prerequisites,
    )
    return [Course(**row) for row in rows]


@app.get("/courses/search", response_model=List[Course], tags=["courses"])
def search_courses(
    q: str = Query(
        ...,
        min_length=1,
        description="Keyword(s) to search in course code, title, or description.",
    )
) -> List[Course]:
    q_normalized = q.strip()
    if not q_normalized:
        # Demonstrates explicit invalid query handling
        raise HTTPException(status_code=400, detail="Search query cannot be empty.")

    rows = db.search_courses(q_normalized)
    # Empty list naturally demonstrates empty-result handling
    return [Course(**row) for row in rows]


@app.get("/courses/{course_id}", response_model=Course, tags=["courses"])
def get_course(course_id: int) -> Course:
    row = db.get_course_with_prereqs(course_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return Course(**row)


@app.get("/courses/{course_id}/prerequisites", tags=["courses"])
def get_course_prerequisites(course_id: int) -> dict:
    """Return only the course code and list of prerequisites for a selected course (structured JSON)."""
    row = db.get_course_with_prereqs(course_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found.")
    return {"course_code": row["course_code"], "prerequisites": row["prerequisites"]}


# --- Chatbot: retrieval + optional RAG (OpenAI) ---


def _rule_based_reply(
    msg: str,
    rows: List[db.CourseRow],
    parsed: query_parser.ParsedQuery,
) -> str:
    """Deterministic reply when LLM is off or fails."""
    if parsed.prerequisite_for_code:
        if not rows:
            return (
                f"I couldn't find a course with code '{parsed.prerequisite_for_code}' "
                "in the catalog."
            )
        course = rows[0]
        prereqs = course["prerequisites"]
        prof = course.get("professor")
        prof_note = f" — Instructor: {prof}" if prof else ""
        if not prereqs:
            return (
                f"Course you asked: {course['course_code']} ({course['title']}){prof_note}\n"
                "This course has no prerequisites."
            )
        required_lines = []
        prereq_rows = rows[1:]
        if prereq_rows:
            for r in prereq_rows:
                line = f"- {r['course_code']} ({r['title']})"
                if r.get("professor"):
                    line += f" — Instructor: {r['professor']}"
                required_lines.append(line)
        else:
            required_lines = [f"- {code}" for code in prereqs]
        return (
            f"Course you asked: {course['course_code']} ({course['title']}){prof_note}\n"
            "Here are prerequisite courses required:\n"
            + "\n".join(required_lines)
        )
    if not rows:
        return (
            "No courses match that. Try a department (e.g. CS, MATH), "
            "credit count (e.g. 3-credit courses), or a keyword."
        )
    if len(rows) <= 10:
        lines: List[str] = []
        for r in rows:
            code = r["course_code"]
            title = r["title"]
            prof = r.get("professor")
            if prof:
                lines.append(f"• {code}: {title} — Instructor: {prof}")
            else:
                lines.append(f"• {code}: {title}")
        return "Here is what matched:\n" + "\n".join(lines)
    return (
        f"Found {len(rows)} course(s). Each card below lists the course details; "
        "when an instructor is assigned, their name appears on the card."
    )


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message / question about courses")
    use_llm: bool = Field(
        default=True,
        description="If true and OPENAI_API_KEY is set, generate a reply with the LLM using retrieved courses as context.",
    )
    include_rag_debug: bool = Field(
        default=False,
        description="If true, include system prompt and full user message sent to the model (for demos).",
    )


class RAGDebug(BaseModel):
    system_prompt: str
    user_message_sent_to_model: str
    model: str


class ChatResponse(BaseModel):
    reply: str
    courses: List[Course] = []
    rag_used: bool = False
    model: Optional[str] = None
    llm_error: Optional[str] = None
    rag_debug: Optional[RAGDebug] = None


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(payload: ChatRequest) -> ChatResponse:
    """
    Parse the message, retrieve courses from SQLite, then optionally answer with OpenAI (RAG).
    Falls back to a short rule-based reply if the API key is missing or the model call fails.
    """
    msg = payload.message.strip()
    parsed = query_parser.parse_query(msg)
    rows = rag.retrieve_courses(msg)
    course_models = [Course(**r) for r in rows]

    rag_debug: Optional[RAGDebug] = None
    if payload.include_rag_debug:
        rag_debug = RAGDebug(
            system_prompt=rag.SYSTEM_PROMPT,
            user_message_sent_to_model=rag.build_user_prompt(
                msg, rag.format_context_block(rows)
            ),
            model=rag.OPENAI_MODEL,
        )

    has_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    if payload.use_llm and has_key:
        llm_reply, err = rag.generate_rag_reply(msg, rows)
        if err:
            return ChatResponse(
                reply=_rule_based_reply(msg, rows, parsed),
                courses=course_models,
                rag_used=False,
                model=None,
                llm_error=err,
                rag_debug=rag_debug,
            )
        return ChatResponse(
            reply=llm_reply,
            courses=course_models,
            rag_used=True,
            model=rag.OPENAI_MODEL,
            llm_error=None,
            rag_debug=rag_debug,
        )

    return ChatResponse(
        reply=_rule_based_reply(msg, rows, parsed),
        courses=course_models,
        rag_used=False,
        model=None,
        llm_error=None,
        rag_debug=rag_debug,
    )


# --- Serve chat UI ---
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/", include_in_schema=False)
def serve_chat_ui():
    """Serve the chatbot page at the root."""
    index = STATIC_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Chat UI not found. Create static/index.html.")
    return FileResponse(index)


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

