# laipc-plus-search

MVP do motor de busca científica orientado por protocolo do LAIPC+.

## Status

- Stage 1: GitHub/cloud foundation - complete
- Stage 2.1: Europe PMC connector - in validation
- Stage 2.2: OpenAlex connector - pending
- Stage 2.3: DataCite connector - pending

## Current test

Use **Actions > LAIPC+ Search Engine > Run workflow**.

The current workflow queries Europe PMC from a GitHub-hosted Python runner and uploads a JSON result plus a short Markdown summary as an artifact.

Scientific eligibility is not inferred by the connector. The search engine retrieves evidence; later stages handle deduplication, prioritization and human/LLM-assisted qualification.
