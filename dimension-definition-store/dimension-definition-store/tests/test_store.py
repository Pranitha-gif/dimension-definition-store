import unittest

from dimstore import Attribute, Dimension, DimensionStore, ValidationError, generate_ddl


def make(**kw):
    base = dict(
        name="dim_customer", grain="One row per customer", source_table="silver.customers",
        attributes=[Attribute("customer_id", "string", "key", is_key=True, nullable=False),
                    Attribute("country", "string")])
    base.update(kw)
    return Dimension(**base)


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.store = DimensionStore(":memory:")

    def test_register_and_get(self):
        d = self.store.register(make())
        self.assertEqual(d.version, 1)
        self.assertEqual(self.store.get("dim_customer").grain, "One row per customer")

    def test_identical_registration_is_noop(self):
        self.store.register(make())
        again = self.store.register(make())
        self.assertEqual(again.version, 1)
        self.assertEqual(len(self.store.history("dim_customer")), 1)

    def test_change_creates_new_version_and_diff(self):
        self.store.register(make())
        attrs = make().attributes + [Attribute("segment", "string")]
        self.store.register(make(attributes=attrs), "add segment")
        self.assertEqual(self.store.get("dim_customer").version, 2)
        self.assertIn("+ attribute segment (string)", self.store.diff("dim_customer", 1, 2))
        self.assertEqual(self.store.get("dim_customer", 1).version, 1)

    def test_validation_errors(self):
        for bad in (make(name="DimCustomer"), make(grain=""), make(scd_type=5),
                    make(attributes=[Attribute("a", "string")]),
                    make(attributes=[Attribute("a", "string", is_key=True, nullable=False),
                                     Attribute("a", "string")]),
                    make(attributes=[Attribute("a", "uuid", is_key=True, nullable=False)])):
            with self.assertRaises(ValidationError):
                self.store.register(bad)

    def test_search(self):
        self.store.register(make())
        self.assertEqual([d.name for d in self.store.search("country")], ["dim_customer"])
        self.assertEqual(self.store.search("nothing-here"), [])

    def test_ddl_scd2_columns(self):
        d = self.store.register(make(scd_type=2))
        ddl = generate_ddl(d)
        self.assertIn("CREATE TABLE gold.dim_customer", ddl)
        self.assertIn("is_current BOOLEAN NOT NULL", ddl)


if __name__ == "__main__":
    unittest.main()
