# AutoClean-ML 🚀

**Autonomous Data Cleaning & Feature Engineering System**

[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![React](https://img.shields.io/badge/React-Next.js_14-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Celery](https://img.shields.io/badge/Celery-Distributed_Workers-lightgreen.svg)](https://docs.celeryq.dev/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

A production-grade, autonomous machine learning pipeline capable of taking raw tabular data, intelligently profiling it, imputing missing values, engineering novel features, and training a baseline LightGBM model without human intervention. 

Built using a microservices architecture to ensure high throughput, reliability, and clear separation of concerns spanning the ETL and modeling lifecycle.

---

## 🏗️ Architecture

The system utilizes an enterprise-grade stack spanning five core orchestrated containers (`docker-compose`):

1.  **Frontend (Next.js 14 App Router):** 
    *   TypeScript, React Server Components.
    *   Tailwind CSS, Framer Motion, and shadcn/UI for a glassmorphic aesthetic.
    *   Zustand for client-side state predictability.
    *   Server-Sent Events (SSE) for interactive real-time pipeline status monitoring.
2.  **API Gateway (FastAPI):**
    *   Asynchronous REST endpoints powered by Uvicorn.
    *   Pydantic v2 schemas for robust data validation.
    *   SQLAlchemy 2.0 (`asyncpg`) for non-blocking database I/O.
3.  **Background Worker (Celery + Redis):**
    *   Handles CPU-intensive Pandas/scikit-learn data transformations asynchronously to prevent API timeouts.
4.  **Database (PostgreSQL 16):**
    *   A fully normalized relational schema storing datasets, rigorous audit logs of all transformations, pipeline execution metrics, and generated features.
5.  **Message Broker (Redis 7):**
    *   In-memory datastore mediating task queues between the FastAPI instances and Celery workers.

---

## 🧠 Autonomous Pipeline Engine (Domain-Driven Design)

The core data science engine is broken down into four pure, testable domain services:

1.  **Data Profiling:** Evaluates dimensional metrics, column types, categorical cardinality, and missingness ratios.
2.  **Cleaner:** Automatically isolates natural text/IDs, applies median (numerical) or mode (categorical) imputation, and caps statistical outliers via Interquartile Range (IQR).
3.  **Feature Engineering:** Extracts temporal structures from dates, applies One-Hot Encoding to low-cardinality features, and implements Frequency Encoding for high-cardinality values. Removes zero-variance attributes.
4.  **Modeling:** Auto-detects Regression vs. Classification based on the selected target, trains a LightGBM default architecture, and logs F1, Accuracy, Log Loss, R², and the resulting test Confusion Matrix.

---

## 🚀 Quickstart Guide

Because the application leverages Linux-based dependencies like Celery and Redis, running natively on Windows can be challenging. The framework is 100% Docker-native.

### Prerequisites
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Ensure the Docker engine is running).

### Running the System
1. Clone the repository and navigate to the root directory.
2. Build and start the infrastructure in detached mode:
   ```bash
   docker compose up --build -d
   ```
3. Once the containers are healthy, access the web UI:
   *   **Dashboard:** `http://localhost:3000`
   *   **API Swagger Docs:** `http://localhost:8000/docs`

### Testing the Pipeline
1. Open the Dashboard.
2. Drag and drop the provided `sample_titanic.csv` into the upload zone.
3. Select `Survived` as the Target Variable.
4. Click **Run Autonomous Pipeline**.
5. Watch the real-time SSE stepper move through Profiling, Cleaning, Engineering, and Training.
6. Verify the interactive Confusion Matrix, Feature Importances, and chronological Transformation Audit Log.

---

## 🧪 Development & Testing

We utilize native `pytest` for the Python Domain logic and Vitest/Playwright for the user interfaces. Let's run the backend test suite locally:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/
```

All 12 backend unit tests isolating the data manipulation logic run deterministically.

---

## 💡 Repository Naming Suggestions

If you are pushing this to GitHub, the following concise names accurately summarize the system architecture:
- `AutoClean-ML` (Recommended)
- `Autonomous-Data-Forge`
- `AutoData-Pipeline`
- `ETL-Autopilot`
