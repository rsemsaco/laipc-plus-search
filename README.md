# laipc-plus-search

MVP do motor de busca científica orientado por protocolo do LAIPC+.

## Status

- Stage 1: GitHub/cloud foundation - complete
- Stage 2.1: Europe PMC connector - validated
- Stage 2.2: OpenAlex connector - validated
- Stage 2.3: DataCite dataset connector - validated
- Stage 3: protocol-oriented query engine - validated
- Stage 4: deduplication + C01-C45 KNOWN/NEW comparison - validated after persistent-ID normalization fix
- Stage 5: final export + GPT/Work qualification handoff - in validation

## Important Stage 4 correction

The first Stage 4 validation exposed an escaping bug in DOI/PMID/PMCID regular expressions. Persistent identifiers were present in provider metadata but were not being normalized, causing known records such as C22 to appear as NEW.

The normalization is now corrected before Stage 5. Stage 5 reruns the search and Stage 4 processing, so no separate Stage 4 rerun is required.

## Stage 5

Stage 5 produces the first practical research-delivery package.

Use **Actions > LAIPC+ Search Engine > Run workflow**.

Choose:

- Mode: `stage5`
- Maximum results per query/provider: `10`

The artifact `laipc-stage5-final-package` contains:

- `LAIPC_Search.xlsx`
- `LAIPC_Search.csv`
- `work_handoff.csv`
- `search_log.json`
- `search_summary.md`
- query plan and raw/audit files for reproducibility

### Workbook

`LAIPC_Search.xlsx` contains:

- `Resumo`
- `Candidatos_NEW`
- `Alta_Prioridade`
- `Datasets`
- `KNOWN`
- `Work_Handoff`
- `Plano_Busca`
- `Metodologia`

### GPT / Work boundary

The search engine does not assign S0-S3 or D0-D4 to NEW records.

`Work_Handoff` contains all high-retrieval-priority NEW/RELATED records plus every dataset record. These records are intended to be brought to ChatGPT for scientific pre-triage. ChatGPT then selects the papers/datasets that require PDF/data audit in Work.

Existing S/D values are carried forward only for matches against the already audited C01-C45 corpus.
