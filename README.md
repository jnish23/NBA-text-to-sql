# NBA Text-to-SQL Agent

An end-to-end data pipeline and LLM-powered query agent that translates natural language questions into executable SQL queries against a SQL NBA database, returning analytical answers.

---

## Overview

Querying complex sports databases traditionally requires domain expertise and SQL fluency. This project bridges that gap by providing a natural language interface over an NBA statistical warehouse. It ingests and structures historical basketball data through an automated ETL pipeline and leverages an LLM agent to validate schemas, generate syntactically correct SQL, execute queries safely, and interpret the results.

---

## Key Features

- **Automated ETL Pipeline**: Extracts, cleans, and standardizes raw NBA data into normalized relational tables for performant SQL querying.
- **Natural Language to SQL**: Converts complex, multi-condition English prompts (e.g., player stats, seasonal trends, head-to-head metrics) into accurate SQL queries.
- **Schema-Aware Context & Guardrails**: Injects database schema constraints and definitions into the agent context to minimize hallucinated table/column names and handle edge cases.
- **End-to-End Evaluation**: Executes generated queries against the database and translates raw tabular outputs back into human-readable insights.

---

## Tech Stack

- **Language**: Python 3.10+
- **LLM & Agent Framework**: LangChain / OpenAI API (or compatible LLM providers)
- **Data Engineering & Storage**: SQLite / PostgreSQL, pandas, SQLAlchemy
- **Environment & Package Management**: `pip`, `dotenv`

---

## Project Structure

```text
NBA-text-to-sql/
├── agent.py            # Text-to-SQL agent orchestration and query execution logic
├── etl_pipeline.py     # Data extraction, transformation, and database loading
├── requirements.txt    # Project dependencies
├── .gitignore          # Environment and cache ignore rules
└── README.md