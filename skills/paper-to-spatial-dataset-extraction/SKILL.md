---
name: paper-to-spatial-dataset-extraction
description: Extract final STRAND-compatible subcellular spatial transcriptomics metadata from a paper PDF, DOI/article URL, repository page, dataset landing page, approved downloaded data file, or optional topic search such as "pancreas subcellular-resolution spatial datasets". Use this skill when the user wants a Datasets.xlsx-style metadata table plus an auditable extraction report for MERFISH, seqFISH, Xenium, CosMx, STARmap, Molecular Cartography, or related subcellular spatial datasets. Also use it for upstream paper/dataset discovery before extraction, missing-field audits, download plans, QC/count-convention explanations, and paper-to-dataset curation runs. Do not use for generic paper summaries, review-only articles without reusable data, non-spatial scRNA-seq, bulk RNA-seq, or spot-level spatial data unless the user explicitly asks.
---

# Paper To Spatial Dataset Extraction

## Goal

Create user-facing STRAND metadata from scientific sources. The default result is a small deliverable package:

```text
outputs/final_metadata.xlsx
outputs/final_metadata.tsv
outputs/extraction_report.md
outputs/internal/
```

The public files are for users. `outputs/internal/` is for audit artifacts, intermediate evidence, download plans, unresolved fields, and optional regression comparisons.

## Core Rule

Treat the LLM as the coordinator of a repeatable prevalidation toolchain, not as a reason to write a one-off extraction script. Every filled field needs one of these evidence types:

- Article/PDF evidence.
- Repository or landing-page evidence.
- File-inspection evidence from a reusable validator.
- Curator-provided truth, clearly marked as regression truth and never used as extraction evidence.

## Workflow

1. Create a run directory, usually `<project>/agent/runs/YYYY-MM-DD_<dataset-slug>/outputs/`, with `outputs/internal/` for intermediate files.
2. Normalize inputs: PDF path, DOI, article URL, repository page, dataset landing page, supplementary files, broad topic/search request, and optional regression workbook. Do not ask the user for a STRAND dataset number; external users normally will not have one.
3. If the user gave only a topic or discovery request, read `references/upstream_paper_search_contract.md`, generate targeted scholarly search queries, call the available paper lookup/search route, and write `internal/upstream_paper_search.json`. Select a candidate only when it clearly points to reusable subcellular spatial data; otherwise ask the user to choose.
4. If the user already gave a PDF, DOI, article URL, repository page, or dataset landing page, skip upstream search and start extraction directly.
5. Read `references/strand_dataset_fields.md` and `references/user_output_contract.md` before creating rows or exports.
6. Extract article evidence first: title, DOI, year, method, organism/sample claims, Data availability, and dataset links.
7. Extract repository evidence next: collection/item names, file names, file sizes, access status, and candidate download URLs.
8. Generate a first-pass candidate row without downloading data. Fill exact count fields only when source evidence is explicit.
9. Write `internal/download_plan.md` and wait for user approval before downloading `.h5ad`, `.zarr`, `.tar.gz`, `.zip`, raw images, or other large data.
10. After approval, use reusable validators from `references/prevalidation_toolchain.md`; for h5ad files, prefer `scripts/inspect_h5ad.py`; for 10x/Xenium full output bundles, prefer `scripts/inspect_10x_xenium_outs.py`; for zarr outputs, bootstrap temporary zarr tooling only when needed; for CosMx TileDB/SOMA archives, inspect schema/encoding version before choosing the reader.
11. When raw and processed files disagree, reconstruct count conventions explicitly: raw points, processed cell mask, matrix/layers, boundary geometry, and QC-filtered point tables are separate evidence sources.
12. Apply or record QC rules from `references/qc_workflow.md` when preparing final STRAND-compatible counts. Write the actual per-run parameters to `internal/qc_parameters.tsv`.
13. Keep audit artifacts in `outputs/internal/`, then generate the public files with `scripts/package_final_outputs.py`.
14. Validate public outputs with `scripts/validate_outputs.py --mode public`.
15. If a truth row is available, compare against it only at the audit stage.

## Output Contract

The user-facing outputs are:

- `outputs/final_metadata.xlsx`
- `outputs/final_metadata.tsv`
- `outputs/extraction_report.md`

Internal audit files should live under `outputs/internal/`. Common internal files include:

- `article_metadata.json`
- `upstream_paper_search.json` when discovery was needed
- `dataset_rows.json`
- `dataset_rows.tsv`
- `Datasets_filled.xlsx`
- `curation_report.md`
- `download_plan.md`
- `qc_parameters.tsv`
- `unresolved_fields.tsv`
- `notes_for_future_skill.md`
- `truth_comparison.md` when regression truth is available
- validator outputs such as `source_metadata_inspection.json`, `postdownload_*.json`, or `downloaded_file_inspection.json`

Use `Category`, never the legacy misspelling `Catagory`. Do not expose large downloaded data files in the skill package or output directory.

Treat `No.` as a compatibility column, not as source metadata. Leave it blank unless the user provides a target registry/workbook row ID or explicitly asks for run-local numbering.

## Evidence Discipline

- Do not infer species, organ, tissue, cell type, boundary status, or exact counts from biological common knowledge unless the source or user explicitly permits it.
- Keep boundary fields unknown until a file manifest or file structure confirms cell or nucleus geometry.
- Prefer processed h5ad or formatted data before raw archives. Download raw image/tarball packages only when smaller processed files cannot resolve required fields.
- Do not collapse raw, processed, and STRAND-compatible QC counts into one number. Record the exact file, table, layer, cell mask, and filter behind each count.
- Install temporary validator dependencies only after download/inspection approval, only under an OS temporary directory or the run download directory, and record package versions. Do not modify project dependencies unless the user explicitly asks.
- Keep large downloaded files outside the repo unless the user explicitly gives a storage location.
- Preserve ambiguity in `curation_notes` and `extraction_report.md`; do not hide it by copying a regression truth row.
- Treat the STRAND schema as the default target. Do not generalize the schema unless the user explicitly asks.
- Keep `curation_notes` concise. Put full QC parameters, thresholds, evidence files, and count effects in `internal/qc_parameters.tsv` and the `QC Parameters Used` report section.
- Do not organize user-facing output around internal pilot labels such as `DatasetN`. Use source names, sample names, DOI, repository IDs, and data links as durable identifiers.
- Treat upstream search results as candidate-selection evidence only. Do not fill final count, boundary, QC, or sample fields from search snippets without downstream article, repository, or file inspection evidence.
- Use the bundled sibling `paper-lookup` skill for upstream paper discovery when it is present and callable. If it is missing, lacks API keys, or a database is rate-limited, record the failure and continue through paper-search MCP, BioMCP, or web-search fallback.

## References

- Read `references/strand_dataset_fields.md` for target columns, row semantics, unresolved-field handling, and export checks.
- Read `references/upstream_paper_search_contract.md` when the user asks to search for candidate papers or datasets before extraction.
- Read `references/user_output_contract.md` for the public output package and report structure.
- Read `references/prevalidation_toolchain.md` when planning downloads or deciding which validator to run.
- Read `references/qc_workflow.md` before applying cell/gene filtering or explaining STRAND-compatible filtered counts.
- Read `references/development_process.md` when continuing this skill in a new conversation or modifying the extraction workflow.
- Read `references/demo_evaluation.md` when judging whether the skill is ready, deciding whether to run another demo, or updating regression/eval coverage.
- Keep `THIRD_PARTY_NOTICES.md` with the skill package when distributing bundled optional dependencies such as `paper-lookup`.
