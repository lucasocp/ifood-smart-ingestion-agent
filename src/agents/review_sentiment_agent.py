
from src.models import ReviewSentimentSummary


class ReviewSentimentAgent:
    """
    Agente focado em minerar avaliações não-estruturadas de consumidores
    para extrair inteligência qualitativa sobre os pratos.
    """
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def analyze_reviews_sync(self, reviews: list[str]) -> ReviewSentimentSummary:
        if not reviews:
            return ReviewSentimentSummary(
                overall_sentiment="neutro",
                average_dish_score=4.0,
                highlight_positive_traits=["Sem avaliações recentes"],
                common_complaints=[],
                taste_profile=["padrão"]
            )

        positive_keywords = ["maravilhoso", "excelente", "quentinha", "crocante", "melhor", "cremoso", "caprichado", "nota 10", "recomendo"]
        negative_keywords = ["pesado", "gorduroso", "demorou", "frio", "ruim", "pequeno"]
        taste_keywords = ["cremoso", "crocante", "trufado", "defumado", "apimentado", "leves", "amanteigado"]

        pos_count = 0
        neg_count = 0
        highlights: list[str] = []
        complaints: list[str] = []
        taste_profile = set()

        for rev in reviews:
            rev_lower = rev.lower()
            for kw in positive_keywords:
                if kw in rev_lower:
                    pos_count += 1
                    if kw not in highlights and len(highlights) < 3:
                        highlights.append(f"Avaliado como {kw}")
            
            for nkw in negative_keywords:
                if nkw in rev_lower:
                    neg_count += 1
                    if nkw not in complaints and len(complaints) < 2:
                        complaints.append(f"Pontuado como {nkw}")

            for tkw in taste_keywords:
                if tkw in rev_lower:
                    taste_profile.add(tkw)

        total = pos_count + neg_count
        if total == 0:
            sentiment = "positivo"
            score = 4.5
        elif pos_count >= neg_count * 2:
            sentiment = "muito positivo"
            score = 4.8
        elif pos_count >= neg_count:
            sentiment = "positivo"
            score = 4.3
        else:
            sentiment = "misto/regular"
            score = 3.6

        return ReviewSentimentSummary(
            overall_sentiment=sentiment,
            average_dish_score=score,
            highlight_positive_traits=highlights or ["Sabor equilibrado", "Aprovado pelos clientes"],
            common_complaints=complaints or ["Nenhuma queixa recorrente"],
            taste_profile=list(taste_profile) or ["equilibrado"]
        )

    async def analyze_reviews(self, reviews: list[str]) -> ReviewSentimentSummary:
        return self.analyze_reviews_sync(reviews)
