"""Command line interface: python -m dimstore <command>"""
import argparse
import json
import sys

from .ddl import generate_ddl
from .models import Dimension, ValidationError
from .store import DimensionStore


def main(argv=None):
    p = argparse.ArgumentParser(prog="dimstore", description="Dimension definition store")
    p.add_argument("--db", default="dimensions.db")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="register a dimension from a JSON file")
    a.add_argument("file")
    a.add_argument("-m", "--message", default="")
    sub.add_parser("list", help="list latest version of each dimension")
    s = sub.add_parser("show", help="show a dimension (JSON)")
    s.add_argument("name")
    s.add_argument("-v", "--version", type=int)
    h = sub.add_parser("history", help="version history")
    h.add_argument("name")
    d = sub.add_parser("diff", help="compare two versions")
    d.add_argument("name")
    d.add_argument("v1", type=int)
    d.add_argument("v2", type=int)
    q = sub.add_parser("search", help="search names, grain, tags, attributes")
    q.add_argument("text")
    g = sub.add_parser("ddl", help="generate CREATE TABLE")
    g.add_argument("name")
    g.add_argument("--schema", default="gold")

    args = p.parse_args(argv)
    store = DimensionStore(args.db)
    try:
        if args.cmd == "add":
            with open(args.file) as f:
                dim = store.register(Dimension.from_dict(json.load(f)), args.message)
            print(f"Registered {dim.name} v{dim.version}")
        elif args.cmd == "list":
            for dim in store.list_latest():
                print(f"{dim.name:<20} v{dim.version}  scd{dim.scd_type}  {dim.grain}")
        elif args.cmd == "show":
            dim = store.get(args.name, args.version)
            if not dim:
                sys.exit(f"Not found: {args.name}")
            print(json.dumps(dim.to_dict(), indent=2))
        elif args.cmd == "history":
            for v, note, ts in store.history(args.name):
                print(f"v{v}  {ts}  {note}")
        elif args.cmd == "diff":
            for line in store.diff(args.name, args.v1, args.v2) or ["(no differences)"]:
                print(line)
        elif args.cmd == "search":
            for dim in store.search(args.text):
                print(f"{dim.name}  - {dim.description}")
        elif args.cmd == "ddl":
            dim = store.get(args.name)
            if not dim:
                sys.exit(f"Not found: {args.name}")
            print(generate_ddl(dim, args.schema))
    except (ValidationError, KeyError) as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
