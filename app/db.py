import os
import sqlite3
from pathlib import Path
from typing import Iterable, List, Optional, TypedDict


BASE_DIR = Path(__file__).resolve().parent.parent


def _is_writable_db_path(path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8"):
            pass
        return True
    except OSError:
        return False


def _resolve_db_path() -> Path:
    """
    Local dev: project root `coursebot.db`. Serverless (e.g. Vercel): project
    tree is read-only, so use /tmp. Override with COURSEBOT_SQLITE_PATH.
    """
    override = os.environ.get("COURSEBOT_SQLITE_PATH", "").strip()
    if override:
        override_path = Path(override)
        if _is_writable_db_path(override_path):
            return override_path
    default_path = BASE_DIR / "coursebot.db"
    if os.environ.get("VERCEL", "").lower() in ("1", "true", "yes"):
        default_path = Path("/tmp/coursebot.db")
    if _is_writable_db_path(default_path):
        return default_path
    return Path("/tmp/coursebot.db")


DB_PATH = _resolve_db_path()


class CourseRow(TypedDict):
    id: int
    course_code: str
    title: str
    description: str
    credits: float
    department: str
    prerequisites: List[str]
    professor: Optional[str]


class CourseAlreadyExistsError(Exception):
    pass


def get_connection() -> sqlite3.Connection:
    def _open(path: Path) -> sqlite3.Connection:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        # Enforce foreign-key constraints
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    global DB_PATH
    primary_path = _resolve_db_path()
    DB_PATH = primary_path
    try:
        return _open(primary_path)
    except (sqlite3.OperationalError, OSError):
        # Serverless fallback: if configured/default path cannot be opened
        # (read-only bundle, missing dir, etc.), use writable /tmp.
        fallback = Path("/tmp/coursebot.db")
        if primary_path == fallback:
            raise
        DB_PATH = fallback
        return _open(fallback)


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

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS professors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """
        )

        cursor.execute("PRAGMA table_info(courses)")
        course_cols = [row[1] for row in cursor.fetchall()]
        if "professor_id" not in course_cols:
            cursor.execute(
                """
                ALTER TABLE courses ADD COLUMN professor_id INTEGER
                REFERENCES professors(id);
                """
            )

        conn.commit()


def count_courses() -> int:
    """Return total number of courses currently stored."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM courses;")
        row = cursor.fetchone()
        return int(row[0]) if row else 0


def get_or_create_professor(name: str) -> int:
    """Return professor id for name, inserting if needed."""
    clean = name.strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM professors WHERE name = ?", (clean,))
        row = cursor.fetchone()
        if row:
            return int(row[0])
        cursor.execute("INSERT INTO professors (name) VALUES (?)", (clean,))
        conn.commit()
        return int(cursor.lastrowid)


def insert_course(
    course_code: str,
    title: str,
    description: str,
    credits: float,
    department: str,
    prerequisites: Iterable[str],
    professor_id: Optional[int] = None,
) -> int:
    """Insert a new course and its prerequisites; returns the new course id."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Ensure course_code uniqueness is handled clearly
        try:
            cursor.execute(
                """
                INSERT INTO courses (course_code, title, description, credits, department, professor_id)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (course_code, title, description, credits, department, professor_id),
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


def set_course_professor(course_id: int, professor_id: Optional[int]) -> None:
    """Set or clear courses.professor_id (use None to clear)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE courses SET professor_id = ? WHERE id = ?",
            (professor_id, course_id),
        )
        conn.commit()


def _rows_to_course_rows(rows: List[sqlite3.Row]) -> List[CourseRow]:
    """Convert denormalized join rows into aggregated CourseRow objects."""
    by_id: dict[int, CourseRow] = {}
    for row in rows:
        course_id = row["id"]
        if course_id not in by_id:
            prof = row["professor"] if "professor" in row.keys() and row["professor"] else None
            cr = row["credits"]
            credits_val: float = float(cr) if cr is not None else 0.0
            by_id[course_id] = CourseRow(
                id=course_id,
                course_code=row["course_code"],
                title=row["title"],
                description=row["description"],
                credits=credits_val,
                department=row["department"],
                prerequisites=[],
                professor=prof,
            )
        prereq_code = row["prerequisite_code"]
        if prereq_code is not None and prereq_code not in by_id[course_id]["prerequisites"]:
            by_id[course_id]["prerequisites"].append(prereq_code)
    return list(by_id.values())


def get_all_courses_with_prereqs(
    department: Optional[str] = None,
    credits: Optional[int] = None,
    has_prerequisites: Optional[bool] = None,
) -> List[CourseRow]:
    """Get all courses with optional filters. Case-insensitive department match."""
    with get_connection() as conn:
        cursor = conn.cursor()
        conditions: List[str] = []
        params: List[object] = []

        if department is not None and department.strip():
            conditions.append("LOWER(TRIM(c.department)) = LOWER(TRIM(?))")
            params.append(department.strip())
        if credits is not None:
            conditions.append("c.credits = ?")
            params.append(credits)
        if has_prerequisites is not None:
            if has_prerequisites:
                conditions.append(
                    "EXISTS (SELECT 1 FROM prerequisites p2 WHERE p2.course_id = c.id)"
                )
            else:
                conditions.append(
                    "NOT EXISTS (SELECT 1 FROM prerequisites p2 WHERE p2.course_id = c.id)"
                )

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        cursor.execute(
            f"""
            SELECT c.id,
                   c.course_code,
                   c.title,
                   c.description,
                   c.credits,
                   c.department,
                   pf.name AS professor,
                   p.prerequisite_code
            FROM courses c
            LEFT JOIN professors pf ON c.professor_id = pf.id
            LEFT JOIN prerequisites p ON c.id = p.course_id
            WHERE {where_clause}
            ORDER BY c.course_code;
            """,
            tuple(params),
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
                   pf.name AS professor,
                   p.prerequisite_code
            FROM courses c
            LEFT JOIN professors pf ON c.professor_id = pf.id
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


def get_course_by_code(course_code: str) -> Optional[CourseRow]:
    """Look up a course by course_code (case-insensitive). Returns same shape as get_course_with_prereqs."""
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
                   pf.name AS professor,
                   p.prerequisite_code
            FROM courses c
            LEFT JOIN professors pf ON c.professor_id = pf.id
            LEFT JOIN prerequisites p ON c.id = p.course_id
            WHERE LOWER(TRIM(c.course_code)) = LOWER(TRIM(?))
            ORDER BY c.course_code;
            """,
            (course_code.strip(),),
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
                   pf.name AS professor,
                   p.prerequisite_code
            FROM courses c
            LEFT JOIN professors pf ON c.professor_id = pf.id
            LEFT JOIN prerequisites p ON c.id = p.course_id
            WHERE LOWER(c.course_code) LIKE LOWER(?)
               OR LOWER(c.title) LIKE LOWER(?)
               OR LOWER(c.description) LIKE LOWER(?)
               OR LOWER(IFNULL(pf.name, '')) LIKE LOWER(?)
            ORDER BY c.course_code;
            """,
            (like_pattern, like_pattern, like_pattern, like_pattern),
        )
        rows = cursor.fetchall()
        return _rows_to_course_rows(rows)

