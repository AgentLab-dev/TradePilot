# ED&A Agent Skills — v2 Architecture Proposal

**Status:** Draft for review with `@workday-inc/eda-devops` (Josh Dixon) and the FQC-ARR team
**Author:** Kotesh (drafted 2026-08-02)
**Target repo:** `workday-inc/eda-agent-skills` (extend, do not fork)
**Parent Jira:** EDADG-4113 · pack work under EDADG-4350 · fleet marketplace EDADG-4351

---

## 1. TL;DR

Josh Dixon's v1 hub gets the *source-of-truth* layout right — hub-root shared
`skills/`+`rules/`+`hooks/`, thin `plugins/<slug>/`, per-item `manifest.yaml`,
Copilot-first PR review, GitHub Release drop-in zips. **Keep it. Extend it.**

Where it stops short of the three goals in your request:

| Goal | v1 gap | v2 answer |
|---|---|---|
| **Enable skills for everyone** | Private repo, `eda` team + peer ED&A teams only; ~50 workmates | Sibling **public-safe hub** + **Cursor Team Marketplace** registration + **Artifactory-hosted installer** for the full private set |
| **Anyone can call a plugin & start using** | Install = clone repo → run `build_agent_packs.py --force` → hand-drop into `~/.cursor/` | `pipx install eda-skills` → `eda-skills install fae` (one command, idempotent, atomic) + first-run wizard on Cursor launch |
| **Everyone at the same level** | Each workmate curates their own `~/.cursor/`; guaranteed drift | Per-skill **semver** + lockfile + auto-sync daemon + weekly parity Slack report + advisory CI gate on `eda-dbt-*` PRs |

Plus a proposed set of **~25 new skills** — including the FQC-ARR pack you
already run locally out of `~/Library/Application Support/AE Agent/` — that
should be contributed as the first proof point.

Effort: 2 engineers × 6 weeks for the platform, plus rolling skill
contributions from the fleet. See §6.

---

## 2. Current state — what v1 gets right (do not touch)

Read before proposing anything new:

- Hub root `skills/` `rules/` `hooks/` = single committed source of truth (DRY)
- `plugins/<slug>/` is **thin** — pack identity + pack-unique skills only
- Full drop-in packs are assembled to `dist/plugins/` (gitignored) and shipped
  as GitHub Release zips via `.github/workflows/release-agent-packs.yml`
- Per-item `manifest.yaml` with tight JSON schema (`schema/manifest.schema.yaml`)
- Explicit CODEOWNERS line per publishable item; `maintainer` must appear on it
- Copilot code review as the primary automated gate (thin human review)
- Two long-lived branches: `qa` (default, feature target) and `prod` (promotion)
- Four packs today: `dataops-engineer`, `devops-engineer`,
  `finance-analytics-engineer`, `finance-data-analyst`
- ~45 shared skills already committed (Snowflake, dbt, Jira, Confluence, Atlan,
  Acceldata, Salesforce CLI, Sigma, Tableau, PDF, Zoom, arr-amendment, ssr-acv,
  product-hierarchy, root-cause-analysis, etc.)

**This is a good foundation.** The rest of this doc is what to add.

---

## 3. Gaps vs your three goals — concrete

### 3.1 "Enable agent skills to everyone"

- Repo is **private**; access limited to GitHub Cloud team `eda` + peer ED&A
  teams. Non-ED&A workmates cannot clone or open PRs.
- Cursor `.cursor-plugin/marketplace.json` exists but is only a manifest — it is
  **not** registered with a Cursor Team Marketplace instance that Workday
  engineers outside ED&A can browse.
- No public-facing catalog page. New joiners cannot see what exists without
  cloning.
- Distribution today is machine-scoped (each install is manual).

### 3.2 "Anyone can call plugin and start using the skill"

- Current install sequence:
  1. `git clone workday-inc/eda-agent-skills`
  2. `python3 -m pip install -r requirements-validate.txt --index-url ...`
  3. `python3 scripts/build_agent_packs.py --force`
  4. Copy `dist/plugins/<pack>/skills/*` into `~/.cursor/skills/`
  5. Copy `dist/plugins/<pack>/rules/*` into `~/.cursor/rules/`
  6. Copy `dist/plugins/<pack>/hooks/*` into `~/.cursor/hooks/`
  7. Restart Cursor
- Steps 1–7 = ~15 minutes for a familiar dev; ~1 hour for a new joiner with
  errors on Artifactory index URLs, Python version, path collisions.
- Zero support for version pinning, upgrade path, uninstall, drift detection.
- No first-run wizard: a new Cursor user doesn't know which pack to install.

### 3.3 "Everyone should be at the same level of skills"

- Local `~/.cursor/` is user-owned and unversioned. There is no lockfile.
- After 3 months, workmate A has 50 skills at various vintages, workmate B has
  10 skills copied 6 months ago, workmate C has zero.
- No signal to the team lead. No way to run `eda-skills doctor` on a laptop
  and get "you are 4 releases behind on 12 skills."
- `--check` in CI validates the *repo*, not any *consumer's* installed state.
- Skill parity today is a folklore problem ("did you copy the latest?").

---

## 4. Proposed v2 architecture — 5 layers

```
┌─────────────────────────────────────────────────────────────┐
│  L5  Discovery + onboarding                                 │
│      /skills slash command · first-run wizard · catalog UI  │
├─────────────────────────────────────────────────────────────┤
│  L4  Parity enforcement                                     │
│      lockfile · auto-sync daemon · Slack parity bot · CI    │
├─────────────────────────────────────────────────────────────┤
│  L3  Installer CLI  (new — pipx install eda-skills)         │
│      install · sync · doctor · list · lock · init · catalog │
├─────────────────────────────────────────────────────────────┤
│  L2  Distribution                                           │
│      GH Release zips · Artifactory pip · Cursor Marketplace │
├─────────────────────────────────────────────────────────────┤
│  L1  Source (extend v1)                                     │
│      hub root · thin plugins · +semver +public +stability   │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1 · Source (backward-compatible extensions to Josh's schema)

Add three optional fields to `schema/manifest.schema.yaml`:

```yaml
# each skill's manifest.yaml — new fields (all optional; validators warn, don't fail)
version: 1.4.2                 # semver per skill (not just per pack)
public: true                   # eligible for auto-promotion to public hub (default false)
stability: stable              # alpha | beta | stable — for progressive rollout
```

**Why:** without semver on a *skill*, the lockfile has nothing to pin. Without
`public`, we cannot mechanically split what's shareable. Without `stability`,
consumers can't opt into "stable only."

**Migration:** validators emit a warning for the first month, then require
`version` for any skill touched in a PR. Skills with no `version` are treated
as `0.1.0`.

### Layer 2 · Distribution (extend, don't replace)

Three channels — pick your preferred install path, one truth behind:

| Channel | What it is | For whom |
|---|---|---|
| **GitHub Release zips** (existing) | `dist/plugins/<pack>.zip` cut from `qa`/`prod` | Air-gapped installs, review-first shops |
| **Artifactory pip package** (new) | `pipx install eda-skills` from `python-virtual` index | 95% of workmates (default) |
| **Cursor Team Marketplace** (new) | Register `.cursor-plugin/marketplace.json` at the Workday Team Marketplace | In-Cursor "install" button UX |

The Artifactory pip package **wraps** the Release zips — one source, three
distribution surfaces. Zero duplication of skill source.

### Layer 3 · Installer CLI — `eda-skills` (new)

```bash
# frictionless install (goal 2)
pipx install eda-skills                    # one-time, from Artifactory
eda-skills init                             # first-run wizard: pick your role → install pack
eda-skills install finance-analytics-engineer  # explicit install
eda-skills install fae                      # alias

# parity (goal 3)
eda-skills sync                             # pull latest, update in place, atomic
eda-skills doctor                           # report drift: "12 skills stale, 3 missing"
eda-skills list                             # show installed packs + versions
eda-skills lock                             # freeze current versions to ~/.cursor/.eda-skills.lock
eda-skills catalog                          # browse available skills (name + description)
eda-skills uninstall <pack>                 # clean uninstall
```

**Implementation shape (~600 lines Python):**

- Reads latest `dist/plugins/<pack>.zip` from GitHub Release or Artifactory
- Unpacks atomically: temp dir → validate → `rename` into `~/.cursor/skills/`,
  `~/.cursor/rules/`, `~/.cursor/hooks/` (never partial state)
- Backs up any pre-existing files to `~/.cursor/.eda-skills.backup/<timestamp>/`
- Writes `~/.cursor/.eda-skills.lock`:

  ```yaml
  installed:
    - pack: finance-analytics-engineer
      version: 0.2.1
      installed_at: 2026-08-02T19:15:00Z
      skills:
        arr-amendment: 3.7.23
        root-cause-analysis: 1.2.0
        # ...
  ```

- Idempotent: rerunning `install` when up-to-date is a no-op
- Honors `stability: alpha|beta|stable` — `eda-skills install --stability=stable`
  filters out alpha/beta skills

**Package the CLI in-repo:** ship it from `scripts/eda_skills/` inside
`workday-inc/eda-agent-skills` and publish to Artifactory via a new GitHub
Action `.github/workflows/release-installer.yml`.

### Layer 4 · Parity enforcement (fixes goal 3)

Four mechanisms, low-friction:

**1. Auto-sync daemon** (macOS `launchd` / Linux `systemd` / Dev Container cron)

  - Runs `eda-skills sync` daily at 8am local
  - Silent when green; posts a single Slack DM ("2 skills updated: `dbt-testing 1.5→1.6`, `mcp-snowflake 2.1→2.2`") when it patches
  - Installed via `eda-skills init --with-autosync`

**2. `~/.cursor/.eda-skills.lock`** (see §Layer 3)

  - Single source of truth for "what version of what is on this machine"
  - `eda-skills doctor` compares against latest release manifest

**3. Advisory CI hook on `eda-dbt-*` repos**

  - New GitHub Action `check-skills-currency.yml` in `eda-dbt-em`, `eda-dbt-base`, etc.
  - Reads `.eda-skills.lock` from a PR-body-attached artifact (author uploads
    output of `eda-skills doctor --json`)
  - **Phase 2:** advisory only — warns if >30 days stale
  - **Phase 3:** blocking on `qa` if >60 days stale

**4. Weekly Slack "skill parity report" bot**

  - Runs Monday 9am PT
  - Reads opt-in lockfile hashes from a private GitHub Gist (workmates opt in
    via `eda-skills lock --publish`)
  - Posts to a `#eda-agent-skills-parity` channel:
    > `Team parity this week: 82%. 4 workmates ≥2 releases behind on the `fae` pack. See who → thread.`
  - Non-shaming — the message thread just links to `eda-skills sync`.

### Layer 5 · Discovery + onboarding (fixes goal 1 + goal 2)

- **`/skills` Cursor slash command** — lists available packs and their install
  commands. Ship as a `commands/` folder entry in the hub.
- **First-run wizard** — on new Cursor install, `eda-skills init` opens a
  webview: "Pick your role: FAE / FDA / DataOps / DevOps → install."
  Autodetects role from `git config user.email` domain heuristics + team lookup.
- **Skill catalog site** — GitHub Pages generated from `manifest.yaml` files.
  URL: `eda-agent-skills.pages.workday.internal`. Searchable, tagged, with
  copy-paste install commands.
- **Public hub for org-wide access** — sibling repo `workday-inc/ai-agent-skills-public`
  with the subset flagged `public: true`. Auto-promotion bot syncs weekly.
  Any Workday engineer can browse and `pipx install ai-skills-public`.

---

## 5. New skills to add (~28 skills, categorized)

All to be authored under hub-root `skills/` unless noted. Every skill ships
with `manifest.yaml`, CODEOWNERS entry, `SKILL.md` (kebab-case name = folder
name), optional `references/`, `scripts/`, `assets/`.

### 5.1 FQC-ARR pack — highest priority (bring your local runtime to the hub)

Your `~/Library/Application Support/AE Agent/agents/arr_quarter_close/` runtime
is 15 sub-agents in Python. The Python **runtime** stays local (per hub
contract: no runtimes committed). But the **prompts, sub-agent contracts,
runbook, and validation patterns** absolutely belong in the hub.

Contribute these as a new pack `plugins/finance-arr-quarter-close/`:

| Skill | Type | Notes |
|---|---|---|
| `arr-quarter-close-runbook` | skill | dbt run/test sequence for the full close |
| `arr-quarter-close-validation` | skill | Waterfall test + IA-migration recon |
| `arr-quarter-close-debugger` | skill | Root-cause + reproducible-fix pattern (fixes the "banned signature" finding) |
| `arr-quarter-close-supervisor` | agent | Supervisor role prompt + smart-gate authorization model |
| `arr-quarter-close-jira-intake` | skill | Ticket-driven mode intake pattern |
| `arr-quarter-close-code-data-validator` | skill | Baseline SQL contract — with dedup keys + sanity thresholds (fixes the "negative ARR" finding) |
| `arr-quarter-close-test-runner` | skill | Test execution + evidence capture |
| `arr-quarter-close-cd-monitor` | skill | Post-merge CD monitoring |
| `arr-quarter-close-lessons-learned` | skill | The lessons-learning loop as a reusable pattern |

Plus one thin `plugins/finance-arr-quarter-close/` pack that composes these.

### 5.2 dbt / Snowflake architect skills

| Skill | Notes |
|---|---|
| `dbt-mesh-cross-project-refs` | Stub-gap pattern (fixes Finding A from the FQC-ARR healthcheck: `stubs.yml` `eda_dbt_common` gap) |
| `dbt-microbatch-incremental` | 1.9+ microbatch strategy |
| `dbt-semantic-layer-metricflow` | MetricFlow integration + semantic-layer publishing |
| `dbt-model-versioning` | v1/v2 side-by-side deploys |
| `snowflake-dynamic-tables` | Target lag, refresh mode selection |
| `snowflake-cost-attribution` | FinOps queries per model / warehouse / user |
| `snowflake-hybrid-tables` | Unistore hybrid-table pattern |
| `snowflake-warehouse-picker` | Pick right warehouse for query size + concurrency |

### 5.3 Cross-cutting engineering

| Skill | Notes |
|---|---|
| `pr-conflict-resolver-dbt-yaml` | Deterministic resolver for dbt YAML merge conflicts |
| `test-generation-from-model` | Generate dbt tests (unique, not_null, accepted_values) from `.yml` |
| `sql-cost-preflight` | Estimate cost via `EXPLAIN` before running |
| `ci-monitor-github-actions` | Watch PR CI + auto-diagnose failed checks |
| `dbt-cloud-job-orchestration` | Job + environment + credential patterns |
| `atlan-lineage-query` | Programmatic lineage pulls via Atlan MCP |
| `acceldata-quality-probe` | Data quality checks via Acceldata MCP |

### 5.4 Governance / security

| Skill | Notes |
|---|---|
| `secrets-hygiene` | Pre-commit hooks + `.gitignore` patterns beyond the basics |
| `pii-classification` | dbt column-level PII tags + downstream masking |
| `owasp-llm-guardrails` | Prompt-injection defenses for tool-using agents |
| `sana-migration-mapping` | Port FQC-ARR concepts to Workday Sana AgentSkills |

### 5.5 Finance domain

| Skill | Notes |
|---|---|
| `finance-metric-catalog` | Canonical ARR / ACV / NRR / GRR / LRR SQL patterns |
| `arr-vs-billing-reconciliation` | Cross-source reconciliation queries |
| `arr-waterfall-quarterly` | Standard quarterly ARR waterfall |

---

## 6. Rollout plan — 12 weeks, three phases

### Phase 1 (weeks 1–4) — Consumer-first: make install painless

**Deliverables**

- `eda-skills` CLI MVP (install, list, uninstall, doctor)
- Artifactory `pipx` publish pipeline
- Docs: `docs/consumer-quickstart.md`
- Pilot with 10 workmates across FAE + FDA

**Success metrics**

- Install success rate ≥95% on macOS + Dev Container
- Median time to "first skill loaded" ≤2 minutes (from `brew install pipx` → done)
- Zero manual `~/.cursor/` file drops in the pilot cohort

### Phase 2 (weeks 5–8) — Contributor-first: parity + new skills

**Deliverables**

- Add `version:` / `public:` / `stability:` to `manifest.schema.yaml`
- Ship `.eda-skills.lock` mechanism (`eda-skills lock`, `eda-skills sync`)
- Advisory CI hook on `eda-dbt-em`
- Contribute the 28 new skills in batches of ~5/week
- Commit the FQC-ARR pack (5 skills + 1 agent) as the flagship

**Success metrics**

- 3+ workmates ship skills into hub (not just the platform team)
- `eda-skills doctor` reports on 80% of active laptops
- Median staleness ≤7 days in pilot cohort

### Phase 3 (weeks 9–12) — Org-wide

**Deliverables**

- Sibling repo `workday-inc/ai-agent-skills-public` (AppSec + Legal review of scope)
- Auto-promotion bot (weekly sync of `public: true` skills, private → public)
- Register in Workday's Cursor Team Marketplace
- Onboarding wizard `eda-skills init` in the ED&A Dev Container image
- Weekly Slack skill-parity bot

**Success metrics**

- 100+ workmates using hub across ≥5 teams
- Public catalog page indexed by Workday internal search
- Team parity ≥90% within active packs

---

## 7. Collaboration with the existing hub (do not fork)

- Every proposal in this doc lands as a PR into `workday-inc/eda-agent-skills`
  targeting `qa` — same branching, same Copilot review, same CODEOWNERS.
- Weekly sync with `@workday-inc/eda-devops` (Josh Dixon) — I will drive.
- File EDADG tickets under the existing EDADG-4113 / EDADG-4350 tree; no new
  parent epic unless AppSec/Legal require one for the public hub.
- Do **not** stand up a competing repo. Do **not** create a `common/` tree.
  Do **not** use Confluence as the store.

---

## 8. Jira tickets to file (proposed)

Under EDADG-4113 (parent):

| Type | Title |
|---|---|
| Story | `eda-skills` CLI — MVP (install/list/uninstall/doctor) |
| Story | Extend `manifest.schema.yaml` with `version` / `public` / `stability` |
| Story | Skill lockfile spec + `eda-skills lock` / `sync` |
| Story | Auto-sync daemon (launchd / systemd / Dev Container cron) |
| Story | Advisory CI hook on `eda-dbt-em` for skill currency |
| Story | Slack weekly parity report bot |
| Story | Sibling public hub repo — AppSec + Legal scoping |
| Story | Auto-promotion bot (private → public hub) |
| Story | Cursor Team Marketplace registration |
| Epic  | FQC-ARR pack contribution (5 skills + 1 agent) |
| Story | New skill: `dbt-mesh-cross-project-refs` (blocks Finding A) |
| Story | New skill: `secrets-hygiene` |
| Story | New skill: `owasp-llm-guardrails` |
| Story | New skill: `sana-migration-mapping` |
| ...   | one per remaining skill in §5 |

Ballpark: 1 epic (FQC-ARR pack) + ~35 stories.

---

## 9. Open decisions — need alignment before Phase 3

1. **Public repo scope.** What's shareable outside ED&A? Everything without
   business-specific SQL and customer names, or a stricter allowlist?
2. **Sana migration.** Does the Sana AgentSkills platform obsolete this hub, or
   coexist? If coexist, does the hub become the *authoring* surface and Sana the
   *runtime*? (See `fqc_arr_sana_migration_design.md` for the current mapping.)
3. **Version pinning.** Opt-in (`eda-skills lock`) or default-on (every install
   writes a lock)? Opt-in is safer; default-on gives parity for free.
4. **CI gate.** After Phase 2, does the `eda-dbt-em` CI hook become
   *blocking* on stale installs? Recommend advisory-only through end of year;
   blocking Q1 next year with 60-day tolerance.
5. **Installer language.** Python (matches hub) or a compiled Go binary (no
   Python 3.11 requirement, single-file distribute)? Recommend Python for MVP,
   revisit if install issues surface.

---

## 10. Immediate next actions (this week)

1. **Show plan to Josh Dixon.** Open a discussion issue on
   `workday-inc/eda-agent-skills` linking this doc; ask for a 30-min sync.
2. **File umbrella EDADG ticket** — "eda-skills v2 architecture (installer +
   parity + public hub)."
3. **Fork a working branch** `feat/v2-architecture-spike` off `qa`.
4. **Ship `eda-skills` CLI MVP in ≤2 days** — install/list/doctor only, no
   parity yet. Prove the ergonomics before building the rest.
5. **Draft the FQC-ARR pack PR** as the first proof point — 5 skills + 1 agent
   + `plugins/finance-arr-quarter-close/` thin plugin + `PACKS` dict entry in
   `scripts/build_agent_packs.py`. Target `qa`.
6. **Circulate this doc** to the FQC-ARR team and the two Finance pack owners
   (FAE + FDA) for review.

---

## Appendix A · Why the "same skills level" problem is real

Today, three workmates on the same finance team:

- **Workmate A** (senior, active contributor): 47 skills in `~/.cursor/`, last
  refreshed 3 days ago from `dist/plugins/finance-analytics-engineer.zip`.
- **Workmate B** (mid, focused on Snowflake): 12 skills, hand-picked from
  the hub 4 months ago. Missed the last 8 skill updates.
- **Workmate C** (new joiner, month 2): 0 skills — never onboarded to the hub.

All three of them ask agents for the same task ("run the ARR waterfall test").
Their agents give *different* answers because the underlying skill set differs.
This is the same class of problem as un-versioned SQL macros or drifting local
dbt profiles — solved historically by lockfiles + package managers.

`.eda-skills.lock` + `eda-skills sync` is not novel — it is `Pipfile.lock`,
`package-lock.json`, `Gemfile.lock` applied to Cursor skills.

## Appendix B · Why not just use Cursor's built-in marketplace?

Cursor's Team Marketplace is the right *front-door* for goal 1 and goal 2 (§
Layer 2 + Layer 5). But it is not sufficient alone:

- No per-machine drift detection → doesn't solve goal 3
- No lockfile → doesn't solve goal 3
- Registration is one-time; no CLI to script bulk install → still needs
  `eda-skills` for Dev Container automation
- Public-vs-private tiering is our concern, not Cursor's → still needs §Layer 1
  extensions

So: register in Cursor's marketplace **and** ship the installer CLI + lockfile.
Two channels, one truth.

## Appendix C · Skills that already solve pieces of this

Existing skills to reuse or extend rather than re-invent:

- `~/.cursor/skills/agentic-architecture-patterns/` → informs L4 parity design
- `~/.cursor/skills/multi-agent-supervisor-pattern/` → informs FQC-ARR pack
- `~/.cursor/skills/twelve-factor-agents/` → informs installer daemon design
- `~/.cursor/skills/owasp-llm-top-10/` → source for `owasp-llm-guardrails`
- `.cursor/skills/arr-quarter-close/` in `eda-dbt-em` → migrate wholesale into
  the FQC-ARR pack

## Appendix D · What v2 does NOT change

- Josh's hub-root/thin-plugin/dist-full split — untouched
- `PACKS` dict in `scripts/build_agent_packs.py` — extended, not replaced
- Copilot-first PR review — kept
- `qa` → `prod` promote-PR flow — kept
- CODEOWNERS-per-item requirement — kept
- Existing 4 packs — kept, gets a 5th (`finance-arr-quarter-close`)

The v2 delta is *additive*. Zero rip-and-replace.
