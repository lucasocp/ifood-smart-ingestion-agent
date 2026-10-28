# 🍽️ iFood Smart Ingestion Agent (Multi-Agent RAG Pipeline)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![Vector Store](https://img.shields.io/badge/VectorDB-ChromaDB%20%7C%20In--Memory-purple.svg)](https://www.trychroma.com/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Pipeline multi-agente autônomo para enriquecimento semântico de catálogos gastronômicos, inferência de alérgenos/dietas e busca semântica em alta dimensão (RAG Retrieval).**

---

## 🎯 Contexto & Impacto de Negócio (iFood AI-First)

Milhares de novos restaurantes ingressam no ecossistema de delivery com cardápios não estruturados, textos ruidosos, descrições ausentes e informações críticas de saúde pública omitidas (como alérgenos e restrições alimentares).

Este projeto resolve esse gargalo através de um **Pipeline Inteligente Multi-Agente**:
1. **Redução drástica do Time-to-Market de novos parceiros:** ingestão automatizada de cardápios via scraping inteligente e parsing semântico.
2. **Segurança Alimentar do Consumidor:** inferência e rotulagem preventiva de alérgenos (glúten, laticínios, crustáceos) e restrições (vegano, sem glúten, low carb).
3. **Conversão de Vendas com Busca Semântica (RAG):** substituição de buscas rígidas por palavras-chave por busca vetorial semântica (ex: *"quero prato com cogumelos trufados até R$70"*).

---

## 🏗️ Arquitetura do Sistema

```mermaid
flowchart TD
    subgraph Ingestion ["1. Coleta & Ingestão"]
        A["Cardápios Brutos & Reviews de Usuários"] --> B["AsyncMenuScraper Engine"]
    end

    subgraph Agents ["2. Camada de Agentes Especializados"]
        B --> C["ReviewSentimentAgent"]
        B --> D["SchemaNormalizerAgent"]
        C -->|"Scores & Perfil Gustativo"| D
        D -->|"Contrato Pydantic Enriquecido"| E["EnrichedMenuItem Model"]
    end

    subgraph Storage ["3. Vetorização & Indexação"]
        E --> F["VectorIndexer / ChromaDB"]
    end

    subgraph API ["4. Camada de Serviço & RAG"]
        G["Usuário / App iFood"] -->|"Query Semântica com Filtros"| H["FastAPI REST Interface"]
        H --> F
        F -->|"Top-K Itens Relevantes + Justificativa"| G
    end
```

---

## 📦 Estrutura do Repositório

```text
├── app.py                      # Servidor FastAPI com rotas REST de ingestão e busca semântica
├── requirements.txt            # Dependências de produção e testes
├── Dockerfile                  # Conteinerização otimizada
├── docker-compose.yml          # Orquestração do app + ChromaDB
├── src/
│   ├── compat.py               # Compatibilidade resiliente (Pydantic v2 + fallback nativo)
│   ├── models.py               # Schemas tipados e contratos de dados
│   ├── pipeline.py             # Orquestrador do fluxo ponta a ponta
│   ├── scraper/
│   │   └── async_scraper.py    # Motor de coleta com controle de concorrência
│   ├── agents/
│   │   ├── schema_normalizer.py    # Normalização de preços, porções e alérgenos
│   │   └── review_sentiment_agent.py # Mineração de sentimentos e atributos culinários
│   └── vector_store/
│       └── chroma_indexer.py   # Busca vetorial por similaridade de cossenos com metadados
└── tests/
    └── test_pipeline.py        # Suíte de testes unitários e de integração
```

---

## 🚀 Como Executar

### 1. Clonar e Executar Localmente
```bash
# Clone o repositório
git clone https://github.com/lucasocp/ifood-smart-ingestion-agent.git
cd ifood-smart-ingestion-agent

# Execute a suíte de testes (100% de cobertura nos componentes centrais)
python -u tests/test_pipeline.py

# Execute o pipeline interativo
python -u src/pipeline.py
```

### 2. Executar via Docker Compose
```bash
docker-compose up --build
```
A API estará disponível em `http://localhost:8000` (documentação interativa Swagger em `http://localhost:8000/docs`).

---

## 🧪 Exemplos de Casos de Teste Atendidos

| Query do Usuário | Filtro Aplicado | Item Retornado | Score de Relevância |
| :--- | :--- | :--- | :--- |
| *"comida vegana saudável com tofu"* | N/A | **Super Bowl Proteico Vegano Zen** | **0.1164** |
| *"fettuccine queijo cogumelos"* | `max_price <= R$ 70,00` | **Fettuccine Alfredo c/ Cogumelos Trufados** | **0.7685** |
| Detecção de Risco Alimentar | Acarajé Baiano | **Detecta Alérgenos: Frutos do Mar & Dendê** | **Alta Confiança** |

---

## 👨‍💻 Autor

**Lucas Oliveira Costa Pinto**  
- **LinkedIn:** [linkedin.com/in/lucas-oliveira-costa-pinto](https://www.linkedin.com/in/lucas-oliveira-costa-pinto/)  
- **GitHub:** [github.com/lucasocp](https://github.com/lucasocp)  
- **Curso:** Engenharia de Software – UCSal (Formação prevista: Dez/2028)
