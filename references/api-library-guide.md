# API & Library Guide

Use this file when explaining a new library, function, or class to the learner.
Apply the API spotlight template from SKILL.md Part 1.4.

---

## Pydantic v2

### `BaseModel`
```
📦 Package: pydantic (pip install "pydantic>=2,<3")
📥 Import: from pydantic import BaseModel

What it does:
  Base class for all domain models. Declares fields with type annotations,
  validates input automatically on instantiation, and provides serialization.

Key arguments (field declarations):
  - Use type annotations directly: `name: str`, `age: int`
  - Optional fields: `title: str | None = None`
  - Fields with defaults: `id: UUID = Field(default_factory=uuid4)`

Returns:
  A validated model instance. Raises ValidationError if input doesn't match.

In the LLM Twin pipeline:
  Used for ALL domain entities — User, RawArticleContent, RawArticleDocument,
  and later vector store documents. The single source of truth for data shape.

Gotcha:
  `model_dump()` alone serializes UUIDs as UUID objects, not strings.
  Always use `model_dump(mode="json")` when writing to JSON files.
```

### `Field(default_factory=...)`
```
📦 Package: pydantic
📥 Import: from pydantic import Field

What it does:
  Customizes field behavior — sets defaults, factories, aliases, constraints.
  `default_factory` takes a callable called once per instance (not shared).

Key arguments:
  - default_factory (callable): called with no args to produce the default value
  - default (any): a static default value (don't use for mutable types like lists)
  - alias (str): alternative name for the field in serialized form

Returns:
  A FieldInfo descriptor — Pydantic uses it internally at class definition time.

In the LLM Twin pipeline:
  `id: UUID = Field(default_factory=uuid4)` — every entity gets a unique ID
  automatically without the caller having to pass one.

Gotcha:
  Never use `default=[]` or `default={}` — the same list/dict would be shared
  across all instances. Always use `default_factory=list` / `default_factory=dict`.
```

### `model_dump(mode="json")`
```
📦 Package: pydantic
📥 Import: (method on any BaseModel instance)

What it does:
  Serializes a Pydantic model to a Python dict. With mode="json", converts
  all values to JSON-serializable types (UUID → str, datetime → ISO string, etc.)

Key arguments:
  - mode ("python" | "json"): "json" converts non-serializable types automatically
  - exclude (set): field names to omit from output
  - include (set): only include these field names

Returns:
  dict — ready to pass to json.dump() or an API

In the LLM Twin pipeline:
  Used in JsonStore.save_users() and save_articles() before json.dump().
  Without mode="json", UUID fields would fail json.dump() with TypeError.

Gotcha:
  The default mode is "python" — silently produces UUID objects that crash
  json.dump(). Always specify mode="json" when writing to files or APIs.
```

---

## Python Standard Library

### `pathlib.Path`
```
📦 Package: pathlib (stdlib)
📥 Import: from pathlib import Path

What it does:
  Object-oriented filesystem paths. Replaces os.path with readable, chainable
  path operations that work cross-platform.

Key operations:
  - Path("data") / "users.json"  → joins paths with /
  - path.exists()                → bool, does the path exist?
  - path.mkdir(parents=True)     → creates dir and all parents
  - path.open("r")               → returns a file handle (use with `with`)

Returns:
  Path objects for path operations; context managers for file handles.

In the LLM Twin pipeline:
  JsonStore uses Path to build file paths and check existence before reading.
  Avoids hardcoded string concatenation like "data" + "/" + "users.json".

Gotcha:
  Path objects aren't strings — you can't pass them to APIs expecting str.
  Use str(path) or path.as_posix() when a string is required.
```

### `urlparse`
```
📦 Package: urllib.parse (stdlib)
📥 Import: from urllib.parse import urlparse

What it does:
  Parses a URL string into its components: scheme, netloc (domain), path,
  query, fragment.

Key attributes on the result:
  - .scheme   → "https"
  - .netloc   → "en.wikipedia.org" (includes subdomain)
  - .path     → "/wiki/Python_(programming_language)"
  - .query    → "q=something" (after ?)

Returns:
  ParseResult namedtuple with the above attributes.

In the LLM Twin pipeline:
  Used in CustomArticleCrawler and CrawlerDispatcher to extract the domain
  from a URL: urlparse(link).netloc.removeprefix("www.")
  This gives "medium.com", "github.com", "en.wikipedia.org" etc. as registry keys.

Gotcha:
  .netloc includes port if present ("example.com:8080"). Strip it with
  .split(":")[0] if port-agnostic matching is needed.
```

### Abstract Base Classes (`ABC`, `@abstractmethod`)
```
📦 Package: abc (stdlib)
📥 Import: from abc import ABC, abstractmethod

What it does:
  ABC makes a class abstract — it cannot be instantiated directly.
  @abstractmethod marks a method that every subclass MUST implement.
  Python raises TypeError if you try to instantiate a subclass that hasn't
  implemented all abstract methods.

In the LLM Twin pipeline:
  BaseCrawler(ABC) defines the interface all crawlers must follow.
  This guarantees every crawler has an extract(link, **kwargs) method,
  so the dispatcher can call it without knowing which crawler it has.

Gotcha:
  If you forget to implement an abstract method, the error only appears
  when you try to instantiate the subclass — not at class definition time.
```

### `logging.getLogger(__name__)`
```
📦 Package: logging (stdlib)
📥 Import: import logging; logger = logging.getLogger(__name__)

What it does:
  Creates a logger scoped to the current module. __name__ resolves to the
  dotted module path (e.g. "data_collection_pipeline.crawlers.custom_article").
  Messages propagate up to the root logger, which the application configures.

Key methods:
  - logger.info("message")           → informational
  - logger.warning("message")        → something unexpected but handled
  - logger.exception("message")      → logs message + full traceback (use in except blocks)
  - logger.debug("message")          → verbose detail, off by default

In the LLM Twin pipeline:
  Library code (crawlers, stores) never calls logging.basicConfig() — that's
  the application's job. The library just creates a logger and uses it.
  try_crawler.py calls logging.basicConfig(level=logging.INFO) to activate output.

Gotcha:
  logger.exception() should only be called inside an except block — it
  automatically attaches the current exception's traceback to the log message.
```

---

## requests

### `requests.get()`
```
📦 Package: requests (pip install requests)
📥 Import: import requests

What it does:
  Makes an HTTP GET request to a URL. Returns a Response object with the
  server's reply including status code, headers, and body.

Key arguments:
  - url (str): the URL to fetch
  - timeout (int | float): seconds before giving up — ALWAYS set this
  - headers (dict): HTTP headers to send (User-Agent, Authorization, etc.)
  - params (dict): query string parameters appended to the URL

Returns:
  requests.Response with:
    .status_code  → int (200 = OK, 403 = Forbidden, 404 = Not Found)
    .text         → response body as string
    .json()       → response body parsed as JSON
    .raise_for_status() → raises HTTPError if status >= 400

In the LLM Twin pipeline:
  CustomArticleCrawler.extract() uses it to fetch the HTML of the target URL.
  Always called with timeout=30 and a User-Agent header to avoid 403s.

Gotcha:
  Without timeout, a slow server can hang your program indefinitely.
  Without raise_for_status(), a 404 silently returns empty/error HTML
  that gets saved to your store as if it were real content.
```

---

## BeautifulSoup

### `BeautifulSoup(html, parser)`
```
📦 Package: beautifulsoup4 (pip install beautifulsoup4)
📥 Import: from bs4 import BeautifulSoup

What it does:
  Parses HTML (or XML) into a navigable tree. Lets you find elements by
  tag name, CSS class, attributes, etc.

Key arguments:
  - markup (str): the raw HTML string
  - features (str): which parser to use — always "html.parser" (stdlib, no extra install)

Returns:
  BeautifulSoup object — the parsed document tree.

Key methods on the result:
  - .find("tag")              → first matching element, or None
  - .find("tag", attrs={...}) → find by attribute (e.g. {"name": "description"})
  - .find_all("tag")          → list of all matching elements
  - .get_text(separator, strip) → extract all text content as a string
  - element.get("attr")       → get an attribute value from an element

In the LLM Twin pipeline:
  CustomArticleCrawler uses it to extract title, meta description, language,
  and main content from the fetched HTML.

Gotcha:
  .find() returns None if the element doesn't exist — always guard with
  `if soup.title and soup.title.string` before accessing .string.
  Forgetting this causes AttributeError on pages missing those elements.
```

---

## ZenML (Chapter 3+ )

### `@step` decorator
```
📦 Package: zenml (pip install zenml)
📥 Import: from zenml import step

What it does:
  Marks a Python function as a ZenML pipeline step. ZenML tracks its inputs,
  outputs, and metadata automatically. Steps are the building blocks of pipelines.

Key rules:
  - Function must have type-annotated parameters and return values
  - ZenML serializes inputs/outputs as artifacts in the artifact store
  - Each step runs in isolation — no shared in-memory state between steps

In the LLM Twin pipeline:
  Each crawler call becomes a ZenML step. The output (list of RawArticleDocuments)
  becomes an artifact that the next step (cleaning) can consume.

Gotcha:
  ZenML steps can't return arbitrary Python objects — only types with registered
  materializers. Pydantic models and standard types work out of the box.
```

### `@pipeline` decorator
```
📦 Package: zenml
📥 Import: from zenml import pipeline

What it does:
  Composes multiple @step functions into an executable pipeline. ZenML
  handles the DAG (directed acyclic graph) of step dependencies automatically
  based on which step outputs feed into which step inputs.

In the LLM Twin pipeline:
  The data collection pipeline is a @pipeline that calls crawl_step → clean_step
  → embed_step in sequence, with each step's output passed to the next.

Gotcha:
  You don't call steps directly inside a pipeline — you call them like functions
  and ZenML infers the execution order from data flow, not call order.
```

---

## Qdrant (Chapter 4+)

### `QdrantClient`
```
📦 Package: qdrant-client (pip install qdrant-client)
📥 Import: from qdrant_client import QdrantClient

What it does:
  Client for interacting with a Qdrant vector database instance (local or cloud).
  Handles collections, upserts, searches, and filtered queries.

Key methods:
  - .create_collection(name, vectors_config)  → create a new collection
  - .upsert(collection_name, points)          → insert/update vectors
  - .search(collection_name, query_vector, limit) → nearest-neighbour search
  - .delete_collection(name)                  → drop a collection

In the LLM Twin pipeline:
  The feature pipeline embeds cleaned text chunks and upserts them into Qdrant.
  The inference pipeline queries Qdrant to retrieve relevant context for the LLM.

Gotcha:
  Qdrant uses "collections" (not tables/indices). Each collection has a fixed
  vector dimension — if you change your embedding model, you must recreate
  the collection with the new dimension.
```

---

## ODM Pattern — Object Document Mapper (Chapter 3)

### What is the ODM pattern?
```
Pattern: ODM (Object Document Mapper)
Chapter: 3 — Data Engineering
Analogous to: ORM (Object Relational Mapper) but for NoSQL document stores

What it does:
  Maps between Python domain objects (Pydantic models) and MongoDB documents.
  Hides raw database operations behind a clean Python interface — callers work
  with User and RawArticleDocument objects, never with raw dicts or pymongo calls.

Why it exists:
  MongoDB stores JSON-like documents. Without an ODM, every read requires
  manually constructing dicts and every write requires manually parsing them back.
  The ODM makes the database feel like a collection of Python objects.

In the LLM Twin project:
  JsonStore is a simplified ODM substitute (using local JSON files instead of
  MongoDB). Its load_users() / save_users() methods ARE the ODM pattern —
  they translate between Pydantic models and serialized storage.
  The book's full MongoDB ODM wraps pymongo with the same pattern at scale.

Structure:
  class ArticleRepository:
      def __init__(self, db: MongoDatabase): ...
      def save(self, doc: RawArticleDocument) -> None: ...
      def find_by_link(self, link: str) -> RawArticleDocument | None: ...
      def exists(self, link: str) -> bool: ...

Gotcha:
  The ODM is a pattern, not a library. Don't confuse it with Beanie or
  MongoEngine (full ODM frameworks). The book implements it from scratch
  using Pydantic + pymongo directly.
```

---

## OVM Pattern — Object Vector Mapper (Chapter 4)

### What is the OVM pattern?
```
Pattern: OVM (Object Vector Mapper)
Chapter: 4 — RAG Feature Pipeline
Analogous to: ODM but for vector databases instead of document stores

What it does:
  Maps between Python domain objects and Qdrant vector points.
  A Qdrant point has three parts: id, vector (list of floats), payload (metadata dict).
  The OVM handles converting a Pydantic model into this structure and back.

Why it exists:
  Qdrant doesn't know about your domain objects. Without an OVM, every upsert
  requires manually constructing PointStruct objects and every search result
  requires manually reconstructing your domain objects from the payload dict.

In the LLM Twin pipeline:
  After the cleaning → chunking → embedding steps, each text chunk becomes a
  Qdrant point. The OVM's job is:
    chunk (Pydantic) → embed → PointStruct(id, vector, payload)  [write path]
    SearchResult → payload dict → chunk (Pydantic)                [read path]

Structure:
  class VectorRepository:
      def __init__(self, client: QdrantClient, collection: str): ...
      def upsert(self, doc: CleanedDocument, embedding: list[float]) -> None: ...
      def search(self, query_vector: list[float], limit: int) -> list[CleanedDocument]: ...

Key difference from ODM:
  ODM stores the full document. OVM stores BOTH the vector (for similarity search)
  AND a payload (metadata for filtering and reconstruction). The vector is what
  makes retrieval semantic rather than keyword-based.

Gotcha:
  The payload is a plain dict — Qdrant doesn't validate its shape. If you change
  your Pydantic model fields, old points in the collection will have stale payloads.
  Always version your collections or re-index after schema changes.
```

---

## PEFT / LoRA (Chapter 5+)

### `LoraConfig`
```
📦 Package: peft (pip install peft)
📥 Import: from peft import LoraConfig, get_peft_model

What it does:
  Configures Low-Rank Adaptation (LoRA) — injects small trainable matrices
  into specified layers of a frozen model. Trains <1% of parameters while
  achieving close to full fine-tune quality.

Key arguments:
  - r (int): rank of the adaptation matrices — higher = more capacity, more memory
  - lora_alpha (int): scaling factor — typically 2× r
  - target_modules (list[str]): which layer names to inject LoRA into
    (e.g. ["q_proj", "v_proj"] for attention layers)
  - lora_dropout (float): dropout on LoRA layers (0.05 typical)
  - task_type (str): "CAUSAL_LM" for decoder-only LLMs

Returns:
  LoraConfig object — pass to get_peft_model(model, config)

In the LLM Twin pipeline:
  Chapter 5 wraps the LLM backbone with LoRA before fine-tuning,
  keeping the base weights frozen and only updating the adapters.

Gotcha:
  target_modules names are model-specific — check the model's named_modules()
  to find the right layer names for your architecture.
```
