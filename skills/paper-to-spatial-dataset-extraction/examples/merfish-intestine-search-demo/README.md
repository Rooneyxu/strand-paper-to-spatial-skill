# MERFISH Intestine Search Demo

This is a lightweight search-first demo for the distributable `paper-to-spatial-dataset-extraction` skill.

## User Input

```text
Find a small-intestine MERFISH subcellular-resolution spatial transcriptomics dataset and prepare the normal STRAND metadata extraction workflow.
```

## What This Demonstrates

- The skill starts from a broad topic rather than a DOI, PDF, or dataset page.
- Optional bundled `paper-lookup` searches PubMed and OpenAlex.
- Semantic Scholar returns a public shared-pool `429` rate limit, which is recorded instead of hidden.
- The best candidate is selected for follow-up, but exact metadata counts and boundary fields remain unresolved until article Data availability and repository files are inspected.

## Public Outputs

```text
final_metadata.xlsx
final_metadata.tsv
extraction_report.md
```

## Internal Audit Files

```text
internal/upstream_paper_search.json
internal/dataset_rows.json
internal/download_plan.md
internal/qc_parameters.tsv
internal/unresolved_fields.tsv
```

This demo intentionally does not include PDFs, h5ad/zarr archives, raw data, repository downloads, or host-specific temporary paths.
