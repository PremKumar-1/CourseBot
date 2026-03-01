import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, TypedDict


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "coursebot.db"


class CourseRow(TypedDict):
    id: int
    course_code: str
    title: str
    description: str
    credits: int
    department: str
    prerequisites: List[str]


class CourseAlreadyExistsError(Exception):
    pass


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce foreign-key constraints
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Create tables if they do not already exist."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                credits INTEGER NOT NULL,
                department TEXT NOT NULL
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS prerequisites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                prerequisite_code TEXT NOT NULL,
                FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
            """
        )

        conn.commit()


def insert_course(
    course_code: str,
    title: str,
    description: str,
    credits: int,
    department: str,
    prerequisites: Iterable[str],
) -> int:
    """Insert a new course and its prerequisites; returns the new course id."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Ensure course_code uniqueness is handled clearly
        try:
            cursor.execute(
                """
                INSERT INTO courses (course_code, title, description, credits, department)
                VALUES (?, ?, ?, ?, ?);
                """,
                (course_code, title, description, credits, department),
            )
        except sqlite3.IntegrityError as exc:
            # Likely UNIQUE constraint violation on course_code
            raise CourseAlreadyExistsError(
                f"Course with code '{course_code}' already exists."
            ) from exc

        course_id = cursor.lastrowid

        for prereq in prerequisites:
            prereq_clean = prereq.strip()
            if not prereq_clean:
                continue
            cursor.execute(
                """
                INSERT INTO prerequisites (course_id, prerequisite_code)
                VALUES (?, ?);
                """,
                (course_id, prereq_clean),
            )

        conn.commit()

        return course_id


def _rows_to_course_rows(rows: List[sqlite3.Row]) -> List[CourseRow]:
    """Convert denormalized join rows into aggregated CourseRow objects."""
    by_id: dict[int, CourseRow] = {}
    for row in rows:
        course_id = row["id"]
        if course_id not in by_id:
            by_id[course_id] = CourseRow(
                id=course_id,
                course_code=row["course_code"],
                title=row["title"],
                description=row["description"],
                credits=row["credits"],
                department=row["department"],
                prerequisites=[],
            )
        prereq_code = row["prerequisite_code"]
        if prereq_code is not None and prereq_code not in by_id[course_id]["prerequisites"]:
            by_id[course_id]["prerequisites"].append(prereq_code)
    return list(by_id.values())


def get_all_courses_with_prereqs(
    department: Optional[str] = None,
) -> List[CourseRow]:
    with get_connection() as conn:
        cursor = conn.cursor()

        if department:
            cursor.execute(
                """
                SELECT c.id,
                       c.course_code,
                       c.title,
                       c.description,
                       c.credits,
                       c.department,
                       p.prerequisite_code
                FROM courses c
                LEFT JOIN prerequisites p ON c.id = p.course_id
                WHERE c.department = ?
                ORDER BY c.course_code;
                """,
                (department,),
            )
        else:
            cursor.execute(
                """
                SELECT c.id,
                       c.course_code,
                       c.title,
                       c.description,
                       c.credits,
                       c.department,
                       p.prerequisite_code
                FROM courses c
                LEFT JOIN prerequisites p ON c.id = p.course_id
                ORDER BY c.course_code;
                """
            )

        rows = cursor.fetchall()
        return _rows_to_course_rows(rows)


def get_course_with_prereqs(course_id: int) -> Optional[CourseRow]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.id,
                   c.course_code,
                   c.title,
                   c.description,
                   c.credits,
                   c.department,
                   p.prerequisite_code
            FROM courses c
            LEFT JOIN prerequisites p ON c.id = p.course_id
            WHERE c.id = ?
            ORDER BY c.course_code;
            """,
            (course_id,),
        )
        rows = cursor.fetchall()
        if not rows:
            return None
        return _rows_to_course_rows(rows)[0]


def search_courses(query: str) -> List[CourseRow]:
    """Case-insensitive keyword search in code, title, or description."""
    like_pattern = f"%{query}%"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.id,
                   c.course_code,
                   c.title,
                   c.description,
                   c.credits,
                   c.department,
                   p.prerequisite_code
            FROM courses c
            LEFT JOIN prerequisites p ON c.id = p.course_id
            WHERE LOWER(c.course_code) LIKE LOWER(?)
               OR LOWER(c.title) LIKE LOWER(?)
               OR LOWER(c.description) LIKE LOWER(?)
            ORDER BY c.course_code;
            """,
            (like_pattern, like_pattern, like_pattern),
        )
        rows = cursor.fetchall()
        return _rows_to_course_rows(rows)

