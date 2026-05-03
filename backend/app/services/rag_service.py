import os
import re

from app.database import list_document_chunks, save_document
from app.schemas import DocumentCreate, DocumentSummary, GenerateRequest, RetrievedContext


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_/{}.-]+")


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text) if len(token) > 2}


class RAGService:
    def __init__(self, chunk_size: int = 700) -> None:
        self.chunk_size = chunk_size

    def index_document(self, document: DocumentCreate) -> DocumentSummary:
        chunks = self.chunk_text(document.content)
        return save_document(document, chunks)

    def chunk_text(self, content: str) -> list[str]:
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", content) if paragraph.strip()]
        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs or [content.strip()]:
            if not current:
                current = paragraph
                continue
            if len(current) + len(paragraph) + 2 <= self.chunk_size:
                current = f"{current}\n\n{paragraph}"
            else:
                chunks.append(current)
                current = paragraph

        if current:
            chunks.append(current)

        expanded: list[str] = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                expanded.append(chunk)
                continue
            for start in range(0, len(chunk), self.chunk_size):
                expanded.append(chunk[start : start + self.chunk_size].strip())
        return [chunk for chunk in expanded if chunk]

    def retrieve(self, query: str, top_k: int | None = None) -> list[RetrievedContext]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []

        limit = top_k or int(os.getenv("RAG_RETRIEVAL_TOP_K", "3"))
        scored: list[RetrievedContext] = []
        for chunk in list_document_chunks():
            overlap = query_tokens.intersection(_tokens(f"{chunk.document_title} {chunk.content}"))
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            scored.append(chunk.model_copy(update={"score": round(score, 4)}))

        scored.sort(key=lambda item: item.score, reverse=True)
        return scored[:limit]

    def retrieve_for_request(self, request: GenerateRequest) -> list[RetrievedContext]:
        query = " ".join(
            item
            for item in [
                request.title,
                request.requirement,
                request.acceptance_criteria,
                request.api_notes or "",
                request.feature_area or "",
            ]
            if item
        )
        retrieved = self.retrieve(query)

        if request.supporting_context and request.supporting_context.strip():
            inline_context = RetrievedContext(
                id=None,
                document_title="Inline supporting context",
                chunk_index=0,
                content=request.supporting_context.strip(),
                score=1.0,
            )
            return [inline_context, *retrieved]

        return retrieved
