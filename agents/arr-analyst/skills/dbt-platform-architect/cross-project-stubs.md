# Cross-Project Stubs for Local Development (dbt Mesh)

## When to read this skill

- Local `dbt parse`, `dbt compile`, or `dbt build` fails with errors like:
  ```
  Compilation Error
    Model 'X' depends on a node named 'Y' in package or project 'Z' which was not found
  ```
- The project has a `dependencies.yml` (dbt Mesh) declaring upstream projects.
- After running `dbt deps`, parse/compile starts failing.

## Why dbt Mesh breaks local dbt

dbt Mesh (`dependencies.yml` projects like `eda_dbt_base`, `eda_dbt_gtm`) is resolved
**only by dbt Cloud's multi-project orchestration**. Locally, `dbt deps` only installs
packages from `packages.yml`, not Mesh dependencies. Yet `dbt parse` requires every
`ref('package', 'model')` to resolve — so without stubs, the whole project is unparseable.

## The standard workaround — stub packages

Place minimal "fake" packages into `dbt_packages/<package_name>/` that contain:

1. A `dbt_project.yml` for the package, e.g. `name: 'eda_dbt_base'`.
2. A `models/` folder with one `.sql` file per cross-project model that the
   downstream project refs.
3. Each stub `.sql` is a simple ephemeral passthrough:
   ```sql
   {{ config(materialized='ephemeral') }}
   select * from BASE_PROD.GOOGLE_SHEETS.REF_PRODUCT_HIERARCHY_REF_PRODUCT_HIERARCHY
   ```

**`materialized='ephemeral'` is critical** — it makes dbt fold the CTE inline into
downstream queries, so the production relation is queried directly. The stub is never
created as a real object in Snowflake.

## Why `dbt deps` wipes them

`dbt deps` rebuilds `dbt_packages/` from `packages.yml`. Anything not declared in
`packages.yml` is destroyed. Since stubs are placed manually (or via a script), they
are wiped on every `dbt deps` run.

## The repeatable pattern (used in eda-dbt-em)

```
scripts/cross-project-stubs/
├── stubs.yml          # YAML mapping: package -> model -> Snowflake relation
├── generate_stubs.py  # Python script that writes the stub files
└── restore.sh         # Shell wrapper: runs generate_stubs.py with sensible defaults
```

Plus a `Makefile` target:

```makefile
deps:
	dbt deps
	bash scripts/cross-project-stubs/restore.sh
```

Users run `make deps` instead of `dbt deps` directly.

## How to enumerate the stubs needed

```bash
# All eda_dbt_base refs:
grep -rh "ref(['\"]eda_dbt_base['\"]" models/ macros/ analyses/ \
  | grep -oE "ref\(['\"]eda_dbt_base['\"][[:space:]]*,[[:space:]]*['\"][^'\"]+['\"]" \
  | sed -E "s/.*,[[:space:]]*['\"]([^'\"]+)['\"].*/\1/" \
  | sort -u
```

Repeat for each upstream project listed in `dependencies.yml`.

## How to find the live Snowflake relation for each stub

`base_*` models from `eda_dbt_base` typically materialize to `BASE_PROD.<source>.<TABLE>`,
where `<source>` is the Fivetran connector schema (`GOOGLE_SHEETS`, `SALESFORCE`,
`WORKDAY`, `SBOX_PROD_CURATE`, etc.).

`wd_*_scd2` models from `eda_dbt_gtm` materialize to `CERTIFIED_PROD.GTM.<TABLE_NAME>`.

Verify each with:

```sql
SELECT table_catalog, table_schema, table_name
FROM <DB>.INFORMATION_SCHEMA.TABLES
WHERE table_name = '<EXPECTED>';
```

## Pitfalls

- **`enabled: false` doesn't work** — dbt rejects refs to disabled nodes. Use
  `materialized: ephemeral` instead.
- **Don't include stubs in `dbt build` selectors** — they're meant for parse-time
  resolution only.
- **Snapshot to `~/dbt-stubs/`** — gives you a fallback if the generator script
  ever gets corrupted.
- **Long-term fix** — ask the platform team to publish a `eda-dbt-stubs` private
  package on `packages.yml`. That would be self-healing on every `dbt deps`.

## Standalone tooling location (branch-independent)

A working copy of the tooling is also kept at `~/dbt-stubs/scripts/` on the user's
laptop. This survives any branch switch, clean checkout, or repo re-clone:

```
~/dbt-stubs/
├── eda_dbt_base/         # 23 snapshot stubs (recoverable backup)
├── eda_dbt_gtm/          # 8 snapshot stubs
└── scripts/
    ├── generate_stubs.py
    ├── restore.sh        # uses pwd as repo root, NOT script location
    ├── stubs.yml
    └── Makefile.example  # copy into a repo if Makefile is missing
```

Use it like this from any dbt repo (works even when the in-repo `Makefile` /
`scripts/cross-project-stubs/` aren't on the current branch):

```bash
cd <my-dbt-repo>
dbt deps                                   # wipes dbt_packages/
bash ~/dbt-stubs/scripts/restore.sh        # restores 31 stubs into ./dbt_packages/
dbt parse --no-partial-parse               # confirm
```

The standalone `restore.sh` differs from the in-repo version: it uses `$PWD` as
the repo root (and refuses to run if there's no `dbt_project.yml` there), so a
single copy works from any dbt project on the laptop.

## Related skills

- `~/.cursor/skills/dbt-platform-architect/SKILL.md` — broader Mesh topology
- `~/.cursor/skills/dbt-system-admin/SKILL.md` — operational dbt patterns
