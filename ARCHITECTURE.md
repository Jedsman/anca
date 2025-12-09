# ANCA Architecture & Execution Flow

## 🔄 Execution Models

ANCA can run in two distinct modes. Here is how they differ:

### 1. Local Execution (CLI)
**Command:** `python run_crew.py`

*   **Entry Point:** The `if __name__ == "__main__":` block in `run_crew.py`.
*   **Trigger:** Manual execution in the terminal.
*   **Flow:** Directly instantiates `Crew` → calls `crew.kickoff()`.
*   **Output:** Streams directly to your terminal (stdout).
*   **File Handling:** Writes files directly to the `./articles` folder on your hard drive.

### 2. Docker Execution (API)
**Command:** `docker-compose up`

*   **Entry Point:** `app.main:app` (FastAPI) via `uvicorn`.
*   **Trigger:** HTTP POST request to `/api/v1/generate`.
*   **Flow:**
    1.  **API Layer:** `app/api/routers/generation.py` receives the request.
    2.  **Service Layer:** `app/services/job_service.py` is called.
    3.  **Background Task:** `job_service.run_job()` runs asynchronously.
    4.  **Crew Invocation:** The service imports `crew` from `run_crew.py` (as a module) and calls `crew.kickoff()`.
*   **Output:**
    *   **Logs:** The "printing" happens inside the container logs (`docker logs anca-api`).
    *   **Function Result:** The return value is captured in memory and returned via the `/status/{job_id}` endpoint.
*   **File Handling:**
    *   The code still writes to `./articles` (relative to the app root in the container).
    *   **Critical Mechanism:** `docker-compose.yml` maps your local folder to the container's folder:
        ```yaml
        volumes:
          - ./articles:/app/articles
        ```
    *   This "bind mount" means when the container writes a file to `/app/articles`, it magically appears in your local `articles` folder.

## 📁 Directory Structure
```
anca/
├── app/                 # FastAPI Application
│   ├── main.py          # App Entry point
│   └── services/        # Logic that calls the Crew
├── run_crew.py          # The Core Logic (imported by App)
├── Dockerfile.api       # Builds the container image
└── docker-compose.yml   # Maps volumes and ports
```
