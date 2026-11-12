---
name: analyzing-vue-components
description: Use when asked to analyze, audit, or review a Vue 3 app's component structure; find performance problems (slow renders, unnecessary re-renders, render-time work, bundle size, memory leaks); or find duplicated code and reuse opportunities (shared components, composables, helpers, styles). The result is a recommendations report, not code changes.
---

# Analyzing Vue Components for Performance and Reuse

## Overview

The deliverable is a **ranked, evidence-backed report**. Every finding cites `file:line`, names the mechanism, and carries a confidence label. The analysis is read-only and never edits the project. Implementing changes is a separate step the user approves.

Mechanical detection is automated by `scripts/analyze-vue.mjs`, which uses the project's own `@vue/compiler-sfc` and has no install step. Your job is what the script cannot do: verify each lead, check the judgment items it cannot see, measure where it matters, and rank.

## Process

1. **Establish the state you are reporting on.** Run `git status --short` and note files with uncommitted changes. Findings in those files are marked *in flux*. Report repo state only from commands you actually ran. If someone else is editing concurrently, run `git status` again just before writing and re-read every cited line, because line numbers drift. A build measures the working tree as it is at that moment, half-finished edits included.
2. **Run the analyzer** from the frontend package root, writing output outside the repo:
   ```bash
   node <skill-dir>/scripts/analyze-vue.mjs src > <scratch>/vue-analysis.md
   # --json for machine-readable output; --min-dup-nodes=N tunes template-duplicate size
   ```
3. **Verify every lead** by reading the code at its `file:line`. Drop false positives and keep a count of what you dropped. Before recommending `shallowRef`, `markRaw`, or `Object.freeze`, confirm the data is never mutated in place (no `push`, `splice`, or index/field assignment). Otherwise the UI silently stops updating.
4. **Check the items the analyzer can't detect** (table below). Read the largest views and every data-loading path.
5. **Measure** before claiming any bundle or runtime impact:
   - Bundle baseline: `npx vite build --outDir <scratch>/dist --emptyOutDir` gives chunk sizes without touching the repo. Record raw and gzip sizes.
   - Bundle effect of a proposed change: build a scratch copy instead of editing the repo.
     ```bash
     mkdir -p <scratch>/trial && cp -R src index.html vite.config.* package.json <scratch>/trial/
     ln -s "$PWD/node_modules" <scratch>/trial/node_modules
     # apply the change inside <scratch>/trial (e.g. lazy route imports), then:
     (cd <scratch>/trial && npx vite build --outDir <scratch>/trial-dist --emptyOutDir)
     ```
   - Runtime: only if the app is running, time route switches or filter changes with Playwright or Vue DevTools. If it isn't, label the impact *Expected*, not *Measured*.
6. **Size the data, then rank.** Count the real data volumes (fixture files, typical API response lengths) before judging any render-cost finding: an O(n·m) loop over 30 items is noise, while over 30,000 it is the headline. Rank by impact × confidence ÷ effort. On a small app, say plainly that the runtime gains are small. Don't inflate them.
7. **Write the report** in the format below. Offer to implement, following the project's delegation rules (for example, a mandatory subagent for `.vue` edits).

## Checks the analyzer can't detect

| Look for | Why it costs | Suggest |
|---|---|---|
| `v-if="loading"` wrapping the whole page, with loading set on every refetch | The whole subtree unmounts and remounts on each filter change, causing flicker and lost scroll | `v-if` only on the first load; keep content visible while refreshing |
| Filter watchers firing requests with no cancellation | An older response can overwrite a newer one | `AbortController` or a request-sequence guard in a shared loader |
| A reload path that sets `loading` but never resets `error` | One failure leaves the page stuck in its error state | Clear `error` at the start of every load, in the shared loader |
| A computed that does `.find`/`.filter` on list B inside a loop over list A | O(n·m) on every recompute | Build a `Map` in its own computed |
| Independent `await`s in sequence | Load time is the sum of the calls | `Promise.all` |
| Large static or read-only data inside `ref`/`reactive` | Deep proxying of data that never changes | `markRaw`, `Object.freeze`, or `shallowRef` (only after the mutation check in step 3) |
| Rarely opened heavy children (modals, charts) imported eagerly | Initial bundle and parse cost | `defineAsyncComponent` |
| The same try/catch/loading/error block plus a filter watcher in several views | Duplication, and inconsistent error handling | `useAsyncData`-style composable (also the home for cancellation) |
| Same structure, different names (`.summary-card` / `.cost-item`) | The analyzer matches exact CSS only | A shared component or class |
| Components past the project's own size rules (check CLAUDE.md) | Hard to reuse or test | Name the extraction targets |
| Mixed API styles (Options, `setup()`, `<script setup>`) | Reuse friction | Note it; don't make it the headline |

**Default to not recommending** `v-memo`, `KeepAlive`, virtual scrolling, or `v-once` unless you can point to the specific large list or expensive subtree and the change that would trigger it.

## Report format

Sections 1–3 are always written in full. Sections 4–7 shrink to one line each ("None") when they have little content. Under a tight word budget, give snippets only for the top 3 findings.

1. **Summary.** Three lines: the scale (file count, largest components, bundle size if measured) and the three highest-value actions.
2. **Findings table**, highest value first:

   | # | Finding | Evidence | Type | Impact | Effort | Confidence |
   |---|---|---|---|---|---|---|

   - Type: Perf or Reuse.
   - Confidence:
     - **Measured**: you have numbers.
     - **Verified**: you read the code and the mechanism is certain.
     - **Likely**: plausible, not confirmed.
3. **Top findings in detail.** For each of the top 3–5 findings give the mechanism, a minimal before/after snippet, and how to verify the gain after the change.
4. **Reuse plan.** Each extraction target (`BaseModal.vue`, `utils/format.js`, `useAsyncData.js`), with its API sketch and the files that adopt it. Flag cases where a shared helper already exists but components redefine it.
5. **Rejected leads.** Analyzer hits you dropped, and why. This shows the verification happened.
6. **Incidental bugs.** Correctness problems found along the way, as one line each with `file:line`. Keep this short and separate so the requested analysis stays the focus.
7. **Coordination.** Findings that touch in-flux files.

## Common mistakes

| Mistake | Fix |
|---|---|
| Asserting repo state ("git status is clean") without running the command | Quote only command output you have in hand. |
| "Lazy-load routes for a big win" with no numbers | Build into scratch and report chunk sizes. Gains are small when the bundle is small. |
| `shallowRef` suggested for data that is `unshift`ed or index-assigned | Run the mutation check from step 3 first. |
| Treating same-name functions as duplicates when one wraps the other (`deleteTask` calling `api.deleteTask`) | That's layering. Duplication means the same logic exists in two places. |
| Proposing a new helper when `utils/` already has one | Search `utils/`, `composables/`, and `api` first; the analyzer flags this. |
| Missing repeated identical calls in a template (`getX('a')` written 4 times) | One computed per distinct call. |
| Calling a per-row formatter "O(n²)" because it loops over a string | Hot paths iterate data collections, not characters. |
| Ranking render-cost findings without knowing the data size | Count fixture and API sizes first (step 6). |
| Citing line numbers from an early analyzer run while files are being edited | Re-run git status and re-read cited lines before writing (step 1). |
| Bug hunting crowds out the perf and reuse analysis | Bugs get their own short section. |
| Editing code during the analysis | Report only. Implementing is a separate, approved step. |
