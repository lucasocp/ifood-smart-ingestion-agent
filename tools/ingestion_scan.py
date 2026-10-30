"""Run a local smoke check for the sample ingestion pipeline."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.models import DietaryPreference, SemanticSearchQuery
from src.pipeline import SmartIngestionPipeline


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    pipeline = SmartIngestionPipeline()
    items = pipeline.run_ingestion_sync("all")
    require(len(items) == 4, f"Esperados 4 itens de demonstração; recebidos {len(items)}.")
    require(
        pipeline.vector_indexer.total_indexed() == len(items),
        "A quantidade indexada não corresponde aos itens ingeridos.",
    )
    require(
        all(item.normalized_price > 0 for item in items),
        "Um ou mais itens ficaram sem preço normalizado.",
    )

    acaraje = next((item for item in items if "Acarajé" in item.canonical_name), None)
    if acaraje is None:
        raise RuntimeError("A ingestão não retornou o item de acarajé esperado.")
    require(
        acaraje.allergens.contains_crustaceans,
        "O scanner não detectou crustáceos no acarajé.",
    )

    price_results = pipeline.search_sync(
        SemanticSearchQuery(
            query="fettuccine cogumelos",
            max_price=70.0,
            top_k=1,
        )
    )
    require(
        len(price_results) == 1
        and "fettuccine" in price_results[0].item.canonical_name.lower()
        and price_results[0].item.normalized_price <= 70.0,
        "A busca com limite de preço não retornou o fettuccine esperado.",
    )

    dietary_results = pipeline.search_sync(
        SemanticSearchQuery(
            query="tofu",
            dietary_filters=[DietaryPreference.VEGAN],
            top_k=2,
        )
    )
    require(
        len(dietary_results) > 0
        and all(
            DietaryPreference.VEGAN in item.dietary_tags
            for item in (result.item for result in dietary_results)
        ),
        "A busca filtrada por dieta retornou itens não veganos ou nenhum item.",
    )

    print(
        "Scanner de ingestão concluído: "
        f"{len(items)} itens ingeridos, alérgenos e filtros de busca validados."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
