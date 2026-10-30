import re
import uuid

from src.models import (
    AllergenAnalysis,
    DietaryPreference,
    EnrichedMenuItem,
    RawMenuItem,
    ReviewSentimentSummary,
)


class SchemaNormalizerAgent:
    """
    Agente responsável por transformar dados brutos e poluídos de cardápios
    em contratos canônicos estruturados (Pydantic), normalizando preços,
    identificando porções e mapeando alérgenos e restrições alimentares.
    """
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _clean_price(self, raw_price_str: str) -> float:
        clean = re.sub(r"[^\d,\.]", "", raw_price_str)
        clean = clean.replace(".", "").replace(",", ".")
        try:
            return round(float(clean), 2)
        except ValueError:
            return 0.0

    def _infer_dietary_tags(self, title: str, description: str) -> list[DietaryPreference]:
        text = f"{title} {description}".lower()
        tags = []
        if "vegano" in text or "plant-based" in text:
            tags.append(DietaryPreference.VEGAN)
            tags.append(DietaryPreference.VEGETARIAN)
        elif "vegetariano" in text or "sem carne" in text:
            tags.append(DietaryPreference.VEGETARIAN)

        if "sem glúten" in text or "sem gluten" in text or "celíaco" in text:
            tags.append(DietaryPreference.GLUTEN_FREE)

        if "sem lactose" in text or "lactose-free" in text or "zero lactose" in text:
            tags.append(DietaryPreference.LACTOSE_FREE)

        if "low carb" in text or "low-carb" in text or "cetogênica" in text:
            tags.append(DietaryPreference.LOW_CARB)

        if not tags:
            tags.append(DietaryPreference.STANDARD)

        return list(set(tags))

    def _infer_allergens(self, title: str, description: str) -> AllergenAnalysis:
        text = f"{title} {description}".lower()
        return AllergenAnalysis(
            contains_peanuts="amendoim" in text or "castanha" in text,
            contains_dairy="queijo" in text or "leite" in text or "manteiga" in text or "parmesão" in text or "cheddar" in text,
            contains_gluten=("pão" in text or "massa" in text or "brioche" in text or "trigo" in text or "fettuccine" in text) and ("sem glúten" not in text and "sem gluten" not in text),
            contains_crustaceans="camarão" in text or "camarao" in text or "frutos do mar" in text or "lagosta" in text,
            other_allergens=["dendê"] if "dendê" in text else []
        )

    def _infer_portion(self, title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if "duplo" in text or "2 pessoas" in text or "para compartilhar" in text:
            return "Serve 2 pessoas (ou porção generosa)"
        elif "combo" in text:
            return "Combo Individual Completo com bebida"
        return "Individual (1 pessoa)"

    def normalize_sync(self, raw: RawMenuItem, sentiment: ReviewSentimentSummary) -> EnrichedMenuItem:
        price = self._clean_price(raw.raw_price_str)
        dietary_tags = self._infer_dietary_tags(raw.raw_title, raw.raw_description)
        allergens = self._infer_allergens(raw.raw_title, raw.raw_description)
        portion = self._infer_portion(raw.raw_title, raw.raw_description)

        canonical = re.sub(r"\[.*?\]|\(.*?\)", "", raw.raw_title).strip()

        keywords = [w.lower() for w in canonical.split() if len(w) > 3]
        for tag in dietary_tags:
            keywords.append(tag.value if hasattr(tag, "value") else str(tag))

        semantic_summary = (
            f"Restaurante: {raw.restaurant_name}. Prato: {canonical}. Preço: R${price:.2f}. "
            f"Descrição: {raw.raw_description}. Tags: {[t.value if hasattr(t, 'value') else str(t) for t in dietary_tags]}. "
            f"Alérgenos: Laticínios={allergens.contains_dairy}, Glúten={allergens.contains_gluten}, "
            f"Frutos do Mar={allergens.contains_crustaceans}. "
            f"Avaliação: {sentiment.average_dish_score}/5 ({sentiment.overall_sentiment}). "
            f"Destaques: {', '.join(sentiment.highlight_positive_traits)}."
        )

        item_id = f"item_{uuid.uuid5(uuid.NAMESPACE_DNS, f'{raw.restaurant_id}_{canonical}').hex[:10]}"

        return EnrichedMenuItem(
            item_id=item_id,
            restaurant_id=raw.restaurant_id,
            restaurant_name=raw.restaurant_name,
            canonical_name=canonical,
            normalized_price=price,
            portion_estimate=portion,
            dietary_tags=dietary_tags,
            allergens=allergens,
            sentiment_summary=sentiment,
            search_keywords=keywords,
            full_semantic_text=semantic_summary
        )

    async def normalize(self, raw: RawMenuItem, sentiment: ReviewSentimentSummary) -> EnrichedMenuItem:
        return self.normalize_sync(raw, sentiment)
