# Data audit — the seed migration

The initial dataset was intentionally dirty. This is a record of every problem in
it and what the migration (`backend/app/seed.py`) does about each one. The guiding
principle: **normalise what's safe to normalise, flag what isn't, and never drop a
record.**

You can see the migration talk through its work — it prints a `[seed-audit]` line
for every correction on first boot.

## Issues found and how they're handled

| # | Record (seed id) | Problem | Resolution |
|---|---|---|---|
| 1 | `id: 4` × 2 (Samsung / Lenovo) | **Duplicate primary id.** Two different devices share `id: 4`. | Both kept. Records use an auto-increment PK; the seed id is stored in `original_seed_id`; the collision is logged and flagged. See "The Correction" in the README. |
| 2 | Logitech MX Master 3 | `purchaseDate: "2027-10-10"` is **in the future** — impossible for a purchase. | Kept, but `data_flag` set to "purchase date in the future". Surfaced by the auditor. Not auto-changed — could be a real typo the admin should verify. |
| 3 | iPad Pro 12.9 | `brand: "Appel"` — **typo**. | Normalised to `Apple` (known-typo map). Logged. |
| 4 | iPad Pro 12.9 | `purchaseDate: "22-05-2023"` — **non-ISO, day-first** format. | Parsed and stored as ISO `2023-05-22`. Logged. |
| 5 | Unknown Device | `status: "Unknown"` — **not a valid status**. | Defaulted to `Available` and flagged. Kept out of an invalid state while preserving the record. |
| 6 | Unknown Device | `brand: ""`, `purchaseDate: null` — **missing fields**. | Kept; flagged as "empty brand" / "missing purchase date". |
| 7 | Dell XPS 15 | `notes: "Battery swelling, do not issue without service."` | Note preserved. The auditor flags it **high severity**: Available but physically unsafe to issue. |
| 8 | MacBook Air M2 | `history: "Returned by user with liquid damage..."` | `history` folded into the `notes` field; auditor flags it high severity. |
| 9 | Sony WH-1000XM4 | `assignedTo: "j.doe@booksy.com"` while `status: "In Use"`. | Consistent — kept as-is; `assigned_to` populated. |

## Design decisions

- **Flag, don't silently fix.** For anything ambiguous (future date, unknown status,
  missing data) the migration records the original problem in `data_flag` so a human
  can review it, rather than pretending the data was clean.
- **`notes` and `history` are the same signal.** The seed used two different keys for
  "free text about this device's condition". I fold both into one `notes` column so
  the auditor has a single field to reason over.
- **The seed id is provenance, not identity.** Because it isn't unique, it can't be a
  key. `original_seed_id` keeps the trail back to the source row without letting a
  collision cause data loss.
