import { ref, computed } from 'vue'

// Must match the inline script in index.html, which applies the saved choice
// before first paint so the page never flashes the wrong theme.
const STORAGE_KEY = 'theme'
const CHOICES = ['system', 'light', 'dark']

function readStoredChoice() {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return CHOICES.includes(value) ? value : 'system'
  } catch {
    // Storage can throw in private mode or when site data is blocked
    return 'system'
  }
}

// Module scope: every component calling useTheme() shares one state
const choice = ref(readStoredChoice())

function applyChoice(value) {
  const root = document.documentElement
  // 'system' removes the override so `color-scheme: light dark` follows the OS
  if (value === 'system') delete root.dataset.theme
  else root.dataset.theme = value

  try {
    if (value === 'system') localStorage.removeItem(STORAGE_KEY)
    else localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Not persisted, but the theme still applies for this visit
  }
}

export function useTheme() {
  // Writable computed so components can bind it with v-model
  const theme = computed({
    get: () => choice.value,
    set: (value) => {
      if (!CHOICES.includes(value)) return
      choice.value = value
      applyChoice(value)
    }
  })

  return { theme }
}
