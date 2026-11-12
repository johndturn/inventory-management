# Platform Reference: Use HTML and CSS Before Vue State

Support status was verified in November 2026. "Baseline" means the feature works in current Chrome, Edge, Firefox, and Safari. Re-check anything marked Limited before relying on it.

## Replace JS with the platform

| Need | Use | Replaces | Support | Fallback |
|---|---|---|---|---|
| Mobile nav drawer, modals | `<dialog>` + `showModal()` | open ref, focus trap, Escape listener, backdrop div, `inert` juggling | Baseline 2022 | — |
| Open/close without handlers | `<button commandfor="id" command="show-modal" \| "close">` | `@click="dialog.showModal()"` | Baseline Dec 2025 (Safari 26.2 last) | `@click` if targeting older browsers |
| Backdrop click dismiss | `<dialog closedby="any">` | click-outside handler | **Limited: no Safari** | `if (e.target === dialog) dialog.close()` (in `NavDrawer`) |
| Dropdown menus | `popover` + `popovertarget` | open ref, click-outside, Escape, manual `aria-expanded` | Baseline 2024 | — |
| Dropdown placement and flip | `anchor-name` / `position-anchor` / `position-area` / `position-try-fallbacks: flip-block` | `placement` props, `getBoundingClientRect` math, Floating UI | Baseline Jan 2026 (Firefox 147 last) | Older browsers show the popover centered; still usable |
| Stacking above sticky chrome | Top layer (dialog, popover) | z-index ladders | Baseline | — |
| Enter/exit animation of dialog or popover | `@starting-style` + `transition: display … allow-discrete` | Vue `<Transition>` | Baseline 2024 (`overlay` property is Chromium-only and harmless) | Instant open/close |
| Scroll lock while modal | `html:has(dialog:modal) { overflow: hidden }` | body-class toggling | Baseline 2023 | — |
| Dark mode | `color-scheme: light dark` + `light-dark()` | theme class swapping, duplicate stylesheets | Baseline 2024 | Lightning CSS lowers it at build time |
| Derived colors (hover, tints) | `color-mix(in oklch, …)` | precomputed hex variants | Baseline 2023 | — |
| Cascade control | `@layer` | `!important`, specificity hacks | Baseline 2022 | — |
| Component responsiveness | `container-type` + `@container` | ResizeObserver, viewport queries that ignore the sidebar | Baseline 2023 | — |
| State-based styling | `:has()`, `[aria-current="page"]`, `:popover-open`, `:user-invalid` | class bookkeeping | Baseline 2023–24 | — |
| Segmented control | `fieldset` + radios + `:has(:checked)` | button-group state | Baseline | — |
| Disclosure, accordion | `<details>` / `<summary>`, `name=""` for exclusive groups | open refs | Baseline 2024 | — |
| Mobile viewport and notches | `dvh`, `env(safe-area-inset-*)` + `viewport-fit=cover` | `innerHeight` listeners | Baseline 2023 | — |
| Native control theming | `accent-color`, `color-scheme` | custom-drawn checkboxes | Baseline | — |
| Heading and paragraph wrap | `text-wrap: balance` / `pretty` | manual `<br>` | balance Baseline 2024; pretty partial | Normal wrapping |

**Enhancement only (Limited availability).** Check current support before use:
- customizable `<select>` (`appearance: base-select`)
- `interestfor` hover cards
- `scroll-state()` container queries
- `interpolate-size`

**Still needs JS (keep it minimal):**
- closing the drawer after a route change
- persisting the theme choice
- the Safari backdrop-dismiss fallback
- closing an open modal when the viewport crosses the wide breakpoint
- computing prefix-match nav state

## Semantic HTML checklist

- **Landmarks:**
  - One `<main id="main">`.
  - The primary nav is `<nav aria-label="…">`.
  - The top bar is a `<header>`; only one banner-level header.
  - Filters sit in `<search>` wrapping a `<form>`.
  - Add a skip link to `#main`.
- **Headings:** one `<h1>` per view (the page title, not the brand), then `<h2>` for sections and card titles. Never skip levels.
- **Lists:** nav items go in `<ul role="list"><li>`.
- **Interactive elements:** use `<button type="button">` for actions and `<a>`/`<router-link>` for navigation. A clickable table row puts a real link or button in its first cell.
- **Current page:** `aria-current="page"`, and style that attribute rather than an `.active` class.
- **Icons:** decorative SVGs get `aria-hidden="true"`. Icon-only buttons get an `aria-label`.
- **Popovers:** items are plain buttons and links. Don't add `role="menu"` without full arrow-key support.
- **Forms:** every control has a `<label for>`. Group related controls in `<fieldset>` + `<legend>`, visually hidden if needed.
- **Data:**
  - `<table>` with `<thead>`/`<th scope>`
  - `<time datetime>` for dates
  - `font-variant-numeric: tabular-nums` for number columns
- **Logical properties:** `padding-inline`, `inset-inline-start`, `border-inline-end`, so RTL locales work without overrides.
- **Motion:** honor `prefers-reduced-motion` (handled globally in `base.css`).
