<!--
  SidebarNav: the primary navigation list.
  items: [{ to, label, icon }]. Labels are already translated, and icon is SVG
  path data for a 24x24 stroke icon. Build items with useNavItems() so they
  come from the router.
  The current page is marked with aria-current="page" and styled through that
  attribute, so there is no class bookkeeping.
-->
<template>
  <nav class="sidebar-nav" :aria-label="label">
    <ul role="list" class="sidebar-nav__list">
      <li v-for="item in items" :key="item.to">
        <router-link
          :to="item.to"
          class="sidebar-nav__link"
          :aria-current="isCurrent(item.to) ? 'page' : undefined"
        >
          <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
            <path :d="item.icon" />
          </svg>
          <span class="truncate">{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<script>
import { useRoute } from 'vue-router'

export default {
  name: 'SidebarNav',
  props: {
    items: { type: Array, required: true },
    label: { type: String, required: true }
  },
  setup() {
    const route = useRoute()

    // '/' must match exactly, or it would be current on every page. Every other
    // item also stays current on its child and detail routes (/orders/123),
    // which router-link's exact-active matching misses.
    const isCurrent = (to) =>
      to === '/'
        ? route.path === '/'
        : route.path === to || route.path.startsWith(`${to}/`)

    return { isCurrent }
  }
}
</script>

<style scoped>
.sidebar-nav__list {
  display: grid;
  gap: var(--space-1);
}

.sidebar-nav__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: var(--control-h);
  padding-inline: var(--space-3);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  font-weight: 500;
  text-decoration: none;
  transition:
    background-color var(--duration) var(--ease-out),
    color var(--duration) var(--ease-out);
}

.sidebar-nav__link:hover {
  background: var(--color-surface-hover);
  color: var(--color-text);
}

.sidebar-nav__link[aria-current='page'] {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
</style>
