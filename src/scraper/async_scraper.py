import logging
from typing import List
from src.models import RawMenuItem

logger = logging.getLogger("ScraperEngine")

SAMPLE_SCRAPED_DATA = [
    {
        "restaurant_id": "rest_sp_01",
        "restaurant_name": "Cantina & Trattoria Bella Italia",
        "raw_title": "FETTUCCINE ALFREDO C/ COGUMELOS TRUFADOS [PROMOÇÃO]",
        "raw_description": "Massa fresca artesanal ao molho cremoso de queijo parmesão reggiano maturado 24m, manteiga clarificada e mix de cogumelos paris e shimeji frescos salteados no azeite trufado. Acompanha fatias de pão italiano.",
        "raw_price_str": "R$ 68,90",
        "raw_category": "Massas Especiais",
        "scraped_reviews": [
            "Prato maravilhoso! Muito cremoso e o aroma de trufas é marcante.",
            "A massa veio quentinha e o queijo derretido no ponto exato. Melhor fettuccine de SP.",
            "Um pouco pesado para o jantar se comer sozinho, mas o sabor é nota 10.",
            "Excelente opção para quem não come carne, muito caprichado."
        ]
    },
    {
        "restaurant_id": "rest_ba_02",
        "restaurant_name": "Acarajé & Sabores da Bahia - Rio Vermelho",
        "raw_title": "Combo Acarajé Completo Tradicional + Coca Lata",
        "raw_description": "Bolinho de feijão fradinho frito no puro azeite de dendê da Costa do Dendê. Acompanha vatapá baiano consistente, caruru de quiabo fresco, camarão seco defumado crocante e salada de vinagrete com pimenta à parte.",
        "raw_price_str": "R$ 34,50",
        "raw_category": "Típicos da Bahia",
        "scraped_reviews": [
            "Dendê de primeiríssima qualidade, não é pesado e a massa é super crocante por fora.",
            "O camarão defumado faz toda a diferença! Chegou rápido e ainda fumegando.",
            "Atenção para quem tem alergia a frutos do mar, pois leva camarão de verdade. Muito bom!",
            "Melhor acarajé de delivery de Salvador."
        ]
    },
    {
        "restaurant_id": "rest_sp_03",
        "restaurant_name": "Green Garden Plant-Based & Bowls",
        "raw_title": "Super Bowl Proteico Vegano Zen (Sem Glúten)",
        "raw_description": "Quinoa real em grãos cozida em caldo de legumes aromático, cubos de tofu defumado grelhado, edamame fresco, avocado hass fatiado, cenoura ralada, repolho roxo marinado e molho cremoso de tahine com limão siciliano.",
        "raw_price_str": "R$ 42,00",
        "raw_category": "Bowls Saudáveis",
        "scraped_reviews": [
            "Perfeito para quem é celíaco e vegano, sem contaminação cruzada.",
            "Muito bem servido, o tofu defumado é bem temperado e crocante.",
            "Refeição leve, saudável e sacia bastante. Pedi para o almoço no escritório.",
            "Molho de tahine excepcional."
        ]
    },
    {
        "restaurant_id": "rest_pr_04",
        "restaurant_name": "Smash Burger & Craft Beer",
        "raw_title": "Duplo Bacon Cheddar Artesanal Melt",
        "raw_description": "Dois burgers ultra smash de 90g (blend Angus fresco grelhado na chapa de ferro quente com crostinha), cheddar inglês derretido cremoso, fatias generosas de bacon artesanal defumado em macieira e maionese secreta de alho tostado no pão brioche amanteigado.",
        "raw_price_str": "R$ 38,90",
        "raw_category": "Smash Burgers",
        "scraped_reviews": [
            "Pão super macio e a crostinha do smash é impecável.",
            "Muito queijo cheddar e o bacon é crocante de verdade, nada daquela borracha.",
            "Um pouco gorduroso mas para quem quer chutar o balde é o melhor burger.",
            "Chegou em 25 minutos, bem embalado."
        ]
    }
]

class AsyncMenuScraper:
    """
    Motor de extração e ingestão de catálogos e avaliações.
    Projetado com interface dual síncrona/assíncrona para compatibilidade com pipelines batch e servidores ASGI.
    """
    def __init__(self, concurrency_limit: int = 5):
        self.concurrency_limit = concurrency_limit

    def fetch_restaurant_catalog_sync(self, restaurant_id: str) -> List[RawMenuItem]:
        logger.info(f"Coletando catálogo para restaurante: {restaurant_id}")
        items = []
        for raw in SAMPLE_SCRAPED_DATA:
            if restaurant_id == "all" or raw["restaurant_id"] == restaurant_id:
                items.append(RawMenuItem(**raw))
        logger.info(f"Coleta concluída para {restaurant_id}: {len(items)} itens extraídos.")
        return items

    async def fetch_restaurant_catalog(self, restaurant_id: str) -> List[RawMenuItem]:
        return self.fetch_restaurant_catalog_sync(restaurant_id)

    def fetch_all_partner_catalogs(self) -> List[RawMenuItem]:
        restaurant_ids = ["rest_sp_01", "rest_ba_02", "rest_sp_03", "rest_pr_04"]
        results = []
        for rid in restaurant_ids:
            results.extend(self.fetch_restaurant_catalog_sync(rid))
        return results
