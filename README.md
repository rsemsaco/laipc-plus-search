# laipc-plus-search

MVP do motor de busca científica orientado por protocolo do LAIPC+.

## Status

- Stage 1: GitHub/cloud foundation - complete
- Stage 2.1: Europe PMC connector - validated
- Stage 2.2: OpenAlex connector - validated
- Stage 2.3: DataCite dataset connector - in validation

## Current test

Use **Actions > LAIPC+ Search Engine > Run workflow**.

Choose a provider, enter the query and maximum number of results, then run the workflow.

Current providers:
- `europe_pmc`
- `openalex`
- `datacite`

The workflow runs Python entirely in GitHub-hosted infrastructure and uploads JSON + Markdown artifacts.

### DataCite behavior

For Stage 2.3, the DataCite connector intentionally restricts results to `resourceTypeGeneral=Dataset`. This is the dataset-first arm of the LAIPC+ MVP and helps discover research data that may be linked back to articles through DOI relationships.

### OpenAlex API key

The OpenAlex connector works without a key for basic/casual queries. If we later need a larger free daily budget, create a GitHub Actions secret named `OPENALEX_API_KEY`; the connector will use it automatically.

Scientific eligibility is not inferred by the connectors. The engine retrieves evidence; later stages handle deduplication, prioritization and human/LLM-assisted qualification.
