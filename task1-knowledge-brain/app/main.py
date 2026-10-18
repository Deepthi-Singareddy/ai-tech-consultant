from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import router
from app.rag.store import knowledge_store
from app.crawler.crawler import PoliteCrawler

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Knowledge Brain for Brilliant Directories Support Center - RAG, Multimodal Screenshots, Citations & Human Escalation"
)

# Enable CORS for cross-service communication (TypeScript client, Web studio UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.on_event("startup")
async def startup_event():
    print(f"[{settings.APP_NAME}] Starting up on port {settings.PORT}...")
    # If index is empty, seed knowledge and build chunks
    if not knowledge_store.chunks:
        print(f"[{settings.APP_NAME}] Empty index detected. Running polite initial ingestion...")
        crawler = PoliteCrawler()
        crawler.crawl(max_pages=15)
        knowledge_store.rebuild_from_articles()
    print(f"[{settings.APP_NAME}] Knowledge base ready: {len(knowledge_store.chunks)} chunks indexed.")

@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }
