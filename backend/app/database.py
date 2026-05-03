import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas import (
    DocumentCreate,
    DocumentSummary,
    GeneratedQAOutput,
    GenerationResponse,
    GenerationSummary,
    GenerateRequest,
    RetrievedContext,
)


def get_database_path() -> Path:
    configured = os.getenv("TESTFORGE_DB_PATH")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[1] / "testforge.db"


def get_connection() -> sqlite3.Connection:
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS generations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT,
                source_type TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
            """
        )
        connection.commit()


def save_generation(request: GenerateRequest, output: GeneratedQAOutput) -> GenerationResponse:
    generated_at = datetime.now(timezone.utc)
    output_json = output.model_dump(mode="json")
    request_json = request.model_dump(mode="json")

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO generations (title, generated_at, request_json, response_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                request.title,
                generated_at.isoformat(),
                json.dumps(request_json),
                json.dumps(output_json),
            ),
        )
        connection.commit()
        generation_id = int(cursor.lastrowid)

    return GenerationResponse(
        id=generation_id,
        title=request.title,
        generated_at=generated_at,
        **output_json,
    )


def _row_to_response(row: sqlite3.Row) -> GenerationResponse:
    output_payload: dict[str, Any] = json.loads(row["response_json"])
    return GenerationResponse(
        id=row["id"],
        title=row["title"],
        generated_at=datetime.fromisoformat(row["generated_at"]),
        **output_payload,
    )


def list_generations() -> list[GenerationSummary]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, generated_at, response_json
            FROM generations
            ORDER BY datetime(generated_at) DESC, id DESC
            """
        ).fetchall()

    summaries: list[GenerationSummary] = []
    for row in rows:
        output_payload = json.loads(row["response_json"])
        summaries.append(
            GenerationSummary(
                id=row["id"],
                title=row["title"],
                generated_at=datetime.fromisoformat(row["generated_at"]),
                positive_count=len(output_payload["positive_test_cases"]),
                negative_count=len(output_payload["negative_test_cases"]),
                edge_count=len(output_payload["edge_cases"]),
                api_count=len(output_payload["api_test_scenarios"]),
            )
        )
    return summaries


def get_generation(generation_id: int) -> GenerationResponse | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, title, generated_at, response_json
            FROM generations
            WHERE id = ?
            """,
            (generation_id,),
        ).fetchone()

    if row is None:
        return None
    return _row_to_response(row)


def save_document(document: DocumentCreate, chunks: list[str]) -> DocumentSummary:
    created_at = datetime.now(timezone.utc)
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO documents (title, filename, source_type, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                document.title,
                document.filename,
                document.source_type or "pasted_text",
                document.content,
                created_at.isoformat(),
            ),
        )
        document_id = int(cursor.lastrowid)
        connection.executemany(
            """
            INSERT INTO document_chunks (document_id, chunk_index, content)
            VALUES (?, ?, ?)
            """,
            [(document_id, index, chunk) for index, chunk in enumerate(chunks)],
        )
        connection.commit()

    return DocumentSummary(
        id=document_id,
        title=document.title,
        filename=document.filename,
        source_type=document.source_type or "pasted_text",
        chunk_count=len(chunks),
        created_at=created_at,
    )


def list_documents() -> list[DocumentSummary]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT d.id, d.title, d.filename, d.source_type, d.created_at, COUNT(c.id) AS chunk_count
            FROM documents d
            LEFT JOIN document_chunks c ON d.id = c.document_id
            GROUP BY d.id
            ORDER BY datetime(d.created_at) DESC, d.id DESC
            """
        ).fetchall()

    return [
        DocumentSummary(
            id=row["id"],
            title=row["title"],
            filename=row["filename"],
            source_type=row["source_type"],
            chunk_count=row["chunk_count"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


def list_document_chunks() -> list[RetrievedContext]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT c.id, d.title AS document_title, c.chunk_index, c.content
            FROM document_chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY d.id DESC, c.chunk_index ASC
            """
        ).fetchall()

    return [
        RetrievedContext(
            id=row["id"],
            document_title=row["document_title"],
            chunk_index=row["chunk_index"],
            content=row["content"],
            score=0.0,
        )
        for row in rows
    ]
