#!/usr/bin/env python3
"""Inspect an h5ad file for STRAND dataset curation."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def to_jsonable(value: Any) -> Any:
    try:
        import numpy as np
        import pandas as pd
    except Exception:
        np = None
        pd = None

    if np is not None and isinstance(value, np.integer):
        return int(value)
    if np is not None and isinstance(value, np.floating):
        return float(value)
    if np is not None and isinstance(value, np.ndarray):
        return value.tolist()
    if pd is not None and isinstance(value, pd.Index):
        return [str(item) for item in value.tolist()]
    return value


def summarize_matrix(adata, exclude_gene_prefixes: list[str]) -> dict[str, Any]:
    import numpy as np

    matrix = adata.X
    per_cell = np.asarray(matrix.sum(axis=1)).ravel()
    summary: dict[str, Any] = {
        "total": int(per_cell.sum()),
        "median_per_cell": float(np.median(per_cell)) if per_cell.size else 0,
    }

    if exclude_gene_prefixes:
        var_names = [str(name) for name in adata.var_names]
        target_mask = np.array(
            [
                not any(name.lower().startswith(prefix.lower()) for prefix in exclude_gene_prefixes)
                for name in var_names
            ],
            dtype=bool,
        )
        target_matrix = matrix[:, target_mask]
        target_per_cell = np.asarray(target_matrix.sum(axis=1)).ravel()
        summary["target_genes_excluding_prefixes"] = int(target_mask.sum())
        summary["target_total_excluding_prefixes"] = int(target_per_cell.sum())
        summary["target_median_per_cell_excluding_prefixes"] = (
            float(np.median(target_per_cell)) if target_per_cell.size else 0
        )

    return summary


def get_points_table(adata):
    import pandas as pd

    points = adata.uns.get("points")
    if points is None:
        return None
    if isinstance(points, pd.DataFrame):
        return points
    try:
        return pd.DataFrame(points)
    except Exception:
        return None


def summarize_points(points, exclude_gene_prefixes: list[str], exclude_cells: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "rows": int(len(points)),
        "columns": [str(col) for col in points.columns],
    }

    lower_columns = {str(col).lower(): col for col in points.columns}
    gene_col = next((lower_columns[name] for name in ("gene", "target", "feature", "gene_name") if name in lower_columns), None)
    cell_col = next((lower_columns[name] for name in ("cell", "cell_id", "cellid", "segmentation_label") if name in lower_columns), None)

    summary["gene_column"] = str(gene_col) if gene_col is not None else None
    summary["cell_column"] = str(cell_col) if cell_col is not None else None

    filtered = points
    if gene_col is not None and exclude_gene_prefixes:
        gene_values = filtered[gene_col].astype(str)
        target_mask = ~gene_values.str.lower().apply(
            lambda name: any(name.startswith(prefix.lower()) for prefix in exclude_gene_prefixes)
        )
        filtered = filtered.loc[target_mask]
        summary["rows_excluding_gene_prefixes"] = int(len(filtered))

    if cell_col is not None:
        per_cell = filtered.groupby(cell_col, observed=True).size()
        summary["cells_with_points"] = int(per_cell.shape[0])
        summary["median_points_per_cell"] = float(per_cell.median()) if not per_cell.empty else 0

        if exclude_cells:
            exclude_set = {str(cell) for cell in exclude_cells}
            cell_values = filtered[cell_col].astype(str)
            after_cell_filter = filtered.loc[~cell_values.isin(exclude_set)]
            per_cell_after = after_cell_filter.groupby(cell_col, observed=True).size()
            summary["excluded_cells"] = sorted(exclude_set)
            summary["rows_after_excluding_cells"] = int(len(after_cell_filter))
            summary["cells_after_excluding_cells"] = int(per_cell_after.shape[0])
            summary["median_points_after_excluding_cells"] = (
                float(per_cell_after.median()) if not per_cell_after.empty else 0
            )

    return summary


def is_geometry_present(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    if not text or text.lower() in {"none", "nan", "<na>"}:
        return False
    return True


def decode_hdf5_value(value: Any) -> Any:
    try:
        import numpy as np
    except Exception:
        np = None

    if isinstance(value, bytes):
        return value.decode("utf-8")
    if np is not None and isinstance(value, np.generic):
        return decode_hdf5_value(value.item())
    return value


def decode_hdf5_array(values: Any) -> list[Any]:
    return [decode_hdf5_value(value) for value in values]


def read_hdf5_dataframe_column(group: Any, column: str) -> Any:
    if "__categories" in group and column in group["__categories"]:
        codes = group[column][()]
        categories = decode_hdf5_array(group["__categories"][column][()])
        return [None if int(code) < 0 else categories[int(code)] for code in codes]

    node = group[column]
    if hasattr(node, "keys") and "codes" in node and "categories" in node:
        codes = node["codes"][()]
        categories = decode_hdf5_array(node["categories"][()])
        return [None if int(code) < 0 else categories[int(code)] for code in codes]
    values = node[()]
    try:
        import numpy as np

        if np.asarray(values).dtype.kind in {"S", "O", "U"}:
            return decode_hdf5_array(values)
    except Exception:
        pass
    return values


def hdf5_dataframe_columns(group: Any) -> list[str]:
    raw_columns = group.attrs.get("column-order")
    if raw_columns is not None:
        return [str(decode_hdf5_value(value)) for value in raw_columns]
    return [key for key in group.keys() if not str(key).startswith("_") and key != "__categories"]


def value_counts(values: Any, limit: int = 20) -> dict[str, int]:
    counter = Counter()
    for value in values:
        if value is None:
            continue
        counter[str(decode_hdf5_value(value))] += 1
    return dict(counter.most_common(limit))


def numeric_summary(values: Any) -> dict[str, Any]:
    import numpy as np

    array = np.asarray(values)
    if array.size == 0:
        return {"sum": 0, "median": 0}
    return {
        "sum": float(array.sum()),
        "median": float(np.median(array)),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def summarize_hdf5_dataset(node: Any) -> dict[str, Any]:
    return {
        "shape": [int(value) for value in getattr(node, "shape", [])],
        "dtype": str(getattr(node, "dtype", "")),
    }


def list_hdf5_paths(group: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    for key, node in group.items():
        path = f"{prefix}/{key}" if prefix else str(key)
        paths.append(path)
        if hasattr(node, "items"):
            paths.extend(list_hdf5_paths(node, path))
    return paths


def count_nonzero_labels(dataset: Any, chunk_rows: int) -> dict[str, Any]:
    import numpy as np

    labels: set[int] = set()
    rows = int(dataset.shape[0])
    for start in range(0, rows, chunk_rows):
        block = dataset[start : min(start + chunk_rows, rows), :]
        labels.update(int(value) for value in np.unique(block) if int(value) != 0)
    return {
        "unique_nonzero_labels": len(labels),
        "min_label": min(labels) if labels else None,
        "max_label": max(labels) if labels else None,
    }


def summarize_sample_stats(obs_columns: dict[str, Any]) -> dict[str, Any]:
    import numpy as np

    sample_values = obs_columns.get("sample")
    if sample_values is None:
        return {}

    sample_indices: dict[str, list[int]] = defaultdict(list)
    for index, value in enumerate(sample_values):
        sample_indices[str(value)].append(index)

    result: dict[str, Any] = {}
    set_columns = ["batch", "time", "group", "replicate", "top_level", "cell_type", "region_merged"]
    numeric_columns = ["n_counts", "total_counts", "n_genes", "n_genes_by_counts", "area"]
    seg_labels = obs_columns.get("seg_label")

    for sample, indices in sorted(sample_indices.items()):
        stats: dict[str, Any] = {"obs_cells": len(indices)}
        for column in set_columns:
            values = obs_columns.get(column)
            if values is not None:
                stats[f"{column}_values"] = sorted({str(values[index]) for index in indices})
        for column in numeric_columns:
            values = obs_columns.get(column)
            if values is not None:
                stats[column] = numeric_summary(np.asarray(values)[indices])
        if seg_labels is not None:
            stats["seg_label_unique_count"] = int(len(set(np.asarray(seg_labels)[indices].tolist())))
        result[sample] = stats
    return result


def inspect_h5ad_hdf5(
    path: Path,
    count_label_images: bool,
    label_chunk_rows: int,
) -> dict[str, Any]:
    import h5py

    with h5py.File(path, "r") as handle:
        result: dict[str, Any] = {
            "path": str(path),
            "file_size_bytes": path.stat().st_size,
            "top_level_keys": sorted(handle.keys()),
            "all_paths_with_boundary_terms": [
                item
                for item in list_hdf5_paths(handle)
                if any(token in item.lower() for token in ("boundary", "shape", "nucleus", "nuclei", "label_img"))
            ],
        }

        if "X" in handle:
            result["X"] = summarize_hdf5_dataset(handle["X"])
        if "layers" in handle:
            result["layers"] = {
                key: summarize_hdf5_dataset(node)
                for key, node in handle["layers"].items()
                if hasattr(node, "shape")
            }
        if "raw" in handle and "X" in handle["raw"]:
            result["raw_X"] = summarize_hdf5_dataset(handle["raw"]["X"])

        obs_columns: dict[str, Any] = {}
        if "obs" in handle:
            obs_group = handle["obs"]
            selected_obs_columns = [
                column
                for column in hdf5_dataframe_columns(obs_group)
                if column
                in {
                    "area",
                    "batch",
                    "cell_type",
                    "group",
                    "n_counts",
                    "n_genes",
                    "n_genes_by_counts",
                    "region_merged",
                    "replicate",
                    "sample",
                    "seg_label",
                    "time",
                    "top_level",
                    "total_counts",
                }
            ]
            obs_columns = {column: read_hdf5_dataframe_column(obs_group, column) for column in selected_obs_columns}
            result["obs"] = {
                "columns": hdf5_dataframe_columns(obs_group),
                "selected_counts": {
                    column: value_counts(values)
                    for column, values in obs_columns.items()
                    if column
                    in {
                        "batch",
                        "cell_type",
                        "group",
                        "region_merged",
                        "replicate",
                        "sample",
                        "time",
                        "top_level",
                    }
                },
                "selected_unique_counts": {
                    column: int(len({str(value) for value in values if value is not None}))
                    for column, values in obs_columns.items()
                    if column
                    in {
                        "batch",
                        "cell_type",
                        "group",
                        "region_merged",
                        "replicate",
                        "sample",
                        "time",
                        "top_level",
                    }
                },
                "selected_numeric_summaries": {
                    column: numeric_summary(values)
                    for column, values in obs_columns.items()
                    if column in {"area", "n_counts", "n_genes", "n_genes_by_counts", "total_counts"}
                },
            }
            result["sample_stats"] = summarize_sample_stats(obs_columns)

        if "var" in handle:
            var_group = handle["var"]
            if "_index" in var_group:
                var_count = int(var_group["_index"].shape[0])
            else:
                var_count = None
            result["var"] = {
                "columns": hdf5_dataframe_columns(var_group),
                "var_count": var_count,
            }

        morph_groups: dict[str, Any] = {}
        if "uns" in handle:
            result["uns_keys"] = sorted(handle["uns"].keys())
            for key, node in handle["uns"].items():
                if not hasattr(node, "keys") or "label_img" not in node:
                    continue
                label_img = node["label_img"]
                sample_name = key[:-6] if key.endswith("_morph") else key
                morph_summary = {
                    "sample": sample_name,
                    "label_img": summarize_hdf5_dataset(label_img),
                    "non_label_img_members": sorted(name for name in node.keys() if name != "label_img"),
                }
                if count_label_images:
                    morph_summary.update(count_nonzero_labels(label_img, label_chunk_rows))
                morph_groups[key] = morph_summary
        result["morph_label_images"] = morph_groups
        result["has_cell_boundary_evidence"] = any(
            item.get("label_img", {}).get("shape") for item in morph_groups.values()
        )
        result["has_nucleus_boundary_evidence"] = any(
            "nucleus" in item.lower() or "nuclei" in item.lower()
            for item in result["all_paths_with_boundary_terms"]
        )
        return result


def inspect_h5ad(path: Path, exclude_gene_prefixes: list[str], exclude_cells: list[str]) -> dict[str, Any]:
    import anndata as ad

    adata = ad.read_h5ad(path)
    obs_columns = [str(col) for col in adata.obs.columns]
    var_columns = [str(col) for col in adata.var.columns]
    obs_lower = {col.lower(): col for col in obs_columns}

    batch_columns = [
        col
        for col in obs_columns
        if any(token in col.lower() for token in ("batch", "sample", "fov", "slice", "field"))
    ]
    boundary_columns = [
        col
        for col in obs_columns
        if any(token in col.lower() for token in ("shape", "boundary", "polygon", "nucleus", "nuclei"))
    ]

    result: dict[str, Any] = {
        "path": str(path),
        "file_size_bytes": path.stat().st_size,
        "shape": [int(adata.n_obs), int(adata.n_vars)],
        "obs_columns": obs_columns,
        "var_columns": var_columns,
        "var_names_count": int(len(adata.var_names)),
        "first_var_names": [str(name) for name in adata.var_names[:10]],
        "uns_keys": [str(key) for key in adata.uns.keys()],
        "batch_columns": batch_columns,
        "boundary_columns": boundary_columns,
        "matrix_summary": summarize_matrix(adata, exclude_gene_prefixes),
    }

    result["batch_counts"] = {
        col: int(adata.obs[col].nunique(dropna=True))
        for col in batch_columns
    }
    result["boundary_non_null_counts"] = {
        col: int(adata.obs[col].notna().sum())
        for col in boundary_columns
    }
    result["boundary_present_counts"] = {
        col: int(adata.obs[col].map(is_geometry_present).sum())
        for col in boundary_columns
    }
    result["has_cell_boundary"] = any(
        "cell" in col.lower() and adata.obs[col].map(is_geometry_present).any()
        for col in boundary_columns
    )
    result["has_nucleus_boundary"] = any(
        any(token in col.lower() for token in ("nucleus", "nuclei"))
        and adata.obs[col].map(is_geometry_present).any()
        for col in boundary_columns
    )

    for candidate in ("batch", "sample", "fov"):
        if candidate in obs_lower:
            result[f"{candidate}_count"] = int(adata.obs[obs_lower[candidate]].nunique(dropna=True))

    points = get_points_table(adata)
    if points is not None:
        result["points_summary"] = summarize_points(points, exclude_gene_prefixes, exclude_cells)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect an h5ad file for STRAND metadata curation.")
    parser.add_argument("h5ad", type=Path)
    parser.add_argument("--exclude-gene-prefix", action="append", default=[])
    parser.add_argument("--exclude-cell", action="append", default=[])
    parser.add_argument("--lazy-hdf5", action="store_true", help="Inspect h5ad HDF5 structure without loading AnnData into memory.")
    parser.add_argument("--count-label-images", action="store_true", help="Count non-zero labels in uns/*/label_img datasets.")
    parser.add_argument("--label-chunk-rows", type=int, default=512)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    if args.lazy_hdf5:
        result = inspect_h5ad_hdf5(args.h5ad, args.count_label_images, args.label_chunk_rows)
    else:
        result = inspect_h5ad(args.h5ad, args.exclude_gene_prefix, args.exclude_cell)
    text = json.dumps(result, indent=2, ensure_ascii=False, default=to_jsonable)
    if args.json_out:
        args.json_out.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
