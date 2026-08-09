# CLAUDE.md

Guidance for Claude Code (and any other agent) working in this repository.

## Project

Scruffy is a media-retention janitor for Seerr (formerly Overseerr): it deletes media X days after
it becomes available, reminds users by email first, and lets them request an
extension. Python 3.13 backend (`scruffy/`), a separate React/TypeScript admin
frontend (`frontend/`), managed with `uv`.

## Commands

```bash
uv run scruffy validate            # validate config
uv run scruffy check                # dry-run: what would be deleted
uv run scruffy process              # run the janitor
uv run pytest                       # full test suite
uv run pytest --cov=scruffy         # with coverage (mirrors CI)
bash scripts/lint.sh                # ruff check, ruff format --check, ty check
uv run mypy scruffy                 # type check (mypy is also in dev deps)
```

CI (`.github/workflows/lint.yml`, `tests.yml`) runs `scripts/lint.sh` and
`pytest --cov=scruffy` on every push/PR to `main`. Run both before opening a PR.

`frontend/` has its own equivalent commands (run from `frontend/`):

```bash
npm run dev                         # start the Vite dev server
npm run build                       # tsc -b && vite build
npm run lint                        # eslint
npm run format                      # prettier --write
npm run format:check                # prettier --check
npm run typecheck                   # tsc -b --noEmit
bash scripts/lint.sh                # eslint, prettier --check, tsc --noEmit (mirrors the backend's lint.sh)
```

CI's `frontend-lint` job (also in `.github/workflows/lint.yml`) runs
`frontend/scripts/lint.sh` on every push/PR to `main`.

---

## Architecture: Clean Architecture

This codebase is organized as Robert C. Martin's **Clean Architecture** (also
known as Ports and Adapters / Hexagonal / Onion — same shape, same intent).
The package layout *is* the architecture:

```
scruffy/
  domain/                 # Entities layer
    entities/              # Media, MediaRequest, Reminder
    services/              # RetentionCalculator
    value_objects/         # MediaStatus, MediaType, RetentionPolicy, ...
  use_cases/               # Use Cases layer
    *_use_case.py           # ProcessMediaUseCase, DeleteMediaUseCase, ...
    interfaces/             # Ports the use cases depend on (ABCs)
    dtos/                   # Data crossing the use-case boundary
  interface_adapters/      # Interface Adapters layer
    gateways/                # RadarrGateway, SonarrGateway, SeerrGateway, ...
    interfaces/              # IHttpClient, ISettingsProvider (ports adapters need)
    notifications/           # EmailNotificationService
    presenters/               # CliPresenter
  frameworks_and_drivers/  # Frameworks & Drivers layer
    api/                      # FastAPI app, routes, scheduler
    cli/                      # Typer CLI
    database/                 # SQLModel engine, models, stores
    di/                       # container.py — the "Main" component
    email/, http/, config/, utils/
```

### The Dependency Rule

> Source code dependencies must point only **inward**. Nothing in an inner
> circle may know anything about an outer circle — not a class name, a
> function, a variable, or a data format.

Inward, here, means: `frameworks_and_drivers` → `interface_adapters` →
`use_cases` → `domain`. Concretely:

- `domain/` imports nothing else in this project. It has zero knowledge of
  FastAPI, SQLModel, HTTP, or any external service.
- `use_cases/` may import `domain/`, but talks to the outside world only
  through the ABCs in `use_cases/interfaces/` (e.g. `MediaRepositoryInterface`,
  `NotificationServiceInterface`). It never imports `interface_adapters/` or
  `frameworks_and_drivers/`.
- `interface_adapters/gateways/` implement those `use_cases/interfaces/` ABCs
  and translate to/from external systems (Radarr, Sonarr, Seerr, email).
  They depend inward on `use_cases/` and `domain/`, never on
  `frameworks_and_drivers/`.
- `frameworks_and_drivers/` is the only layer allowed to know about everything.
  `di/container.py` is the **Main component** (Ch. 26 of the book): the one
  place concrete classes are constructed and wired to the abstractions the
  inner layers depend on. Routes and CLI commands pull already-wired use cases
  out of the `Container`; they don't construct gateways themselves.

If you catch yourself importing `frameworks_and_drivers` (or a
`sqlmodel`/`fastapi`/`httpx` symbol) from `domain/` or `use_cases/`, that's a
Dependency Rule violation — invert it with a new/existing interface instead.

### Where does new code go?

- Pure business rule/data that would be true even without a computer
  (retention math, what "available" means) → `domain/`.
- A new application workflow that orchestrates entities and ports
  (a new "use case") → `use_cases/`, plus a DTO if data needs to cross the
  boundary and an interface if it needs something external.
- A new integration with an external system (a new media manager, a new
  notification channel) → implement the relevant `use_cases/interfaces/` ABC
  as a gateway in `interface_adapters/gateways/`.
- A new delivery mechanism (route, CLI command, scheduled job, DB model) →
  `frameworks_and_drivers/`, wired up via `di/container.py`.
- `frontend/` is a separate detail entirely — a UI talking to the API over
  HTTP. Per Ch. 31 ("The Web Is a Detail"), it should never dictate shapes in
  `domain/` or `use_cases/`.

### Naming/testing conventions already in place

- Ports are ABCs (`abc.ABC` + `@abstractmethod`) named either `IXxx`
  (`IHttpClient`, `ISettingsProvider`) or `XxxInterface`
  (`MediaRepositoryInterface`) — either is fine, match the existing one in the
  file you're touching.
- Entities are frozen `@dataclass`es with behavior, not anemic bags of fields
  (see `domain/entities/media.py::is_available`).
- `tests/` mirrors `scruffy/` 1:1 by layer. Test `domain/` and `use_cases/`
  with plain objects/fakes — no framework, no DB, no HTTP. Only
  `frameworks_and_drivers/` tests touch a real (test) DB, FastAPI `TestClient`,
  etc. This is the **Humble Object pattern** (Ch. 23): keep the hard-to-test
  I/O code as thin as possible and push logic inward where it's cheap to test.

---

## SOLID (distilled from *Clean Architecture*, Chapters 7–11)

These are the principles the layering above exists to serve. Apply them at
the class/module level as you write code inside each layer.

- **SRP — Single Responsibility Principle.** *A module should be responsible
  to one, and only one, actor.* Not "do one thing" — split code when two
  different stakeholders would independently demand changes to it for
  different reasons. Example smell: a `Media` class with both business
  calculations and a `save()` that a DBA cares about — that's two actors, two
  responsibilities, two files.
- **OCP — Open-Closed Principle.** *A software artifact should be open for
  extension but closed for modification.* Adding a new media manager
  (Jellyseerr, etc.) should mean adding a new gateway class, not editing
  `ProcessMediaUseCase`. Achieved here by SRP (separating what changes for
  different reasons) + DIP (depending on the interface, not the gateway).
- **LSP — Liskov Substitution Principle.** Any implementation of an interface
  must be swappable for another without the caller noticing. If
  `SonarrGateway` and `RadarrGateway` both implement `MediaRepositoryInterface`,
  `MediaRepositoryComposite` must not need to know or care which one it's
  holding.
- **ISP — Interface Segregation Principle.** Don't force a client to depend
  on methods it doesn't use. Prefer several small `*Interface` ABCs
  (`MediaRepositoryInterface`, `NotificationServiceInterface`, ...) over one
  fat `RepositoryInterface` — this repo already does this; keep doing it.
- **DIP — Dependency Inversion Principle.** *Depend on abstractions, not
  concretions.* High-level policy (`use_cases/`) defines the interface;
  low-level detail (`interface_adapters/gateways/`) implements it. This is
  the mechanism that makes the Dependency Rule possible even though runtime
  control flow goes the other way (use case calls into the gateway) — the
  *source code* dependency still points inward because the interface lives in
  `use_cases/`. Only add an interface for things that are actually volatile
  (external services, I/O, anything you'd swap or mock); don't add one for a
  stable stdlib/platform concern (DIP itself says it's fine to depend
  directly on things like `datetime` or `dataclasses`).

---

## Ponytail

This repo is worked on in **ponytail full mode** by default (installed
plugin, `/ponytail lite|full|ultra` to change level, "stop ponytail" to turn
off for a session). Before writing code: does it need to exist (YAGNI)? Is
there already a helper/pattern in this codebase? Does the stdlib or an
already-installed dependency solve it? Ship the shortest correct diff; mark
any deliberate corner cut with a `# ponytail: <ceiling>, <upgrade path>`
comment.

**This does not conflict with the Clean Architecture layering above — it
sharpens it.** DIP already says: add an interface only for things that are
genuinely volatile, not speculatively. So:

- Don't add a `*Interface` for something with exactly one implementation and
  no real prospect of a second (that's an unrequested abstraction).
- Do add one when you're wrapping an external system, the DB, or anything a
  use case needs to be tested without (that's the volatile boundary DIP is
  for, not speculation).
- Don't invent a fifth layer, a new package-by-something scheme, or a plugin
  system nobody asked for. Use the four layers that already exist.
- Do keep respecting the Dependency Rule even in a one-line fix — inverting a
  dependency isn't the kind of boilerplate ponytail tells you to skip.
