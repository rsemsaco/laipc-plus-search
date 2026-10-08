# laipc-plus-search

MVP do motor de busca científica orientado por protocolo do LAIPC+.

## Status

- Stage 1: GitHub/cloud foundation - complete
- Stage 2.1: Europe PMC connector - validated
- Stage 2.2: OpenAlex connector - validated
- Stage 2.3: DataCite dataset connector - validated
- Stage 3: protocol-oriented query engine - validated
- Stage 4: deduplication + C01-C45 KNOWN/NEW comparison - in validation
- Stage 5: final export + GPT/Work qualification handoff - pending

## Stage 4

Stage 4 reruns the protocol search and then:

1. deduplicates article records by DOI, then PMID/PMCID, then normalized title;
2. applies conservative fuzzy title matching only to records that lack persistent identifiers;
3. consolidates DataCite concept/version DOI records using identity/version relations;
4. preserves article and dataset records as different resource classes;
5. aggregates the queries and sources that retrieved each unique record;
6. compares unique records against the audited 45-record reference corpus in `reference/corpus_known.csv`;
7. labels records as:
   - `KNOWN`
   - `RELATED_TO_KNOWN` for datasets/resources linked to a known article
   - `NEW`
8. assigns only a retrieval-priority heuristic: `Alta`, `Media`, or `Exploratoria`.

The priority heuristic is not an S/D classification. New records are never assigned S0-S3 or D0-D4 automatically.

When a result matches the existing C01-C45 corpus, the previously audited S/D values are carried forward as reference metadata.

## Stage 4 test

Use **Actions > LAIPC+ Search Engine > Run workflow**.

Choose:

- Mode: `stage4`
- Maximum results per query/provider: `10`

The artifact `laipc-stage4-dedup-known-new` contains:

- `query_plan.json`
- `query_plan.md`
- `protocol_raw_results.json`
- `stage4_unique_records.json`
- `stage4_all_unique.csv`
- `stage4_new_candidates.csv`
- `stage4_dedup_audit.json`
- `stage4_summary.md`

Stage 5 will create the final XLSX/CSV package and prepare the selected NEW records for GPT + Work review and S/D qualification.
