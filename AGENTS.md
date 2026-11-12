# AGENTS.md

**Single source of truth** for any coding agent (Claude Code, Codex, etc.) working in this repository.
`CLAUDE.md` only imports this file; edit instructions here, not there.

Factory Inventory Management System Demo with GitHub integration - Full-stack application with Vue 3 frontend, Python FastAPI backend, and in-memory mock data (no database).

> ⚠️ **This repository and any fork you create are PUBLIC.** Do not commit credentials, internal hostnames, or private registry URLs. `client/.npmrc` pins the public npm registry and `client/package-lock.json` is gitignored to prevent locally-configured registries from leaking into commits — leave both in place.

## Critical Tool Usage Rules

### Subagents
Use the Task tool with these specialized subagents for appropriate tasks:

- **vue-expert**: Use for Vue 3 frontend features, UI components, styling, and client-side functionality
  - Examples: Creating components, fixing reactivity issues, performance optimization, complex state management
  - **MANDATORY RULE: ANY time you need to create or significantly modify a .vue file, you MUST delegate to vue-expert**
- **code-reviewer**: Use after writing significant code to review quality and best practices
- **Explore**: Use for understanding codebase structure, searching for patterns, or answering questions about how components work
- **general-purpose**: Use for complex multi-step tasks or when other agents don't fit

### Skills
- **backend-api-test** skill: Use when writing or modifying tests in `tests/backend` directory with pytest and FastAPI TestClient

### MCP Tools
- **ALWAYS use GitHub MCP tools** (`mcp__github__*`) for ALL GitHub operations
  - Exception: Local branches only - use `git checkout -b` instead of `mcp__github__create_branch`
- **ALWAYS use Playwright MCP tools** (`mcp__playwright__*`) for browser testing
  - Test against: `http://localhost:3000` (frontend), `http://localhost:8001` (API)

## Stack
- **Frontend**: Vue 3 + Composition API + Vite (port 3000)
- **Backend**: Python FastAPI (port 8001)
- **Data**: JSON files in `server/data/` loaded via `server/mock_data.py`

## Quick Start

```bash
# Backend
cd server
uv run python main.py

# Frontend
cd client
npm install && npm run dev
```

## Key Patterns

**Filter System**: 4 filters (Time Period, Warehouse, Category, Order Status) apply to all data via query params
**Data Flow**: Vue filters → `client/src/api.js` → FastAPI → In-memory filtering → Pydantic validation → Computed properties
**Reactivity**: Raw data in refs (`allOrders`, `inventoryItems`), derived data in computed properties

## API Endpoints
- `GET /api/inventory` - Filters: warehouse, category
- `GET /api/orders` - Filters: warehouse, category, status, month
- `GET /api/dashboard/summary` - All filters
- `GET /api/demand`, `/api/backlog` - No filters
- `GET /api/spending/*` - Summary, monthly, categories, transactions

## Common Issues
1. Use unique keys in v-for (not `index`) - use `sku`, `month`, etc.
2. Validate dates before `.getMonth()` calls
3. Update Pydantic models when changing JSON data structure
4. Inventory filters don't support month (no time dimension)
5. Revenue goals: $800K/month single, $9.6M YTD all months

## File Locations
- Views: `client/src/views/*.vue`
- API Client: `client/src/api.js`
- Backend: `server/main.py`, `server/mock_data.py`
- Data: `server/data/*.json`
- Styles: `client/src/App.vue`

## Design System
- Colors: Slate/gray (#0f172a, #64748b, #e2e8f0)
- Status: green/blue/yellow/red
- Charts: Custom SVG, CSS Grid for layouts
- No emojis in UI

## Code Conventions
- Always document non-obvious logic changes with comments

## Issue tracking: beads_rust (`br`) + beads_viewer (`bv`)

All epics, bugs, and tasks for this repo are tracked in `.beads/` with
[beads_rust](https://github.com/Dicklesworthstone/beads_rust) (`br`, the CLI that reads and writes issues) and
[beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) (`bv`, read-only triage, graph analysis, and prioritization).
Do not track work in ad-hoc markdown TODO files or GitHub issues; create a bead instead.

- **Source of truth in git:** `.beads/issues.jsonl` (committed). The SQLite DB (`.beads/beads.db`) is a local cache and is gitignored.
- **ID prefix:** `inv-` (e.g. `inv-a1b`).
- **Install (macOS):** `br` via the beads_rust installer (`~/.local/bin/br`), `bv` via Homebrew. Check with `br version` and `bv --version`.
- **Agents must never run bare `bv`**: it launches an interactive TUI that will hang a non-interactive shell. Always use `bv --robot-*` flags.
- **This repo is public:** issue titles, descriptions, and comments are committed in `issues.jsonl`, so no credentials, internal hostnames, or customer data in beads.

### Conventions for this repo

- **Epics** group work by audit lens or theme; child tasks link to them with `--parent <epic-id>`.
- **Labels:** `security`, `performance`, `ux`, `a11y`, `i18n`, `backend`, `frontend`, `ci`, `quick-win` (S effort, one sitting).
- **Priority:** `0` fix now, `1` next, `2` backlog, `3` low or nice-to-have, `4` someday.
- Cite `file:line` evidence in descriptions, and record the original audit id (e.g. `SEC-3`, `PERF-6`, `UX-10`) so findings stay traceable.
- Use `br dep add <issue> <depends-on>` when one fix must land before another (e.g. auth depends on the shared axios instance).

### Triage and prioritization with `bv`

```bash
bv --robot-triage          # Ranked recommendations, quick wins, blockers to clear (start here)
bv --robot-next            # Single top pick
bv --robot-plan            # Dependency-respecting execution tracks (what can run in parallel)
bv --robot-insights        # Graph metrics: PageRank, critical path, cycles
bv --robot-label-health    # Per-label health (e.g. is the `security` backlog stalling?)
bv --robot-priority        # Priority misalignment suggestions
bv --export-md report.md   # Human-readable report of all issues
```

Typical agent session: `bv --robot-triage` (or `br ready`) to choose work, `br update <id> --status=in_progress` to claim it, implement and test, `br close <id> --reason="..."`, then `br sync --flush-only` and commit `.beads/issues.jsonl` along with the code.

### Keeping the managed sections current

The `bv-agent-instructions` block at the end of this file is generated by beads_viewer. Refresh it with
`bv --agents-update`. Do **not** run `br agents --add/--update`: br treats the bv block as "legacy" and would
replace it with its own shorter block, dropping the bv triage guidance.

<!-- bv-agent-instructions-v2 -->

---

## Beads Workflow Integration

This project uses [beads_rust](https://github.com/Dicklesworthstone/beads_rust) (`br`) for issue tracking and [beads_viewer](https://github.com/Dicklesworthstone/beads_viewer) (`bv`) for graph-aware triage. Issues are stored in `.beads/` and tracked in git.

### Using bv as an AI sidecar

bv is a graph-aware triage engine for Beads projects (.beads/beads.jsonl). Instead of parsing JSONL or hallucinating graph traversal, use robot flags for deterministic, dependency-aware outputs with precomputed metrics (PageRank, betweenness, critical path, cycles, HITS, eigenvector, k-core).

**Scope boundary:** bv handles *what to work on* (triage, priority, planning). `br` handles creating, modifying, and closing beads.

**CRITICAL: Use ONLY --robot-* flags. Bare bv launches an interactive TUI that blocks your session.**

#### The Workflow: Start With Triage

**`bv --robot-triage` is your single entry point.** It returns everything you need in one call:
- `quick_ref`: at-a-glance counts + top 3 picks
- `recommendations`: ranked actionable items with scores, reasons, unblock info
- `quick_wins`: low-effort high-impact items
- `blockers_to_clear`: items that unblock the most downstream work
- `project_health`: status/type/priority distributions, graph metrics
- `commands`: copy-paste shell commands for next steps

```bash
bv --robot-triage        # THE MEGA-COMMAND: start here
bv --robot-next          # Minimal: just the single top pick + claim command

# Token-optimized output (TOON) for lower LLM context usage:
bv --robot-triage --format toon
```

#### Other bv Commands

| Command | Returns |
|---------|---------|
| `--robot-plan` | Parallel execution tracks with unblocks lists |
| `--robot-priority` | Priority misalignment detection with confidence |
| `--robot-insights` | Full metrics: PageRank, betweenness, HITS, eigenvector, critical path, cycles, k-core |
| `--robot-alerts` | Stale issues, blocking cascades, priority mismatches |
| `--robot-suggest` | Hygiene: duplicates, missing deps, label suggestions, cycle breaks |
| `--robot-diff --diff-since <ref>` | Changes since ref: new/closed/modified issues |
| `--robot-graph [--graph-format=json\|dot\|mermaid]` | Dependency graph export |

#### Scoping & Filtering

```bash
bv --robot-plan --label backend              # Scope to label's subgraph
bv --robot-insights --as-of HEAD~30          # Historical point-in-time
bv --recipe actionable --robot-plan          # Pre-filter: ready to work (no blockers)
bv --recipe high-impact --robot-triage       # Pre-filter: top PageRank scores
```

### br Commands for Issue Management

```bash
br ready              # Show issues ready to work (no blockers)
br list --status=open # All open issues
br show <id>          # Full issue details with dependencies
br create --title="..." --type=task --priority=2
br update <id> --status=in_progress
br close <id> --reason="Completed"
br close <id1> <id2>  # Close multiple issues at once
br sync --flush-only  # Export DB to JSONL
```

### Workflow Pattern

1. **Triage**: Run `bv --robot-triage` to find the highest-impact actionable work
2. **Claim**: Use `br update <id> --status=in_progress`
3. **Work**: Implement the task
4. **Complete**: Use `br close <id>`
5. **Sync**: Always run `br sync --flush-only` at session end

### Key Concepts

- **Dependencies**: Issues can block other issues. `br ready` shows only unblocked work.
- **Priority**: P0=critical, P1=high, P2=medium, P3=low, P4=backlog (use numbers 0-4, not words)
- **Types**: task, bug, feature, epic, chore, docs, question
- **Blocking**: `br dep add <issue> <depends-on>` to add dependencies

### Session Protocol

```bash
git status              # Check what changed
git add <files>         # Stage code changes
br sync --flush-only    # Export beads changes to JSONL
git commit -m "..."     # Commit everything
git push                # Push to remote
```

<!-- end-bv-agent-instructions -->
