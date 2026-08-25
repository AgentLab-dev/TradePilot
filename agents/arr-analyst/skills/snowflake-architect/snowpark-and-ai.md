# Snowpark, Container Services, and Cortex AI

Reference companion to `snowflake-architect/SKILL.md` §1 and §6.

## 1. Snowpark — Python / Java / Scala inside Snowflake

Snowpark lets you embed custom code directly into Snowflake. Three execution surfaces:

| Surface | When to use | Cost |
|---|---|---|
| **Snowpark UDF / UDTF** | Single-row or table-valued transformation | Per query credits |
| **Snowpark Stored Procedure** | Multi-step orchestration (CALL syntax) | Per query credits |
| **Snowpark Container Service** | Long-running services (REST API, ML inference, GPU) | Per-second compute (separate from warehouses) |

## 2. Snowpark UDFs (Python)

```sql
CREATE OR REPLACE FUNCTION fiscal_quarter_from_date(d DATE)
RETURNS VARCHAR
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
HANDLER = 'fiscal_quarter'
AS $$
def fiscal_quarter(d):
    if d is None:
        return None
    month = d.month
    if month >= 2 and month <= 4: return f"FY{(d.year + (1 if month >= 2 else 0))%100:02d}Q1"
    if month >= 5 and month <= 7: return f"FY{(d.year + 1)%100:02d}Q2"
    if month >= 8 and month <= 10: return f"FY{(d.year + 1)%100:02d}Q3"
    return f"FY{(d.year + (1 if month >= 2 else 0))%100:02d}Q4"
$$;

-- Use like any SQL function
SELECT fiscal_quarter_from_date('2026-03-15');    -- 'FY26Q1'
```

### When to use Python UDF vs SQL UDF

| Need | Python UDF | SQL UDF / Macro |
|---|---|---|
| Cross-tabular math (e.g., regression coef) | Yes | No |
| Library-dependent logic (numpy, pandas, etc.) | Yes | No |
| Pattern matching that's awkward in SQL (e.g., regex grammar) | Yes | Possible but ugly |
| Simple branching CASE WHEN | No (slower) | Yes |
| Aggregate operations | No (Python UDFs are scalar by default) | Yes |
| Cross-row logic | UDTF (table function) | Window function |

### Python package management

```sql
CREATE OR REPLACE FUNCTION my_ml_score(features ARRAY)
RETURNS NUMBER
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('scikit-learn==1.4.0', 'numpy==1.26.0')
HANDLER = 'score'
IMPORTS = ('@my_stage/model.pkl')
AS $$
import pickle
import numpy as np
from joblib import load
model = load('/tmp/model.pkl')

def score(features):
    return float(model.predict(np.array([features]))[0])
$$;
```

Available packages: Snowflake ships ~10,000 pre-built Python packages via the Anaconda channel. List via:

```sql
SELECT * FROM information_schema.packages
WHERE package_name = 'scikit-learn'
ORDER BY version DESC;
```

### Performance: vectorized UDFs (the principal pattern)

Standard UDFs process one row at a time. Vectorized UDFs process batches via Pandas:

```sql
CREATE OR REPLACE FUNCTION my_vectorized_udf(x NUMBER)
RETURNS NUMBER
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('pandas')
HANDLER = 'vec_handler'
AS $$
import pandas as pd
from _snowflake import vectorized

@vectorized(input=pd.DataFrame, max_batch_size=10000)
def vec_handler(df):
    return df[0] * 2 + 1     # vectorized — much faster than row-by-row
$$;
```

Vectorized UDFs are 10-100× faster than scalar UDFs for any non-trivial Python logic.

## 3. Snowpark Stored Procedures (Python)

```sql
CREATE OR REPLACE PROCEDURE refresh_finance_data(start_date DATE, end_date DATE)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.11'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'run'
AS $$
def run(session, start_date, end_date):
    session.sql(f"""
        DELETE FROM finance_line_analytics
        WHERE as_was_date BETWEEN '{start_date}' AND '{end_date}'
    """).collect()

    session.sql(f"""
        INSERT INTO finance_line_analytics
        SELECT * FROM stg_finance_line_analytics
        WHERE as_was_date BETWEEN '{start_date}' AND '{end_date}'
    """).collect()

    row_count = session.sql("SELECT COUNT(*) FROM finance_line_analytics").collect()[0][0]
    return f"Refreshed {row_count} rows for {start_date} to {end_date}"
$$;

-- Call it
CALL refresh_finance_data('2026-01-01', '2026-03-31');
```

### Stored proc vs Task vs dbt run

| | Stored Procedure | Task | dbt run |
|---|---|---|---|
| Trigger | Explicit CALL | Schedule / stream | Manual / orchestrator |
| Multi-step logic | Yes (Python control flow) | Yes (SQL only) | Yes (dbt graph) |
| Error handling | Try/except in Python | Limited (next task or alert) | dbt test failures |
| Best for | One-off complex orchestrations (e.g., backfill) | Recurring atomic SQL | Standard ETL |

## 4. Snowpark Container Services (SPCS)

For workloads that don't fit the warehouse model: long-running services, GPU-needed inference, custom servers.

### Architecture

```
Snowflake Account
└── Compute Pool (set of GPU or CPU nodes)
    └── Service (a Docker container running on the pool)
        ├── Endpoint (HTTP/REST)
        └── Mounts to Snowflake stages (data access)
```

### Setup

```sql
-- Compute pool (where containers run)
CREATE COMPUTE POOL my_pool
    MIN_NODES = 1
    MAX_NODES = 4
    INSTANCE_FAMILY = GPU_NV_S;    -- GPU instances

-- Service from container image
CREATE SERVICE my_inference_service
    IN COMPUTE POOL my_pool
    FROM SPECIFICATION '
spec:
  containers:
    - name: inference
      image: /my_db/my_schema/my_repo/inference:latest
      env:
        MODEL_PATH: /app/model.pkl
      volumeMounts:
        - name: model
          mountPath: /app
      readinessProbe:
        httpGet:
          path: /health
          port: 8080
  endpoints:
    - name: predict
      port: 8080
      public: true
  volumes:
    - name: model
      source: "@my_stage/model.pkl"
';
```

### Call the service

```sql
-- Service function (called like a UDF, executes in the container)
CREATE FUNCTION predict_arr(features ARRAY)
    RETURNS NUMBER
    SERVICE = my_inference_service
    ENDPOINT = predict;

SELECT predict_arr([1.0, 2.5, 100]) AS predicted_arr;
```

### Use cases

- **ML inference at scale** — model too big for UDF; SPCS handles it
- **Custom REST APIs** — host a service inside Snowflake to avoid data egress
- **GPU-bound workloads** — LLM fine-tuning, image processing
- **Long-running jobs** — daemons that watch a stream and process events

### Cost

SPCS charges per second of compute (separate from warehouse credits). GPU instances are 10-50× more expensive than CPU. Tune `MIN_NODES = 0` for cost when idle.

## 5. Cortex AI — LLM in SQL

Cortex provides built-in LLM functions invokable from SQL. No external API call, no data egress.

### Single-row functions

```sql
-- Complete a prompt
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'mistral-large',
    'Summarize this support ticket: ' || ticket_text
) AS summary
FROM support_tickets
WHERE created_at > DATEADD('day', -1, CURRENT_DATE());

-- Translate
SELECT SNOWFLAKE.CORTEX.TRANSLATE(comment_text, 'en', 'es')
FROM customer_comments;

-- Sentiment
SELECT SNOWFLAKE.CORTEX.SENTIMENT(review_text) AS sentiment_score
FROM product_reviews;

-- Summarize
SELECT SNOWFLAKE.CORTEX.SUMMARIZE(article_text)
FROM articles;
```

### AI functions (newer, aggregation-friendly)

```sql
-- AI_FILTER: filter rows by natural language predicate
SELECT * FROM support_tickets
WHERE AI_FILTER('Is this ticket about a billing issue?', ticket_text);

-- AI_CLASSIFY: multi-class
SELECT ticket_id,
       AI_CLASSIFY(ticket_text, ['Billing', 'Technical', 'Account', 'Other'])::VARIANT:label AS category
FROM support_tickets;

-- AI_SUMMARIZE_AGG: summarize a GROUP of rows
SELECT account_id,
       AI_SUMMARIZE_AGG(ticket_text, 'top 3 themes in 50 words') AS account_themes
FROM support_tickets
GROUP BY account_id;

-- AI_AGG: aggregate by natural-language instruction
SELECT product_l1,
       AI_AGG(review_text, 'extract the most common complaint as a single sentence') AS complaint
FROM reviews
GROUP BY product_l1;
```

### Cortex Search (hybrid keyword + vector)

```sql
-- One-time setup
CREATE CORTEX SEARCH SERVICE doc_search
    ON content
    ATTRIBUTES title, doc_id
    WAREHOUSE = compute_wh
    TARGET_LAG = '1 hour'
AS
    SELECT doc_id, title, content FROM documents;

-- Query
SELECT * FROM TABLE(doc_search.SEARCH('cancellation refund policy', 10));
```

### Embedding-based vector search

```sql
-- Generate embedding
SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', 'my query text')
    AS query_vec;

-- Cosine similarity against pre-computed embeddings
SELECT doc_id, content,
       VECTOR_COSINE_SIMILARITY(embedding_vec, query_vec) AS sim
FROM documents
ORDER BY sim DESC LIMIT 10;
```

### Cortex cost model

Cortex functions charge per token (input + output). Track via:

```sql
SELECT function_name, SUM(token_credits) AS total_credits
FROM snowflake.account_usage.cortex_functions_usage_history
WHERE start_time > DATEADD('day', -7, CURRENT_TIMESTAMP())
GROUP BY 1
ORDER BY 2 DESC;
```

### When to use Cortex vs external LLM (OpenAI, Anthropic, etc.)

| Need | Cortex | External LLM |
|---|---|---|
| Data must stay in Snowflake (compliance) | Yes | No (egress) |
| Need latest GPT-5 / Claude Opus / Gemini Ultra | Limited (Snowflake hosts a curated set) | Yes |
| Cost per token | Comparable | Provider-dependent |
| Latency | Low (no network egress) | Higher |
| Throughput (high-volume batch) | Yes | Yes |
| Sub-second per-row inference | OK | Better w/ provider streaming |

**Rule:** for governance-sensitive data, use Cortex. For cutting-edge models, integrate external via External Functions.

## 6. External Functions (call out to AWS Lambda / GCP Cloud Functions)

When Cortex doesn't have the model you need, call out:

```sql
-- API integration setup (one-time, per cloud provider)
CREATE OR REPLACE API INTEGRATION my_api_int
    API_PROVIDER = AWS_API_GATEWAY
    API_AWS_ROLE_ARN = 'arn:aws:iam::xxx:role/snowflake_external_func'
    API_ALLOWED_PREFIXES = ('https://xxx.execute-api.us-west-2.amazonaws.com/')
    ENABLED = TRUE;

-- External function
CREATE OR REPLACE EXTERNAL FUNCTION call_openai(prompt STRING, model STRING)
    RETURNS VARCHAR
    API_INTEGRATION = my_api_int
    AS 'https://xxx.execute-api.us-west-2.amazonaws.com/prod/openai';

-- Use
SELECT call_openai('Summarize: ' || ticket_text, 'gpt-4') FROM support_tickets;
```

### External Function vs Snowpark Container Service

| | External Function | SPCS |
|---|---|---|
| Compute location | Outside Snowflake (Lambda, etc.) | Inside Snowflake account |
| Data egress | Yes (data leaves Snowflake) | No |
| Latency | Higher (network hop) | Lower |
| Cost | External + minor Snowflake | All in Snowflake bill |
| Best for | Calling cutting-edge external APIs | Self-hosted ML / custom services |

## 7. Common AI patterns

### Pattern: text enrichment pipeline

```sql
-- 1. Capture raw tickets via Stream
CREATE STREAM ticket_stream ON TABLE support_tickets;

-- 2. Task triggered on new ticket
CREATE TASK enrich_tickets
    WAREHOUSE = compute_wh
    SCHEDULE = '5 MINUTE'
    WHEN SYSTEM$STREAM_HAS_DATA('ticket_stream')
AS
    INSERT INTO ticket_enrichments (ticket_id, category, summary, sentiment, embedding)
    SELECT
        ticket_id,
        AI_CLASSIFY(ticket_text, ['Billing','Technical','Account'])::VARIANT:label,
        SNOWFLAKE.CORTEX.SUMMARIZE(ticket_text),
        SNOWFLAKE.CORTEX.SENTIMENT(ticket_text),
        SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', ticket_text)
    FROM ticket_stream
    WHERE METADATA$ACTION = 'INSERT';

ALTER TASK enrich_tickets RESUME;
```

### Pattern: semantic search over docs

```sql
-- Generate embeddings on insert
CREATE TABLE doc_embeddings AS
SELECT doc_id, title, content,
       SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', content) AS embedding
FROM documents;

-- Query
SELECT doc_id, title,
       VECTOR_COSINE_SIMILARITY(
           embedding,
           SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', :query)
       ) AS similarity
FROM doc_embeddings
ORDER BY similarity DESC
LIMIT 10;
```

### Pattern: data quality triage with LLM

```sql
SELECT
    model_name,
    error_message,
    SNOWFLAKE.CORTEX.COMPLETE(
        'mistral-large',
        'You are a dbt expert. Classify this error into one of: schema_change, permission, timeout, data_quality, other. Error: ' || error_message
    ) AS llm_classification
FROM dbt_run_failures
WHERE failure_time > DATEADD('day', -1, CURRENT_TIMESTAMP());
```

## 8. Anti-patterns to refuse in code review

| Anti-pattern | Why it's bad | Refusal script |
|---|---|---|
| Python UDF for trivial CASE WHEN logic | 10× slower than SQL macro | "Use a macro; UDFs are for library-dependent logic" |
| Non-vectorized UDF for >1M rows | Performance disaster | "Switch to @vectorized; 10-100× faster" |
| Cortex AI for financial metric computation | Non-deterministic; auditability nightmare | "Cortex is for narrative/classification, not numbers" |
| Storing model files in stages without versioning | Reproducibility lost | "Use SP versioning + model registry" |
| SPCS always-on (MIN_NODES = MAX_NODES) | Idle cost | "Set MIN_NODES = 0; auto-scale on demand" |
| External function with no caching | Same prompt computed 1000× | "Cache results in a table; query the cache before calling" |
| Calling external OpenAI from a UDF in a slim CI run | Slim CI hits OpenAI for every changed model | "Move AI enrichment to a dedicated task, not a model UDF" |
