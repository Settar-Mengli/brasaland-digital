from tests.fixtures.seed_suppliers import SEED_SUPPLIERS
from supplier_directory import seed_batch


def main() -> None:
    inserted, skipped = seed_batch(SEED_SUPPLIERS)
    print(f"Seeded {inserted} suppliers ({skipped} skipped).")


if __name__ == "__main__":
    main()
