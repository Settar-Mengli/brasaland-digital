# Public knowledge base (guest FAQ)

Mock customer-facing facts for the Brasaland portfolio demo. English only.

## Scope

This directory is the **single source of truth** for guest FAQ topics: locations, hours, menu, loyalty, allergens, reservations, ordering, and contact.

Do **not** index `docs/company-knowledge-base/` for public guests — that corpus includes internal operations content (waste protocols, supplier ordering).

## Content owner

Portfolio mock data invented for demonstration. All addresses, phones, hours, and prices are fictional but must stay **internally consistent** with:

- Canonical location slugs in `services/auth/auth/locations.py`
- Country/currency mapping in `data/pipelines/locations.py`
- Loyalty earn facts in `docs/company-knowledge-base/loyalty-program.md` and `apps/operations-toolkit/src/constants/brasa-points.ts`

## Manifest allowlist

`manifest.json` lists every file the future public RAG indexer (branch 2) may load. Only paths under this directory are permitted. Never add internal paths to the manifest.

## Reindexing (branch 2)

After editing content, reindex the public Qdrant collection with:

```powershell
uv run --directory data --python 3.13 python ../scripts/index_knowledge_base.py --corpus docs/public-knowledge-base
```

(Exact flags ship in branch 2; procedure documented here for forward compatibility.)

## Prohibited fields

Public JSON must **not** include operational fields from internal toolkit types, such as:

- `manager`, `staffCount`, `monthlyRentCost`, `seatingCapacity`
- `ingredientCost`, `prepTimeMinutes`

See `apps/operations-toolkit/src/types/location.ts` and `menu-item.ts` for internal shapes — do not mirror them here.

## File inventory

| File | Format | Topic |
| --- | --- | --- |
| `locations.json` | JSON | 14 canonical locations |
| `menu.json` | JSON | Guest menu with prices |
| `loyalty.md` | Markdown | Brasa Points program |
| `allergens.md` | Markdown | Guest allergen guide |
| `reservations.md` | Markdown | Reservation policy |
| `ordering.md` | Markdown | Order and delivery policy |
| `contact.md` | Markdown | Contact channels |
| `hours-holidays.md` | Markdown | Hours and holidays |
