# Demo Evaluation

Purpose: summarize the eight completed pilots that justify the current project-local `paper-to-spatial-dataset-extraction` skill design.

## Evaluation Standard

The current standard is `complete and auditable`, not exact reproduction of every `Datasets.xlsx` value.

- Filled fields must cite source, repository, file-inspection, or curator-provided truth evidence.
- Missing fields must stay in `unresolved_fields.tsv` with a reason and next action.
- Regression truth may be used only in `truth_comparison.md`, never as extraction evidence.
- Count mismatches are acceptable when `truth_comparison.md` explains the QC or count-convention gap.
- Boundary fields require manifest, file structure, polygon, mask, or geometry evidence.

## Status Classes

- `complete_auditable`: standard outputs exist; core metadata and count fields are supported; remaining issues are curator-owned ontology or schema-convention review.
- `complete_with_qc_gap`: complete candidate table exists, but final numeric fields differ from current workbook because of QC or count-convention differences.
- `partial_requires_dataset_specific_qc`: source/file metadata was recovered, but final STRAND fields remain unresolved until a dataset-specific QC or curation rule is supplied.

## Completed Pilot Matrix

| Pilot | Technology | Source route | Rows | Downloaded? | Status | Boundary evidence | QC / unresolved summary |
| --- | --- | --- | ---: | --- | --- | --- | --- |
| Dataset1 MERFISH U2OS | MERFISH | Bento / Figshare | 1 | Yes | `complete_auditable` | h5ad `cell_shape` and `nucleus_shape` | Counts match regression truth after processed h5ad inspection; remaining review is U2OS species/organ inference and raw-count convention. |
| Dataset2 SeqFISH+ fibroblast | seqFISH+ | Bento / Figshare | 1 | Yes | `complete_auditable` | raw and processed h5ad geometry | Counts match regression truth using raw points restricted to processed cells plus `min_cells >= 50`; `Organ = Skin` remains curator ontology. |
| Dataset6 Cardiomyocytes | Molecular Cartography | Bento / Figshare | 4 | Yes | `complete_with_qc_gap` | h5ad cell and nucleus geometry | Complete table uses preserved QC workflow estimates; transcript/median values are close but not exact for all replicates. |
| Dataset18 Xenium Human Pancreas | Xenium | 10x Genomics page | 1 | Yes | `complete_with_qc_gap` | `cells.zarr.zip` cell/nucleus polygons | Complete file-derived row; workbook differences are not explained by `nc_ratio = nucleus_area / cell_area`. |
| Dataset30 CosMx Breast | CosMx | Zenodo TileDB | 1 | Yes | `complete_with_qc_gap` | CosMx cell segmentation; no reusable nucleus geometry found | Official Breast predicate plus `nFeature_RNA >= 15` recovers filtered cells; genes/transcripts/median remain minor count-convention mismatches. |
| Dataset3 MERFISH intestine | MERFISH | Dryad / ExperimentHub | 1 | Yes | `partial_requires_dataset_specific_qc` | ExperimentHub Baysor cell polygons | Source metadata and cell boundary are supported, but final cells/genes/transcripts/median and nucleus-boundary truth need a dataset-specific rule. |
| Dataset5 STARmap AD | STARmap | Zenodo / Google Drive | 12 | Yes | `partial_requires_dataset_specific_qc` | Drive h5ad label images support cell boundary; no nucleus geometry found | 2,766-gene rows are close under matrix/QC probes; 64-gene rows need reads-assignment archives or final pkl rule. |
| Dataset20 Xenium Breast Preview | Xenium | 10x Genomics page | 3 | Yes | `complete_with_qc_gap` | `cells.zarr.zip` proves cell and nucleus boundaries for every raw cell | Complete file-derived table; workbook counts use a different final QC/count convention and Sample2 has a base-panel versus custom-panel convention gap. |

## Source Route Coverage

The completed pilots cover the source routes that matter for the current STRAND metadata workflow:

- Bento / Figshare h5ad datasets, including Figshare 403/proxy behavior.
- 10x Genomics Xenium pages with `__NEXT_DATA__`, analysis summaries, output bundles, h5 matrix files, and zipped zarr structures.
- Zenodo TileDB/SOMA archives for CosMx, including legacy reader-version constraints.
- Dryad blocked downloads with Bioconductor ExperimentHub fallback resources.
- Google Drive / Zenodo STARmap resources with large h5ad inspection and partial unresolved count conventions.

## Validator Coverage

Current reusable validators and packagers:

- `scripts/inspect_h5ad.py`: h5ad/AnnData inspection, including lazy HDF5 paths used by STARmap.
- `scripts/package_final_outputs.py`: converts legacy/internal audit files into the public `final_metadata.xlsx`, `final_metadata.tsv`, and `extraction_report.md` package, including a `QC Parameters Used` section.
- `scripts/validate_outputs.py`: run-output schema validator for public TSV/XLSX/report outputs, `internal/qc_parameters.tsv`, legacy JSON/TSV/XLSX pilot outputs, unresolved-field audit shape, `Category` spelling, and `truth_comparison.md` presence.
- `scripts/inspect_10x_xenium_outs.py`: 10x Xenium full `outs.zip` validator for `outs/` or ZIP-root layouts, h5 matrix counts, `cells.zarr.zip`, transcript CSV counts, barcode or numeric `cell_id`, and `nc_ratio = nucleus_area / cell_area`.

Not yet generalized:

- CosMx TileDB/SOMA validator.
- STARmap reads-assignment / matrix convention validator.
- ExperimentHub/Dryad RDS validator.

## Current Conclusion

The skill is ready to be organized as a distributable Codex Skill with a small public output contract. It can produce STRAND-style metadata tables with auditable evidence across multiple technology families. Future work should improve validator reuse and regression checks, not add more demo datasets by default.
