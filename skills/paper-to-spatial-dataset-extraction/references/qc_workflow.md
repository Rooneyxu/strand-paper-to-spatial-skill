# QC Workflow Reference

Source preserved from the project-local `agent/QC workflow.docx`.

This file keeps the user's filtering rules in a form the extraction skill can load. Do not treat these rules as evidence from a paper. They are STRAND curation rules used after source extraction and file inspection.

## Universal STRAND QC Steps

Every dataset prepared for STRAND pkl-style metadata should be audited against these five steps before final table counts are reported:

1. **Noise feature filtering**
   - Remove noise, control, or non-biological feature names before final gene counts when they are present.
   - Common patterns include `BLANK`, `NegControl`, `notarget`, `ambiguous`, and `codeword`, but the exact vocabulary is dataset-specific.
2. **Cell-level minimum gene filtering**
   - Apply the dataset-specific `min_genes` threshold to remove low-information cells.
   - Do not assume the threshold is universal. Record the actual value in `internal/qc_parameters.tsv`.
3. **Gene-level minimum cell filtering**
   - Apply the dataset-specific `min_cells` threshold to remove genes detected in too few cells.
   - Record the actual value in `internal/qc_parameters.tsv`.
4. **Nucleus/cell area ratio filtering**
   - When both areas are available, compute `nc_ratio = nucleus_area / cell_area`.
   - Remove cells with `nc_ratio > 1`.
   - If areas are unavailable, record `not_available` instead of silently skipping the step.
5. **Mitochondrial gene check**
   - Check whether mitochondrial genes are present.
   - If mitochondrial genes are absent, record `mt_genes = 0` and `checked_no_effect`.
   - If mitochondrial genes are present, record the threshold or reason if a mitochondrial filter is applied.

The workflow is universal; parameter values are dataset-specific. A run is not fully auditable unless the concrete values are printed in `internal/qc_parameters.tsv` and summarized in `extraction_report.md`.

## Before Final PKL Assembly

### Cell-Level Filtering

- Segmentation quality by `nc ratio`: remove morphologically abnormal cells with nuclear/cell area ratio greater than 1.
  - When both areas are available, compute `nc_ratio = nucleus_area / cell_area`.
- `min_genes`: remove cells with too few detected gene types. Example threshold: `min_genes < 20`; adjust according to the total genes detectable by the platform.
- `percent.mt`: set an upper threshold, usually 5% to 20%, using default single-cell parameters when available. High mitochondrial percentage can indicate membrane damage, cytoplasm loss, or apoptosis.

### Gene-Level Filtering

- `min_cells`: remove genes expressed in very few cells. Example threshold: `min_cells < 50`; adjust according to the total number of cells detected by the platform.

## Before RNA Localization And Colocalization

Default thresholds can be changed when the dataset requires it.

- Cell filtering: inspect the global cell `nc ratio` distribution and remove extreme cells using quantiles `low = 0.025` and `high = 0.975`.
- Gene filtering by `min_transcripts`: remove very low-expression genes. A retained gene should have at least 6 transcripts in at least 10 cells.
- Cell-gene filtering: remove cell-gene entries with transcript count less than 6.

## Metadata Count Semantics

The STRAND main dataset table and downstream RNA localization/colocalization inputs can use different filtered count conventions.

- For main-table fields such as `genes`, `No.transcripts`, and `median transcripts`, first identify the final-pkl or STRAND-compatible curation rule. This commonly means applying cell filtering, then a gene-level `min_cells` rule, then keeping all transcript rows for retained genes.
- For RNA localization and colocalization analysis, apply the localization-specific `min_transcripts` and cell-gene filters above. Do not automatically use those analysis-input filters to fill the main dataset metadata table.
- When raw and processed files both exist, record the source point table, processed cell mask, gene filter, and whether counts come from `uns/points`, `X`, a layer such as `spliced`, or a QC-filtered point table.
- Keep `curation_notes` short. Put the complete QC parameter profile in `internal/qc_parameters.tsv`.

## QC Parameter TSV Schema

Every run should create `internal/qc_parameters.tsv`:

```text
dataset	sample	step	parameter	value	applied	evidence_source	effect_on_counts	notes
```

Use one row per QC step or audit check. `sample` may be `all` when the same parameter applies to every sample. `applied` should be one of a small set of plain statuses such as `yes`, `no`, `checked_no_effect`, `not_available`, or `audit_only`.

Xenium Human Pancreas example:

```text
dataset	sample	step	parameter	value	applied	evidence_source	effect_on_counts	notes
Xenium Human Pancreas	all	noise_feature_filter	patterns	BLANK|NegControl|notarget|ambiguous|codeword	yes	internal/source_metadata_inspection.json	removed control/noise features before final gene counts	Dataset-specific noise vocabulary.
Xenium Human Pancreas	all	min_genes_per_cell	min_genes	8	yes	internal/downloaded_file_inspection.json	retained cells with at least 8 detected genes	Dataset-specific threshold.
Xenium Human Pancreas	all	min_cells_per_gene	min_cells	50	yes	internal/downloaded_file_inspection.json	retained genes detected in at least 50 cells	Dataset-specific threshold.
Xenium Human Pancreas	all	nc_ratio_filter	nucleus_area / cell_area <= 1	yes	internal/downloaded_file_inspection.json	removed cells with nc_ratio > 1	Requires both area arrays.
Xenium Human Pancreas	all	mitochondrial_gene_check	mt_genes	0	checked_no_effect	internal/downloaded_file_inspection.json	no mitochondrial filter applied	No mitochondrial genes were present.
```

## Pilot-Derived Rule Example

These examples come from internal validation pilots. They document count-convention lessons; they are not identifiers an external user needs to provide.

SeqFISH+ fibroblast reproduced the current STRAND regression row by:

1. loading raw `seqfish.h5ad` transcript points;
2. restricting points to processed `seqfish_processed.h5ad` cell IDs;
3. retaining genes detected in at least 50 processed cells;
4. keeping all transcript rows for retained genes.

This produced 2811 genes, 4,350,180 transcripts, and median 23,867 transcripts per cell. Applying the localization/colocalization `>=6 transcripts` cell-gene rule instead gives different numbers, so that rule is not the main-table convention for this dataset.

CosMx Breast partially reproduced the current STRAND regression row by:

1. using the official sample predicate from the paper GitHub repository: `Run_Tissue_name == "CxAms124 S1" and y_slide_mm < 6.5`;
2. keeping cells with `nFeature_RNA >= 15`, which exactly matched the current workbook filtered-cell count of 111,258;
3. reading the legacy TileDB RNA/X matrix as `var_id x obs_id` and using the factor-of-two count scale needed to match the workbook median-transcript convention.

This produced 1000 genes, 51,683,274 transcripts, and median 402 transcripts per cell, close but not identical to the workbook values 997 genes, 51,487,258 transcripts, and median 400. Gene-level `min_cells` did not explain 997 because all 1000 genes were detected in at least 100 retained cells. Treat this as a dataset-specific convention mismatch until an exact downstream pkl rule or curator rule is supplied.

MERFISH intestine did not reproduce the current STRAND regression row from the generic QC workflow alone:

1. ExperimentHub resources validated the source structure: raw molecules 819,665, Baysor counts 241 x 5800, Cellpose counts 241 x 8439, and Baysor cell polygons with `z, cell, x, y`.
2. The biologically relevant candidate subset, Baysor epithelial-like cells with cell polygons, gave 2076 cells, 240 expressed genes, 482,677 transcripts, and median 197. This is close to workbook raw cells 2064 but not the final filtered row.
3. A molecule-level probe `qc_score >= 0.9796` gave 255,810 transcripts, close to workbook 256,489, but it did not reproduce cells, genes, or median together.
4. No reusable nucleus-boundary geometry was found in the downloaded RDS resources. DAPI stain/image evidence does not justify `Nuclei boundary = Yes`.

Treat this MERFISH intestine case as a rule-gap example until the exact curator subset/filter is supplied.

## Skill Usage Notes

- Record whether a count is source-provided, validator-derived, or QC-derived.
- If a threshold is changed for a platform, put the exact threshold and reason in `curation_notes`.
- Do not conflate dataset-specific reconstruction rules with this QC reference. For example, excluding control probes or one known bad cell must be supported by file evidence, source evidence, or curator instruction.
