<!--
  AppSidebar: the sidebar's vertical layout. The brand sits at the top, the
  nav scrolls in the middle, and the footer is pinned to the bottom.
  It is purely presentational; the same markup renders in both the persistent
  sidebar and the mobile drawer.
-->
<template>
  <div class="app-sidebar">
    <div class="app-sidebar__brand">
      <slot name="brand" />
    </div>
    <div class="app-sidebar__nav">
      <slot />
    </div>
    <div v-if="$slots.footer" class="app-sidebar__footer">
      <slot name="footer" />
    </div>
  </div>
</template>

<script>
export default { name: 'AppSidebar' }
</script>

<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  block-size: 100%;
}

.app-sidebar__brand {
  padding: var(--space-5) var(--space-5) var(--space-4);
  /* Leaves room for the drawer's close button */
  padding-inline-end: calc(var(--control-h) + var(--space-4));
}

.app-sidebar__nav {
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: var(--space-2) var(--space-3);
}

.app-sidebar__footer {
  display: grid;
  gap: var(--space-2);
  padding: var(--space-3);
  border-block-start: 1px solid var(--color-border);
}
</style>
