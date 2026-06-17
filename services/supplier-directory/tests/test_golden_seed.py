from supplier_directory.seed_data import SEED_SUPPLIERS
from supplier_directory import get_supplier, list_suppliers, seed_batch


def test_seed_batch_inserts_fifteen() -> None:
    inserted, skipped = seed_batch(SEED_SUPPLIERS)

    assert inserted == 15
    assert skipped == 0
    assert len(list_suppliers()) == 15


def test_seed_batch_is_idempotent() -> None:
    seed_batch(SEED_SUPPLIERS)
    inserted, skipped = seed_batch(SEED_SUPPLIERS)

    assert inserted == 0
    assert skipped == 15
    assert len(list_suppliers()) == 15


def test_seed_batch_country_counts() -> None:
    seed_batch(SEED_SUPPLIERS)

    colombia = list_suppliers(country="Colombia")
    usa = list_suppliers(country="USA")

    assert len(colombia) == 9
    assert len(usa) == 6


def test_seed_batch_spot_checks() -> None:
    seed_batch(SEED_SUPPLIERS)

    carnes = next(
        supplier
        for supplier in list_suppliers()
        if supplier["name"] == "Carnes del Valle S.A.S."
    )
    assert carnes["country"] == "Colombia"
    assert carnes["currency"] == "COP"
    assert carnes["categories"] == ["meat"]
    assert carnes["status"] == "active"
    assert carnes["contact_email"] == "ventas@carnesdelvalle.co"

    miami = next(
        supplier
        for supplier in list_suppliers()
        if supplier["name"] == "Miami Meat Distributors LLC"
    )
    assert miami["country"] == "USA"
    assert miami["currency"] == "USD"
    assert miami["categories"] == ["meat"]
    assert miami["status"] == "active"

    limpiahogar = next(
        supplier
        for supplier in list_suppliers()
        if supplier["name"] == "Limpiahogar Profesional"
    )
    assert limpiahogar["country"] == "Colombia"
    assert limpiahogar["categories"] == ["cleaning_products"]
    assert limpiahogar["status"] == "suspended"
    assert limpiahogar["contact_email"] == "limpiahogar@promail.co"


def test_seed_batch_sets_rate_updated_at() -> None:
    seed_batch(SEED_SUPPLIERS)

    for supplier in list_suppliers():
        assert supplier["rate_updated_at"]
        assert isinstance(supplier["rate_updated_at"], str)


def test_list_suppliers_filter_by_country() -> None:
    seed_batch(SEED_SUPPLIERS)

    colombia = list_suppliers(country="Colombia")

    assert len(colombia) == 9
    assert all(supplier["country"] == "Colombia" for supplier in colombia)


def test_list_suppliers_filter_by_category() -> None:
    seed_batch(SEED_SUPPLIERS)

    meat = list_suppliers(category="meat")

    assert len(meat) == 3
    assert {supplier["name"] for supplier in meat} == {
        "Carnes del Valle S.A.S.",
        "Frigorifico Antioqueno",
        "Miami Meat Distributors LLC",
    }


def test_get_supplier_returns_record() -> None:
    seed_batch(SEED_SUPPLIERS)

    first = list_suppliers()[0]
    loaded = get_supplier(first["id"])

    assert loaded == first
