<!--
  ThemeSwitcher: one icon button. The icon shows the theme that is currently
  on (sun = light, computer = terminal); the label and tooltip name the action
  the click performs. The button holds no ids, so it is safe to render twice
  (sidebar and mobile drawer).
-->
<template>
  <button
    type="button"
    class="icon-btn"
    :aria-label="actionLabel"
    :title="actionLabel"
    @click="toggleTheme"
  >
    <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
      <path :d="iconPath" />
    </svg>
  </button>
</template>

<script>
import { computed } from 'vue'
import { useTheme } from '../../composables/useTheme'
import { useI18n } from '../../composables/useI18n'

// 24x24 stroke paths. Sun: a circle drawn as two arcs plus eight rays.
const SUN_PATH =
  'M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8z' +
  'M12 2v2M12 20v2M2 12h2M20 12h2' +
  'M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41'
// Computer: monitor screen, neck and base
const COMPUTER_PATH = 'M3 4h18v12H3z M12 16v4 M8 20h8'

export default {
  name: 'ThemeSwitcher',
  setup() {
    // scheme is the theme on screen (already resolved against the OS)
    const { scheme, toggleTheme } = useTheme()
    const { t } = useI18n()

    const isDark = computed(() => scheme.value === 'dark')
    const iconPath = computed(() => (isDark.value ? COMPUTER_PATH : SUN_PATH))
    // Describes the action, not the current state
    const actionLabel = computed(() =>
      isDark.value ? t('shell.switchToLight') : t('shell.switchToTerminal')
    )

    return { iconPath, actionLabel, toggleTheme }
  }
}
</script>
