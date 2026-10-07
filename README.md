# laipc-plus-search

MVP do motor de busca científica orientado por protocolo do LAIPC+.

## Status

- Stage 1: GitHub/cloud foundation - complete
- Stage 2.1: Europe PMC connector - validated
- Stage 2.2: OpenAlex connector - validated
- Stage 2.3: DataCite dataset connector - validated
- Stage 3: protocol-oriented query engine - in validation
- Stage 4: deduplication + KNOWN/NEW corpus comparison - pending
- Stage 5: final export + first research run - pending

## Stage 3

The active research profile is stored in:

`config/research_profile.yaml`

The engine generates controlled query families instead of a full Cartesian product:

- broad literature
- named stress models
- multidimensional assay signals
- dataset-first searches

The current profile generates at most 14 queries. Each query is sent to:

- Europe PMC
- OpenAlex
- DataCite

At the default limit of 10 records per provider/query, Stage 3 makes at most 42 provider-query calls and can retrieve up to 420 raw records before deduplication.

## How to test Stage 3

Use **Actions > LAIPC+ Search Engine > Run workflow**.

Choose:

- Mode: `protocol`
- Maximum results per query/provider: `10`

Provider and manual query fields are ignored in protocol mode.

The artifact `laipc-stage3-protocol-search` contains:

- `query_plan.json`
- `query_plan.md`
- `protocol_raw_results.json`
- `protocol_run_summary.md`

Duplicates are intentionally retained in Stage 3. Deduplication, corpus comparison and priority classification are Stage 4 responsibilities.

Scientific eligibility is not inferred automatically. S0-S3 / D0-D4 remain part of the later GPT/Work qualification workflow.
