# Development Process

Purpose: preserve the working rules and current development state for the STRAND paper-to-spatial-dataset extraction skill across conversation switches.

## Must-Read Files At Session Start

1. Project `AGENTS.md`
   - Project rules, response language, workflow constraints, networking route, and validation commands.
2. Project `PLAN.md`
   - Current STRAND truth and short-term priorities.
3. `agent/skills/paper-to-spatial-dataset-extraction/SKILL.md`
   - Active skill workflow.
4. These skill references when relevant:
   - `references/strand_dataset_fields.md`
   - `references/upstream_paper_search_contract.md`
   - `references/prevalidation_toolchain.md`
   - `references/qc_workflow.md`
   - `references/demo_evaluation.md`

## User Rules To Preserve

- Reply in Chinese.
- Start each conversational reply with `好的，rooneyxu大哥`, except for inline quick edits where no reply is needed.
- Keep changes simple and targeted.
- Do not add unrelated features or refactors.
- Explain uncertainty and tradeoffs before coding when the task is ambiguous.
- Use evidence, not assumption. Separate current truth, plan, and unresolved items.
- For networking or web extraction, use the project-approved web route and proxy rules from `AGENTS.md`.
- Do not download large data before writing a download plan and receiving user approval.
- Do not treat regression truth as extraction evidence.
- Do not ask external users for STRAND-internal dataset numbers. `No.` is a compatibility column and should stay blank unless a target registry/workbook ID is supplied.
- If the user gives only a topic such as `pancreas subcellular-resolution datasets`, run the optional upstream paper/dataset discovery stage before extraction. Search results choose candidates; they do not fill final metadata counts.
- Keep `paper-lookup` as an optional bundled sibling dependency when distributing the skill. Use it when present, but do not fail extraction when it is missing or a database is rate-limited.
- Preserve third-party license notices for bundled skills. The `paper-lookup` notice belongs in `THIRD_PARTY_NOTICES.md`.

## Skill Development Principle

The CellAtria-inspired design point is:

```text
LLM coordinates a prevalidated toolchain; it should not improvise a new one-off script for every paper.
```

Reusable validators should be created only when a repeated check needs deterministic behavior. Current reusable validators are:

```text
scripts/inspect_h5ad.py
scripts/inspect_10x_xenium_outs.py
scripts/package_final_outputs.py
scripts/validate_outputs.py
```

- `inspect_h5ad.py` inspects AnnData/h5ad structure for STRAND curation fields such as shape, batch count, boundary geometry, control probes, transcript totals, and median transcripts.
- `inspect_10x_xenium_outs.py` inspects full 10x Xenium `outs.zip` bundles with h5 matrix, zipped zarr cell geometry, transcript CSVs, barcode or numeric `cell_id`, and `nc_ratio = nucleus_area / cell_area`.
- `package_final_outputs.py` packages legacy/internal audit outputs into `final_metadata.xlsx`, `final_metadata.tsv`, `extraction_report.md`, and `internal/`.
- `validate_outputs.py` validates public distributable outputs, `internal/qc_parameters.tsv`, and legacy pilot outputs; it is the first regression gate for project-local reproducibility.

## Current Artifacts

- U2OS pilot run:
  - `agent/runs/2026-06-19_merfish-u2os-pilot/`
- SeqFISH+ fibroblast pilot run:
  - `agent/runs/2026-06-20_seqfish-fibroblast-pilot/`
- Cardiomyocytes Molecular Cartography pilot run:
  - `agent/runs/2026-06-20_cardiomyocytes-molecular-cartography-pilot/`
- Xenium Human Pancreas pilot run:
  - `agent/runs/2026-06-20_xenium-human-pancreas-pilot/`
- CosMx Breast pilot run:
  - `agent/runs/2026-06-20_cosmx-breast-pilot/`
- MERFISH Intestine pilot run:
  - `agent/runs/2026-06-20_merfish-intestine-pilot/`
- STARmap AD pilot run:
  - `agent/runs/2026-06-21_starmap-ad-pilot/`
- Xenium Breast Preview pilot run:
  - `agent/runs/2026-06-21_xenium-breast-preview-pilot/`
- Skill draft:
  - `agent/skills/paper-to-spatial-dataset-extraction/`
- Optional bundled search dependency:
  - `agent/skills/paper-lookup/`
- Lightweight distributable demo:
  - `agent/skills/paper-to-spatial-dataset-extraction/examples/merfish-intestine-search-demo/`
- Demo evaluation:
  - `references/demo_evaluation.md`
- User QC source document:
  - `agent/QC workflow.docx`
- Preserved QC reference:
  - `references/qc_workflow.md`

## U2OS Pilot Lessons

- First pass should parse PDF and repository landing pages without downloading data.
- Figshare API or shell downloads may fail with 403 while browser DOM inspection still reveals file links.
- Download processed/formatted h5ad before raw archives.
- Boundary fields require file evidence; AnnData `obs.cell_shape` and `obs.nucleus_shape` can support `Cell boundary = Yes` and `Nuclei boundary = Yes`.
- For Bento MERFISH U2OS, processed h5ad inspection reproduced the STRAND-compatible row after excluding notarget controls and one filtered cell. This is an eval case, not a shortcut for future extraction.
- Ambiguous fields such as `Raw No.cells` must keep notes explaining which file and convention produced the count.

## SeqFISH+ Fibroblast Pilot Lessons

- The same Bento article and Figshare collection can produce another dataset row without changing the workflow. This is the first positive forward-test that the skill is reusable beyond MERFISH U2OS.
- Direct Figshare and Figshare API access can return 403 in this environment. The proxy route `socks5h://127.0.0.1:10809` worked for the SeqFISH+ h5ad downloads after user approval.
- For Bento datasets, the package dataset registry can recover file IDs, download URLs, and basic file-level counts when the Figshare landing page is incomplete.
- Raw h5ad, processed h5ad, matrix sums, layer sums, and STRAND-compatible metadata counts are different evidence sources. Do not expect `X.sum()`, `spliced.sum()`, `uns["points"]`, and final `No.transcripts` to match.
- SeqFISH+ Dataset2 matched current truth by restricting raw `seqfish.h5ad` points to the 179 processed cells from `seqfish_processed.h5ad`, then applying the final-pkl gene filter `min_cells >= 50`. The retained values were 2811 genes, 4,350,180 transcripts, and median 23,867 transcripts per cell.
- The RNA localization/colocalization rule requiring at least 6 transcripts in at least 10 cells is not the main-table rule for this dataset. Use the final-pkl rule for `genes`, `No.transcripts`, and `median transcripts` unless the user explicitly asks for localization/colocalization analysis inputs.
- All file-derived and QC-derived numeric fields matched the current Dataset2 truth row. `Organ = Skin` remains a curator ontology field because the no-download sources identified 3T3 mouse fibroblast cells but did not explicitly state the STRAND organ label.

## Dataset6 Cardiomyocytes Pilot Lessons

- Run:
  - `agent/runs/2026-06-20_cardiomyocytes-molecular-cartography-pilot/`
- This pilot extends the workflow to Molecular Cartography while staying inside the Bento/Figshare source route.
- PDF evidence supports human iPSC-derived cardiomyocytes, DMSO vehicle versus 2.5 μM DOX for 12 h, Resolve Bioscience Molecular Cartography, a 100-gene cardiomyocyte panel, ClusterMap cell boundaries, and Cellpose nuclei boundaries.
- Figshare collection and item API were enough to generate a concrete download plan without downloading data. Direct Figshare API returned 403; proxy route `socks5h://127.0.0.1:10809` was required for metadata.
- Figshare item API lists four h5ad files with MD5 checksums: `32786-slide5_A1-1.h5ad`, `32786-slide5_A2-1.h5ad`, `32786-slide5_B1-1.h5ad`, and `32786-slide5_B2-1.h5ad`.
- HEAD-only preflight on the four Figshare ndownloader URLs returned 302 redirects to S3 with matching `content-disposition` filenames and Range-related headers exposed. Record this preflight in `download_plan.md`; it does not replace user approval for downloading h5ad bodies.
- Treat Figshare MD5 values as part of the post-download validator checklist.
- Post-download pass completed after user approval. Files were downloaded through the proxy into a temporary download directory outside the skill package; all four MD5 checks matched Figshare.
- Direct h5ad inspection filled `Raw No.cells` and confirmed 100 genes plus `obs.cell_shape`, `obs.nucleus_shape`, and `uns["points"]` for all four samples. Raw cells matched workbook row order: A1_1=3786, A2_1=3664, B1_1=3050, B2_1=3607.
- Plain AnnData reads missing geometry as the string `"None"` in this dataset, so validators must distinguish real WKT geometry from non-null placeholder strings. `inspect_h5ad.py` now records geometry-present counts separately from pandas non-null counts.
- Tested QC reconstructions included `min_genes >= 20`, nucleus-polygon filtering, `nc_ratio <= 1`, gene-level `min_cells >= 50`, and the Bento manuscript figure-analysis Leiden cluster 4 rule. No single tested rule reproduced all four current workbook rows.
- If exact truth reproduction is not required, Dataset6 can be exported as a complete candidate table using the preserved QC workflow estimate: keep cells with `min_genes >= 20`, remove cells with `nc_ratio > 1`, then retain genes detected in at least 50 retained cells and keep all retained-gene transcript rows. Under this estimate, all `genes` values match truth; A1_1 filtered cells also match truth; transcript and median values remain close but not exact.
- B2_1 exactly matched current truth under `nucleus polygon + min_genes >= 20 + min_cells >= 50`; B1_1 was off by one cell and 493 transcripts under that alternative rule; A1_1/A2_1 remained close but not exact under tested h5ad-derived rules.
- The Bento manuscript Leiden cluster 4 filter appears figure-analysis-specific: it over-filtered DOX samples and should not be promoted as a STRAND main-table metadata rule unless it is encoded as an explicit dataset-specific QC parameterization.
- Source sample naming differs from the current workbook: Figshare uses `A2-1` and `B2-1`, while `Datasets.xlsx` currently uses `A1_2` and `B1_2` for the second replicates. Record source tokens in `curation_notes` and flag the workbook naming for curator review.
- Figshare says A1/A2 are vehicle and B1/B2 are DOX-treated; the current workbook leaves the second replicate group cells blank. This is a source-supported review item, not a reason to copy truth silently.
- Current run exports a complete table using QC workflow estimates for `Filtered No.cells/nuclei`, `genes`, `No.transcripts`, `median transcripts`, and `No.NucleiBoundary`. Exact workbook reproduction would still require deterministic dataset-specific detail such as exact handling of missing nucleus polygons, `nc_ratio`, percent.mt availability, and which point table defines the final main-table count.

## Dataset18 Xenium Human Pancreas Pilot Lessons

- Run:
  - `agent/runs/2026-06-20_xenium-human-pancreas-pilot/`
- No-download pass completed against the 10x Genomics official dataset page and analysis summary. Large data files were not downloaded.
- 10x dataset pages expose a useful `__NEXT_DATA__` payload with source text, file URLs, sizes, MD5 checksums, and fileset metadata.
- 10x `analysis_summary.html` embeds a parseable `const data = {...}` payload with metric cards, panel specification, segmentation summaries, histogram totals, software version, and region metadata.
- Source-supported Dataset18 fields include Xenium technology, human pancreas/pancreatic cancer tissue, 377 target genes, 140,702 cells detected, median 31 transcripts per cell, and 7,170,423 high-quality decoded transcripts.
- The source metric convention does not match current STRAND truth for transcript fields: workbook truth has 6,059,862 transcripts and median 40. Treat 10x source metrics as raw/source summary evidence, not final STRAND post-QC counts.
- Analysis summary histogram totals sum to 140,194 non-empty cells, while source cells detected is 140,702. The 508-cell difference is zero-transcript cells, not a STRAND filtered-cell count.
- Summary payload includes `nucleus_count = 141,810`, but current workbook `No.NucleiBoundary = 120,530`; do not map nucleus count to nucleus-boundary count without inspecting boundary files.
- 10x output docs and page body indicate the smaller Explorer subset zip contains `cells.zarr.zip`, `cell_feature_matrix.zarr.zip`, `transcripts.zarr.zip`, and `analysis.zarr.zip`. Download plan prioritizes the small `gene_panel.json`, then the smaller subset zip, and reserves the 5.69 GB full outs zip as fallback.
- Post-download pass completed after user approval. `gene_panel.json` and the 1.74 GB Explorer subset zip were downloaded into a temporary download directory outside the skill package; both MD5 checks matched 10x metadata. The 5.69 GB full outs zip was not downloaded.
- The subset zip was enough for a complete file-derived candidate row: `experiment.xenium`, `cells.zarr.zip`, `cell_feature_matrix.zarr.zip`, `transcripts.zarr.zip`, and `analysis.zarr.zip` were inspected.
- A temporary install of `zarr` and `numcodecs` was used to read 10x zipped zarr arrays without changing project dependencies.
- `cell_feature_matrix.zarr` has 542 features: 377 genes, 20 negative control probes, 41 negative control codewords, 103 unassigned codewords, and one aggregate `Total transcripts` feature. Do not sum all features; the aggregate double-counts gene transcripts.
- File-derived candidate convention for Dataset18 is now: retained cells = non-empty cells with gene counts > 0 in `cell_feature_matrix.zarr`; `genes = 377`; `No.transcripts = 5,511,215`; `median transcripts = 31`; `No.NucleiBoundary = 141,309` nucleus-boundary rows attached to retained cells.
- Tested alternatives did not reproduce workbook truth exactly: q>=20 source gene transcripts = 7,170,423; q>=36 gene transcripts = 6,088,083; matrix `gene_counts >= 9` = 125,259 cells and 5,435,753 transcripts; matrix `gene_counts >= 10` = 122,678 cells and 5,412,524 transcripts; default `min_genes >= 20` over-filters to 56,850 cells.
- Dataset18 `cells.zarr` includes `cell_area` and `nucleus_area`, so user-defined `nc_ratio = nucleus_area / cell_area` is computable. It gives 0 positive-nucleus cells with `nc_ratio > 1`; applying `nonempty & nc_ratio <= 1` leaves the non-empty-cell convention unchanged at 140,194 cells, 5,511,215 transcripts, and 141,309 retained nucleus-boundary rows. Therefore Dataset18 workbook differences are not explained by `nc_ratio <= 1`.
- Exact workbook truth reproduction remains a historical-QC task, not a blocker for the skill's goal of producing a complete auditable candidate table.
- Add reusable validators for 10x page extraction, 10x analysis-summary extraction, zip content listing, selective extraction, and zarr/parquet count reconstruction.

## Dataset20 10x Xenium Breast Cancer Preview Pilot Lessons

- Run:
  - `agent/runs/2026-06-21_xenium-breast-preview-pilot/`
- No-large-download pass completed against the 10x Genomics official preview page, the Nature Communications article, 10x analysis summaries, metrics summaries, gene panels, and the published cell annotation workbook. The 7.49-9.18 GB `outs.zip` files were not downloaded.
- The 10x product page `__NEXT_DATA__` payload exposed three In Situ filesets: Sample 1 Replicate 1, Sample 1 Replicate 2, and Sample 2. It also exposed stable file URLs, file sizes, MD5 checksums, and software-version context.
- Even when the page payload does not list all small summary files directly, 10x URLs can be derived from the resource ID for `_analysis_summary.html` and `_metrics_summary.csv`. HEAD preflight plus small-file download was enough to recover source cell counts, panel composition, source transcript totals, medians, and analysis versions.
- Source-supported rows were generated for all three Xenium samples. Raw cell counts match current workbook truth exactly: 167,780; 118,752; and 142,272.
- Source metric conventions differ from the current workbook final fields. 10x source summaries give non-empty/quality-decoded counts, while the workbook appears to use a later STRAND QC/export convention for filtered cells, transcript totals, and median transcripts.
- Sample 2 has a panel convention difference: the 10x source panel is 280 predesigned genes plus 8 custom genes, while the current workbook records 280. Keep this as a curator-review convention rather than silently collapsing the source panel count.
- The cell annotation workbook is a small, useful metadata source. It recovered supervised or unsupervised cell-type label counts for the three Xenium samples, including 20 labels for the three table rows used in this pilot.
- `Cell boundary = Yes` and `Nuclei boundary = Yes` are supported by 10x Xenium output semantics and the available output bundles, but `No.NucleiBoundary` still requires inspecting `outs.zip` / `cells.zarr.zip` boundary arrays. Do not infer boundary counts from page-level nucleus counts.
- This is a positive no-large-download test: the skill can produce a usable, auditable source-metric candidate table for a 10x multi-sample preview dataset before downloading large zarr/zip outputs. Exact final STRAND parity remains a post-approval output-bundle and QC task.
- Post-download pass completed after user approval. Three large `outs.zip` bundles were downloaded to a temporary download directory outside the skill package and all MD5 checks matched 10x metadata: Rep1 `7d42a0b232f92a2e51de1f513b1a44fd`, Rep2 `d266097b3550b721cabbed942f88538d`, Sample2 `6f1ca8861ee981c0b0b86bae00748ced`.
- Archive layout differs across 10x releases. Rep1/Rep2 store files under `outs/`; Sample2 stores `cell_feature_matrix.h5`, `cells.zarr.zip`, `transcripts.csv.gz`, and boundary files at ZIP root. Validators must detect both layouts before selective extraction.
- Transcript `cell_id` encoding differs across 10x releases. Rep1/Rep2 use numeric IDs; Sample2 uses barcode strings such as `aagigajm-1`. Per-cell transcript validators must map barcode `cell_id` through `matrix/barcodes`.
- Downloaded `cells.zarr.zip` proved both cell and nucleus boundaries for every raw cell in all three samples. `nc_ratio = nucleus_area / cell_area` was computed from `cell_summary`; all three samples had zero cells with `nc_ratio > 1`.
- File-derived complete table convention for Dataset20 is source/QV20 non-empty gene cells: Rep1 166,363 retained cells, 313 genes, 34,442,716 QV20 gene transcripts, median 166; Rep2 118,691 retained cells, 313 genes, 25,444,036 QV20 gene transcripts, median 164; Sample2 141,828 retained cells, 288 genes, 12,919,042 QV20 gene transcripts, median 63.
- Current workbook truth uses a different final count convention: it is closer to all-QV assigned gene transcripts after an additional low-count/QC filter. A generic `detected_genes >= 20` probe is close for Rep1/Rep2 but over-filters Sample2, so do not promote that threshold as a universal Xenium rule.
- `unresolved_fields.tsv` is empty after post-download validation. Remaining review items are count-convention differences and Sample2 panel convention (280 base genes versus 280 + 8 custom source targets), not missing metadata.

## Dataset30 CosMx Breast Pilot Lessons

- Run:
  - `agent/runs/2026-06-20_cosmx-breast-pilot/`
- No-download pass completed against the local Genome Biology PDF, official Supplementary Table S1, and Zenodo record `10.5281/zenodo.17986017`.
- The paper title is `A technical comparison of spatial transcriptomics platforms across six cancer types`; Dataset30 belongs to the Zenodo `Xenium & CosMx` repository, not the separate Visium or segmented Xenium repositories.
- Official Supplementary Table S1 is a small source metadata file and can be downloaded during the no-download metadata pass. It supports Breast/CosMx sample identity, subtype, raw observations, post-threshold observations, panel name, segmentation mode, and source medians.
- Dataset30 source-supported first-pass values include CosMx, Homo sapiens, Breast, infiltrating carcinoma of non-special type, Human Universal Cell Characterization 1000-gene panel, multi-modal segmentation, raw observations 113,115, source post-threshold observations 113,115, and source post-threshold median transcripts 198.
- Current workbook truth differs for final STRAND fields: filtered cells 111,258, detected genes 997, transcripts 51,487,258, and median transcripts 400. These are not in the PDF, Zenodo landing page, or Supplementary Table S1, so approved file inspection is required for exact reconstruction.
- Zenodo record lists one processed-looking aggregated TileDB archive plus two large CosMx source packages. Download plan should prioritize `cosmx_4fa4fec4-3ee0-4763-bf32-ed32a891af55_TileDB.zip` and only download `cosmx_CxAms124S1.zip` / `cosmx_CxAms124S2.zip` if the TileDB archive cannot resolve transcript, boundary, or sample-mapping fields.
- CosMx methods say all samples were aggregated in a single TileDB object and separated into individual samples by slide coordinates. Validators need to recover the Breast mapping before final sample-level counts are trusted.
- Post-download pass completed after user approval. The 4.4 GB TileDB zip was downloaded into a temporary download directory outside the skill package, MD5 matched `fd2ce9812a06f4a3c8448072ba76711e`, and the extracted TileDB was inspected without downloading the S1/S2 raw source packages.
- The TileDB object uses legacy SOMA encoding version 0. New `tiledbsoma` versions failed; the working temporary validator environment used `tiledbsoma==0.1.22`, `tiledb==0.22.3`, and `numpy<1.24`.
- The public CosMx TileDB stores all six samples together. Official GitHub code `preprocessing/alignment/alignment_cosmx_xenium.R` provides the Breast predicate: `Run_Tissue_name == "CxAms124 S1" and y_slide_mm < 6.5`. This gives raw Breast cells = 113,115 across 65 FOVs, matching Supplementary Table S1.
- The RNA counts matrix is physically `var_id x obs_id` (genes x cells), so validators must inspect TileDB schema before assuming modern obs x var orientation. FOV-prefix range reads were faster and more reliable than passing 113k cell labels to the old Python SOMA wrapper.
- The complete candidate row now uses a truth-like filtered-cell rule `nFeature_RNA >= 15` after the official Breast predicate. This exactly reproduces workbook filtered cells = 111,258 and gives file-derived `genes = 1000`, `No.transcripts = 51,683,274`, and `median transcripts = 402`.
- Remaining Dataset30 mismatches are count-convention issues, not missing metadata: workbook has `genes = 997`, `No.transcripts = 51,487,258`, and `median transcripts = 400`. Gene-level `min_cells` did not explain 997 because all 1000 genes are detected in at least 100 retained Breast cells; TileDB probe QC has only 2 background-fail genes, which would give 998.
- No reusable nucleus-boundary geometry was found in the downloaded TileDB object. Keep `Nuclei boundary = -` for this candidate unless a future raw-source download proves otherwise.

## Dataset3 MERFISH Intestine Pilot Lessons

- Dryad landing page and API gave strong source metadata but direct file download was blocked in this environment: `file_stream/1019818` returned 403, API download returned bearer-token 401, and browser-cookie curl hit an Anubis validation page. The skill should not keep retrying one blocked route.
- The better validation route was Bioconductor ExperimentHub. `MerfishData` source metadata mapped Dataset3 to typed RDS resources: EH7543 molecules, EH7547 Baysor segmentation, EH7548 Baysor counts, EH7549 Baysor colData, EH7550 Baysor polygons, EH7551 Cellpose counts, and EH7552 Cellpose colData.
- Downloaded RDS resources were enough to validate basic metadata without the 735 MB Dryad zip: raw molecules 819,665; source panel 241 genes; Baysor counts 241 x 5800; Cellpose counts 241 x 8439; Baysor cell polygons with columns `z, cell, x, y`.
- `Cell boundary = Yes` is file-supported by EH7550. `Nuclei boundary = -` remains correct because DAPI stain/image evidence and Cellpose counts/colData do not prove reusable nucleus boundary polygons or masks.
- The closest source-supported STRAND-like subset is Baysor epithelial-like cells with polygons: 2076 cells, 240 expressed genes, 482,677 transcripts, median 197. This is close to workbook raw cells 2064 but not the full final row.
- A molecule-level audit probe `qc_score >= 0.9796` on that subset gives 255,810 transcripts, close to workbook 256,489, but cells, genes, and median still differ. Treat this as a clue, not a final rule.
- The preserved generic QC workflow alone did not reproduce workbook final fields 1704 cells, 200 genes, 256,489 transcripts, median 122, or 1704 nucleus boundaries. Dataset3 needs a dataset-specific curator rule before final counts should be filled.

## Completed Demo Coverage

Status: the initial demo sequence is complete. Do not continue to a ninth dataset by default. Use `references/demo_evaluation.md` as the compact audit table.

| Demo | Technology | Route | Status |
|---|---|---|---|
| Dataset1 MERFISH U2OS | MERFISH | Bento/Figshare | `complete_auditable` |
| Dataset2 SeqFISH+ fibroblast | seqFISH+ | Bento/Figshare | `complete_auditable` |
| Dataset6 Cardiomyocytes | Molecular Cartography | Bento/Figshare | `complete_with_qc_gap` |
| Dataset18 Xenium Human Pancreas | Xenium | 10x Genomics | `complete_with_qc_gap` |
| Dataset30 CosMx Breast | CosMx | Zenodo TileDB | `complete_with_qc_gap` |
| Dataset3 MERFISH intestine | MERFISH | Dryad/ExperimentHub | `partial_requires_dataset_specific_qc` |
| Dataset5 STARmap AD | STARmap | Zenodo/Google Drive | `partial_requires_dataset_specific_qc` |
| Dataset20 Xenium Breast Preview | Xenium | 10x Genomics | `complete_with_qc_gap` |

## Next Development Milestones

1. **Demo evaluation**
   - Keep `references/demo_evaluation.md` as the source of truth for demo coverage, run status, source-route coverage, and known gaps.
   - Treat `complete_auditable`, `complete_with_qc_gap`, and `partial_requires_dataset_specific_qc` as the controlled status vocabulary.
2. **Validator solidification**
   - Use `scripts/validate_outputs.py` after every run to check JSON/TSV/XLSX field completeness, `Category` spelling, unresolved-field audit shape, and truth-comparison presence.
   - Use `scripts/inspect_10x_xenium_outs.py` for 10x full `outs.zip` bundles with h5 matrix, `cells.zarr.zip`, and transcript CSV evidence.
   - Keep `scripts/inspect_h5ad.py` as the default h5ad validator.
3. **Skill documentation closure**
   - Keep `SKILL.md` lean and route detailed behavior to `references/strand_dataset_fields.md`, `references/prevalidation_toolchain.md`, `references/qc_workflow.md`, `references/development_process.md`, and `references/demo_evaluation.md`.
   - Promote repeated lessons only after they generalize across at least two pilots.
   - Keep the public user contract to three root files: `final_metadata.xlsx`, `final_metadata.tsv`, and `extraction_report.md`.
   - Record full QC details in `internal/qc_parameters.tsv`; keep `curation_notes` as a compact row-level summary.
   - Optimize for the real user path: the user provides a paper, DOI, URL, PDF, or repository page, not an internal Dataset1/Dataset18-style label.
   - Keep the distributable README focused on the method: LLM-orchestrated prevalidation, not generic paper summarization.
   - Keep optional bundled dependencies documented with license notices and fallback behavior.
4. **Regression eval**
   - The acceptance bar is complete, auditable metadata, not exact workbook parity.
   - `truth_comparison.md` must explain QC/count-convention differences and must not use workbook truth as extraction evidence.
   - `unresolved_fields.tsv` may be non-empty only when each row has a reason and a next action or needed evidence.
5. **Deferred work**
   - Do not generalize CosMx TileDB, STARmap reads-assignment, or ExperimentHub RDS validators until another repeated case justifies the added code.
   - Do not build an external one-click web app or standalone CLI yet; the distributable Codex Skill is the current scope.
   - Do not modify main `Datasets.xlsx` or front-end dataset pages as part of skill-development work.

## Preferred Development Loop

1. Define the next source input and expected run directory from user-provided paper/data links, not from an internal dataset number.
2. If the user supplied only a topic/search request, generate search queries, call the available paper lookup/search route, write `internal/upstream_paper_search.json`, and select or ask the user to select a candidate.
3. Run no-download extraction first.
4. Produce `download_plan.md`.
5. Wait for approval.
6. Run reusable validators on approved files.
7. Apply `qc_workflow.md` only as a STRAND curation rule, not as source evidence.
8. Export internal JSON/TSV/XLSX, `qc_parameters.tsv`, and unresolved fields.
9. Run `scripts/package_final_outputs.py` to create public `final_metadata.xlsx`, `final_metadata.tsv`, and `extraction_report.md`.
10. Run `scripts/validate_outputs.py --mode public` on the run outputs. Add `--require-upstream-search` for search-first runs.
11. Compare against truth only when truth is provided.
12. Add a short lesson to the run's `notes_for_future_skill.md`.
13. Promote repeated lessons into this skill only when they generalize beyond one dataset.

## Validation Checklist

- `final_metadata.tsv` and `final_metadata.xlsx` column order matches `strand_dataset_fields.md`.
- XLSX opens locally.
- `internal/qc_parameters.tsv` exists with the fixed header and at least one row.
- Search-first runs include `internal/upstream_paper_search.json` with generated queries, candidate papers, selected candidate or confirmation need, and tool route used.
- `No.` is blank unless a target registry/workbook ID was supplied or the user explicitly requested run-local numbering.
- `Category` is used; `Catagory` is not used.
- Large files are outside the repository unless the user explicitly asks otherwise.
- Downloaded-data-derived numbers cite the inspected file.
- `internal/truth_comparison.md` separates matched fields, post-download fields, and curator-review fields.
- Run outputs pass:

```bash
python3 agent/skills/paper-to-spatial-dataset-extraction/scripts/validate_outputs.py --mode public --require-truth <run-dir>
```

- Skill edits pass:

```bash
python3 <skill-creator>/scripts/quick_validate.py agent/skills/paper-to-spatial-dataset-extraction
```

## When To Use Handoff

Use the `handoff` skill for a one-time temporary transition document. It writes to the OS temporary directory by design. For durable project memory, update this file or a run-local `notes_for_future_skill.md` instead.
