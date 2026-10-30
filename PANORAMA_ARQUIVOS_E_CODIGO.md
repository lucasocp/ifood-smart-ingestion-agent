# Panorama de arquivos e código

Este documento apresenta a estrutura do projeto, a responsabilidade de cada arquivo e o caminho percorrido pelos dados. O foco é explicar o que o código **faz hoje**, incluindo limitações importantes para quem for estudar, demonstrar ou evoluir o projeto.

## Visão geral

O projeto é um protótipo Python de ingestão e enriquecimento de cardápios. Ele lê um pequeno catálogo de demonstração local, normaliza os itens, estima sentimento, atributos alimentares e alérgenos por regras simples, guarda os resultados em memória e permite fazer buscas textuais com filtros.

> **Escopo atual:** não há conexão real com o iFood, scraping externo, chamada a modelos de linguagem, geração de embeddings ou banco vetorial persistente. Apesar de alguns nomes e textos do projeto usarem “agente”, “vetorial” e “RAG”, as análises são heurísticas locais e a busca usa similaridade entre tokens.

## Estrutura do repositório

```text
.
├── app.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── PANORAMA_ARQUIVOS_E_CODIGO.md
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── compat.py
│   ├── models.py
│   ├── pipeline.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── review_sentiment_agent.py
│   │   └── schema_normalizer.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   └── async_scraper.py
│   └── vector_store/
│       ├── __init__.py
│       └── vector_indexer.py
├── tests/
│   └── test_pipeline.py
└── tools/
    ├── ingestion_scan.py
    ├── quality_scan.py
    └── security_scan.py
```

`.venv/`, `.mypy_cache/` e `.ruff_cache/` podem existir durante o desenvolvimento. São, respectivamente, o ambiente virtual local e caches de ferramentas; não fazem parte do código-fonte que compõe o produto. O `.gitignore` exclui esses itens, arquivos gerados, segredos locais e bancos/logs.

## Caminho dos dados

1. `AsyncMenuScraper` seleciona registros em `SAMPLE_SCRAPED_DATA`. Os quatro registros são dados fixos incluídos no código.
2. Cada registro é representado como `RawMenuItem`.
3. `ReviewSentimentAgent` conta palavras-chave em avaliações e monta um resumo heurístico de sentimento.
4. `SchemaNormalizerAgent` limpa o preço e estima nome canônico, porção, tags dietéticas e alérgenos a partir de texto.
5. O resultado é um `EnrichedMenuItem`, com dados estruturados e texto consolidado para busca.
6. `VectorIndexer` mantém os itens em um dicionário na memória e compara os tokens da consulta com os tokens dos itens.
7. A busca aplica, antes de ranquear, filtros opcionais de preço máximo e de tags dietéticas.

O mesmo pipeline é usado pelos testes, pelos scanners e pela API. A API carrega o catálogo de demonstração durante a importação de `app.py`; por isso, ao iniciar o servidor, a indexação acontece antes de as rotas atenderem às requisições.

## Arquivos da raiz

### [`app.py`](./app.py)

Cria a API HTTP com FastAPI e uma instância global de `SmartIngestionPipeline`.

- Ao carregar o módulo, ingere o catálogo `"all"` para pré-popular o índice em memória.
- `GET /health`: informa o estado e a quantidade de itens indexados.
- `POST /api/v1/ingest?restaurant_id=...`: executa novamente a ingestão do restaurante informado (ou de todos) e devolve uma amostra dos nomes.
- `POST /api/v1/search`: recebe um `SemanticSearchQuery` em JSON e devolve resultados com pontuação, nome, preço, porção, tags, alérgenos e destaques de sentimento.
- Executado diretamente, inicia Uvicorn na porta `8000`. O bind local padrão é `127.0.0.1`; a variável `HOST` pode alterá-lo. No contêiner, o comando do Docker define `0.0.0.0`.
- Se FastAPI não estiver instalado, o módulo usa um modo de demonstração/CLI, em vez de expor as rotas.

### [`requirements.txt`](./requirements.txt)

Dependências de execução: FastAPI, Uvicorn e Pydantic. Não há dependência de banco vetorial nem de provedor de IA.

### [`requirements-dev.txt`](./requirements-dev.txt)

Inclui as dependências de execução e ferramentas de desenvolvimento: pytest, pytest-asyncio, Bandit, pip-audit, Ruff e mypy. O scanner de qualidade usa `unittest` da biblioteca padrão, embora pytest também esteja disponível.

### [`Dockerfile`](./Dockerfile)

Constrói a imagem da API com Python 3.11 slim, instala `requirements.txt`, copia os arquivos do projeto e inicia Uvicorn na porta 8000, ouvindo em `0.0.0.0`.

### [`docker-compose.yml`](./docker-compose.yml)

Define o serviço `smart-ingestion-api`, constrói a imagem local e publica a porta 8000 do contêiner na porta 8000 do host. Não configura banco de dados ou volume persistente: o índice é reconstruído na inicialização.

### [`README.md`](./README.md)

Apresenta a proposta, um diagrama de arquitetura, instruções de execução, scanners e exemplos. O README também exibe um badge de licença que aponta para `LICENSE`, mas esse arquivo não está presente na estrutura atual. Para o funcionamento efetivo e as limitações implementadas, use este panorama junto com o código-fonte.

### [`.gitignore`](./.gitignore)

Ignora ambientes virtuais, caches e artefatos Python, configurações de editor, arquivos de ambiente/credenciais, bancos locais, dados de vetores e logs. Arquivos `.env.example` e `.env.template` são explicitamente permitidos.

## Pacote `src/`

### [`src/__init__.py`](./src/__init__.py)

Inicializa o pacote `src` e garante que a raiz do projeto esteja no `sys.path`, permitindo imports como `from src.models import ...`.

### [`src/models.py`](./src/models.py)

Define os contratos de dados usados pelos componentes:

- `DietaryPreference`: enumera tags como vegano, vegetariano, sem glúten e convencional.
- `RawMenuItem`: dados brutos de restaurante, título, descrição, preço, categoria e avaliações.
- `AllergenAnalysis`: campos booleanos de alérgenos conhecidos e lista de outros itens identificados.
- `ReviewSentimentSummary`: sentimento, nota estimada, destaques, reclamações e perfil de sabor.
- `EnrichedMenuItem`: formato enriquecido que é indexado e devolvido na busca.
- `SemanticSearchQuery`: texto de busca, preço máximo opcional, filtros dietéticos e quantidade máxima de resultados (`top_k`).
- `SearchResultItem`: item encontrado e sua pontuação de relevância.

Os modelos usam `BaseModel` e `Field` de `src.compat`, em vez de importar diretamente Pydantic.

### [`src/compat.py`](./src/compat.py)

Tenta importar `BaseModel` e `Field` do Pydantic. Se a dependência não estiver instalada, define uma implementação de compatibilidade simples com recursos básicos de objetos, campos padrão e serialização `model_dump()`.

O fallback não substitui toda a validação, conversão e geração de schema do Pydantic; é apenas uma alternativa mínima para permitir alguns usos básicos sem a biblioteca.

### [`src/pipeline.py`](./src/pipeline.py)

Orquestra scraper, análise de sentimento, normalização e indexação. `run_ingestion_sync()` executa a sequência para um restaurante e retorna os itens enriquecidos; `search_sync()` encaminha a consulta ao indexador.

Há também métodos com `async` (`run_ingestion_for_restaurant()` e `search()`), mas atualmente eles apenas chamam as versões síncronas. Portanto, as operações subjacentes não se tornam assíncronas por serem chamadas por esses métodos.

Quando executado como script, ingere os dados de exemplo e imprime demonstrações de busca, filtro de preço e alérgenos do acarajé.

## Subpacotes de `src/`

### `src/scraper/`

#### [`src/scraper/__init__.py`](./src/scraper/__init__.py)

Marca o diretório como pacote Python.

#### [`src/scraper/async_scraper.py`](./src/scraper/async_scraper.py)

- Define `SAMPLE_SCRAPED_DATA`, uma lista local de quatro registros de exemplo: fettuccine, acarajé, bowl vegano e hambúrguer.
- Define `ScrapedMenuRecord` para tipar os registros de exemplo.
- `fetch_restaurant_catalog_sync()` filtra os registros por identificador ou retorna todos quando recebe `"all"`.
- `fetch_restaurant_catalog()` é uma fachada assíncrona que chama o método síncrono.
- `fetch_all_partner_catalogs()` percorre os quatro identificadores de demonstração.

Apesar do nome `AsyncMenuScraper` e do parâmetro `concurrency_limit`, não há requisição HTTP, scraping externo ou concorrência implementada atualmente.

### `src/agents/`

#### [`src/agents/__init__.py`](./src/agents/__init__.py)

Marca o diretório como pacote Python.

#### [`src/agents/review_sentiment_agent.py`](./src/agents/review_sentiment_agent.py)

`ReviewSentimentAgent` analisa as avaliações com listas de palavras-chave positivas, negativas e relacionadas a sabores. A contagem determina categorias e notas predefinidas; algumas palavras também preenchem destaques, reclamações e perfil de sabor.

Não chama um modelo de IA nem realiza análise linguística contextual. Por exemplo, a presença de uma palavra-chave não é suficiente para compreender negação, ironia ou o contexto completo da avaliação. `analyze_reviews()` é um wrapper assíncrono que chama a implementação síncrona.

#### [`src/agents/schema_normalizer.py`](./src/agents/schema_normalizer.py)

`SchemaNormalizerAgent` converte um registro bruto em `EnrichedMenuItem`:

- limpa símbolos do preço e converte o formato brasileiro com vírgula decimal;
- infere tags dietéticas procurando expressões no título e na descrição;
- detecta alguns alérgenos procurando palavras predefinidas;
- estima a porção por palavras como “duplo” ou “combo”;
- limpa trechos entre colchetes/parênteses do nome;
- cria palavras-chave e um texto descritivo para indexação;
- gera um identificador determinístico a partir do restaurante e do nome normalizado.

As inferências são heurísticas de texto, não validação nutricional. Uma ausência de correspondência não garante ausência do ingrediente ou de contaminação cruzada. `normalize()` também é um wrapper assíncrono de uma função síncrona.

### `src/vector_store/`

#### [`src/vector_store/__init__.py`](./src/vector_store/__init__.py)

Marca o diretório como pacote Python.

#### [`src/vector_store/vector_indexer.py`](./src/vector_store/vector_indexer.py)

Implementa o índice em memória:

- tokeniza o texto em minúsculas e remove tokens curtos;
- cria vetores de frequência normalizados por documento;
- calcula similaridade de cosseno sobre tokens em comum;
- acrescenta uma pequena pontuação quando palavras-chave do item aparecem na consulta;
- aplica filtros opcionais de preço máximo e tags dietéticas;
- ordena os resultados e retorna até `top_k`.

Isso não gera embeddings semânticos: consultas que usam sinônimos, paráfrases ou vocabulário diferente podem não encontrar o item esperado. Os dados também se perdem quando o processo termina. Os métodos assíncronos de indexação e busca apenas encaminham para as versões síncronas.

## Testes e scanners

### [`tests/test_pipeline.py`](./tests/test_pipeline.py)

Suíte `unittest` com cinco verificações:

1. leitura dos registros de demonstração;
2. cálculo heurístico de sentimento;
3. normalização de preço, nome e alérgenos;
4. busca com filtro de preço;
5. execução ponta a ponta para o restaurante de acarajé e detecção de crustáceos.

Os testes são locais e usam os dados fixos do projeto; não testam integrações externas.

### [`tools/security_scan.py`](./tools/security_scan.py)

Executa duas verificações locais e retorna código de saída de falha se alguma não passar:

- Bandit para análise estática do código em `src/` e `app.py`;
- pip-audit para auditoria das dependências declaradas em `requirements.txt`.

### [`tools/quality_scan.py`](./tools/quality_scan.py)

Executa sequencialmente:

- Ruff em `app.py`, `src/` e `tests/`;
- mypy em `app.py` e `src/`, incluindo verificação de funções sem anotações completas;
- descoberta e execução dos testes `unittest` em `tests/`.

### [`tools/ingestion_scan.py`](./tools/ingestion_scan.py)

Executa uma verificação funcional local: ingere os quatro itens, confere a quantidade indexada e os preços, valida a detecção de crustáceos no acarajé e verifica uma busca com filtro de preço e outra com filtro vegano. Não acessa serviços externos.

## Como executar

Na raiz do projeto, usando PowerShell no Windows:

```powershell
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python .\src\pipeline.py
python .\tools\ingestion_scan.py
python .\tools\quality_scan.py
python .\tools\security_scan.py
```

Para iniciar a API localmente:

```powershell
python .\app.py
```

Rotas e documentação interativa, quando o servidor estiver ativo:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/docs`

Para executar em contêiner, com Docker instalado:

```powershell
docker compose up --build
```

## Limitações e considerações para evolução

- **Dados:** catálogo de quatro itens fixos; não há coleta real nem atualização de restaurantes.
- **“Agentes”:** regras e palavras-chave, sem modelo de linguagem, provedor externo ou classificação treinada.
- **Busca:** similaridade lexical local, sem embeddings semânticos e sem persistência.
- **Assincronicidade:** interfaces `async` atuais encaminham para métodos síncronos.
- **Alérgenos e dietas:** estimativas heurísticas, inadequadas para prometer segurança alimentar ou substituir informação oficial do restaurante.
- **API:** executa a ingestão inicial ao importar a aplicação; o armazenamento é local ao processo e reinicia vazio a cada nova inicialização.
- **Escala e produção:** não há banco persistente, autenticação, monitoramento ou integração externa configurada.

Esses limites não impedem o uso como demonstração educacional do fluxo, mas devem ser comunicados claramente em apresentações e entrevistas.
