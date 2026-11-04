"""Generate a CREATE TABLE statement from a dimension definition."""
from .models import Dimension

SQL_TYPES = {
    "string": "VARCHAR(255)", "integer": "INTEGER", "decimal": "DECIMAL(18,2)",
    "boolean": "BOOLEAN", "date": "DATE", "timestamp": "TIMESTAMP",
}


def generate_ddl(dim: Dimension, schema: str = "gold") -> str:
    # (column definition, optional comment) pairs; commas are added before comments
    cols = [(f"{dim.name}_key INTEGER NOT NULL", "surrogate key")]
    for a in dim.attributes:
        null = "NOT NULL" if not a.nullable else "NULL"
        cols.append((f"{a.name} {SQL_TYPES[a.data_type]} {null}", a.description))
    if dim.scd_type == 2:
        cols += [("valid_from TIMESTAMP NOT NULL", ""), ("valid_to TIMESTAMP NULL", ""),
                 ("is_current BOOLEAN NOT NULL", "")]
    cols.append((f"PRIMARY KEY ({dim.name}_key)", ""))

    lines = []
    for i, (definition, comment) in enumerate(cols):
        comma = "," if i < len(cols) - 1 else ""
        suffix = f"  -- {comment}" if comment else ""
        lines.append(f"    {definition}{comma}{suffix}")

    keys = ", ".join(a.name for a in dim.attributes if a.is_key)
    header = (f"-- {dim.name} v{dim.version}: {dim.description}\n"
              f"-- Grain: {dim.grain}\n-- Business key: {keys}\n"
              f"-- Source: {dim.source_table}\n")
    return f"{header}CREATE TABLE {schema}.{dim.name} (\n" + "\n".join(lines) + "\n);"
