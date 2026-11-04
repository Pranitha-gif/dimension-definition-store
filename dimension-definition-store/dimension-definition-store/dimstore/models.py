"""Dimension definition models with basic validation."""
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DATA_TYPES = {"string", "integer", "decimal", "boolean", "date", "timestamp"}
SCD_TYPES = {0, 1, 2}


class ValidationError(ValueError):
    pass


@dataclass
class Attribute:
    name: str
    data_type: str = "string"
    description: str = ""
    is_key: bool = False          # part of the natural/business key
    nullable: bool = True

    def validate(self):
        if not NAME_RE.match(self.name):
            raise ValidationError(f"Invalid attribute name '{self.name}' (use snake_case)")
        if self.data_type not in DATA_TYPES:
            raise ValidationError(
                f"Attribute '{self.name}': data_type must be one of {sorted(DATA_TYPES)}")
        if self.is_key and self.nullable:
            raise ValidationError(f"Key attribute '{self.name}' cannot be nullable")


@dataclass
class Dimension:
    name: str                      # e.g. dim_customer
    description: str = ""
    grain: str = ""                # what one row represents
    source_table: str = ""         # where it is built from (e.g. silver.customers)
    owner: str = ""
    scd_type: int = 1              # slowly changing dimension type: 0, 1 or 2
    attributes: List[Attribute] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    version: Optional[int] = None  # assigned by the store

    def validate(self):
        if not NAME_RE.match(self.name):
            raise ValidationError(f"Invalid dimension name '{self.name}' (use snake_case)")
        if not self.grain:
            raise ValidationError(f"Dimension '{self.name}' needs a grain statement")
        if self.scd_type not in SCD_TYPES:
            raise ValidationError(f"scd_type must be one of {sorted(SCD_TYPES)}")
        if not self.attributes:
            raise ValidationError(f"Dimension '{self.name}' needs at least one attribute")
        names = [a.name for a in self.attributes]
        dupes = {n for n in names if names.count(n) > 1}
        if dupes:
            raise ValidationError(f"Duplicate attribute names: {sorted(dupes)}")
        for a in self.attributes:
            a.validate()
        if not any(a.is_key for a in self.attributes):
            raise ValidationError(f"Dimension '{self.name}' needs at least one key attribute")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Dimension":
        d = dict(d)
        d["attributes"] = [Attribute(**a) for a in d.get("attributes", [])]
        return cls(**d)
