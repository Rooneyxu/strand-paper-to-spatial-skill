# Upstream Paper Search Contract

Use this reference only when the user has not supplied a specific PDF, DOI, article URL, repository page, or dataset landing page and instead asks to find candidate subcellular-resolution spatial transcriptomics datasets.

## Purpose

The upstream search stage finds candidate papers and dataset landing pages. It does not extract final STRAND metadata by itself. Search snippets, abstracts, and paper-lookup results can justify candidate selection, but final metadata fields still need article, repository, or file-inspection evidence.

## When To Run

Run upstream search when the input is broad, for example:

- `Find pancreas subcellular spatial transcriptomics datasets.`
- `Search for MERFISH intestine datasets and make a metadata table.`
- `I want a Xenium cancer dataset, choose a good candidate first.`
- `Look for a reusable CosMx dataset with downloadable data.`

Skip upstream search when the user already provides any of these:

- Local PDF path.
- DOI.
- Article URL.
- Repository or dataset landing page.
- Downloaded data file.

## Tool Routing

Prefer the most paper-aware route available in the current environment.

1. Use a `paper-lookup` skill if it is installed and callable. In this distribution it may be bundled as the optional sibling skill `agent/skills/paper-lookup/`. It is designed to orchestrate scholarly lookups across sources such as PubMed, PMC, bioRxiv, medRxiv, arXiv, OpenAlex, Crossref, Semantic Scholar, CORE, and Unpaywall.
2. If `paper-lookup` is not available, use an academic paper-search MCP/tool when available.
3. For biomedical topics, BioMCP/PubMed-style search is acceptable, especially for DOI, article, and Data availability discovery.
4. Use the project-approved web search route only as fallback or to read dataset landing pages that scholarly APIs do not expose.

Record which route was used in `internal/upstream_paper_search.json`. If no paper-search tool is available, say so in the report and continue with the best web-search fallback instead of pretending a scholarly API was used.

`paper-lookup` is optional. A missing sibling skill, missing API keys, or rate-limited database such as Semantic Scholar must not block extraction from a user-supplied DOI, PDF, article URL, or dataset page. Record the failure in `databases_queried.status` and continue with available sources.

## Query Generation

Generate 3-6 targeted queries. Combine the user's tissue/disease/entity with subcellular spatial terms and technology terms.

For a request like `pancreas subcellular-resolution datasets`, good query candidates are:

```text
"pancreas" "subcellular" "spatial transcriptomics"
"pancreatic cancer" Xenium dataset
"pancreas" MERFISH OR seqFISH OR CosMx OR STARmap
"pancreas" "Data availability" "spatial"
"single-cell spatial in situ" pancreas
```

For broad requests, include both biology terms and repository/data terms:

```text
<tissue or disease> "spatial transcriptomics" "data availability"
<tissue or disease> "Xenium" "dataset"
<tissue or disease> "CosMx" "Zenodo"
<tissue or disease> "MERFISH" "Figshare"
<tissue or disease> "seqFISH" "Dryad"
```

## Candidate Filter

Keep a candidate only when the result suggests all of the following:

- It is spatial transcriptomics or in situ transcriptomics.
- It plausibly has subcellular or single-molecule resolution, or provides cell/nucleus segmentation evidence.
- It has reusable data availability: repository page, accession, DOI, direct dataset URL, or clear supplementary data route.
- It is a primary dataset paper, dataset landing page, or official preview dataset, not a review-only article.

Reject or down-rank:

- Spot-level spatial data such as Visium unless the user explicitly asks for it.
- scRNA-seq-only, bulk RNA-seq, imaging-only, or simulation-only records.
- Review articles without reusable dataset links.
- Results where repository access is unclear and no DOI/article lead exists.

## Selection Rules

Select one candidate automatically only when confidence is high:

- The article or landing page clearly names the technology and biological context.
- A DOI or stable article URL is available.
- A data repository or official dataset URL is available.
- The candidate matches the user's requested tissue/disease/technology.

If there are multiple plausible candidates or confidence is medium/low, write the candidate list and ask the user to choose before downstream extraction or downloading.

## Required Internal JSON

Write `outputs/internal/upstream_paper_search.json` with this shape:

```json
{
  "user_query": "pancreas subcellular-resolution spatial datasets",
  "search_was_needed": true,
  "search_tools_available": ["paper-lookup", "paper-search", "biomcp", "web-search"],
  "tool_route_used": "paper-lookup",
  "queries": [
    {
      "query": "\"pancreas\" \"subcellular\" \"spatial transcriptomics\"",
      "purpose": "Find primary subcellular spatial transcriptomics papers for pancreas.",
      "tool": "paper-lookup"
    }
  ],
  "databases_queried": [
    {
      "tool": "paper-lookup",
      "database": "PubMed",
      "endpoint": "recorded by paper lookup tool when available"
    }
  ],
  "candidate_papers": [
    {
      "title": "Paper or dataset title",
      "doi": "10.xxxx/xxxxx",
      "year": "2024",
      "journal": "Journal name",
      "article_url": "https://example.org/article",
      "oa_pdf_url": "https://example.org/article.pdf",
      "data_links": ["https://example.org/dataset"],
      "technology_hints": ["Xenium"],
      "species_hints": ["Homo sapiens"],
      "organ_tissue_hints": ["Pancreas"],
      "subcellular_relevance": "yes",
      "repository_evidence": "Official dataset page lists Xenium output files.",
      "rejection_reason": ""
    }
  ],
  "selected_paper": {
    "title": "Selected candidate title",
    "doi": "10.xxxx/xxxxx",
    "article_url": "https://example.org/article",
    "data_links": ["https://example.org/dataset"]
  },
  "selection_confidence": "high",
  "selection_reason": "Best match to requested pancreas subcellular spatial dataset with a stable dataset page.",
  "needs_user_confirmation": false
}
```

Use an empty object for `selected_paper` when no candidate is selected. Use `needs_user_confirmation: true` when candidate choice is ambiguous.

## Downstream Handoff

After selection, hand off only stable identifiers to the normal extraction workflow:

- DOI or article URL.
- Local PDF if downloaded or supplied.
- Dataset landing page or repository URL.
- Any explicit data accessions.

Do not transfer count values, boundary values, or QC assumptions from search snippets into `dataset_rows.json`. Those fields must be re-derived in the extraction stage.
