## CourseBot – Academic Course Assistant Backend

This repository contains the backend implementation for **CourseBot**, an AI-powered academic course assistant.

- **Checkpoint 1**: System architecture, SQLite schema, basic endpoints (insert, list, search).
- **Checkpoint 2**: Filtered queries (credits, department, no-prerequisites), prerequisites endpoint, case-insensitive search, seed data.

### Architecture Overview

- **Frontend**: Web-based chat interface (HTML/CSS/JavaScript) – to be implemented in later checkpoints.
- **Backend API (FastAPI)**:
  - REST endpoints for courses and `POST /chat` (retrieval + optional OpenAI RAG).
- **Database (SQLite)**:
  - `courses` and `prerequisites` tables.
- **Retrieval layer**:
  - Rule-based parsing → filtered SQL / keyword search (`app/query_parser.py`, `app/db.py`).
- **LLM layer (Checkpoint 3)**:
  - RAG in `app/rag.py`: retrieved rows as JSON context + structured system prompt → OpenAI Chat Completions.

### Running the Backend (Checkpoint 1)

1. **Install dependencies** (preferably in a virtual environment):

```bash
pip install -r requirements.txt
```

2. **Run the development server**:

```bash
uvicorn app.main:app --reload
```

3. **Open the interactive docs** in a browser:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### Database Schema (Checkpoint 1)

- **Table: `professors`**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `name` TEXT NOT NULL UNIQUE

- **Table: `courses`**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `course_code` TEXT NOT NULL UNIQUE
  - `title` TEXT NOT NULL
  - `description` TEXT NOT NULL
  - `credits` REAL NOT NULL (supports fractional credits, e.g. `0.5`)
  - `department` TEXT NOT NULL
  - `professor_id` INTEGER NULL (FK → `professors.id`)

- **Table: `prerequisites`**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `course_id` INTEGER NOT NULL (FK → `courses.id`, ON DELETE CASCADE)
  - `prerequisite_code` TEXT NOT NULL

Tables and migrations (e.g. adding `professor_id`) run automatically on application startup.

**Seed data** ([`scripts/seed_courses.py`](scripts/seed_courses.py)): 60 courses including **0.5-credit** seminars/workshops. Each course row gets a **`professor`** name (deterministic random `"Dr. First Last"` names); the same name is reused for blocks of **3** courses so each instructor teaches 1–3 classes. If you already seeded an older catalog, remove `coursebot.db` and run `python -m scripts.seed_courses` again.

### Key Endpoints for Checkpoint 1 Demo

- **Health check**
  - `GET /health` – simple `"status": "ok"` response.

- **Insert a new course**
  - `POST /courses`
  - Request body includes `course_code`, `title`, `description`, `credits`, `department`, and optional `prerequisites` list.
  - Demonstrates successful insertion and returns the created course with prerequisites.
  - Duplicate course codes return **400 Bad Request** (invalid query example).

- **Retrieve all courses**
  - `GET /courses`
  - Optional `department` query parameter to filter by department.

- **Search courses (for empty and invalid queries)**
  - `GET /courses/search?q=...`
  - Case-insensitive keyword search over code, title, and description.
  - Empty `q` returns **400 Bad Request** (invalid query handling).
  - No matches return an empty list `[]` (empty-result handling).

You can use Swagger UI to drive the entire Checkpoint 1 demonstration:

- Show schema via the `README` and DB description above.
- Demonstrate **inserting** a course with `POST /courses`.
- Demonstrate **retrieving all** courses with `GET /courses`.
- Demonstrate **invalid queries** and **empty results** using `GET /courses/search`.

---

### Checkpoint 2: Filtered Queries and Seed Data

**Seed the database** (run once from project root; safe to re-run, skips existing courses):

```bash
python -m scripts.seed_courses
```

This adds 50+ sample courses across CS, MATH, EE, PHYS, CHEM, BIO, ECON, PSYCH, ENGL, HIST, PHIL, STAT, ART, MUS with realistic prerequisites.

**Checkpoint 2 demo endpoints**

- **Natural-language-style filtered queries**
  - *"Show 3-credit CS courses"* → `GET /courses?department=CS&credits=3`
  - *"Courses with no prerequisites"* → `GET /courses?has_prerequisites=false`
  - *"4-credit MATH courses"* → `GET /courses?department=MATH&credits=4`
- **Case-insensitive matching**: `GET /courses?department=cs` and `GET /courses?department=CS` return the same; `GET /courses/search?q=calculus` matches "Calculus" in titles.
- **Prerequisites for a selected course**: `GET /courses/{course_id}/prerequisites` returns `{"course_code": "CS102", "prerequisites": ["CS101"]}` (structured JSON).
- **Structured JSON**: All responses are JSON; use Swagger UI or browser to show response shape.
- **Complex filtering**: Combine `department`, `credits`, and `has_prerequisites` in one request, e.g. `GET /courses?department=CS&credits=3&has_prerequisites=true`.

---

### Checkpoint 3: RAG (OpenAI) and chat UI

1. **Environment** — copy [`.env.example`](.env.example) to `.env` and set `OPENAI_API_KEY`. Optional: `OPENAI_MODEL` (default `gpt-4o-mini`).

2. **Install** — `pip install -r requirements.txt` (includes `openai`).

3. **Flow** — User message → `parse_query` → SQLite retrieval → JSON **COURSE DATA** block + **system prompt** (in `app/rag.py`) → model → natural-language `reply`. Response always includes `courses` (retrieved rows) for transparency.

4. **`POST /chat` body**
   - `message` (required)
   - `use_llm` (default `true`) — if `false`, rule-based reply only
   - `include_rag_debug` (default `false`) — if `true`, response includes `rag_debug`: full system prompt and user message sent to the model (for demos / Swagger)

5. **Response fields** — `reply`, `courses`, `rag_used`, `model`, `llm_error` (set when the key is present but the API call fails; app falls back to rule-based text), optional `rag_debug`.

6. **Frontend** — Open [http://127.0.0.1:8000](http://127.0.0.1:8000) for the chat page (async `fetch` to `/chat`). Use toggles for “Use AI answer” and “Show prompt debug (demo)”.

