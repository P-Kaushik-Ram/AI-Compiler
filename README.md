# AI Compiler

> A deterministic multi-stage AI System Compiler that transforms natural language requirements into validated system architectures, database schemas, and structured intermediate representations.

**Status:** Complete MVP

---

## Overview

AI Compiler is a full-stack software engineering project that demonstrates how natural language system requirements can be transformed into structured software design artifacts through a deterministic compiler pipeline.

Unlike LLM-based approaches, this project uses a rule-driven architecture where every compilation stage is transparent, testable, and reproducible.

The compiler accepts a plain-English system description and executes a sequence of compiler stages:

```
Natural Language
       │
       ▼
Intent Extraction
       │
       ▼
System Design
       │
       ▼
Schema Generation
       │
       ▼
Validation
       │
       ▼
Compilation Result
```

A React frontend provides an interactive interface for compiling prompts, visualizing every stage of the pipeline, and benchmarking multiple datasets through a built-in evaluation dashboard.

---

## Features

### Backend

* Deterministic Intent Extraction engine
* System Design generation
* Database Schema generation
* Cross-stage Validation Engine
* Runtime orchestration
* Streaming Evaluation Framework
* REST API built with FastAPI
* Strongly typed Pydantic models

### Frontend

* Interactive Compile interface
* Live pipeline visualization
* Stage-by-stage result viewer
* Evaluation dashboard
* TypeScript throughout
* Zustand state management
* Responsive dark UI

### Quality

* 102 backend tests
* 62 frontend tests
* 164 automated tests
* Layered architecture
* Modular compiler stages
* Fully typed frontend

---

## Compiler Pipeline

### Stage 1 — Intent Extraction

Transforms natural language into a structured Intent IR.

Extracts:

* entities
* actions
* relationships
* risks
* confidence

---

### Stage 2 — System Design

Builds an architectural model from the Intent IR.

Generates:

* modules
* workflows
* capabilities
* actors
* dependencies

---

### Stage 3 — Schema Generation

Produces a normalized database schema.

Generates:

* entities
* fields
* primary keys
* foreign keys
* relationships
* constraints

---

### Stage 4 — Validation

Performs cross-stage consistency checking.

Detects:

* orphan relationships
* naming conflicts
* traceability failures
* propagated risks
* schema inconsistencies

Produces one of:

* Proceed
* Proceed with Warnings
* Halt

---

## Evaluation Framework

The evaluation framework benchmarks the compiler across multiple datasets.

Supports:

* CRM systems
* Healthcare systems
* Mixed domain prompts
* Custom datasets

Reports:

* Success rate
* Validation rate
* Confidence statistics
* Runtime statistics
* Failure categories

---

## Technology Stack

| Layer      | Technology      |
| ---------- | --------------- |
| Backend    | Python 3.11     |
| API        | FastAPI         |
| Models     | Pydantic v2     |
| Frontend   | React 18        |
| Build Tool | Vite            |
| Language   | TypeScript      |
| State      | Zustand         |
| Testing    | pytest + Vitest |

---

## Project Structure

```
backend/
    app/
        api/
        services/
        models/
        schemas/

frontend/
    src/
        api/
        components/
        pages/
        store/
        styles/
        types/

tests/
    backend/
    frontend/

docs/

evaluation/
```

---

## Screenshots

### Compile Interface

> *Add screenshot here*

### Pipeline Visualization

> *Add screenshot here*

### Evaluation Dashboard

> *Add screenshot here*

---

## Running Locally

### Backend

```bash
pip install -r requirements.txt

set PYTHONPATH=backend

python -m uvicorn app.main:app --reload
```

Backend runs at:

```
http://localhost:8000
```

---

### Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs at:

```
http://localhost:5173
```

---

## Running Tests

### Backend

```bash
pytest
```

### Frontend

```bash
cd frontend

npm test -- --run
```

Current project status:

* Backend: 102 tests passing
* Frontend: 62 tests passing

Total:

**164 automated tests**

---

## Example Prompt

```
Build a CRM where users can sign up, log in, and manage their own contacts and leads through a sales pipeline.
```

The compiler produces:

* Intent IR
* System Design
* Database Schema
* Validation Report

---

## Future Improvements

* LLM-assisted compiler mode
* Architecture diagram generation
* SQL generation
* Code generation
* Cloud deployment
* Docker support
* Authentication
* Persistent compile history

---

## License

MIT License
