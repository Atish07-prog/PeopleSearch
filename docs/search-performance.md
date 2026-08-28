# Search Performance

The People Search API uses PostgreSQL for normalized-name search. Phase 10 adds the `pg_trgm` extension and a GIN trigram index on `search_profiles.normalized_name`.

This supports the existing substring name search as the dataset grows, without changing the API or adding a separate search engine.

## Result ordering

For a query, results are ordered by:

1. Exact normalized-name match.
2. Name beginning with the normalized query.
3. Other substring matches.

## Measuring after a larger load

Use PostgreSQL to inspect the actual query plan once a representative category batch has been ingested:

```sql
EXPLAIN ANALYZE
SELECT id, display_name
FROM search_profiles
WHERE normalized_name LIKE '%kishan%'
ORDER BY normalized_name
LIMIT 10;
```

Do not add OpenSearch, vector search, or AI ranking unless measurements show PostgreSQL is no longer sufficient for the required query volume and relevance.
