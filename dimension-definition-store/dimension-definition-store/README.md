# dimension-definition-store

A small, dependency-free Python registry for semantic-layer dimension definitions.

- Define dimensions (grain, owner, source table, SCD type, attributes, tags) in JSON
- Validation: snake_case names, allowed data types, key attributes, no duplicates
- Every change creates a new version; re-registering an identical definition is a no-op
- Diff any two versions, search, and generate `CREATE TABLE` DDL (adds SCD2 columns automatically)
- Storage: SQLite (`dimensions.db`). Python 3.8+, standard library only.

## Quick start
    python -m dimstore add examples/dim_customer.json -m "initial"
    python -m dimstore add examples/dim_product.json
    python -m dimstore list
    python -m dimstore add examples/dim_customer_v2.json -m "add is_active"
    python -m dimstore history dim_customer
    python -m dimstore diff dim_customer 1 2
    python -m dimstore search country
    python -m dimstore ddl dim_customer --schema gold

## Tests
    python -m unittest discover -s tests -v   # run from project root

## Use as a library
    from dimstore import DimensionStore, Dimension, Attribute
    store = DimensionStore("dimensions.db")
    store.register(Dimension(name="dim_date", grain="One row per day",
        attributes=[Attribute("date_value", "date", is_key=True, nullable=False)]))
