#!/usr/bin/env python3
"""Inspect a 10x Xenium full outs.zip for STRAND metadata evidence."""

import argparse
import csv
import gzip
import hashlib
import json
import time
import zipfile
from pathlib import Path

import h5py
import numpy as np

try:
    import zarr
    from zarr.storage import ZipStore
except Exception:  # pragma: no cover - dependency gate is reported in output.
    zarr = None
    ZipStore = None


CORE_MEMBERS = [
    "experiment.xenium",
    "metrics_summary.csv",
    "gene_panel.json",
    "cell_feature_matrix.h5",
    "cell_feature_matrix.zarr.zip",
    "cells.zarr.zip",
    "cell_boundaries.csv.gz",
    "nucleus_boundaries.csv.gz",
    "transcripts.csv.gz",
]


def md5sum(path):
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_selected(zip_path, extract_dir):
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        for prefix in ("outs/", ""):
            members = [f"{prefix}{name}" for name in CORE_MEMBERS]
            if all(name in names for name in members):
                break
        else:
            candidates = [name for name in sorted(names) if Path(name).name in CORE_MEMBERS]
            raise SystemExit(f"missing zip members for known layouts; matched candidates: {candidates}")

        for name in members:
            target = extract_dir / name
            if not target.exists():
                archive.extract(name, extract_dir)
    return extract_dir / prefix.rstrip("/") if prefix else extract_dir


def load_gene_matrix(h5_path):
    with h5py.File(h5_path, "r") as handle:
        matrix = handle["matrix"]
        data = matrix["data"][()]
        indices = matrix["indices"][()]
        indptr = matrix["indptr"][()]
        barcodes = [item.decode() for item in matrix["barcodes"][()]]
        feature_type = np.array([item.decode() for item in matrix["features"]["feature_type"][()]])
        feature_names = [item.decode() for item in matrix["features"]["name"][()]]

    gene_mask = feature_type == "Gene Expression"
    qv20_counts = np.zeros(len(indptr) - 1, dtype=np.int64)
    detected_genes = np.zeros(len(indptr) - 1, dtype=np.int32)
    detected_cells_by_gene = np.zeros(int(gene_mask.sum()), dtype=np.int32)
    gene_index_to_compact = {int(index): offset for offset, index in enumerate(np.flatnonzero(gene_mask))}

    for cell_index in range(len(indptr) - 1):
        start = int(indptr[cell_index])
        end = int(indptr[cell_index + 1])
        if start == end:
            continue
        feature_indices = indices[start:end]
        values = data[start:end]
        is_gene = gene_mask[feature_indices]
        if not is_gene.any():
            continue
        gene_values = values[is_gene]
        gene_indices = feature_indices[is_gene]
        qv20_counts[cell_index] = int(gene_values.sum())
        detected_genes[cell_index] = int(len(gene_values))
        for gene_index in gene_indices:
            detected_cells_by_gene[gene_index_to_compact[int(gene_index)]] += 1

    nonempty = qv20_counts > 0
    return {
        "gene_names": {name for name, kind in zip(feature_names, feature_type) if kind == "Gene Expression"},
        "cell_id_to_index": {barcode: index for index, barcode in enumerate(barcodes)},
        "qv20_counts": qv20_counts,
        "detected_genes": detected_genes,
        "metrics": {
            "barcodes": int(len(indptr) - 1),
            "feature_count": int(len(feature_type)),
            "gene_features": int(gene_mask.sum()),
            "genes_detected_at_least_one_cell": int((detected_cells_by_gene > 0).sum()),
            "genes_detected_min_cells_50": int((detected_cells_by_gene >= 50).sum()),
            "nonempty_gene_cells": int(nonempty.sum()),
            "qv20_gene_matrix_transcripts": int(qv20_counts.sum()),
            "median_qv20_gene_transcripts_nonempty": int(np.median(qv20_counts[nonempty])) if nonempty.any() else None,
            "median_detected_genes_nonempty": float(np.median(detected_genes[nonempty])) if nonempty.any() else None,
        },
    }


def inspect_cells_zarr(cells_zarr_zip):
    if zarr is None:
        return {"available": False, "error": "zarr is not installed"}
    with ZipStore(str(cells_zarr_zip), mode="r") as store:
        root = zarr.open_group(store=store, mode="r")
        attrs = dict(root.attrs)
        polygon_num_vertices = root["polygon_num_vertices"][:]
        result = {
            "available": True,
            "attrs": attrs,
            "number_cells": int(attrs.get("number_cells")),
            "polygon_set_names": attrs.get("polygon_set_names"),
            "nucleus_boundary_count_raw": int((polygon_num_vertices[0] > 0).sum()),
            "cell_boundary_count_raw": int((polygon_num_vertices[1] > 0).sum()),
            "nucleus_vertices_min": int(polygon_num_vertices[0].min()),
            "nucleus_vertices_max": int(polygon_num_vertices[0].max()),
            "cell_vertices_min": int(polygon_num_vertices[1].min()),
            "cell_vertices_max": int(polygon_num_vertices[1].max()),
        }
        if "cell_summary" in root:
            cell_summary = root["cell_summary"][:]
            names = list(root["cell_summary"].attrs.get("column_names", []))
            if "cell_area" in names and "nucleus_area" in names:
                cell_area = cell_summary[:, names.index("cell_area")]
                nucleus_area = cell_summary[:, names.index("nucleus_area")]
                ratio = nucleus_area / cell_area
                result["nc_ratio"] = {
                    "formula": "nucleus_area / cell_area",
                    "cell_area_positive": int((cell_area > 0).sum()),
                    "nucleus_area_positive": int((nucleus_area > 0).sum()),
                    "gt_1": int((ratio > 1).sum()),
                    "le_1": int((ratio <= 1).sum()),
                    "min": float(np.nanmin(ratio)),
                    "median": float(np.nanmedian(ratio)),
                    "max": float(np.nanmax(ratio)),
                }
    return result


def resolve_cell_index(cell_id, cell_id_to_index, cell_count):
    if cell_id in cell_id_to_index:
        return cell_id_to_index[cell_id]
    try:
        cell_index = int(cell_id) - 1
    except ValueError:
        return None
    return cell_index if 0 <= cell_index < cell_count else None


def stream_transcripts(transcripts_csv_gz, gene_names, cell_id_to_index, qv20_counts, detected_genes):
    allqv_gene_counts = np.zeros(len(qv20_counts), dtype=np.int64)
    counts = {
        "rows_total": 0,
        "rows_qv_ge_20": 0,
        "gene_rows_total": 0,
        "gene_rows_qv_ge_20": 0,
        "assigned_rows_total": 0,
        "assigned_gene_rows_total": 0,
        "assigned_gene_rows_qv_ge_20": 0,
        "overlaps_nucleus_rows_total": 0,
        "overlaps_nucleus_gene_rows_total": 0,
    }
    features = set()
    gene_features = set()
    cell_ids = set()
    gene_cell_ids = set()
    gene_cell_ids_qv20 = set()
    start = time.time()
    with gzip.open(transcripts_csv_gz, "rt", newline="") as handle:
        reader = csv.DictReader(handle)
        for row_index, row in enumerate(reader, 1):
            feature = row["feature_name"]
            qv = float(row["qv"])
            cell_id = row["cell_id"]
            assigned = cell_id not in ("", "0", "-1", "None", "UNASSIGNED")
            is_gene = feature in gene_names
            overlaps = row.get("overlaps_nucleus") in ("1", "True", "true")

            counts["rows_total"] += 1
            features.add(feature)
            if qv >= 20:
                counts["rows_qv_ge_20"] += 1
            if assigned:
                counts["assigned_rows_total"] += 1
                cell_ids.add(cell_id)
            if overlaps:
                counts["overlaps_nucleus_rows_total"] += 1
            if is_gene:
                counts["gene_rows_total"] += 1
                gene_features.add(feature)
                if assigned:
                    counts["assigned_gene_rows_total"] += 1
                    gene_cell_ids.add(cell_id)
                    cell_index = resolve_cell_index(cell_id, cell_id_to_index, len(allqv_gene_counts))
                    if cell_index is not None:
                        allqv_gene_counts[cell_index] += 1
                if qv >= 20:
                    counts["gene_rows_qv_ge_20"] += 1
                    if assigned:
                        counts["assigned_gene_rows_qv_ge_20"] += 1
                        gene_cell_ids_qv20.add(cell_id)
                if overlaps:
                    counts["overlaps_nucleus_gene_rows_total"] += 1
            if row_index % 10_000_000 == 0:
                print(f"progress {row_index} rows {round(time.time() - start, 1)} sec", flush=True)

    counts.update(
        {
            "unique_features": len(features),
            "unique_gene_features": len(gene_features),
            "unique_assigned_cells": len(cell_ids),
            "unique_assigned_gene_cells": len(gene_cell_ids),
            "unique_assigned_gene_cells_qv_ge_20": len(gene_cell_ids_qv20),
            "elapsed_sec": round(time.time() - start, 2),
        }
    )
    filter_probes = []
    for filter_name, values, thresholds in [
        ("detected_genes", detected_genes, range(10, 31)),
        ("qv20_gene_counts", qv20_counts, range(10, 41)),
        ("allqv_gene_counts", allqv_gene_counts, range(10, 61)),
    ]:
        for threshold in thresholds:
            keep = values >= threshold
            cells = int(keep.sum())
            if cells == 0:
                continue
            filter_probes.append(
                {
                    "filter": filter_name,
                    "threshold": threshold,
                    "cells": cells,
                    "allqv_gene_transcripts": int(allqv_gene_counts[keep].sum()),
                    "median_allqv_gene_transcripts": int(np.median(allqv_gene_counts[keep])),
                    "qv20_gene_transcripts": int(qv20_counts[keep].sum()),
                    "median_qv20_gene_transcripts": int(np.median(qv20_counts[keep])),
                }
            )
    return counts, filter_probes


def inspect(resource_id, zip_path, output_json):
    extract_dir = zip_path.parent / f"{resource_id}_selected"
    data_dir = extract_selected(zip_path, extract_dir)
    matrix = load_gene_matrix(data_dir / "cell_feature_matrix.h5")
    cells_zarr = inspect_cells_zarr(data_dir / "cells.zarr.zip")
    transcript_counts, filter_probes = stream_transcripts(
        data_dir / "transcripts.csv.gz",
        matrix["gene_names"],
        matrix["cell_id_to_index"],
        matrix["qv20_counts"],
        matrix["detected_genes"],
    )
    result = {
        "resource_id": resource_id,
        "zip_path": str(zip_path),
        "zip_bytes": zip_path.stat().st_size,
        "zip_md5": md5sum(zip_path),
        "selected_extract_dir": str(extract_dir),
        "selected_data_dir": str(data_dir),
        "matrix": matrix["metrics"],
        "cells_zarr": cells_zarr,
        "transcripts_csv": transcript_counts,
        "filter_probes": filter_probes,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resource_id")
    parser.add_argument("outs_zip", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()

    result = inspect(args.resource_id, args.outs_zip, args.output_json)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
