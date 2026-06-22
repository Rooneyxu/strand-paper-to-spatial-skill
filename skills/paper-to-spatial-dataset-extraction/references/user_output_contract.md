# User Output Contract

Use this reference when turning extraction evidence into a distributable result for a user.

## Public Files

Each completed run should expose only these files at `outputs/` root:

```text
final_metadata.xlsx
final_metadata.tsv
extraction_report.md
internal/
```

`final_metadata.xlsx` and `final_metadata.tsv` contain the same STRAND target columns in the order defined by `strand_dataset_fields.md`. `extraction_report.md` explains what was extracted, what evidence supports it, what was downloaded, what QC or count convention was used, and what remains unresolved.

Do not expose `dataset_rows.json`, `download_plan.md`, validator JSON, truth comparisons, or source-inspection dumps at the public root. Put them under `outputs/internal/`.

External users are not expected to know STRAND-internal dataset numbers. Keep the `No.` column for spreadsheet compatibility, but leave it blank unless the user supplies a registry/workbook row ID or explicitly asks for run-local numbering.

## Demo Example Layout

Distributable demo examples should be lightweight and use the same public contract:

```text
examples/<demo-name>/
README.md
final_metadata.xlsx
final_metadata.tsv
extraction_report.md
internal/
```

Demo `internal/` directories may include source/search JSON, `download_plan.md`, `qc_parameters.tsv`, `unresolved_fields.tsv`, and a compact `dataset_rows.json`. They must not include PDFs, h5ad files, zarr directories, tarballs, zip archives, raw images, downloaded large data, private workbooks, or host-specific paths.

## Report Sections

`extraction_report.md` should use these sections:

```text
# Extraction Report - <dataset name>
## Final Metadata Summary
## Upstream Paper Search
## Evidence Sources
## Downloaded Files And Checksums
## Field-Level Evidence
## QC Parameters Used
## QC And Count Convention Notes
## Unresolved Or Curator-Review Fields
## Review Conclusion
## Internal Audit Files
```

The report should be readable without opening the internal files, but it should point to the internal files when a curator wants to audit details.

`Upstream Paper Search` should say whether discovery was used. If the user supplied a PDF, DOI, article URL, or data page directly, report that search was skipped. If discovery was used, summarize the generated queries, selected paper/data page, selection confidence, and whether user confirmation was required.

## Internal Files

Common internal files are:

```text
article_metadata.json
upstream_paper_search.json
dataset_rows.json
dataset_rows.tsv
Datasets_filled.xlsx
curation_report.md
download_plan.md
qc_parameters.tsv
unresolved_fields.tsv
notes_for_future_skill.md
truth_comparison.md
source_metadata_inspection.json
downloaded_file_inspection.json
postdownload_*.json
```

Keep raw data files, downloaded archives, h5ad files, zarr directories, TileDB directories, images, and PDF copies outside the skill package unless the user explicitly requests a local research workspace.

## Evidence Rules

- `final_metadata.*` can contain inferred or QC-derived values only when `curation_notes` and `extraction_report.md` explain the rule.
- Regression truth may appear only in `internal/truth_comparison.md` and in the report as an audit comparison, not as extraction evidence.
- Upstream search results may appear in `internal/upstream_paper_search.json` and in the report as candidate-selection evidence, not as final count, QC, boundary, or sample-level extraction evidence.
- Missing values must remain blank, `-`, or unresolved. Do not fill them with closest-looking numbers.
- Boundary fields require file, manifest, polygon, mask, or repository evidence.
- Count fields should distinguish source metrics, raw object shape, processed cell masks, transcript/point tables, matrix/layer sums, and final STRAND-compatible QC counts.
- `curation_notes` should summarize the result, not carry the full QC workflow. Put complete thresholds and count effects in `internal/qc_parameters.tsv`.

## QC Parameter Table

Every run should write `internal/qc_parameters.tsv` with this header:

```text
dataset	sample	step	parameter	value	applied	evidence_source	effect_on_counts	notes
```

Use one row per actual QC decision or audit check. The five common steps are:

```text
noise_feature_filter
min_genes_per_cell
min_cells_per_gene
nc_ratio_filter
mitochondrial_gene_check
```

`applied` should be a short status such as `yes`, `no`, `checked_no_effect`, `not_available`, or `audit_only`. `effect_on_counts` should state the observed effect when known, such as `removed 0 cells`, `retained 377 genes`, or `not used for final table`.

Example:

```text
dataset	sample	step	parameter	value	applied	evidence_source	effect_on_counts	notes
Xenium Human Pancreas	all	noise_feature_filter	patterns	BLANK|NegControl|notarget|ambiguous|codeword	yes	internal/source_metadata_inspection.json	removed control/noise features before final gene counts	Dataset-specific noise vocabulary.
Xenium Human Pancreas	all	min_genes_per_cell	min_genes	8	yes	internal/downloaded_file_inspection.json	retained cells with at least 8 detected genes	Dataset-specific threshold.
Xenium Human Pancreas	all	min_cells_per_gene	min_cells	50	yes	internal/downloaded_file_inspection.json	retained genes detected in at least 50 cells	Dataset-specific threshold.
Xenium Human Pancreas	all	nc_ratio_filter	nucleus_area / cell_area <= 1	yes	internal/downloaded_file_inspection.json	removed cells with nc_ratio > 1	Requires both area arrays.
Xenium Human Pancreas	all	mitochondrial_gene_check	mt_genes	0	checked_no_effect	internal/downloaded_file_inspection.json	no mitochondrial filter applied	No mitochondrial genes were present.
```

## Packaging Command

For legacy pilot outputs, run:

```bash
python3 agent/skills/paper-to-spatial-dataset-extraction/scripts/package_final_outputs.py <run-dir> --tidy --overwrite
```

Then validate the public package:

```bash
python3 agent/skills/paper-to-spatial-dataset-extraction/scripts/validate_outputs.py --mode public <run-dir>
```

For an external-user run where no registry/workbook row IDs were supplied, validate that `No.` stayed blank:

```bash
python3 agent/skills/paper-to-spatial-dataset-extraction/scripts/validate_outputs.py --mode public --external-user <run-dir>
```

For a search-first run, also require the upstream search audit file:

```bash
python3 agent/skills/paper-to-spatial-dataset-extraction/scripts/validate_outputs.py --mode public --require-upstream-search <run-dir>
```
