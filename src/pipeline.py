import logging
import sys
from pathlib import Path

# Garante inclusão do diretório raiz no PYTHONPATH
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from src.agents.review_sentiment_agent import ReviewSentimentAgent
from src.agents.schema_normalizer import SchemaNormalizerAgent
from src.models import EnrichedMenuItem, SearchResultItem, SemanticSearchQuery
from src.scraper.async_scraper import AsyncMenuScraper
from src.vector_store.vector_indexer import VectorIndexer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SmartIngestionPipeline")

class SmartIngestionPipeline:
    """
    Pipeline multi-agente de ponta a ponta:
    1. Coleta e normalização de cardápios e avaliações brutas (AsyncMenuScraper)
    2. Mineração de sentimento e perfil gustativo (ReviewSentimentAgent)
    3. Normalização canônica de schema e inferência de alérgenos/dietas (SchemaNormalizerAgent)
    4. Indexação vetorial para RAG / Semantic Retrieval (VectorIndexer)
    """
    def __init__(self):
        self.scraper = AsyncMenuScraper(concurrency_limit=4)
        self.sentiment_agent = ReviewSentimentAgent()
        self.normalizer_agent = SchemaNormalizerAgent()
        self.vector_indexer = VectorIndexer()

    def run_ingestion_sync(self, restaurant_id: str = "all") -> list[EnrichedMenuItem]:
        logger.info(f"==> Iniciando pipeline de ingestão inteligente para: {restaurant_id}")
        raw_items = self.scraper.fetch_restaurant_catalog_sync(restaurant_id)
        
        enriched_items: list[EnrichedMenuItem] = []
        for raw in raw_items:
            sentiment = self.sentiment_agent.analyze_reviews_sync(raw.scraped_reviews)
            enriched = self.normalizer_agent.normalize_sync(raw, sentiment)
            enriched_items.append(enriched)

        self.vector_indexer.index_items_sync(enriched_items)
        logger.info(f"==> Pipeline finalizado! {len(enriched_items)} itens enriquecidos e vetorizados.")
        return enriched_items

    async def run_ingestion_for_restaurant(self, restaurant_id: str = "all") -> list[EnrichedMenuItem]:
        return self.run_ingestion_sync(restaurant_id)

    def search_sync(self, query: SemanticSearchQuery) -> list[SearchResultItem]:
        return self.vector_indexer.search_sync(query)

    async def search(self, query: SemanticSearchQuery) -> list[SearchResultItem]:
        return self.search_sync(query)

if __name__ == "__main__":
    pipeline = SmartIngestionPipeline()
    items = pipeline.run_ingestion_sync("all")

    print("\n--- Teste 1: Busca Semântica 'comida vegana saudável com tofu' ---")
    results = pipeline.search_sync(SemanticSearchQuery(query="comida vegana saudável com tofu", top_k=2))
    for r in results:
        print(f"[{r.relevance_score}] {r.item.restaurant_name} -> {r.item.canonical_name} (R$ {r.item.normalized_price})")

    print("\n--- Teste 2: Busca com Filtro de Preço 'fettuccine queijo cogumelos' (max R$ 70) ---")
    results2 = pipeline.search_sync(SemanticSearchQuery(query="fettuccine queijo cogumelos", max_price=70.0, top_k=1))
    for r in results2:
        print(f"[{r.relevance_score}] {r.item.restaurant_name} -> {r.item.canonical_name} (R$ {r.item.normalized_price})")

    print("\n--- Teste 3: Alérgenos Detectados no Acarajé Baiano ---")
    acaraje = next(i for i in items if "Acarajé" in i.canonical_name)
    print(f"Prato: {acaraje.canonical_name}")
    print(f"Alérgenos detectados: Frutos do Mar={acaraje.allergens.contains_crustaceans}, Outros={acaraje.allergens.other_allergens}")
    print(f"Sentimento da comunidade: {acaraje.sentiment_summary.overall_sentiment} (Nota {acaraje.sentiment_summary.average_dish_score})")
