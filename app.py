"""
FastAPI application for iFood Smart Ingestion Agent.
Exposes REST endpoints for catalog ingestion, semantic RAG search, and health checks.
"""
import os
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parent)
if root not in sys.path:
    sys.path.insert(0, root)

try:
    from fastapi import FastAPI
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from src.models import SemanticSearchQuery
from src.pipeline import SmartIngestionPipeline

pipeline = SmartIngestionPipeline()
# Pré-carrega o catálogo padrão na inicialização
pipeline.run_ingestion_sync("all")

if HAS_FASTAPI:
    app = FastAPI(
        title="iFood Smart Ingestion Agent API",
        description="Pipeline Multi-Agente para Enriquecimento de Catálogos e Busca Semântica RAG",
        version="1.0.0"
    )

    @app.get("/health")
    def health():
        return {"status": "healthy", "indexed_items": pipeline.vector_indexer.total_indexed()}

    @app.post("/api/v1/ingest")
    def trigger_ingestion(restaurant_id: str = "all"):
        items = pipeline.run_ingestion_sync(restaurant_id)
        return {
            "status": "success",
            "message": f"{len(items)} itens processados e indexados no banco vetorial.",
            "items_sample": [item.canonical_name for item in items]
        }

    @app.post("/api/v1/search")
    def semantic_search(query: SemanticSearchQuery):
        results = pipeline.search_sync(query)
        return {
            "query": query.query,
            "total_matches": len(results),
            "results": [
                {
                    "relevance_score": r.relevance_score,
                    "restaurant": r.item.restaurant_name,
                    "dish": r.item.canonical_name,
                    "price": r.item.normalized_price,
                    "portion": r.item.portion_estimate,
                    "dietary_tags": [t.value if hasattr(t, "value") else str(t) for t in r.item.dietary_tags],
                    "allergens": {
                        "dairy": r.item.allergens.contains_dairy,
                        "gluten": r.item.allergens.contains_gluten,
                        "crustaceans": r.item.allergens.contains_crustaceans
                    },
                    "sentiment_score": r.item.sentiment_summary.average_dish_score,
                    "highlights": r.item.sentiment_summary.highlight_positive_traits
                }
                for r in results
            ]
        }

if __name__ == "__main__":
    if HAS_FASTAPI:
        import uvicorn
        uvicorn.run("app:app", host=os.getenv("HOST", "127.0.0.1"), port=8000, reload=True)
    else:
        print("[INFO] Executando em modo CLI / Standalone demonstrativo.")
        res = pipeline.search_sync(SemanticSearchQuery(query="hambúrguer artesanal bacon", top_k=1))
        for r in res:
            print(f"Top Result: {r.item.canonical_name} - R${r.item.normalized_price}")
