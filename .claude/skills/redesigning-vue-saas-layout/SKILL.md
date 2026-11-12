---
name: redesigning-vue-saas-layout
description: Use when asked to modernize, restyle, or "make professional" a Vue 3 app's UI; replace a top navigation bar with a left/vertical sidebar; convert to a SaaS or admin-dashboard layout; add dark mode or a centralized design-token system; make a Vue app mobile friendly with a mobile nav drawer; or fix inconsistent spacing and visual polish across Vue views.
---

# Redesigning a Vue 3 App into a SaaS Sidebar Layout

## Overview

A SaaS redesign has three parts, and all three are required:

1. **Design system**: one layered, tokenized CSS source with light and dark mode.
2. **Shell**: sidebar, top bar, content column, and mobile drawer, built on native platform features.
3. **Sweep**: every view moved onto the tokens and shared primitives.

Agents reliably build the shell and then stop, so the pages stay as inconsistent as before. The redesign is done when the views match, in both themes, at every width.

**Platform first.** Where HTML or CSS provides a behavior natively, use it rather than Vue state:
- dialogs, popovers, and anchor positioning
- invoker commands (`commandfor`/`command`)
- `:has()` and container queries
- `light-dark()` and `@starting-style`

JS is for what the platform can't do. `reference/platform.md` lists each replacement, its browser support, and the semantic HTML checklist.

**Templates.** `templates/` holds a verified kit to copy and adapt:
- `styles/`: the layered design system
- `components/`: AppShell, AppSidebar, SidebarNav, NavDrawer, PopoverMenu, ThemeSwitcher
- `composables/`: useTheme, useNavItems
- an `index.html` head

Convert the script style to the project's convention (for example, `setup()` vs `<script setup>`).

## Phase 0: Inventory (read-only, before any edit)

1. **Coordination.** Run `git status`. If someone else (another agent or the user) has uncommitted changes in files you need, ask before editing those files. New files and untouched components can proceed in parallel.
2. **Project rules.** CLAUDE.md files can define the design-system colors, banned elements (such as emojis), mandatory delegation (such as routing all `.vue` edits through a specific subagent), and the browser-testing tools to use. These rules win over this skill.
3. **Browser target.** Check `browserslist` and `build.target`. Without one, the target is Baseline Newly available. Limited-availability features are enhancements only (see `reference/platform.md`).
4. **Routes vs pages.** List the router's routes and the `views/*.vue` files. Flag views that have no route, and nav labels that bypass i18n. Ask before routing an orphaned view.
5. **Shell contents.** Record every item in the current header: logo, links, filters or search, switchers, profile menu, notifications.
6. **JS the platform can replace.** Grep for these:
   - `ref(false)` open flags
   - click-outside handlers
   - `keydown` Escape listeners
   - positioned overlay `<div>` modals
   - dropdown `top: 100%` math
   - `placement` props
7. **Layout assumptions.** Grep for sticky or fixed positioning with offsets (`top: 70px`), `max-width` page containers, the z-index ladder, and `100vh`.
8. **Theme blockers.** Count the hex, `rgb`/`rgba`, `white`, and `#fff` values per file, plus hard-coded SVG `fill`/`stroke` colors in charts. These literals are where dark mode breaks.
9. **Before screenshots.** Capture every route at 1440, 1024, 768, and 390 px in light mode. Without them there is nothing to compare against afterwards.

## Phase 1: Design system

Copy `templates/styles/` to `src/styles/` and import `index.css` once in `main.js`.

- **Layers.** The order is `reset, tokens, base, components, utilities`. Scoped SFC styles are unlayered, so they win over all of these, which is intended.
- **Three token tiers.** Primitives are the raw palette. Semantic tokens (`--color-surface`) carry light/dark via `light-dark()`. Component tokens (`--sidebar-w`) are layout constants. Views use semantic and component tokens only.
- **Map, don't rebrand.** Primitives come from the project's existing palette (hex is fine). Normalize spacing and type to the nearest token. Ask before shifting headings or body text more than one step.
- **Dark mode.**
  - Set `color-scheme: light dark` on `:root`. Pair every semantic color with `light-dark()`.
  - Elevation gets lighter in dark mode: bg, then surface, then raised.
  - Accents lighten in dark mode. Status backgrounds become low-alpha tints, not pastels.
  - Chart colors come from `--chart-*` tokens.
- **User override.** `[data-theme]` on `<html>` is set by `useTheme()`, and by the inline script in the `templates/index.html` head before first paint. Merge those head tags, including `viewport-fit=cover` and `<meta name="color-scheme">`.
- **Shared primitives.** Move the project's global card, table, badge, and page-header classes into `components.css`, rewritten against tokens. Keep the project's existing class names so views don't all need renaming.

## Phase 2: Shell

Build `App.vue` purely by composition. It holds no layout CSS of its own:

```vue
<AppShell>
  <template #sidebar>
    <AppSidebar>
      <template #brand>...</template>
      <SidebarNav :items="navItems" :label="t('nav.primary')" />
      <template #footer><ThemeSwitcher /> <LanguageSwitcher /> <ProfileMenu /></template>
    </AppSidebar>
  </template>
  <template #topbar><FilterBar /></template>
  <router-view />
</AppShell>
```

| Old top-nav item | New home |
|---|---|
| Logo / product name | Sidebar `#brand` |
| Route links | `SidebarNav`, with items from route `meta.nav` via `useNavItems()` |
| Filters, search, page actions | `#topbar`, with filters in `<search><form>` |
| Profile / account menu | Sidebar footer, rebuilt on `PopoverMenu` (flips upward on its own) |
| Language / theme switchers | Sidebar footer |

Mobile nav comes for free. Below 64rem the `#sidebar` slot renders inside `NavDrawer` (a modal `<dialog>`), opened by an invoker-command button.

## Phase 3: Sweep every view (required)

For **each** view, one at a time:

1. Replace hex, rgba, and spacing literals with tokens. Chart SVGs use `fill: var(--chart-n)`.
2. Use the shared primitives and delete per-view overrides of them. A real variant becomes a shared modifier class.
3. Semantics: give each view one `<h1>` and nest headings correctly beneath it. Interactive elements must be `<button>` or `<a>`, never clickable `<div>` or `<tr>` elements.
4. Responsiveness: replace viewport media queries inside views with `@container content (...)`.
5. Replace JS-driven modals and dropdowns with `<dialog>` and `PopoverMenu` (see `reference/platform.md`).
6. Check the view at 1440 and 390 in **both** themes before moving on.

## Verification checklist

- [ ] `npm run build` passes. There are no console errors or Vue warnings on any route.
- [ ] Every routed page is reachable from the nav. Exactly one link has `aria-current="page"`, including on detail routes.
- [ ] At 1440, 1024, 768, and 390: no horizontal page scroll (`scrollWidth === innerWidth`). Wide tables scroll inside `.table-container`.
- [ ] Drawer at 390:
  - It opens from the menu button.
  - Focus moves into it, and the page is inert and scroll-locked.
  - It closes on Escape, on a link click, and on a backdrop tap. Test the backdrop tap in Safari too.
  - Focus returns to the menu button after it closes.
- [ ] Popover menus open fully on screen from the sidebar footer and inside the drawer.
- [ ] Light, dark, and system themes all apply. The choice survives a reload with no flash. Text contrast is at least 4.5:1 in both themes.
- [ ] Tabbing goes skip link, then sidebar, then top bar, then content, with visible focus rings throughout.
- [ ] i18n: after switching language, labels truncate rather than overflow.
- [ ] After screenshots match the Phase 0 set route by route, and dark-mode shots are taken.
- [ ] Grep: the Phase 0 color and spacing literals in views are substantially gone, and none of the old offsets (`top: 70px` and similar) remain.

## Common mistakes

| Mistake | Fix |
|---|---|
| Shell rebuilt, views untouched | Phase 3 is the redesign. Consistency lives in the views. |
| Dark mode added, but views keep `#fff`, `white`, `rgba(0,0,0,…)`, or chart hex | Grep those per view and replace them with semantic tokens. |
| `color-scheme` set on a nested element to theme a section | Set it on `:root` only. Vite's Lightning CSS compiles `light-dark()` against the root scheme. |
| Grid column `1fr`, or an implicit `auto` track, wrapping a wide table | Use `minmax(0, 1fr)`. Otherwise the table's min-content width widens the page. |
| `exact-active-class` on every link, or `active-class` on `/` | Use `SidebarNav`'s `isCurrent()`: `/` matches exactly, other links also match by prefix. |
| Duplicate ids or radio `name`s, because the sidebar slot renders twice | Generate them with `useId()`, as `PopoverMenu` and `ThemeSwitcher` do. |
| `<search>` triggers "Failed to resolve component" | Add `compilerOptions.isCustomElement: (tag) => tag === 'search'` to `vue()` in the Vite config. |
| CSS nesting inside `<style scoped>` | Vue scopes only the innermost selector, so the parent leaks. Nest only in global layer files. |
| Hiding an open modal `<dialog>` with CSS at desktop width | That leaves the page inert. Close it with a `matchMedia` listener instead (see `NavDrawer`). |
| Relying on `closedby="any"` alone | Safari lacks it. Keep the `event.target === dialog` backdrop check. |
| `role="menu"` on a popover of buttons | Omit it unless arrow-key navigation is implemented. |
| `list-style: none` on nav lists | Add `role="list"`, or Safari/VoiceOver drops the list semantics. |
| Mobile inputs under 16px | iOS zooms on focus. `base.css` sets `max(16px, 1em)` for coarse pointers. |
| Icons via `v-html` or emojis | Render SVG path data: `<svg class="icon"><path :d="…"/></svg>`. |
| Sticky top bar with wrapping filters on phones | The top bar is static below 40rem. Don't make it sticky. |
| Loading a font from a third-party CDN without asking | Self-host it, or keep the system stack. Public repos and privacy both matter. |
