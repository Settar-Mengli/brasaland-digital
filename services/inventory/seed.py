from __future__ import annotations

import sys
from typing import TypedDict

from sqlmodel import Session, SQLModel, select

import models  # noqa: F401
from database import engine
from models import Ingredient, IngredientEntry, IngredientExit

SEED_USER_UUID = "1"

IngredientSeed = TypedDict(
    "IngredientSeed",
    {"name": str, "sku": str, "unit": str, "category": str, "country": str},
)

EntrySeed = TypedDict(
    "EntrySeed",
    {
        "sku": str,
        "quantity": float,
        "unit_cost": float,
        "supplier_name": str,
        "location_id": int,
    },
)

ExitSeed = TypedDict(
    "ExitSeed",
    {"sku": str, "quantity": float, "reason": str, "location_id": int},
)

INGREDIENTS: list[IngredientSeed] = [
    {
        "name": "Beef brisket",
        "sku": "BRS-BEEF-001",
        "unit": "kg",
        "category": "meat",
        "country": "CO",
    },
    {
        "name": "Pork ribs",
        "sku": "BRS-PORK-001",
        "unit": "kg",
        "category": "meat",
        "country": "US",
    },
    {
        "name": "Chimichurri sauce",
        "sku": "BRS-SAUCE-001",
        "unit": "litre",
        "category": "sauce",
        "country": "CO",
    },
    {
        "name": "House BBQ sauce",
        "sku": "BRS-SAUCE-002",
        "unit": "litre",
        "category": "sauce",
        "country": "US",
    },
    {
        "name": "Yuca (cassava)",
        "sku": "BRS-PROD-001",
        "unit": "kg",
        "category": "produce",
        "country": "CO",
    },
    {
        "name": "Takeaway box (M)",
        "sku": "BRS-PKG-001",
        "unit": "unit",
        "category": "packaging",
        "country": "CO",
    },
]

ENTRIES: list[EntrySeed] = [
    {
        "sku": "BRS-BEEF-001",
        "quantity": 50.0,
        "unit_cost": 32000.0,
        "supplier_name": "Carnes del Valle S.A.",
        "location_id": 1,
    },
    {
        "sku": "BRS-BEEF-001",
        "quantity": 30.0,
        "unit_cost": 34500.0,
        "supplier_name": "Carnes del Valle S.A.",
        "location_id": 1,
    },
    {
        "sku": "BRS-PORK-001",
        "quantity": 40.0,
        "unit_cost": 11.5,
        "supplier_name": "MiamiMeat Co.",
        "location_id": 5,
    },
    {
        "sku": "BRS-SAUCE-001",
        "quantity": 20.0,
        "unit_cost": 12000.0,
        "supplier_name": "Salsas Artesanales Ltda.",
        "location_id": 2,
    },
]

EXITS: list[ExitSeed] = [
    {
        "sku": "BRS-BEEF-001",
        "quantity": 15.0,
        "reason": "consumption",
        "location_id": 1,
    },
    {
        "sku": "BRS-BEEF-001",
        "quantity": 5.0,
        "reason": "waste",
        "location_id": 1,
    },
    {
        "sku": "BRS-PORK-001",
        "quantity": 10.0,
        "reason": "consumption",
        "location_id": 5,
    },
]


def _get_ingredient_by_sku(session: Session, sku: str) -> Ingredient | None:
    return session.exec(select(Ingredient).where(Ingredient.sku == sku)).first()


def _entry_exists(
    session: Session,
    ingredient_id: int,
    quantity: float,
    supplier_name: str,
    location_id: int,
) -> bool:
    existing = session.exec(
        select(IngredientEntry).where(
            IngredientEntry.ingredient_id == ingredient_id,
            IngredientEntry.quantity == quantity,
            IngredientEntry.supplier_name == supplier_name,
            IngredientEntry.location_id == location_id,
        )
    ).first()
    return existing is not None


def _exit_exists(
    session: Session,
    ingredient_id: int,
    quantity: float,
    reason: str,
    location_id: int,
) -> bool:
    existing = session.exec(
        select(IngredientExit).where(
            IngredientExit.ingredient_id == ingredient_id,
            IngredientExit.quantity == quantity,
            IngredientExit.reason == reason,
            IngredientExit.location_id == location_id,
        )
    ).first()
    return existing is not None


def seed_database() -> tuple[dict[str, int], dict[str, int]]:
    inserted = {"ingredients": 0, "entries": 0, "exits": 0}
    skipped = {"ingredients": 0, "entries": 0, "exits": 0}

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        sku_to_id: dict[str, int] = {}

        for ingredient_data in INGREDIENTS:
            existing = _get_ingredient_by_sku(session, ingredient_data["sku"])
            if existing is not None and existing.id is not None:
                skipped["ingredients"] += 1
                sku_to_id[ingredient_data["sku"]] = existing.id
                continue
            ingredient = Ingredient.model_validate(ingredient_data)
            session.add(ingredient)
            session.commit()
            session.refresh(ingredient)
            if ingredient.id is None:
                raise RuntimeError(f"Failed to insert ingredient {ingredient_data['sku']}")
            inserted["ingredients"] += 1
            sku_to_id[ingredient_data["sku"]] = ingredient.id

        for entry_data in ENTRIES:
            ingredient_id = sku_to_id[entry_data["sku"]]
            if _entry_exists(
                session,
                ingredient_id,
                entry_data["quantity"],
                entry_data["supplier_name"],
                entry_data["location_id"],
            ):
                skipped["entries"] += 1
                continue
            session.add(
                IngredientEntry(
                    ingredient_id=ingredient_id,
                    quantity=entry_data["quantity"],
                    unit_cost=entry_data["unit_cost"],
                    supplier_name=entry_data["supplier_name"],
                    location_id=entry_data["location_id"],
                    user_uuid=SEED_USER_UUID,
                )
            )
            inserted["entries"] += 1

        for exit_data in EXITS:
            ingredient_id = sku_to_id[exit_data["sku"]]
            if _exit_exists(
                session,
                ingredient_id,
                exit_data["quantity"],
                exit_data["reason"],
                exit_data["location_id"],
            ):
                skipped["exits"] += 1
                continue
            session.add(
                IngredientExit(
                    ingredient_id=ingredient_id,
                    quantity=exit_data["quantity"],
                    reason=exit_data["reason"],
                    location_id=exit_data["location_id"],
                    user_uuid=SEED_USER_UUID,
                )
            )
            inserted["exits"] += 1

        session.commit()

    return inserted, skipped


def main() -> None:
    try:
        inserted, skipped = seed_database()
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error

    print(
        "Seed complete — "
        f"ingredients: {inserted['ingredients']} inserted, {skipped['ingredients']} skipped; "
        f"entries: {inserted['entries']} inserted, {skipped['entries']} skipped; "
        f"exits: {inserted['exits']} inserted, {skipped['exits']} skipped."
    )


if __name__ == "__main__":
    main()
