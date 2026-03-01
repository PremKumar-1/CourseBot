from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from . import db


class CourseCreate(BaseModel):
    course_code: str = Field(..., example="CS101")
    title: str = Field(..., example="Introduction to Computer Science")
    description: str = Field(..., example="Fundamentals of programming and computer science.")
    credits: int = Field(..., ge=0, le=10, example=3)
    department: str = Field(..., example="CS")
    prerequisites: Optional[List[str]] = Field(
        default=None,
        description="List of prerequisite course codes, e.g. ['MATH101']",
    )


class Course(BaseModel):
    id: int
    course_code: str
    title: str
    description: str
    credits: int
    department: str
    prerequisites: List[str]


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
    db.init_db()


@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok"}


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
        description="Optional department code filter, e.g. 'CS'",
    )
) -> List[Course]:
    rows = db.get_all_courses_with_prereqs(department=department)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

