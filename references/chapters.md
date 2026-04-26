# Chapter-by-Chapter Reference

## Chapter 1 — LLM Twin Concept & Architecture
- What the LLM Twin is and why it matters vs. using ChatGPT directly
- Defining the MVP scope
- FTI pipeline design pattern and its benefits
- System architecture: data collection → feature pipeline → training pipeline → inference pipeline

## Chapter 2 — Tooling & Installation
Key tools used throughout the book:
- **Poetry** — dependency/virtual environment management
- **Poe the Poet** — task runner
- **ZenML** — pipeline orchestrator, artifact store, metadata tracking
- **Hugging Face** — model registry
- **Comet ML** — experiment tracker
- **Opik** — prompt monitoring
- **MongoDB** — NoSQL data warehouse for unstructured data
- **Qdrant** — vector database for embeddings
- **AWS SageMaker** — training and inference compute

## Chapter 3 — Data Engineering
- Designing and implementing the LLM Twin's **data collection pipeline**
- Crawlers: `GitHubCrawler`, `CustomArticleCrawler`, `MediumCrawler`
- **Dispatcher pattern** for instantiating the right crawler per URL domain
- ODM (Object Document Mapper) pattern for MongoDB
- ZenML pipeline steps for orchestration
- Storing raw data in the NoSQL data warehouse

### Dispatcher Pattern (Chapter 3 deep dive)
The dispatcher is a registry mapping domain strings to crawler classes.

```python
class CrawlerDispatcher:
    def __init__(self, store):
        self._registry: dict[str, type[BaseCrawler]] = {}
        self.store = store

    def register(self, domain: str, crawler_class: type[BaseCrawler]) -> "CrawlerDispatcher":
        self._registry[domain] = crawler_class
        return self  # enables chaining

    def get_crawler(self, link: str) -> BaseCrawler:
        domain = urlparse(link).netloc.removeprefix("www.")
        crawler_class = self._registry.get(domain, CustomArticleCrawler)
        return crawler_class(store=self.store)
```

Key design points:
- Stores **classes**, not instances — deferred instantiation, no shared state
- Falls back to `CustomArticleCrawler` for unknown domains
- Returns `self` from `register()` for method chaining
- Domain extraction reuses `urlparse().netloc.removeprefix("www.")`

## Chapter 4 — RAG Feature Pipeline
Core RAG concepts:
- Why use RAG (hallucinations, stale knowledge)
- Vanilla RAG: ingestion → retrieval → generation
- Embeddings: what they are, how they're created, why they're powerful
- Vector DB internals: indexing algorithms, HNSW, operations
- Advanced RAG techniques: pre-retrieval, retrieval, post-retrieval optimization

Implementation:
- Feature store design (batch pipelines, Change Data Capture)
- Cleaning → chunking → embedding pipeline steps
- Pydantic domain entities, OVM (Object Vector Mapper)
- Dispatcher + handler layers
- Loading documents to Qdrant

## Chapter 5 — Supervised Fine-Tuning (SFT)
Dataset creation:
- General framework for instruction datasets
- Data quantity guidelines
- Curation: rule-based filtering, deduplication, decontamination, quality eval
- Data generation and augmentation strategies

SFT techniques:
- When to fine-tune vs. use RAG/prompting
- Instruction dataset formats and chat templates
- **LoRA** — Low-Rank Adaptation for efficient fine-tuning
- **QLoRA** — quantized LoRA for lower memory usage
- Full fine-tuning tradeoffs
- Key training parameters: learning rate, batch size, max length, epochs, optimizers,
  weight decay, gradient checkpointing

## Chapter 6 — Preference Alignment
- Preference datasets: structure, quantity, generation, evaluation
- Generating and evaluating preference pairs
- **DPO** (Direct Preference Optimization)
- **PPO** (Proximal Policy Optimization) / RLHF overview
- Creating the LLM Twin's preference dataset
- Practical preference alignment training

## Chapter 7 — Evaluation
- LLM evaluation frameworks and best practices
- Types of evaluation: automatic vs. human
- Benchmark datasets and metrics
- Evaluating the LLM Twin's outputs
- Using LLM-as-judge patterns
- Evaluation during fine-tuning vs. post-deployment

## Chapter 8 — Training Pipeline (Production)
- End-to-end SFT training pipeline architecture
- ZenML training pipeline integration
- SageMaker training jobs
- Experiment tracking with Comet ML
- Model versioning and artifact management
- Checkpointing and resuming training

## Chapter 9 — RAG Inference Pipeline
Advanced RAG for production:
- **Query expansion** — generating multiple query variants
- **Self-querying** — extracting metadata filters from natural language
- **Filtered vector search** — using metadata to narrow retrieval
- **Reranking** — post-retrieval relevance scoring
- Retrieval module implementation
- Assembling the full RAG inference pipeline with the fine-tuned LLM

## Chapter 10 — Inference Pipeline Deployment
Deployment decisions:
- Throughput vs. latency tradeoffs
- Online real-time vs. async vs. batch inference
- Monolithic vs. microservices architecture for model serving

LLM Twin deployment:
- Deploying to **AWS SageMaker** using Hugging Face DLCs
- Configuring SageMaker roles and endpoints
- Building a **FastAPI** business microservice
- **Autoscaling** configuration (scalable targets, policies, cooldown periods)

## Chapter 11 — MLOps & LLMOps
- DevOps → MLOps → LLMOps evolution
- MLOps core components and principles
- LLMOps additions: human feedback, guardrails, prompt monitoring
- Deploying all pipelines to AWS cloud (MongoDB, Qdrant, ZenML cloud)
- Containerizing with Docker
- **CI/CD/CT pipelines** using GitHub Actions
- Prompt monitoring and alerting with Opik

---

## Chapter 3 — Checkpoint Exercises

### Checkpoint 3.7 — MediumCrawler

**🎯 Goal**: Build a site-specific crawler for Medium that extracts cleaner article
content than the generic `CustomArticleCrawler`.

**💡 Concept warm-up**

1. `CustomArticleCrawler` uses `<article>` → `<main>` → `<body>` fallback.
   Open any Medium article in your browser, right-click → Inspect. What HTML tag
   or CSS class wraps the actual article body? How is this different from the generic fallback?

2. The dispatcher registers crawlers by domain. What domain string should
   `MediumCrawler` be registered under? (Hint: try `urlparse` on a Medium URL.)

3. `MediumCrawler` will still use `JsonStore` and `User` exactly like
   `CustomArticleCrawler`. What does that tell you about how much of
   `extract()` you can reuse vs. what you need to change?

**🔨 Exercise**

Create `src/data_collection_pipeline/crawlers/medium.py`:

```python
class MediumCrawler(BaseCrawler):
    model = RawArticleDocument

    def __init__(self, store: JsonStore) -> None: ...

    def extract(self, link: str, *, user: User, **kwargs) -> None:
        # Same structure as CustomArticleCrawler.extract()
        # but use Medium-specific selectors for main_content
        # instead of the generic <article>/<main>/<body> fallback
        ...
```

Then register it in `try_crawler.py`:
```python
dispatcher.register("medium.com", MediumCrawler)
```

**What good looks like**:
- Same interface as `CustomArticleCrawler` — only the content extraction logic differs
- Uses a Medium-specific CSS selector or tag to get cleaner body text
- Falls back gracefully if the selector doesn't match (some Medium pages differ)
- Tested against a real Medium article URL

---

### Checkpoint 3.8 — GitHubCrawler

**🎯 Goal**: Build a crawler for GitHub repository pages that extracts the README
as the main content rather than the full page HTML.

**💡 Concept warm-up**

1. A GitHub repo page (`github.com/user/repo`) has a lot of navigation, sidebars,
   and footer content. Where does the README content live in the DOM?
   (Hint: Inspect the page — look for an `article` tag with a specific class.)

2. GitHub is aggressive about bot blocking. What does `requests.get()` return
   when it blocks you — a 403, a 429, or something else? How does
   `raise_for_status()` help you detect this?

3. The book's `GitHubCrawler` is designed for repository pages, not arbitrary
   GitHub URLs (issues, PRs, profiles). Should the crawler validate that the
   link is a repo page before scraping? What's the trade-off?

**🔨 Exercise**

Create `src/data_collection_pipeline/crawlers/github.py`:

```python
class GitHubCrawler(BaseCrawler):
    model = RawArticleDocument

    def __init__(self, store: JsonStore) -> None: ...

    def extract(self, link: str, *, user: User, **kwargs) -> None:
        # Fetch the GitHub repo page
        # Extract the README content from the article tag
        # Build RawArticleDocument and save via JsonStore
        ...
```

Register it:
```python
dispatcher.register("github.com", GitHubCrawler)
```

**What good looks like**:
- Targets the README `<article>` element specifically
- Handles the case where a repo has no README (content_root falls back gracefully)
- User-Agent header set (GitHub blocks `python-requests/*` too)
- Tested against a real GitHub repo URL

---

### Checkpoint 3.9 — ZenML Pipeline Steps

**🎯 Goal**: Wrap the dispatcher + crawlers in a ZenML `@step` and compose them
into a `@pipeline` so the data collection is orchestrated and tracked.

**💡 Concept warm-up**

1. Right now `try_crawler.py` calls `crawler.extract()` directly in a script.
   What does wrapping it in a `@step` give you that the script doesn't have?
   (Think: what does ZenML track that your script doesn't?)

2. A ZenML `@step` must declare typed inputs and outputs. What would the
   *output* of a crawl step be? What type annotation would you use?

3. ZenML pipelines compose steps by passing outputs to inputs. If you have:
   - `crawl_step()` → returns `list[RawArticleDocument]`
   - `clean_step(docs: list[RawArticleDocument])` → Chapter 4
   
   How does ZenML know to run `crawl_step` before `clean_step`?
   Is it the order you write the calls, or something else?

**🔨 Exercise**

Create `src/data_collection_pipeline/pipelines/data_collection.py`:

```python
from zenml import step, pipeline
from data_collection_pipeline.domain.models import RawArticleDocument

@step
def crawl_articles_step(
    links: list[str],
    author_full_name: str,
    data_dir: str = "data",
) -> list[RawArticleDocument]:
    """Crawl a list of URLs and return stored article documents."""
    ...

@pipeline
def data_collection_pipeline(links: list[str], author_full_name: str) -> None:
    """End-to-end data collection pipeline."""
    crawl_articles_step(links=links, author_full_name=author_full_name)
```

**API spotlight — `@step`**: See `references/api-library-guide.md` ZenML section.

**What good looks like**:
- `@step` function has fully type-annotated parameters and return value
- Uses `CrawlerDispatcher` internally — not hardcoded to one crawler
- `@pipeline` composes the step cleanly
- Can be run with `data_collection_pipeline(links=[...], author_full_name="...")`

---

## Appendix — MLOps Principles
1. Automation/operationalization
2. Versioning
3. Experiment tracking
4. Testing (types, what to test, examples)
5. Monitoring (logs, metrics, system metrics)
