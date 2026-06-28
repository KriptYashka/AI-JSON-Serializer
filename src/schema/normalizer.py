from pathlib import Path
from typing import Any
from openpyxl import load_workbook, Workbook

from src.schema.models import MappingRule, Schema


class Normalizer:
    def __init__(self, schema: Schema, mapping: list[MappingRule]) -> None:
        self._schema = schema
        self._map = self._build_column_map(mapping)

    @staticmethod
    def _build_column_map(mapping: list[MappingRule]) -> dict[str, str]:
        return {r.from_.strip().lower(): r.to for r in mapping}

    def normalize(self, input_path: str | Path, output_path: str | Path) -> int:
        wb_in = load_workbook(input_path, read_only=True, data_only=True)
        ws_in = wb_in.active

        rows_iter = ws_in.iter_rows(values_only=True)
        raw_headers = [str(c).strip() if c else "" for c in next(rows_iter)]
        header_map = self._match_headers(raw_headers)

        out_cols = [c.name for c in self._schema.columns]
        wb_out = Workbook()
        ws_out = wb_out.active
        ws_out.title = self._schema.name
        ws_out.append(out_cols)

        row_count = 0
        for row in rows_iter:
            mapped = self._transform_row(row, raw_headers, header_map, out_cols)
            if mapped is not None:
                ws_out.append(mapped)
                row_count += 1

        wb_out.save(output_path)
        wb_in.close()
        wb_out.close()
        return row_count

    def _match_headers(self, raw_headers: list[str]) -> dict[int, str]:
        header_map: dict[int, str] = {}
        for i, h in enumerate(raw_headers):
            target = self._map.get(h.lower())
            if target:
                header_map[i] = target
        return header_map

    def _transform_row(
        self,
        row: tuple[Any, ...],
        raw_headers: list[str],
        header_map: dict[int, str],
        out_cols: list[str],
    ) -> list[Any] | None:
        mapped: dict[str, Any] = {}
        for col_idx, target_col in header_map.items():
            if col_idx < len(row):
                mapped[target_col] = row[col_idx]

        for col in self._schema.columns:
            val = mapped.get(col.name)
            if col.required and (val is None or val == ""):
                return None

        return [mapped.get(c, None) for c in out_cols]
