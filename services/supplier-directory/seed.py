import sys

from supplier_directory.seed_data import SEED_SUPPLIERS
from supplier_directory import seed_batch


def main() -> None:
    try:
        inserted, skipped = seed_batch(SEED_SUPPLIERS)
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Seeded {inserted} suppliers ({skipped} skipped).")


if __name__ == "__main__":
    main()
