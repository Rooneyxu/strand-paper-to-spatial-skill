# Extraction Report - Systematic discovery of subcellular RNA patterns in the gut epithelium

## Final Metadata Summary

- Rows: 1
- Dataset: Systematic discovery of subcellular RNA patterns in the gut epithelium
- Technology: MERFISH
- Species: -
- Organ: Gut
- Samples: -
- Usability status: needs_article_data_availability
- Curator review required: Yes

## Upstream Paper Search

- Search was needed: Yes
- User query: small-intestine MERFISH subcellular-resolution spatial transcriptomics dataset
- Tool route used: bundled optional `paper-lookup`
- Databases queried: PubMed, OpenAlex, Semantic Scholar
- Candidate selected for follow-up: `Systematic discovery of subcellular RNA patterns in the gut epithelium`
- DOI: `10.1186/s13059-025-03786-1`
- Semantic Scholar status: rate-limited with public shared-pool `429`
- Selection confidence: Medium
- Needs user confirmation: Yes

Search results are candidate-selection evidence only. They are not used to fill count, QC, boundary, or sample-level metadata fields.

## Evidence Sources

- `internal/upstream_paper_search.json`
- `internal/dataset_rows.json`
- `internal/download_plan.md`
- `internal/qc_parameters.tsv`
- `internal/unresolved_fields.tsv`

## Downloaded Files And Checksums

- No files were downloaded in this demo.
- No checksums were produced.
- `internal/download_plan.md` lists the next no-download extraction and download-planning actions.

## Field-Level Evidence

| Field | Filled values | Evidence note |
| --- | --- | --- |
| Dataset | Systematic discovery of subcellular RNA patterns in the gut epithelium | PubMed/OpenAlex candidate metadata. |
| Category | tissue | Candidate title indicates gut epithelium tissue context; curator review required. |
| Technology | MERFISH | Search query and candidate match; downstream article verification required. |
| Species | - | Not filled from search metadata. |
| Organ | Gut | Candidate title evidence only; downstream article verification required. |
| Tissue | gut epithelium | Candidate title evidence only; downstream article verification required. |
| Cell boundary | - | Requires repository/file evidence. |
| Nuclei boundary | - | Requires repository/file evidence. |
| Count fields | - | Requires article source metrics or file validators. |
| Data link | https://doi.org/10.1186/s13059-025-03786-1 | DOI from PubMed/OpenAlex. |

## QC Parameters Used

| Step | Parameter | Value | Applied | Evidence source | Effect on counts | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| qc_parameter_profile | not_applicable_search_only | - | not_applied | internal/upstream_paper_search.json | no count fields filled | Search-only demo; QC starts after repository/file evidence exists. |

## QC And Count Convention Notes

No QC filters were applied. This demo stops after upstream paper discovery, so final STRAND count fields remain unresolved.

## Unresolved Or Curator-Review Fields

| Field | Reason | Next action |
| --- | --- | --- |
| Species | Search metadata did not verify species. | Read article methods and Data availability. |
| Cell boundary | Search metadata cannot prove reusable geometry. | Inspect repository files or manifests. |
| Nuclei boundary | Search metadata cannot prove reusable nucleus geometry. | Inspect repository files or manifests. |
| Count fields | Search metadata cannot provide final STRAND count conventions. | Run source extraction and approved file validators. |
| Data repository | DOI identified, repository not yet verified. | Read article Data availability and dataset landing pages. |

## Review Conclusion

The upstream search stage works and produced a plausible candidate, but the metadata package is intentionally partial. Downstream article and repository extraction are required before this row can be considered ready for ingestion.

## Internal Audit Files

- `internal/upstream_paper_search.json`
- `internal/dataset_rows.json`
- `internal/download_plan.md`
- `internal/qc_parameters.tsv`
- `internal/unresolved_fields.tsv`
