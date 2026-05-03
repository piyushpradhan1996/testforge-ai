import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from app.database import get_generation, init_db, list_documents, list_generations, save_generation
from app.schemas import (
    DocumentCreate,
    DocumentSummary,
    EvalRunRequest,
    EvalRunResponse,
    GenerationResponse,
    GenerationSummary,
    GenerateRequest,
)
from app.services.ai_provider import AIProvider, AIProviderError
from app.services.eval_service import EvalService
from app.services.guardrail_service import GuardrailService
from app.services.mock_ai_provider import MockAIProvider
from app.services.openai_provider import OpenAIProvider
from app.services.rag_service import RAGService
from app.utils.markdown_export import generation_to_markdown


load_dotenv()


def get_ai_provider() -> AIProvider:
    provider_name = os.getenv("AI_PROVIDER", "mock").strip().lower()
    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))
    if provider_name == "openai" and has_openai_key:
        try:
            return OpenAIProvider()
        except AIProviderError:
            return MockAIProvider()
    return MockAIProvider()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="TestForge AI API",
    description="AI-powered QA assistant API with mock-first generation.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/generate", response_model=GenerationResponse)
def generate(request: GenerateRequest) -> GenerationResponse:
    provider = get_ai_provider()
    retrieved_context = RAGService().retrieve_for_request(request)
    try:
        output = provider.generate(request, retrieved_context=retrieved_context)
    except AIProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    output.guardrail_result = GuardrailService().validate(
        output,
        request=request,
        retrieved_context=retrieved_context,
    )
    return save_generation(request, output)


@app.get("/api/generations", response_model=list[GenerationSummary])
def generations() -> list[GenerationSummary]:
    return list_generations()


@app.post("/api/documents", response_model=DocumentSummary)
def create_document(document: DocumentCreate) -> DocumentSummary:
    return RAGService().index_document(document)


@app.get("/api/documents", response_model=list[DocumentSummary])
def documents() -> list[DocumentSummary]:
    return list_documents()


@app.get("/api/generations/{generation_id}", response_model=GenerationResponse)
def generation_detail(generation_id: int) -> GenerationResponse:
    generation = get_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    return generation


@app.get("/api/generations/{generation_id}/export", response_class=PlainTextResponse)
def export_generation(generation_id: int) -> PlainTextResponse:
    generation = get_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail="Generation not found")
    safe_title = "".join(character if character.isalnum() else "-" for character in generation.title.lower())
    markdown = generation_to_markdown(generation)
    return PlainTextResponse(
        markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}-qa-output.md"'},
    )


@app.post("/api/evals/run", response_model=EvalRunResponse)
def run_evals(_: EvalRunRequest | None = None) -> EvalRunResponse:
    return EvalService().run_all()
