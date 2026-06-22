# Prevalidation Toolchain

The skill should coordinate predictable validators. Avoid rewriting bespoke scripts for every dataset unless a reusable validator is missing.

## Pipeline

1. **Input normalizer**
   - Collect PDF path, DOI, article URL, repository links, supplementary links, and optional truth workbook.
   - Detect whether the user gave a broad discovery request instead of a concrete source.
   - Assign a run slug from the source title, DOI, technology, tissue, or repository record. Do not require or invent a STRAND-internal dataset number for external users.
   - Write all outputs under one run directory.

2. **Upstream article/dataset discovery, optional**
   - Run only when the user asks to search for a dataset or gives a broad topic with no PDF, DOI, article URL, repository page, or dataset landing page.
   - Read `upstream_paper_search_contract.md`, generate targeted paper/data queries, and call the available paper lookup/search route.
   - Prefer a `paper-lookup` skill when available. Otherwise use an academic paper-search tool, BioMCP/PubMed-style search for biomedical topics, or the approved web search route as fallback.
   - Write `internal/upstream_paper_search.json` with generated queries, candidate papers, selected paper if any, confidence, and whether user confirmation is needed.
   - Use the selected DOI/article URL/data links as downstream inputs. Do not copy search-snippet counts or boundary claims into final metadata fields.

3. **Article evidence extractor**
   - Parse local PDF first when available.
   - Extract title, DOI, year, method scope, Data availability, and dataset-specific text snippets.
   - Use web/article pages only as secondary evidence when local PDF is insufficient.

4. **Repository landing-page extractor**
   - Read collection pages and item pages before downloading files.
   - Capture file names, sizes, item IDs, direct download URLs if visible, and access failures.
   - For Figshare, browser DOM inspection may be needed when API or `curl` returns 403.
   - For Bento datasets, use the Bento package registry or tutorial pages as fallback evidence for file IDs, download URLs, and basic raw/processed object counts when Figshare pages are incomplete.

5. **Candidate row builder**
   - Create candidate rows without downloading large data.
   - Leave exact counts unresolved unless the page or paper explicitly gives them.
   - Write `internal/download_plan.md` for every needed file.

6. **Download gate**
   - Do not download `.h5ad`, `.zarr`, `.tar.gz`, `.zip`, image archives, or large raw data before the user approves `internal/download_plan.md`.
   - Prefer formatted/processed files first. Download raw archives only if processed files cannot answer required fields.
   - Before asking for approval, HEAD-only URL preflight is allowed when it does not save a file body. Record HTTP status, redirects, `content-disposition`, exposed `Range` headers, and expected file size or checksum when available.
   - If direct Figshare download returns 403 and the user has approved downloading, retry through the project proxy route from `AGENTS.md` before declaring the file inaccessible.

7. **File validators**
   - h5ad: run `scripts/inspect_h5ad.py` when AnnData data is available.
   - 10x/Xenium full `outs.zip`: run `scripts/inspect_10x_xenium_outs.py <resource_id> <outs_zip> <output_json>` when the bundle contains `cell_feature_matrix.h5`, `cells.zarr.zip`, and `transcripts.csv.gz`.
   - Zarr: before reading `.zarr` or zipped 10x zarr outputs, check whether `zarr` and `numcodecs` are importable. If missing, install them into a temporary validator directory outside the skill package after user approval, add that directory to `PYTHONPATH`, and record package versions.
   - Legacy TileDB/SOMA: inspect the TileDB schema and SOMA encoding version before choosing a reader. Some public CosMx TileDB exports use SOMA encoding version 0 and require an old temporary validator stack such as `tiledbsoma==0.1.22`, `tiledb==0.22.3`, and `numpy<1.24`; newer `tiledbsoma` may fail before any biological inspection.
   - Tables: inspect headers, row counts, sample columns, gene columns, cell columns, coordinate columns, and boundary references.
- Archives: list contents first; extract only the minimum needed files.
- 10x archives can use different layouts across releases. Detect whether required members live under `outs/` or at ZIP root before declaring files missing.
   - Manifests: verify referenced files, sample/batch/FOV counts, coordinate columns, boundary files, and gene panels.
   - For repository files with declared checksums, verify the checksum immediately after download before inspecting biological content.
   - Do not add validator-only dependencies to project `package.json`, `requirements.txt`, `pyproject.toml`, or the active app environment unless the user explicitly asks.

8. **QC validator**
   - Load `qc_workflow.md` when preparing final STRAND-compatible counts.
   - Record original counts and filtered counts separately.
   - Write the exact run-specific thresholds and audit checks to `internal/qc_parameters.tsv`.
   - Keep `curation_notes` as a short summary; do not use it as the only record of QC parameters.
   - When raw and processed h5ad files both exist, test whether final counts come from raw points restricted to processed cells, processed matrices, processed point tables, or layers. Write the tested convention and result into `internal/downloaded_file_inspection.json` and `internal/curation_report.md`.

9. **Export validator**
   - Run `scripts/package_final_outputs.py <run_dir_or_outputs_dir> --tidy --overwrite` after writing internal audit files.
   - Run `scripts/validate_outputs.py --mode public <run_dir_or_outputs_dir>` after writing the public output files.
   - Add `--require-truth` when regression truth is available and `internal/truth_comparison.md` should exist.
   - Confirm no large downloaded data files were written into the repository unless explicitly requested.

10. **Regression truth comparator**
   - Use only after extraction. Never use truth rows to fill evidence fields.
   - Explain each mismatch with source evidence, validator evidence, unresolved reason, or curation decision.

## h5ad Inspection Expectations

For each h5ad file, collect:

- `adata.shape`
- `obs` columns and likely sample/batch columns
- `var` names and control probes
- matrix transcript/count totals when meaningful
- `uns` keys and point/transcript tables
- cell boundary and nucleus boundary columns or geometry structures
- batch/sample/FOV counts
- per-cell transcript summaries when transcript tables are available

Use direct file evidence for `Cell boundary`, `Nuclei boundary`, `No.batch`, `Raw No.cells`, `No.genes`, `Filtered No.cells/nuclei`, `genes`, `No.transcripts`, `median transcripts`, and `No.NucleiBoundary`.

## 10x/Xenium Zarr Inspection Expectations

For 10x Xenium outputs, collect:

- available bundle members, such as `experiment.xenium`, `gene_panel.json`, `cells.zarr.zip`, `cell_feature_matrix.zarr.zip`, `transcripts.zarr.zip`, and `analysis.zarr.zip`
- gene panel size and probe/control annotations when present
- raw cell count from `cells.zarr.zip`, including boundary and nucleus boundary arrays
- non-empty or filtered cell count from `cell_feature_matrix.zarr.zip`, with the exact retained-cell rule
- transcript-like counts from both source transcript tables and cell-feature matrices, without assuming they are equivalent
- q-score threshold, feature type, and control-probe handling when using `transcripts.zarr.zip`
- transcript `cell_id` mapping convention: numeric cell IDs and barcode-string cell IDs both occur; map barcode strings through `matrix/barcodes` before computing per-cell transcript summaries
- nucleus boundary counts both before and after restricting to retained cells, when the final cell set is filtered
- `nc_ratio` must be computed as `nucleus_area / cell_area` when both arrays are present; report cells with `nc_ratio > 1` separately from retained-cell count decisions

When `zarr` is missing, bootstrap temporary dependencies only for validator execution. Record the install command, target path, package versions, and import test in `internal/downloaded_file_inspection.json` or `internal/curation_report.md`.

The reusable `inspect_10x_xenium_outs.py` validator currently targets full output bundles with `cell_feature_matrix.h5` plus `transcripts.csv.gz`. For smaller Explorer subset zips that expose only zarr members, use the same evidence requirements but keep the run-local validator until the pattern repeats.

## CosMx TileDB Inspection Expectations

For CosMx TileDB or SOMA archives, collect:

- archive size, checksum, extracted root, root members, SOMA object type, and encoding version
- working reader package versions, plus failed reader attempts when version compatibility matters
- obs shape, var shape, obs keys, var QC keys, and matrix schema dimension order
- sample mapping evidence; if the object is aggregated across samples, prefer official code predicates or source metadata over ad hoc FOV guesses
- raw sample cells from the source predicate and FOV count
- RNA/X matrix count sums, per-cell medians, detected gene count, and alternative QC-flag conventions
- probe/gene QC flags separately from matrix-detected genes
- boundary evidence separately for source-supported cell segmentation, reusable cell geometry, and reusable nucleus geometry

Do not assume CosMx `Run_Tissue_name` is the biological sample. A prior CosMx Breast pilot showed `Run_Tissue_name` only identified slide/run (`CxAms124 S1` / `CxAms124 S2`); sample names required coordinate predicates from the official GitHub preprocessing script. Also do not assume modern SOMA matrix orientation: inspect the TileDB schema because legacy exports can store counts as `var_id x obs_id` (genes x cells).

## Count Reconstruction Expectations

When exact counts are not source-provided, the validator output should make the count convention auditable:

- raw object shape and processed object shape
- raw transcript/point rows and processed transcript/point rows
- matrix and layer sums, with layer names
- cell IDs used as a processed cell mask
- gene filter rule and threshold
- retained genes, retained transcript rows, and median transcripts per retained cell
- boundary evidence source, such as `obs.cell_shape` or `obs.nucleus_shape`

Do not fill final STRAND-compatible count fields from the closest-looking number. Fill them only after the reconstruction rule is stated and reproducible.
