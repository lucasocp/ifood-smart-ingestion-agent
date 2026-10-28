import unittest
import sys
from pathlib import Path

root = str(Path(__file__).resolve().parent.parent)
if root not in sys.path:
    sys.path.insert(0, root)

from src.models import RawMenuItem, DietaryPreference, SemanticSearchQuery
from src.scraper.async_scraper import AsyncMenuScraper
from src.agents.schema_normalizer import SchemaNormalizerAgent
from src.agents.review_sentiment_agent import ReviewSentimentAgent
from src.vector_store.chroma_indexer import VectorIndexer
from src.pipeline import SmartIngestionPipeline

class TestSmartIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.scraper = AsyncMenuScraper()
        self.sentiment_agent = ReviewSentimentAgent()
        self.normalizer = SchemaNormalizerAgent()
        self.indexer = VectorIndexer()

    def test_scraper_returns_records(self):
        items = self.scraper.fetch_restaurant_catalog_sync("all")
        self.assertGreaterEqual(len(items), 4)
        self.assertEqual(items[0].restaurant_id, "rest_sp_01")

    def test_sentiment_agent_scoring(self):
        reviews = [
            "Prato maravilhoso e crocante!",
            "Nota 10, atendimento excelente",
            "Um pouco pesado, mas recomendo"
        ]
        res = self.sentiment_agent.analyze_reviews_sync(reviews)
        self.assertGreaterEqual(res.average_dish_score, 4.0)
        self.assertIn("crocante", res.taste_profile)

    def test_schema_normalizer_price_and_allergens(self):
        raw = RawMenuItem(
            restaurant_id="test_01",
            restaurant_name="Cantina Teste",
            raw_title="Fettuccine c/ Queijo e Pão de Alho [Promo]",
            raw_description="Massa com queijo cremoso e manteiga.",
            raw_price_str="R$ 55,90",
            scraped_reviews=[]
        )
        sentiment = self.sentiment_agent.analyze_reviews_sync([])
        enriched = self.normalizer.normalize_sync(raw, sentiment)

        self.assertEqual(enriched.normalized_price, 55.90)
        self.assertTrue(enriched.allergens.contains_dairy)
        self.assertTrue(enriched.allergens.contains_gluten)
        self.assertFalse(enriched.allergens.contains_crustaceans)
        self.assertEqual(enriched.canonical_name, "Fettuccine c/ Queijo e Pão de Alho")

    def test_vector_search_and_filters(self):
        pipeline = SmartIngestionPipeline()
        pipeline.run_ingestion_sync("all")

        # Teste de filtro por preço
        query = SemanticSearchQuery(query="fettuccine trufado", max_price=70.0, top_k=1)
        results = pipeline.search_sync(query)
        self.assertEqual(len(results), 1)
        self.assertIn("fettuccine", results[0].item.canonical_name.lower())
        self.assertLessEqual(results[0].item.normalized_price, 70.0)

    def test_end_to_end_pipeline(self):
        pipeline = SmartIngestionPipeline()
        items = pipeline.run_ingestion_sync("rest_ba_02")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].restaurant_name, "Acarajé & Sabores da Bahia - Rio Vermelho")
        self.assertTrue(items[0].allergens.contains_crustaceans)

if __name__ == "__main__":
    unittest.main()
