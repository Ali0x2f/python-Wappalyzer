import importlib
import json
import sqlite3
import uuid

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple


DETAIL_KEYS = {"categories", "versions", "confidence", "matched_on"}


def _detect_paramstyle(connection: Any) -> str:
    module_name = connection.__class__.__module__.split(".", 1)[0]
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return "qmark"
    return getattr(module, "paramstyle", "qmark")


def _format_parameters(
    columns: Sequence[str],
    values: Mapping[str, Any],
    paramstyle: str,
) -> Tuple[str, Any]:
    if paramstyle == "qmark":
        return ", ".join("?" for _ in columns), tuple(values[column] for column in columns)
    if paramstyle == "format":
        return ", ".join("%s" for _ in columns), tuple(values[column] for column in columns)
    if paramstyle == "numeric":
        return ", ".join(f":{index}" for index, _ in enumerate(columns, start=1)), tuple(values[column] for column in columns)
    if paramstyle == "named":
        return ", ".join(f":{column}" for column in columns), {column: values[column] for column in columns}
    if paramstyle == "pyformat":
        return ", ".join(f"%({column})s" for column in columns), {column: values[column] for column in columns}
    raise ValueError(f"Unsupported DB-API paramstyle: {paramstyle}")


def _execute_insert(cursor: Any, table_name: str, values: Mapping[str, Any], paramstyle: str) -> None:
    columns = tuple(values.keys())
    placeholders, parameters = _format_parameters(columns, values, paramstyle)
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    cursor.execute(sql, parameters)


def _normalize_results(results: Mapping[str, Any], url: Optional[str]) -> Mapping[str, Mapping[str, Mapping[str, Any]]]:
    if url is not None:
        return {url: results}
    if not results:
        return {}
    if all(
        isinstance(value, Mapping) and DETAIL_KEYS.intersection(value.keys())
        for value in results.values()
    ):
        raise ValueError(
            "Cannot determine if results are single-URL or multi-URL format; "
            "provide url parameter for single-URL results"
        )
    return results


def _iter_result_rows(
    results: Mapping[str, Mapping[str, Mapping[str, Any]]],
    scan_id: str,
) -> Iterable[Dict[str, Any]]:
    for target_url, technologies in results.items():
        for technology_name, details in technologies.items():
            yield {
                "scan_id": scan_id,
                "url": target_url,
                "technology_name": technology_name,
                "versions_json": json.dumps(details.get("versions", [])),
                "categories_json": json.dumps(details.get("categories", [])),
                "confidence": details.get("confidence"),
                "matched_on_json": json.dumps(details.get("matched_on", [])),
            }


def ensure_database_schema(connection: Any) -> None:
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS wappalyzer_scans (
            scan_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS wappalyzer_results (
            scan_id TEXT NOT NULL,
            url TEXT NOT NULL,
            technology_name TEXT NOT NULL,
            versions_json TEXT NOT NULL,
            categories_json TEXT NOT NULL,
            confidence INTEGER,
            matched_on_json TEXT NOT NULL,
            PRIMARY KEY (scan_id, url, technology_name)
        )
        """
    )


def store_analysis_results(
    results: Mapping[str, Any],
    connection: Any,
    url: Optional[str] = None,
    scan_id: Optional[str] = None,
    scanned_at: Optional[datetime] = None,
    paramstyle: Optional[str] = None,
) -> str:
    normalized_results = _normalize_results(results, url=url)
    resolved_scan_id = scan_id or str(uuid.uuid4())
    resolved_scanned_at = scanned_at or datetime.now(timezone.utc)
    resolved_paramstyle = paramstyle or _detect_paramstyle(connection)

    ensure_database_schema(connection)
    cursor = connection.cursor()
    _execute_insert(
        cursor,
        "wappalyzer_scans",
        {
            "scan_id": resolved_scan_id,
            "created_at": resolved_scanned_at.isoformat(),
        },
        resolved_paramstyle,
    )
    for row in _iter_result_rows(normalized_results, scan_id=resolved_scan_id):
        _execute_insert(cursor, "wappalyzer_results", row, resolved_paramstyle)
    connection.commit()
    return resolved_scan_id


def store_analysis_results_to_sqlite(
    database_path: str,
    results: Mapping[str, Any],
    url: Optional[str] = None,
    scan_id: Optional[str] = None,
    scanned_at: Optional[datetime] = None,
) -> str:
    resolved_database_path = Path(database_path).expanduser().resolve()
    resolved_database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(resolved_database_path)
    try:
        return store_analysis_results(
            results,
            connection,
            url=url,
            scan_id=scan_id,
            scanned_at=scanned_at,
            paramstyle="qmark",
        )
    finally:
        connection.close()
