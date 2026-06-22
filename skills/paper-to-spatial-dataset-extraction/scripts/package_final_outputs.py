#!/usr/bin/env python3
"""Package a STRAND extraction run into user-facing outputs."""

import argparse
import csv
import json
import shutil
import sys
from pathlib import Path


PUBLIC_FILES = {
    "final_metadata.xlsx",
    "final_metadata.tsv",
    "extraction_report.md",
}
QC_PARAMETER_FIELDS = [
    "dataset",
    "sample",
    "step",
    "parameter",
    "value",
    "applied",
    "evidence_source",
    "effect_on_counts",
    "notes",
]
LEGACY_TO_PUBLIC = {
    "Datasets_filled.xlsx": "final_metadata.xlsx",
    "dataset_rows.tsv": "final_metadata.tsv",
}


def output_dir(path):
    path = Path(path)
    return path if path.name == "outputs" else path / "outputs"


def find_artifact(out_dir, name):
    candidates = [out_dir / name, out_dir / "internal" / name]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def ensure_writable(path, overwrite):
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists; use --overwrite")


def load_rows(out_dir):
    path = find_artifact(out_dir, "dataset_rows.json")
    if not path:
        return []
    data = json.loads(path.read_text())
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    return data if isinstance(data, list) else []


def read_unresolved(out_dir):
    path = find_artifact(out_dir, "unresolved_fields.tsv")
    if not path or not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_qc_parameters(out_dir):
    path = find_artifact(out_dir, "qc_parameters.tsv")
    if not path or not path.exists():
        return []
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_upstream_search(out_dir):
    path = find_artifact(out_dir, "upstream_paper_search.json")
    if not path or not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        return {"_error": str(exc)}
    return data if isinstance(data, dict) else {"_error": "upstream_paper_search.json must be an object"}


def ensure_qc_parameters(out_dir, rows):
    internal = out_dir / "internal"
    internal.mkdir(exist_ok=True)
    path = internal / "qc_parameters.tsv"
    if path.exists():
        return path
    dataset = compact_values(rows, "Dataset") if rows else "-"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=QC_PARAMETER_FIELDS, delimiter="\t")
        writer.writeheader()
        writer.writerow(
            {
                "dataset": dataset,
                "sample": "all",
                "step": "qc_parameter_profile",
                "parameter": "not_recorded",
                "value": "-",
                "applied": "not_recorded",
                "evidence_source": "-",
                "effect_on_counts": "QC parameter profile was not provided for this legacy run.",
                "notes": "Future runs should record noise filters, min_genes, min_cells, nc_ratio, and mitochondrial checks.",
            }
        )
    return path


def read_curation_report(out_dir):
    path = find_artifact(out_dir, "curation_report.md")
    return path.read_text() if path else ""


def compact_values(rows, field, limit=6):
    values = []
    for row in rows:
        value = row.get(field, "")
        if value in ("", "-", None):
            continue
        text = str(value)
        if text not in values:
            values.append(text)
    if not values:
        return "-"
    suffix = "" if len(values) <= limit else f", ... (+{len(values) - limit})"
    return ", ".join(values[:limit]) + suffix


def markdown_cell(value):
    text = str(value if value not in (None, "") else "-")
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def append_upstream_search_section(lines, upstream_search):
    lines.extend(["", "## Upstream Paper Search", ""])
    if not upstream_search:
        lines.append("- Not used; extraction started from user-provided article, DOI, PDF, repository, or dataset-page inputs.")
        return

    if upstream_search.get("_error"):
        lines.append(f"- `internal/upstream_paper_search.json` could not be parsed: {upstream_search['_error']}")
        return

    search_was_needed = upstream_search.get("search_was_needed")
    lines.append(f"- Search was needed: {'Yes' if search_was_needed else 'No'}")
    if upstream_search.get("user_query"):
        lines.append(f"- User query: {upstream_search['user_query']}")
    if upstream_search.get("tool_route_used"):
        lines.append(f"- Tool route used: {upstream_search['tool_route_used']}")
    if upstream_search.get("search_tools_available"):
        lines.append(f"- Tools available: {', '.join(map(str, upstream_search['search_tools_available']))}")

    queries = upstream_search.get("queries") or []
    if queries:
        lines.append("- Generated queries:")
        for query in queries[:6]:
            query_text = query.get("query", query) if isinstance(query, dict) else query
            tool = query.get("tool", "-") if isinstance(query, dict) else "-"
            lines.append(f"  - `{query_text}` via `{tool}`")

    candidates = upstream_search.get("candidate_papers") or []
    lines.append(f"- Candidate papers/data pages recorded: {len(candidates)}")

    selected = upstream_search.get("selected_paper") or {}
    if isinstance(selected, dict) and any(selected.values()):
        lines.append("- Selected candidate:")
        for key in ["title", "doi", "article_url"]:
            value = selected.get(key)
            if value:
                lines.append(f"  - {key}: {value}")
        data_links = selected.get("data_links") or []
        if data_links:
            lines.append(f"  - data_links: {', '.join(map(str, data_links[:5]))}")
    else:
        lines.append("- Selected candidate: none")

    if upstream_search.get("selection_confidence"):
        lines.append(f"- Selection confidence: {upstream_search['selection_confidence']}")
    if upstream_search.get("selection_reason"):
        lines.append(f"- Selection reason: {upstream_search['selection_reason']}")
    lines.append(f"- Needs user confirmation: {'Yes' if upstream_search.get('needs_user_confirmation') else 'No'}")


def first_heading_text(markdown, heading):
    lines = markdown.splitlines()
    capture = False
    captured = []
    for line in lines:
        if line.strip() == heading:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            captured.append(line)
    text = "\n".join(captured).strip()
    return text


def move_internal_artifacts(out_dir, overwrite):
    internal = out_dir / "internal"
    internal.mkdir(exist_ok=True)
    for path in sorted(out_dir.iterdir()):
        if path.name == "internal" or path.name in PUBLIC_FILES:
            continue
        if path.is_dir():
            continue
        target = internal / path.name
        ensure_writable(target, overwrite)
        if target.exists():
            target.unlink()
        path.rename(target)


def copy_public_outputs(out_dir, overwrite):
    for legacy_name, public_name in LEGACY_TO_PUBLIC.items():
        source = find_artifact(out_dir, legacy_name)
        if not source:
            raise FileNotFoundError(f"missing {legacy_name}; cannot create {public_name}")
        target = out_dir / public_name
        ensure_writable(target, overwrite)
        shutil.copy2(source, target)


def internal_files(out_dir):
    internal = out_dir / "internal"
    if not internal.exists():
        return []
    return sorted(path.name for path in internal.iterdir() if path.is_file())


def report_title(rows):
    datasets = [row.get("Dataset") for row in rows if row.get("Dataset")]
    dataset = datasets[0] if datasets else "Spatial Dataset"
    return f"# Extraction Report - {dataset}"


def build_report(out_dir):
    rows = load_rows(out_dir)
    ensure_qc_parameters(out_dir, rows)
    unresolved = read_unresolved(out_dir)
    qc_parameters = read_qc_parameters(out_dir)
    upstream_search = read_upstream_search(out_dir)
    curation_report = read_curation_report(out_dir)
    files = internal_files(out_dir)

    datasets = compact_values(rows, "Dataset")
    technologies = compact_values(rows, "Technology")
    species = compact_values(rows, "Species")
    organs = compact_values(rows, "Organ")
    sample_names = compact_values(rows, "Sample Name", limit=10)
    statuses = compact_values(rows, "usability_status", limit=10)
    review_required = any(str(row.get("review_required", "")).lower() == "true" for row in rows)

    source_files = [
        name
        for name in files
        if name.endswith(".json") or name in {"download_plan.md", "curation_report.md", "truth_comparison.md"}
    ]
    postdownload_files = [name for name in files if name.startswith("postdownload_") or "inspection" in name]

    lines = [
        report_title(rows),
        "",
        "## Final Metadata Summary",
        "",
        f"- Rows: {len(rows)}",
        f"- Dataset: {datasets}",
        f"- Technology: {technologies}",
        f"- Species: {species}",
        f"- Organ: {organs}",
        f"- Samples: {sample_names}",
        f"- Usability status: {statuses}",
        f"- Curator review required: {'Yes' if review_required else 'No'}",
    ]
    append_upstream_search_section(lines, upstream_search)
    lines.extend(["", "## Evidence Sources", ""])
    if source_files:
        lines.extend(f"- `internal/{name}`" for name in source_files)
    else:
        lines.append("- No internal source files were found.")

    lines.extend(
        [
            "",
            "## Downloaded Files And Checksums",
            "",
        ]
    )
    if postdownload_files:
        lines.extend(
            f"- See `internal/{name}` for file-inspection, checksum, or post-download evidence."
            for name in postdownload_files
        )
    else:
        lines.append("- No downloaded-file inspection artifacts were found. This may be a no-download extraction.")

    lines.extend(
        [
            "",
            "## Field-Level Evidence",
            "",
            "| Field | Filled values | Evidence note |",
            "| --- | --- | --- |",
        ]
    )
    for field in [
        "Dataset",
        "Category",
        "Technology",
        "Species",
        "Organ",
        "Tissue",
        "Cell Type",
        "Group",
        "Sample Name",
        "No.batch",
        "Raw No.cells",
        "No.genes",
        "cellclass",
        "celltype（minor）",
        "Cell boundary",
        "Nuclei boundary",
        "Filtered No.cells/nuclei",
        "cells",
        "genes",
        "No.transcripts",
        "median transcripts",
        "No.NucleiBoundary",
        "Data link",
    ]:
        values = compact_values(rows, field)
        note = "See row-level `curation_notes` and internal evidence files."
        if values == "-":
            note = "Not filled; check unresolved fields or curator notes."
        lines.append(f"| {field} | {values} | {note} |")

    lines.extend(
        [
            "",
            "## QC Parameters Used",
            "",
        ]
    )
    if qc_parameters:
        lines.append("| Step | Parameter | Value | Applied | Evidence source | Effect on counts | Notes |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for row in qc_parameters:
            lines.append(
                "| "
                + " | ".join(
                    [
                        markdown_cell(row.get("step", "-")),
                        markdown_cell(row.get("parameter", "-")),
                        markdown_cell(row.get("value", "-")),
                        markdown_cell(row.get("applied", "-")),
                        markdown_cell(row.get("evidence_source", "-")),
                        markdown_cell(row.get("effect_on_counts", "-")),
                        markdown_cell(row.get("notes", "-")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("- No QC parameter rows were recorded.")

    qc_text = first_heading_text(curation_report, "## QC Workflow Use")
    if not qc_text:
        qc_text = first_heading_text(curation_report, "## Current Status")
    if not qc_text:
        qc_text = "See `internal/curation_report.md` and row-level `curation_notes` for count conventions."

    lines.extend(
        [
            "",
            "## QC And Count Convention Notes",
            "",
            qc_text,
            "",
            "## Unresolved Or Curator-Review Fields",
            "",
        ]
    )
    if unresolved:
        lines.append("| Field | Reason | Next action |")
        lines.append("| --- | --- | --- |")
        for row in unresolved:
            field = row.get("field", "-")
            reason = row.get("reason") or row.get("status") or "-"
            next_action = row.get("next_action") or row.get("needed_source") or "-"
            lines.append(f"| {field} | {reason} | {next_action} |")
    else:
        lines.append("- No unresolved fields were recorded. Remaining differences, if any, are QC/count-convention or curator-review notes.")

    conclusion = "The metadata package is complete and auditable."
    if review_required:
        conclusion = "The metadata package is complete enough for review; curator review remains required for the noted fields or conventions."
    if unresolved:
        conclusion = "The metadata package is partial: unresolved fields need the listed next actions before final curation."

    lines.extend(
        [
            "",
            "## Review Conclusion",
            "",
            conclusion,
            "",
            "## Internal Audit Files",
            "",
        ]
    )
    if files:
        lines.extend(f"- `internal/{name}`" for name in files)
    else:
        lines.append("- No internal audit files were found.")
    return "\n".join(lines).rstrip() + "\n"


def package_outputs(path, tidy, overwrite):
    out_dir = output_dir(path)
    if not out_dir.exists():
        raise FileNotFoundError(f"outputs directory not found: {out_dir}")
    (out_dir / "internal").mkdir(exist_ok=True)

    copy_public_outputs(out_dir, overwrite)
    if tidy:
        move_internal_artifacts(out_dir, overwrite)

    report_path = out_dir / "extraction_report.md"
    ensure_writable(report_path, overwrite)
    report_path.write_text(build_report(out_dir))
    return out_dir


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Run directory or outputs directory to package")
    parser.add_argument("--tidy", action="store_true", help="Move non-public root files into outputs/internal")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing public/internal files")
    args = parser.parse_args()

    try:
        out_dir = package_outputs(args.path, args.tidy, args.overwrite)
    except Exception as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print(f"PASS {out_dir}")
    print("  - final_metadata.xlsx")
    print("  - final_metadata.tsv")
    print("  - extraction_report.md")
    print("  - internal/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
