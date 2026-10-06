# laipc-plus-search

MVP do motor de busca científica orientado por protocolo do LAIPC+.

## Status

- Stage 1: GitHub/cloud foundation - complete
- Stage 2.1: Europe PMC connector - validated
- Stage 2.2: OpenAlex connector - in validation
- Stage 2.3: DataCite connector - pending

## Current test

Use **Actions > LAIPC+ Search Engine > Run workflow**.

Choose a provider, enter the query and maximum number of results, then run the workflow.

Current providers:
- `europe_pmc`
- `openalex`

The workflow runs Python entirely in GitHub-hosted infrastructure and uploads JSON + Markdown artifacts.

### OpenAlex API key

The connector works without a key for basic/casual queries. If we later need a larger free daily budget, create a GitHub Actions secret named `OPENALEX_API_KEY`; the connector will use it automatically.

Scientific eligibility is not inferred by the connectors. The engine retrieves evidence; later stages handle deduplication, prioritization and human/LLM-assisted qualification.
