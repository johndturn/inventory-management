<!--
  ThemeSwitcher: a System / Light / Dark segmented control built from native
  radios inside a fieldset. Arrow keys, focus, and screen-reader grouping come
  from the platform. The selected state is styled with :has(:checked).
-->
<template>
  <fieldset class="theme-switcher">
    <legend class="visually-hidden">{{ label }}</legend>
    <label v-for="option in options" :key="option.value" class="theme-switcher__option">
      <input
        v-model="theme"
        class="visually-hidden"
        type="radio"
        :name="groupName"
        :value="option.value"
      />
      <span>{{ option.label }}</span>
    </label>
  </fieldset>
</template>

<script setup>
import { useId } from 'vue'
import { useTheme } from '../composables/useTheme'

defineProps({
  label: { type: String, default: 'Color theme' },
  // Pass translated labels; values must stay system | light | dark
  options: {
    type: Array,
    default: () => [
      { value: 'system', label: 'System' },
      { value: 'light', label: 'Light' },
      { value: 'dark', label: 'Dark' }
    ]
  }
})

const { theme } = useTheme()

// Rendered in both the sidebar and the drawer. A shared radio name would merge
// the two copies into one group, so each instance gets its own name.
const groupName = `theme-${useId()}`
</script>

<style scoped>
.theme-switcher {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 1fr;
  gap: var(--space-1);
  padding: var(--space-1);
  border: 0;
  border-radius: var(--radius-md);
  background: var(--color-surface-hover);
}

.theme-switcher__option {
  display: grid;
  place-items: center;
  min-height: calc(var(--control-h) - var(--space-2));
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-muted);
  cursor: pointer;
}

.theme-switcher__option:has(input:checked) {
  background: var(--color-surface-raised);
  color: var(--color-text);
  box-shadow: var(--shadow-sm);
}

.theme-switcher__option:has(input:focus-visible) {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}
</style>
