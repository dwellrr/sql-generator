# SQL Generator API

A FastAPI-based service that uses an LLM to generate SQL queries from natural language, with optional schema-awareness and database verification.

---

## Overview

This project provides:

- Natural language → SQL generation via an LLM  
- Optional schema + data upload  
- Automatic validation of generated SQL  
- Safe execution check against a database using transactional rollback  
- Retry loop with error feedback to improve query correctness  

The system operates in two modes:

- **Schema-aware mode**  
  → SQL is validated *and* checked against the database  

- **Schema-less mode**  
  → SQL is generated and syntax-validated only  

---

## Core Features

### 1. Schema + Data Upload
- Upload your database schema
- Optionally load data into your database
- Schema is used to guide LLM generation

### 2. SQL Generation
- Query the LLM using natural language
- Works with or without schema

### 3. Validation Pipeline

Each generated query goes through:

1. **LLM generation**
2. **Syntax validation**
3. **Database verification (if schema is available)**  
   - Executed inside a nested transaction (`SAVEPOINT`)
   - Always rolled back → no side effects

### 4. Retry Mechanism
- Failed attempts are fed back into the prompt
- Improves correctness across iterations

---

## Tech Stack

- FastAPI  
- PostgreSQL  
- SQLAlchemy  
- OpenAI-compatible LLM APIs (Groq, OpenAI, local models)

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a .env file:

```env
LLM_HOST=<LLM_HOST>
LLM_MODEL=<LLM_MODEL>
LLM_API_KEY=<LLM_API_KEY>

DB_URL=<DB_URL>
```

## Running the Service

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:

http://localhost:8000/docs

FastAPI provides an interactive Swagger UI with all endpoints.

## Usage Flow
### With Schema
- Upload schema
- (Optional) Load data
- Send natural language query
- Receive validated SQL guaranteed to run on the DB
- Use the runquery endpoint if needded to run on the database
- Generate Schema/data from DB if changed and you would like it to persist
- Can be exported as data schema or dump

### Without Schema
- Send natural language query
- Receive best-effort SQL (syntax-validated only)

### Example

**Input:**

```text
Get all users older than 30
```

**Output:**

```text
SELECT * FROM users WHERE age > 30;
```

## Design Notes

- Database verification uses SAVEPOINT + rollback → no persistent writes
- Failed SQL attempts are fed back into the LLM prompt
- Output is constrained to raw SQL (no markdown / explanations)
- Model-agnostic via OpenAI-compatible interface

## Limitations
- Schema-less mode may produce non-executable SQL
- LLM may hallucinate tables/columns without schema
- Complex queries depend on prompt quality and schema completeness

## Possible future Improvements
- Structured output (AST → SQL)
- Query cost estimation
- Role-based query restrictions
- Query caching