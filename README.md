# Hardware Hub

An internal tool for managing, renting and maintaining company equipment. Admins
add gear and create accounts, employees rent and return it, and an AI layer keeps
an eye on the inventory — flagging devices that shouldn't be handed out and letting
people search for gear in plain English.

Built with **FastAPI + SQLite** on the backend and **Vue 3 (Vite)** on the frontend.

---

## Live demo

Deployed on Fly.io as a single service (FastAPI serves the built Vue SPA):

> **https://hardware-hub-booksy-demo.fly.dev**
>
> Admin login: **admin@booksy.com** — the password is in my submission email
> (I keep live credentials out of the public repo on purpose).

Running in `ENVIRONMENT=production`, so the fail-closed guard (see
[Security](#security)) is active — the app would refuse to boot on the default
signing key or admin password, so both are set to real secrets on the host. The
machine sleeps when idle, so the first request after a while has a short cold
start. The demo runs on SQLite with a fresh seed, so data resets on redeploy.

---

## Running it locally

You need Python 3.11+ and Node 18+.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Optional: turn on the live LLM. Without a key the AI layer still works
# in a deterministic fallback mode, so you can skip this for a quick look.
cp .env.example .env        # then paste an ANTHROPIC_API_KEY if you have one

uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

The database (`hardware_hub.db`) is created and seeded automatically on first
start. A default admin is seeded so there's a way in:

> **admin@booksy.com / admin123**

### Frontend

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

The dev server proxies `/api` to the backend on port 8000, so just open
`localhost:5173` and log in.

### Tests

```bash
cd backend
source .venv/bin/activate
pytest
```

---

## Implementation status & trade-offs

I spent the time budget on getting the core rock-solid rather than spreading it
thin, so the rental logic, the data migration and the tests are the parts I'm
most confident in.

### ✅ Fully implemented

- **Auth** — JWT login, bcrypt-hashed passwords, admin-only account creation
  (no public sign-up, as the brief requires). Route guards on the frontend.
  Hardened against forged tokens, user enumeration and brute-force — see
  [Security](#security) below.
- **Admin command center** — add / delete hardware, toggle repair status, create
  user accounts, see each device's data-migration flags.
- **Dashboard** — hardware list with Name / Brand / Purchase date / Status, plus
  server-side sorting and filtering (by status, brand, and name search).
- **Rental engine** — rent / return with guards that block the impossible states:
  can't rent something that isn't Available, can't return something that isn't out,
  can't return gear assigned to someone else (admins can force-return).
- **AI layer (both features)** — Inventory Auditor and Semantic Search, each backed
  by Claude with a deterministic fallback so the app is always demoable.
- **Data audit migration** — the dirty seed is cleaned and every correction is
  logged. See [`docs/DATA_AUDIT.md`](docs/DATA_AUDIT.md).
- **Tests** — 17 tests covering the critical rules, incl. auth hardening (see below).

### ⚡ Shortcuts & hacks

- **JWT in `localStorage`.** Simple and it works, but it's readable by any injected
  script (XSS). *Why it's OK for the MVP:* this is an internal tool behind SSO in
  reality, and there's no XSS surface here. *Production:* move to an httpOnly,
  SameSite cookie with a short-lived access token + refresh rotation.
- **Seeded default admin with a known password.** Fine for review/demo; in
  production the first admin would be provisioned out-of-band and forced to reset.
- **`create_all()` instead of migrations.** No Alembic — the schema is created from
  the models on boot. Fine while the schema is young; a real app needs versioned
  migrations before the first schema change hits production data.
- **Seed-on-startup.** The seed runs in the app lifespan. Convenient for a
  file-based DB you can throw away; production seeding belongs in a separate,
  idempotent command.
- **Best-effort JSON parsing from the LLM.** I strip code fences and grab the outer
  JSON object. A hardening step would be to use tool-use / structured outputs so the
  model can't return unparseable text at all.

### ⚠️ Partial / missing

- **Rental history UI.** The `rentals` table records every rent/return with
  timestamps, but I didn't build a screen to browse a device's history yet.
- **Semantic-search fallback is crude.** Without an API key it's keyword/intent
  matching, so it over-matches (e.g. the word "test" in a query hits "Test Laptop").
  With a key, Claude handles it well. I left the fallback honest rather than faking
  intelligence.
- **No pagination.** Fine for ~12 rows; would matter at scale.
- **No password reset / user deletion / edit.**

### 🔮 Next steps (the 24h roadmap)

1. **Structured LLM outputs** — swap the best-effort JSON parsing for Anthropic
   tool-use so the audit/search responses are schema-validated, and let the auditor
   *propose* a status change the admin can accept in one click.
2. **Rental history view** — surface the data I'm already storing: per-device
   timeline and "who has what right now" for admins.
3. **Finish hardening auth** — the ASVS login hardening is done (see
   [Security](#security)); still on the list are the httpOnly-cookie token flow,
   forced admin password reset, and a proper migration tool (Alembic) before
   locking the schema.

---

## Security

Most of my security effort went into the login endpoint, since that's the place
where a small mistake becomes a full compromise. Rather than list these as
"production TODOs" I fixed them. All three line up with the OWASP ASVS login
requirements, and each has a test in
[`tests/test_security.py`](backend/tests/test_security.py).

- **No forged tokens (ASVS V6).** JWTs are signed with `SECRET_KEY`. If that key
  is left at the shipped default, anyone can sign their own admin token, so the
  app now refuses to start in production until it's changed (same check for the
  default admin password). Locally the placeholder still works, so a quick run
  isn't blocked. See `config.py`.
- **No user enumeration (ASVS V2.2).** Login answers with the same "Incorrect
  email or password" whether the account exists or not, and it runs the bcrypt
  check even when the email is unknown. Without that, an unknown email would come
  back faster and you could tell real accounts apart by response time.
- **Brute-force throttling (ASVS V2.2.1).** After 5 failed attempts for the same
  IP + email, login returns 429 with a `Retry-After` and stays locked for 15
  minutes. A correct login clears the counter. See `ratelimit.py`.

Passwords are bcrypt-hashed and never stored or logged in plaintext. I also cap
the input at bcrypt's 72-byte limit explicitly, so an over-long password fails
loudly instead of being quietly truncated.

Two known trade-offs I left in on purpose: the rate limiter keeps its state in
memory, so it only covers one process (a real deploy would move that to Redis so
the limit is shared), and the JWT lives in `localStorage`, which an injected
script can read. The trade-offs section above explains why that's fine for this
MVP and what the production version looks like.

---

## A note on the wireframes

I used the provided wireframes as a feel/reference and remodelled the layout. The
main deliberate change: I merged "search" and "browse" into one dashboard with an
AI search bar on top of the filterable table, instead of separate screens — for an
inventory this small, one screen with good filtering beats navigating between views.
Admin actions live in their own "command center" so the day-to-day rental view stays
clean for regular employees.

---

## AI development log

### Tooling

- **Claude Code (Opus)** was my main pair-programmer for this — scaffolding, the
  data migration, the Vue components and the tests. I drove the architecture and
  the decisions; it did the typing and caught boilerplate.
- **Claude (Sonnet)** is the model the app itself calls at runtime for the AI layer.

### Data strategy — auditing the seed

The seed is deliberately nasty, and treating it as clean would have quietly
corrupted the inventory. Rather than hand-fix it, I wrote the migration to **clean
and log every correction**, and to **flag** (not silently mutate) anything it can't
safely decide. Full breakdown in [`docs/DATA_AUDIT.md`](docs/DATA_AUDIT.md); the
headline issues:

- Two records share `id: 4` → both kept (see The Correction below).
- `"Appel"` → normalised to `Apple`.
- `"22-05-2023"` → parsed and stored as ISO `2023-05-22`.
- `2027-10-10` purchase date (future) → kept but flagged for review.
- `status: "Unknown"`, empty brand, `null` date → flagged as incomplete.
- `notes` / `history` mentioning battery swelling & liquid damage → fed to the
  auditor, which flags them as "Available but physically damaged".

### Prompt trail

The prompts that shaped the architecture and the key decisions are in
[`docs/PROMPTS.md`](docs/PROMPTS.md).

### The correction

The most useful catch was noticing that the first version of the data migration was
quietly doing the wrong thing.

It de-duplicated the seed by keying records on their `id` (`by_id[rec["id"]] = rec`).
That seems fine until you notice the seed has two records with `id: 4`. The second
one (`Duplicate ID Test Laptop`) overwrote the first (`SAMSUNG Galaxy S21`), so a
real device just disappeared from the inventory: 11 records went in, 10 came out.
Nothing threw an error, so a quick look would never have caught it.

What gave it away was the row count after seeding. 11 in, 10 out, so I went digging
for why. The fix was to stop treating the seed's `id` as a primary key. Every record
now gets its own auto-increment id, the original one is kept in `original_seed_id`
for traceability, and the collision gets logged instead of quietly resolved. I added
a test (`test_seed_preserves_duplicate_id_records`) so it can't come back. See commit
`fix(seed): preserve duplicate-id records instead of dropping them`.

That's the whole reason the migration logs everything it touches. The AI mistakes
that actually bite aren't the ones that crash, they're the plausible ones that slip
by without a sound.

---

## Testing

Seventeen tests, run with `pytest`. The critical ones:

| Test | Rule it guards |
|---|---|
| `test_cannot_rent_hardware_in_repair` | Can't rent broken gear |
| `test_cannot_rent_already_in_use` | Can't double-rent |
| `test_cannot_return_item_that_is_not_in_use` | Can't return what isn't out |
| `test_seed_preserves_duplicate_id_records` | Migration never drops a record |
| `test_non_admin_cannot_create_user` | Account creation is admin-only |
| `test_forged_token_with_wrong_key_is_rejected` | No forged JWTs (auth bypass) |
| `test_unknown_user_and_wrong_password_are_indistinguishable` | No user enumeration |
| `test_repeated_failures_get_locked_out` | Brute-force is throttled |

Plus brand-typo normalisation, future-date flagging, the rent/return happy path,
and the fail-closed config guard against shipping default secrets.
