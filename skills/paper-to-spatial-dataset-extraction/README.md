# Paper To Spatial Dataset Extraction

Generate STRAND-style metadata for subcellular spatial transcriptomics datasets from papers, DOI/article links, dataset pages, or approved data files.

The skill is designed for curation, not paper summarization. It coordinates a repeatable toolchain: scholarly search, article/data-page reading, download planning, file validators, QC parameter recording, unresolved-field tracking, and a final evidence report.

## Inputs

Use any of these as starting points:

- Topic search, such as `Find small-intestine MERFISH subcellular spatial datasets`.
- Local PDF path.
- DOI or article URL.
- Repository or dataset landing page.
- Approved downloaded data file, such as h5ad, zarr, 10x Xenium output bundle, or TileDB/SOMA archive.

External users do not need a STRAND dataset number. The `No.` column is kept for spreadsheet compatibility and stays blank unless the user supplies a registry/workbook ID.

## Outputs

Each completed run exposes three user-facing files:

```text
outputs/final_metadata.xlsx
outputs/final_metadata.tsv
outputs/extraction_report.md
```

Audit files live under `outputs/internal/`, commonly including:

```text
upstream_paper_search.json
article_metadata.json
dataset_rows.json
download_plan.md
qc_parameters.tsv
unresolved_fields.tsv
source_metadata_inspection.json
downloaded_file_inspection.json
postdownload_*.json
truth_comparison.md
```

The report explains data sources, downloaded files, field-level evidence, QC/count conventions, unresolved fields, and review status. Missing or uncertain values stay unresolved rather than being filled from nearest-looking numbers.

## Optional Paper Lookup

This distribution can bundle `paper-lookup` as a sibling optional dependency:

```text
agent/skills/paper-lookup/
```

When a user starts with only a topic, the workflow prefers `paper-lookup` for upstream discovery across scholarly databases. If `paper-lookup` is not available, or if one of its databases is rate-limited, the extraction skill records that failure and falls back to available paper-search MCP, BioMCP/PubMed-style search, or web search. Metadata extraction should still proceed when the user provides a concrete paper or dataset link.

See `THIRD_PARTY_NOTICES.md` for the bundled dependency license notice.

## Methodology

This skill follows a CellAtria-inspired agent pattern: the LLM does not act as a one-off script generator. Instead, it orchestrates a prevalidated toolchain and keeps the resulting evidence auditable. Search results can select candidate papers, but final STRAND metadata fields must be supported by article text, repository pages, source metrics, or deterministic file inspection. Large files require a download plan and user approval before inspection. QC thresholds and dataset-specific count conventions are recorded in `internal/qc_parameters.tsv` and summarized in `extraction_report.md`.

Article-ready description:

```text
We implemented paper-to-dataset curation as an agent-orchestrated prevalidation workflow. Given a topic, paper, DOI, repository page, or approved data file, the agent first identifies candidate dataset sources, then coordinates source extraction, download planning, reusable file validators, QC parameter recording, and field-level evidence reporting. The LLM is used to route and audit these tools rather than to directly hallucinate database fields: uncertain values are left unresolved, large files require explicit approval, and each final metadata value is traceable to article, repository, or file-inspection evidence.
```

## Demo

A lightweight search-first demo is included at:

```text
examples/merfish-intestine-search-demo/
```

It starts from a broad request for a small-intestine MERFISH dataset, uses upstream paper lookup to identify a candidate gut epithelium paper, records a Semantic Scholar rate-limit failure, and leaves final count fields unresolved until article Data availability and repository files are inspected.

## Not For

- Generic paper summaries.
- Review writing.
- Automatic large-file downloading without user approval.
- Copying regression truth rows into metadata.
- Non-spatial scRNA-seq, bulk RNA-seq, or spot-level spatial data unless explicitly requested.
