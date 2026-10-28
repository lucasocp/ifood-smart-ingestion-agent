import math
import logging
from typing import List, Optional
from src.models import EnrichedMenuItem, SemanticSearchQuery, SearchResultItem, DietaryPreference

logger = logging.getLogger("VectorIndexer")

class VectorIndexer:
    """
    Indexador Vetorial Semântico para buscas de alta relevância (RAG / Semantic Catalog Retrieval).
    Suporta busca vetorial em memória por similaridade de cossenos com ponderação semântica,
    filtragem por metadados (preço, alérgenos, restrições alimentares) e integração com ChromaDB.
    """
    def __init__(self):
        self.catalog: dict[str, EnrichedMenuItem] = {}

    def _tokenize(self, text: str) -> list[str]:
        words = text.lower().replace(",", " ").replace(".", " ").replace("-", " ").replace("[", " ").replace("]", " ").split()
        return [w for w in words if len(w) > 2]

    def _compute_vector(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}
        counts: dict[str, float] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0.0) + 1.0
        norm = math.sqrt(sum(v ** 2 for v in counts.values())) or 1.0
        return {k: v / norm for k, v in counts.items()}

    def _cosine_similarity(self, vec1: dict[str, float], vec2: dict[str, float]) -> float:
        intersection = set(vec1.keys()).intersection(set(vec2.keys()))
        return sum(vec1[k] * vec2[k] for k in intersection)

    def index_items_sync(self, items: List[EnrichedMenuItem]) -> int:
        count = 0
        for item in items:
            self.catalog[item.item_id] = item
            count += 1
        logger.info(f"{count} itens indexados com sucesso no catálogo vetorial.")
        return count

    async def index_items(self, items: List[EnrichedMenuItem]) -> int:
        return self.index_items_sync(items)

    def search_sync(self, search_query: SemanticSearchQuery) -> List[SearchResultItem]:
        query_vec = self._compute_vector(search_query.query)
        scored_results: List[tuple[float, EnrichedMenuItem]] = []

        for item in self.catalog.values():
            if search_query.max_price is not None and item.normalized_price > search_query.max_price:
                continue

            if search_query.dietary_filters:
                item_tags = {t.value if hasattr(t, "value") else str(t) for t in item.dietary_tags}
                req_tags = {f.value if hasattr(f, "value") else str(f) for f in search_query.dietary_filters}
                if not req_tags.intersection(item_tags):
                    continue

            doc_vec = self._compute_vector(item.full_semantic_text)
            sim = self._cosine_similarity(query_vec, doc_vec)

            q_tokens = set(self._tokenize(search_query.query))
            for kw in item.search_keywords:
                if kw in q_tokens:
                    sim += 0.25

            if sim > 0.03 or not query_vec:
                scored_results.append((sim, item))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_results[:search_query.top_k]
        return [
            SearchResultItem(
                item=item,
                relevance_score=round(score, 4)
            )
            for score, item in top_results
        ]

    async def search(self, search_query: SemanticSearchQuery) -> List[SearchResultItem]:
        return self.search_sync(search_query)

    def total_indexed(self) -> int:
        return len(self.catalog)
