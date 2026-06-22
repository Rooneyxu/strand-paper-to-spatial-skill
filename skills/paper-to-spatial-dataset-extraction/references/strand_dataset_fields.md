# STRAND Dataset Fields

Use this reference when generating `final_metadata.xlsx`, `final_metadata.tsv`, and the internal `dataset_rows.*` audit files.

## Row Semantics

One row represents one sample. If sample granularity is unclear, create one dataset-level candidate row, set `Sample Name` to `-`, set `review_required` to `true`, and explain the ambiguity in `curation_notes`.

## Target Columns

Export columns in this order:

```text
FINISH
No.
Dataset
Category
Technology
Species
Organ
Tissue
Cell Type
Group
Sample Name
No.batch
Raw No.cells
No.genes
cellclass
celltype（minor）
Cell boundary
Nuclei boundary
Filtered No.cells/nuclei
cells
genes
No.transcripts
median transcripts
No.NucleiBoundary
Data link
suggested_finish_status
usability_status
review_required
curation_notes
```

Use `Category`; never output `Catagory`.

## Filling Rules

- `FINISH`: leave blank. It is a human curator status.
- `No.`: compatibility column for STRAND-style tables. External users usually do not know a STRAND registry number; leave blank by default. Fill only when the user provides a target workbook/registry ID, or when they explicitly request run-local row numbering.
- `Dataset`: use source names when available; otherwise use `Technology + tissue/cell line + condition`.
- `Category`: usually `cell line` or `tissue`; explain other values.
- `Technology`: use source terminology such as `MERFISH`, `seqFISH+`, `Xenium`, `CosMx`, `STARmap`, or `Molecular Cartography`.
- `Species`, `Organ`, `Tissue`, `Cell Type`: use source terminology. Do not infer unless the user has approved inference.
- `Group`: treatment, disease state, control/case, anatomical region, or `-` when absent.
- Count fields: fill only from explicit source statements or file validators. If a count depends on filtering, record the filter.
- Count semantics:
  - `No.genes` can be a processed matrix/source panel count, while `genes` can be the STRAND-compatible post-QC gene count.
  - `Raw No.cells` may follow the curated workbook convention rather than the largest raw h5ad `n_obs`; record both when they differ.
  - `No.transcripts` and `median transcripts` must state whether they came from `uns/points`, `X`, a layer such as `spliced`, or a QC-filtered point table.
- Boundary fields: set `Yes` only when repository metadata, manifest, or file structure confirms cell/nucleus geometry for the sample.
- `Data link`: prefer the stable repository collection/item URL over direct file download links.
- `suggested_finish_status`: agent recommendation, not a replacement for `FINISH`.
- `usability_status`: use a small controlled vocabulary such as `ready_for_ingest`, `ready_after_download_inspection`, `needs_download`, `blocked`, or `out_of_scope`.
- `review_required`: set `true` when any biologically meaningful field is inferred, ambiguous, or missing.

## Required Checks

- JSON row contains every target column.
- Public TSV and XLSX use the same column order.
- XLSX can be opened by the local spreadsheet library.
- `internal/unresolved_fields.tsv` lists missing fields, reason, attempted evidence, and next action.
- `internal/truth_comparison.md`, if present, separates:
  - Automatically matched fields.
  - Fields resolved only after download or validation.
  - Fields requiring curator review.
