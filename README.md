## CourseBot – Checkpoint 1 Backend

This repository contains the initial backend implementation for **CourseBot**, an AI-powered academic course assistant. Checkpoint 1 focuses on:

- **System architecture definition**
- **SQLite database schema for courses and prerequisites**
- **FastAPI backend skeleton with basic endpoints**

### Architecture Overview

- **Frontend**: Web-based chat interface (HTML/CSS/JavaScript) – to be implemented in later checkpoints.
- **Backend API (FastAPI)**:
  - Exposes RESTful endpoints for inserting and retrieving courses.
  - Will later host retrieval logic and RAG/LLM integration.
- **Database (SQLite)**:
  - `courses` table: core course attributes.
  - `prerequisites` table: prerequisite relationships by course code.
- **Retrieval Layer (planned)**:
  - Keyword and embedding-based search over course records.
- **LLM Layer (planned)**:
  - Retrieval-Augmented Generation using OpenAI (or compatible) APIs.

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

- **Table: `courses`**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `course_code` TEXT NOT NULL UNIQUE
  - `title` TEXT NOT NULL
  - `description` TEXT NOT NULL
  - `credits` INTEGER NOT NULL
  - `department` TEXT NOT NULL

- **Table: `prerequisites`**
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `course_id` INTEGER NOT NULL (FK → `courses.id`, ON DELETE CASCADE)
  - `prerequisite_code` TEXT NOT NULL

Tables are created automatically on application startup.

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

