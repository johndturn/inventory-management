# Terminal dark mode ("floor terminal") design

Date: 2026-11-12
Status: approved by the product owner after review of the live prototype
Branch: `design/terminal-dark`

## Intent

Give dark mode a true-black, terminal, slightly "hackery" identity with tasteful
pixel-styled motion, while keeping the application and the data it communicates
exactly as they are. Light mode does not change.

The concept is grounded in the product's subject: factory inventory and ERP
systems historically ran on IBM 5250 "green screen" terminals. Dark mode borrows
that vernacular (phosphor text on black, high-intensity white for what matters,
a small fixed set of semantic colours) rather than a generic "black plus one
neon accent" look.

## Goals

- True black (`#000`) backgrounds and surfaces in dark mode.
- A terminal type system: monospace interface text, a pixel face for page titles
  and headline numbers, including Japanese.
- Terminal structure: square corners, no shadows, panel titles set into the top
  border, reverse-video selection, bracketed status codes, double-line dialogs.
- One orchestrated motion moment per page plus motion that answers user actions,
  all in visible pixel steps.
- Every text colour at least 4.5:1 on black; chart colours validated on black.

## Non-goals

- No change to light mode. Light-mode screenshots must stay byte-identical.
- No change to layout, information architecture, copy, data, or behaviour,
  apart from the theme switcher below.

## Anti-goals (failure even if it "works")

- Animating data: numbers must never scramble, count up, type in or arrive late.
- Reduced legibility of dense tables or of any value.
- Loading fonts from a third-party CDN (public repo, privacy).
- Fonts or effects leaking into light mode, or costing light-mode users bytes.

## Constraints

- Vue 3 + Vite 8, existing layered design system in `client/src/styles/`
  (`reset, tokens, base, components, utilities`) with `light-dark()` tokens.
- Views use Vue `<style scoped>` blocks, which are unlayered and beat any
  `@layer`.
- Public repository; fonts must be OFL or similar and self-hosted.
- `.vue` changes go through the `vue-expert` subagent (AGENTS.md). This design
  needs none: it is CSS, tokens and two small JS files.

## Design decisions

### Colour

| Token / role | Value | Contrast on #000 |
|---|---|---|
| Background, surfaces | `#000000` | n/a |
| Body text (phosphor) | `#b4f0be` | 16.2:1 |
| Headings, key values (high intensity) | `#eef6ec` | 19.0:1 |
| Muted text | `#86c995` | 10.8:1 |
| Subtle text (labels) | `#5f9e6e` | 6.6:1 |
| Interactive / info (turquoise) | `#45d3cc` | 11.4:1 |
| Warning (yellow) | `#f2c94c` | 13.2:1 |
| Danger (red) | `#ff6b6b` | 7.6:1 |
| Success (green) | `#4be07f` | 12.3:1 |
| Decorative rule | `#1e3d27` | 1.75:1 (decorative only) |
| Control outline | `#2f6a3e` | 3.25:1 (meets 3:1 for UI boundaries) |
| Hover / selected row | `#0c1f12` | n/a |

Chart marks keep the light palette's order (shipped, delivered, processing,
backordered, neutral) and use `#037ac0`, `#29ac68`, `#bb881a`, `#af2843`,
`#6f8f78`. Validated with the dataviz validator against `#000`, all pairs:
lightness band, chroma floor, normal-vision ΔE 17.0 and contrast pass; worst CVD
ΔE is 7.6 (deutan), inside the 6-8 band that is legal only with secondary
encoding. Every chart in the app already has a legend and printed values.
Related existing issue: light-mode chart contrast and legend counts
(`inv-ebv.1`) is separate and not addressed here.

### Typography

- **IBM Plex Mono** 400/500/600: all interface text. The IBM lineage fits the
  5250 reference. Body drops to 13px because monospace sets wider.
- **VT323** (pixel face from the DEC VT320): page titles, the sidebar brand,
  modal titles, stat values, the donut total.
- **DotGothic16**: the same pixel role for Japanese glyphs, via per-glyph
  fallback in `--font-display`.
- Stat value sizing is measured, not guessed: VT323 digits advance 0.4em and
  caps are 0.56em tall (Plex 0.70em), so values run larger. The longest value (a
  14-character yen total) is 5.6em wide, so `clamp(2rem, 17cqi, 3.75rem)` keeps
  it inside any stat card.
- Labels drop the light theme's uppercase tracking; Japanese brand text uses
  `line-break: strict` so a line never starts with ー or small kana.

### Structure

- Radii and shadows are zeroed through tokens.
- Card titles sit in the top border (terminal window chrome); a header holding
  only its title collapses.
- Current nav item in reverse video (phosphor background, black text).
- Badges and Restocking's "Partial" marker render as bracketed codes with no
  fill; the brackets are decorative (`content: '[' / ''`) so screen readers do
  not announce them.
- Primary buttons reverse video in turquoise; secondary buttons invert on hover.
- Dialogs use a 3px double border (box-drawing "═" feel).
- Group headings get a turquoise `>` prompt.
- A 1.8% white scanline texture every 3px over the page (top-layer dialogs and
  popovers sit above it).

### Theme switcher (requested by the product owner during review)

The three-way System / Light / Dark segmented control becomes **one icon
button**: a **sun** for the light theme and a **computer** for the terminal
theme. Calls made by the builder, flagged for review:

- The icon shows the theme that is **currently on**; the button's accessible
  name and tooltip state the action ("Switch to terminal theme" / "Switch to
  light theme"), so the icon is never the only description.
- "System" is no longer a visible option, but it remains the **initial state**:
  until someone presses the button the app follows the OS preference, exactly
  as before. Pressing it flips whatever scheme is on screen and stores an
  explicit light or dark choice (same `theme` localStorage key, same pre-paint
  script), except that landing on the scheme the OS already prefers clears the
  stored choice, so pressing and pressing back never stops following the OS.
- The labels call the dark theme the terminal theme ("Switch to terminal
  theme" / "ターミナルテーマに切り替え"). The old System / Light / Dark strings are
  removed.
- Placement: the button shares the sidebar footer row with the language picker
  (picker fills the row, button at the inline-end), profile menu below.

### Motion

All motion uses `steps()` timing so it moves in visible pixel increments, and
`prefers-reduced-motion` (already global in `base.css`) disables it.

- **Arriving on a page (the one orchestrated moment):** the `<h1>` types in left
  to right (stepped clip reveal, 520ms), then a block cursor blinks four times
  and rests solid. Column charts reveal bottom-up and KPI goal meters grow from
  their start, each in eight steps. The chart reveals run only under a
  `data-route-enter` flag the router sets for 1.2s after each navigation:
  views remount their content on every filter change, and replaying the reveal
  there would hide data that is already loaded. The Dashboard category bars do
  not animate at all, because their printed value sits inside the bar and any
  grow would squash or hide it.
- **User-triggered:** dialogs open like a CRT warming up, from a horizontal line
  to full height in six steps (240ms).
- **Loading:** an ASCII spinner (`| / - \`) after loading text, with empty
  alt text so screen readers don't announce each frame.
- Reveal animations use `animation-fill-mode: backwards` so no clip-path lingers
  after they finish (a lingering `inset(0)` clipped rotated chart labels).

## Architecture

- **`data-scheme` attribute.** Colours can follow `light-dark()`, but fonts,
  shapes and motion cannot. `index.html` resolves the scheme actually on screen
  before first paint (explicit choice, else OS preference) and sets
  `data-scheme="dark|light"` on `<html>`; `useTheme.js` keeps it current when the
  choice or the OS preference changes. Every terminal rule needs one selector,
  `:root[data-scheme='dark']`, instead of a media-query copy plus a toggle copy.
- **`client/src/styles/terminal.css`, deliberately unlayered.** Scoped view
  styles are unlayered and would beat any layer; the `:root[data-scheme]` prefix
  adds (0,2,0) specificity so the skin wins without `!important`. Token
  overrides replace the dark half of the system, so view styles that already
  read tokens follow automatically.
- **Fonts** come from `@fontsource/*` packages imported in
  `client/src/styles/index.css` and bundled by Vite. `@font-face` downloads only
  when a rendered rule uses the family, so light mode fetches nothing, and
  DotGothic16 is split by unicode-range so only the glyph slices on screen load.

## Verification

- Light mode on this branch is byte-identical to `main` in full-page screenshots
  (Dashboard, Restocking, Reports) and loads zero font files.
- Dark sweep: 7 routes × 4 widths (1440, 1024, 768, 390) × 2 languages with no
  horizontal page scroll, no stat value overflow, no panel title overflow.
- Dialog motion sampled per animation frame: seven distinct stepped clip states.
- Production build passes.

## Left to the builder / follow-ups

- Dashboard "Inventory shortages" item names wrap to two or three lines in the
  wider monospace face.
- Four solid turquoise "Create PO" buttons in one column read loudly; a quieter
  variant for repeated row actions may be better.
