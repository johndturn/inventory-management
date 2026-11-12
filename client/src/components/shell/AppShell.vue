<!--
  AppShell: page frame only. It has no knowledge of routes, users, or filters.

  Slots:
    sidebar  Rendered twice: inline as the persistent sidebar at 64rem and up,
             and inside the mobile <dialog> drawer. Only one copy is ever
             displayed, but both exist in the DOM, so any id or radio name
             inside the slot must be unique per instance (useId()).
    topbar   Filters, search, and page actions. Sticky at 40rem and up.
    default  The routed page. <main> is a size container named `content`.
-->
<template>
  <div class="app-shell">
    <a class="skip-link" href="#main">{{ skipLabel }}</a>

    <div class="app-shell__sidebar">
      <slot name="sidebar" />
    </div>

    <NavDrawer id="nav-drawer" :label="navLabel" :close-label="closeNavLabel">
      <slot name="sidebar" />
    </NavDrawer>

    <div class="app-shell__main">
      <header class="app-shell__topbar">
        <!-- Invoker command: opens the drawer with no click handler -->
        <button
          type="button"
          class="icon-btn app-shell__menu-btn"
          commandfor="nav-drawer"
          command="show-modal"
          :aria-label="openNavLabel"
        >
          <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <slot name="topbar" />
      </header>

      <main id="main" class="app-shell__content" tabindex="-1">
        <slot />
      </main>
    </div>
  </div>
</template>

<script>
import NavDrawer from './NavDrawer.vue'

export default {
  name: 'AppShell',
  components: { NavDrawer },
  // Labels arrive as props so the shell stays i18n-agnostic
  props: {
    navLabel: { type: String, default: 'Navigation' },
    openNavLabel: { type: String, default: 'Open navigation' },
    closeNavLabel: { type: String, default: 'Close navigation' },
    skipLabel: { type: String, default: 'Skip to content' }
  }
}
</script>

<style scoped>
/* Mobile first: one column; the sidebar lives in the drawer */
.app-shell {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  min-height: 100dvh;
}

.app-shell__sidebar {
  display: none;
}

.app-shell__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-shell__topbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--topbar-h);
  padding-block: var(--space-2);
  padding-inline: max(var(--page-gutter), env(safe-area-inset-left))
    max(var(--page-gutter), env(safe-area-inset-right));
  background: var(--color-surface);
  border-block-end: 1px solid var(--color-border);
}

.app-shell__content {
  flex: 1;
  /* Views use @container content (...) so they respond to the width they
     actually have beside the sidebar */
  container: content / inline-size;
  padding-block: var(--space-6) var(--space-10);
  padding-inline: max(var(--page-gutter), env(safe-area-inset-left))
    max(var(--page-gutter), env(safe-area-inset-right));
}

/* Focus lands on <main> through the skip link; no ring on the whole page */
.app-shell__content:focus {
  outline: none;
}

.skip-link {
  position: absolute;
  inset-block-start: var(--space-2);
  inset-inline-start: var(--space-2);
  z-index: calc(var(--z-topbar) + 1);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: var(--color-on-primary);
  translate: 0 -200%;
}

.skip-link:focus-visible {
  translate: 0 0;
}

/* Compact and up: the top bar sticks. Below 40rem it scrolls away, because
   wrapped filters would otherwise cover a large share of a phone screen. */
@media (width >= 40rem) {
  .app-shell__topbar {
    position: sticky;
    top: 0;
    z-index: var(--z-topbar);
    background: color-mix(in oklch, var(--color-surface) 85%, transparent);
    backdrop-filter: blur(8px);
  }
}

/* Wide: persistent sidebar. Keep 64rem in sync with NavDrawer.vue */
@media (width >= 64rem) {
  .app-shell {
    grid-template-columns: var(--sidebar-w) minmax(0, 1fr);
  }

  .app-shell__sidebar {
    display: block;
    position: sticky;
    top: 0;
    height: 100dvh;
    background: var(--color-surface);
    border-inline-end: 1px solid var(--color-border);
  }

  .app-shell__menu-btn {
    display: none;
  }
}
</style>
