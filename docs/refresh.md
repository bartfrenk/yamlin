# yamlin overview and simplification suggestions

## Overview

**yamlin** is a small library for concurrently resolving "deferred" values
embedded anywhere inside a nested `dict`/`list` structure — e.g. values
parsed out of a YAML config that need async work (network calls, sleeps,
etc.) before the structure is usable.

Actual code is tiny — two real modules plus a test file:

- **`src/yamlin/deferred.py`** — the live implementation, and the only thing
  under test:
  - `Deferred` (ABC): a `result()` coroutine, e.g. custom lazy objects. Its
    earlier `# TODO: might not be necessary` comment (added in `646f1a5`)
    was resolved by `755af06`, which taught `force` to also accept plain
    coroutines directly (`iscoroutine(value)` case).
  - `force(obj, deep=True)`: BFS over the structure via two helpers:
    - `run_deferreds` — finds `Deferred`/coroutine leaves, wraps each in
      `create_task`, mutates the leaf in place, returns the flat task list.
    - `replace_tasks` — a **second** full BFS pass that finds `Task` leaves
      and swaps in `.result()`.
    - Loops these two passes until a pass finds nothing (so `Deferred`s that
      resolve to more `Deferred`s get unwrapped too), unless `deep=False`.
  - `indexed()`: a generator giving `(key, value)` pairs uniformly for dicts
    (`.items()`) and lists (`enumerate`).
  - Imports `log_time` from `utils.py` but never calls it — dead import.
  - Well covered by `tests/test_yamlin/test_deferred.py` (concurrency
    timing, nesting, `deep=False`, coroutine support). One test is
    `@pytest.mark.skip` — per-layer resolution isn't implemented yet.

- **`src/yamlin/utils.py`** — `measure` (time an async call) and `log_time`
  (measure + log). `measure` is used by the tests; `log_time` isn't used
  anywhere.

- **`src/yamlin/base.py`** — a **separate, self-contained prototype** that
  duplicates the same idea with a completely different design: a PyYAML
  `SafeLoader` subclass (`ConfigLoader`) with a custom `!sleep` tag, its own
  dataclass-based `Deferred`/`Resolver`/`SleepResolver`, its own
  `force`/`result` functions, and a `main()` that loads `config.yaml` and
  resolves it via `devtools.pprint`. It predates `deferred.py` (first commit
  `5d44f63`, "Change name to yamlin") and is **not imported by anything** —
  not tests, not `main.py`, not `__init__.py`.

- **`src/yamlin/main.py`** and **`src/yamlin/__init__.py`** — `main.py` is
  empty; `__init__.py` just has a stub `def main(): print("Hello from
  aero!")`, a leftover from the project's previous name (`aero`, before the
  `5d44f63` rename). `pyproject.toml`'s `[project.scripts] aero =
  "yamlin:main"` still points at this stub, so `uv run aero` prints a
  hello-world message unrelated to the rest of the project.

- **`config.yaml`** — a 3-line sample (`!sleep 2` twice) that only
  `base.py`'s dead `main()` knows how to read.

## Suggested simplifications

1. **Delete `base.py`.** It's an orphaned earlier spike with its own
   incompatible `Deferred` type, unreferenced anywhere, and its existence is
   the single biggest source of confusion (two unrelated classes both named
   `Deferred` in the same package). If the `!sleep`/custom-YAML-tag idea is
   still wanted, it should be rebuilt on top of `deferred.py`'s `force`, not
   kept as a parallel implementation.

2. **Fix or remove the `aero` stub.** `__init__.py`'s `main()` and the
   `aero` script entry in `pyproject.toml` are pre-rename debris pointing
   nowhere useful. Either wire up a real CLI (e.g. load a YAML file with the
   `!sleep`-style tags, run `force`, print the result — effectively what
   `base.py:main` tried to do) or delete the stub and the script entry until
   there's a real one.

3. **Drop the second BFS pass in `force`.** `run_deferreds` already visits
   every container once to plant `Task`s; `replace_tasks` then re-walks the
   *entire* structure again just to find the `Task`s that were only just
   placed. Since `run_deferreds` already knows exactly which
   `(container, key)` pairs it mutated, it could record those alongside the
   task list and replace results directly after `gather`, cutting the tree
   traversal from two full passes to one. Simpler and cheaper on large
   structures.

4. **Remove the dead `log_time` import in `deferred.py`** (or actually use
   it to time each pass — there's an obvious hook in `force`'s
   `make_single_pass`).

5. **Minor:** `indexed()`'s two independent `if` statements can be an
   `if`/`elif` (functionally identical today since only one type matches,
   but reads clearer as one branch).

6. **Un-skip or delete the "per-layer resolution" test.** It documents
   desired-but-unimplemented behavior with no tracking elsewhere (no TODO,
   no issue) — worth either implementing it or removing the aspirational
   test so the suite reflects only current guarantees.
