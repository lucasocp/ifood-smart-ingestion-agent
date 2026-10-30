import logging
import math

from src.models import EnrichedMenuItem, SearchResultItem, SemanticSearchQuery

logger = logging.getLogger("VectorIndexer")


class VectorIndexer:
    """Indexa itens em memória e faz buscas por similaridade de cossenos."""

    def __init__(self) -> None:
        self.catalog: dict[str, EnrichedMenuItem] = {}

    def _tokenize(self, text: str) -> list[str]:
        words = text.lower().replace(",", " ").replace(".", " ").replace("-", " ").replace("[", " ").replace("]", " ").split()
        return [word for word in words if len(word) > 2]

    def _compute_vector(self, text: str) -> dict[str, float]:
        tokens = self._tokenize(text)
        if not tokens:
            return {}

        counts: dict[str, float] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0.0) + 1.0
        norm = math.sqrt(sum(value**2 for value in counts.values())) or 1.0
        return {token: value / norm for token, value in counts.items()}

    def _cosine_similarity(
        self, first: dict[str, float], second: dict[str, float]
    ) -> float:
        shared_tokens = first.keys() & second.keys()
        return sum(first[token] * second[token] for token in shared_tokens)

    def index_items_sync(self, items: list[EnrichedMenuItem]) -> int:
        for item in items:
            self.catalog[item.item_id] = item
        logger.info("%s itens indexados no catálogo em memória.", len(items))
        return len(items)

    async def index_items(self, items: list[EnrichedMenuItem]) -> int:
        return self.index_items_sync(items)

    def search_sync(self, search_query: SemanticSearchQuery) -> list[SearchResultItem]:
        query_vector = self._compute_vector(search_query.query)
        query_tokens = set(self._tokenize(search_query.query))
        scored_results: list[tuple[float, EnrichedMenuItem]] = []

        for item in self.catalog.values():
            if (
                search_query.max_price is not None
                and item.normalized_price > search_query.max_price
            ):
                continue

            if search_query.dietary_filters:
                item_tags = {
                    tag.value if hasattr(tag, "value") else str(tag)
                    for tag in item.dietary_tags
                }
                requested_tags = {
                    tag.value if hasattr(tag, "value") else str(tag)
                    for tag in search_query.dietary_filters
                }
                if not requested_tags.intersection(item_tags):
                    continue

            document_vector = self._compute_vector(item.full_semantic_text)
            score = self._cosine_similarity(query_vector, document_vector)

            for keyword in item.search_keywords:
                if keyword in query_tokens:
                    score += 0.25

            if score > 0.03 or not query_vector:
                scored_results.append((score, item))

        scored_results.sort(key=lambda result: result[0], reverse=True)
        return [
            SearchResultItem(item=item, relevance_score=round(score, 4))
            for score, item in scored_results[: search_query.top_k]
        ]

    async def search(self, search_query: SemanticSearchQuery) -> list[SearchResultItem]:
        return self.search_sync(search_query)

    def total_indexed(self) -> int:
        return len(self.catalog)
