## CourseBot – Academic Course Assistant Backend

This repository contains the backend implementation for **CourseBot**, an AI-powered academic course assistant.

- **Checkpoint 1**: System architecture, SQLite schema, basic endpoints (insert, list, search).
- **Checkpoint 2**: Filtered queries (credits, department, no-prerequisites), prerequisites endpoint, case-insensitive search, seed data.
- **Checkpoint 3**: Chat UI at `/`, `POST /chat` with optional OpenAI RAG, professors on course rows.

### Architecture Overview

- **Frontend**: Web-based chat interface ([`static/index.html`](static/index.html)) served at **`/`** (async `fetch` to `/chat`).
- **Backend API (FastAPI)**:
  - REST endpoints for courses and `POST /chat` (retrieval + optional OpenAI RAG).
- **Database (SQLite)**:
  - `courses` and `prerequisites` tables.
- **Retrieval layer**:
  - Rule-based parsing → filtered SQL / keyword search (`app/query_parser.py`, `app/db.py`).
- **LLM layer (Checkpoint 3)**:
  - RAG in `app/rag.py`: retrieved rows as JSON context + structured system prompt → OpenAI Chat Completions.

### Running the backend

1. **Install dependencies** (preferably in a virtual environment):

```bash
pip install -r requirements.txt
```

2. **Optional: OpenAI RAG** — copy [`.env.example`](.env.example) to `.env`, set `OPENAI_API_KEY`, and optionally `OPENAI_MODEL`. **Never put a real API key in `.env.example` or commit `.env`** (`.env` is listed in [`.gitignore`](.gitignore)).

3. **Seed the catalog** (recommended before trying the chat):

```bash
python -m scripts.seed_courses
```

4. **Run the development server**:

```bash
uvicorn app.main:app --reload
```

5. **Open in a browser**:

- Chat UI: `http://127.0.0.1:8000/`
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

**Seed data** ([`scripts/seed_courses.py`](scripts/seed_courses.py)): **54** sample courses across CS, MATH, EE, PHYS, CHEM, BIO, ECON, PSYCH, ENGL, HIST, PHIL, STAT, ART, and MUS with realistic prerequisites. Each row may include an optional **`professor`** string; the script creates/links `professors` rows and sets `courses.professor_id`. **Re-running the seed** inserts any missing courses and **updates instructors** for codes that already exist (so you usually do not need to delete `coursebot.db` just to refresh professors). Credits are stored as **REAL** (e.g. `0.5` or `3`) if you extend the seed list.

### Key Endpoints for Checkpoint 1 Demo

- **Health check**
  - `GET /health` – simple `"status": "ok"` response.

- **Insert a new course**
  - `POST /courses`
  - Request body includes `course_code`, `title`, `description`, `credits`, `department`, optional `prerequisites`, and optional `professor_id`.
  - Demonstrates successful insertion and returns the created course with prerequisites.
  - Duplicate course codes return **400 Bad Request** (invalid query example).

- **List / filter courses**
  - `GET /courses`
  - Optional query parameters: `department`, `credits`, `has_prerequisites` (combine as needed, e.g. `?department=CS&credits=1`).

- **Search courses (for empty and invalid queries)**
  - `GET /courses/search?q=...`
  - Case-insensitive keyword search over course code, title, description, and **instructor name**.
  - Empty `q` returns **400 Bad Request** (invalid query handling).
  - No matches return an empty list `[]` (empty-result handling).

You can use Swagger UI to drive the entire Checkpoint 1 demonstration:

- Show schema via the `README` and DB description above.
- Demonstrate **inserting** a course with `POST /courses`.
- Demonstrate **retrieving all** courses with `GET /courses`.
- Demonstrate **invalid queries** and **empty results** using `GET /courses/search`.

---

### Checkpoint 2: Filtered Queries and Seed Data

**Seed the database** (from project root; safe to re-run: new codes are inserted, existing codes get **professor** updates from the seed list):

```bash
python -m scripts.seed_courses
```

This loads the **54** courses defined in the seed script (see above).

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

1. **Environment** — copy [`.env.example`](.env.example) to `.env`, add your real `OPENAI_API_KEY`, and optionally `OPENAI_MODEL` (default `gpt-4o-mini`). Keep secrets only in `.env`; **commit `.env.example` with empty placeholders, not real keys.**

2. **Dependencies** — `pip install -r requirements.txt` (includes `openai`).

3. **Flow** — User message → `parse_query` (`app/query_parser.py`) → SQLite retrieval (`app/rag.py` + `app/db.py`) → JSON **COURSE DATA** block + **system prompt** → optional OpenAI Chat Completions → natural-language `reply`. Every response includes **`courses`** (the retrieved rows, including `professor` when set) for transparency.

4. **Prerequisite questions** — Messages like “prerequisites for CS102” resolve to the target course **plus** rows for each prerequisite course so the UI can show what is required, not only the course code list.

5. **`POST /chat` body**
   - `message` (required)
   - `use_llm` (default `true`) — if `false`, rule-based reply only
   - `include_rag_debug` (default `false`) — if `true`, response includes `rag_debug`: full system prompt and user message sent to the model (for demos / Swagger)

6. **Response fields** — `reply`, `courses`, `rag_used`, `model`, `llm_error` (set when the key is present but the API call fails; app falls back to rule-based text), optional `rag_debug`.

7. **Frontend** — Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the chat page. Use toggles for “AI answer (RAG)” and “Show prompt debug”.

---

### Deploying to Vercel (and similar serverless)

Vercel discovers FastAPI at certain filenames only (see [Vercel’s FastAPI docs](https://vercel.com/docs/frameworks/backend/fastapi)). This project defines the app in [`app/main.py`](app/main.py) and re-exports it from [`app/index.py`](app/index.py) so the platform can find the `app` instance.

- **Set environment variables** in the Vercel project: at least `OPENAI_API_KEY` (and `OPENAI_MODEL` if you want a non-default model). Vercel sets `VERCEL=1` automatically.
- **SQLite** — On Vercel the deploy bundle is not a reliable place to *write* a database file. When `VERCEL=1`, the app uses `/tmp/coursebot.db` by default. That location can be **empty or reset** across cold starts; run [`scripts/seed_courses.py`](scripts/seed_courses.py) locally, commit a **separate** strategy for production (hosted SQL), or use an external store if you need **durable** data.
- **Optional** — `COURSEBOT_SQLITE_PATH` overrides the database file path (see [`.env.example`](.env.example)).
- If you still see **`FUNCTION_INVOCATION_FAILED`**, open **Vercel → your deployment → Logs**; the *nested* error (import error, timeout, `readonly database`, etc.) is what you need to fix.

