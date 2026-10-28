from enum import Enum
from typing import List, Optional
from src.compat import BaseModel, Field

class DietaryPreference(str, Enum):
    VEGAN = "vegano"
    VEGETARIAN = "vegetariano"
    GLUTEN_FREE = "sem_gluten"
    LACTOSE_FREE = "sem_lactose"
    LOW_CARB = "low_carb"
    HALAL = "halal"
    KOSHER = "kosher"
    STANDARD = "convencional"

class RawMenuItem(BaseModel):
    restaurant_id: str
    restaurant_name: str
    raw_title: str
    raw_description: str
    raw_price_str: str
    raw_category: Optional[str] = None
    scraped_reviews: List[str] = Field(default_factory=list)

class AllergenAnalysis(BaseModel):
    contains_peanuts: bool = False
    contains_dairy: bool = False
    contains_gluten: bool = False
    contains_crustaceans: bool = False
    other_allergens: List[str] = Field(default_factory=list)

class ReviewSentimentSummary(BaseModel):
    overall_sentiment: str = Field(description="positivo, neutro ou negativo")
    average_dish_score: float = Field(ge=0.0, le=5.0)
    highlight_positive_traits: List[str] = Field(default_factory=list)
    common_complaints: List[str] = Field(default_factory=list)
    taste_profile: List[str] = Field(default_factory=list, description="Ex: 'crocante', 'apimentado', 'doce'")

class EnrichedMenuItem(BaseModel):
    item_id: str
    restaurant_id: str
    restaurant_name: str
    canonical_name: str
    normalized_price: float
    portion_estimate: str
    dietary_tags: List[DietaryPreference] = Field(default_factory=list)
    allergens: AllergenAnalysis
    sentiment_summary: ReviewSentimentSummary
    search_keywords: List[str] = Field(default_factory=list)
    full_semantic_text: str = Field(description="Texto consolidado otimizado para embeddings vetoriais")

class SemanticSearchQuery(BaseModel):
    query: str
    max_price: Optional[float] = None
    dietary_filters: Optional[List[DietaryPreference]] = None
    top_k: int = 5

class SearchResultItem(BaseModel):
    item: EnrichedMenuItem
    relevance_score: float
