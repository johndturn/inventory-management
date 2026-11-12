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

// matchMedia is missing in some test/embedded environments; treat that as "OS light"
const darkQuery = typeof matchMedia === 'function' ? matchMedia('(prefers-color-scheme: dark)') : null
const osPrefersDark = () => Boolean(darkQuery?.matches)

// The scheme actually on screen ('light' | 'dark'), reactive for the switcher
const scheme = ref('light')

// data-scheme mirrors the scheme actually on screen (choice resolved against the
// OS). Colors don't need it (light-dark() handles them), but the dark terminal
// skin also swaps fonts, shapes and motion, which light-dark() can't express.
function syncScheme() {
  const dark = choice.value === 'dark' || (choice.value === 'system' && osPrefersDark())
  scheme.value = dark ? 'dark' : 'light'
  document.documentElement.dataset.scheme = scheme.value
}

// Follow OS changes live while the choice is 'system'
darkQuery?.addEventListener('change', syncScheme)
syncScheme()

// Vite HMR re-evaluates this module; drop the old listener so stale copies
// (closing over an old `choice`) don't keep writing data-scheme
if (import.meta.hot) {
  import.meta.hot.dispose(() => darkQuery?.removeEventListener('change', syncScheme))
}

function applyChoice(value) {
  const root = document.documentElement
  // 'system' removes the override so `color-scheme: light dark` follows the OS
  if (value === 'system') delete root.dataset.theme
  else root.dataset.theme = value
  syncScheme()

  try {
    if (value === 'system') localStorage.removeItem(STORAGE_KEY)
    else localStorage.setItem(STORAGE_KEY, value)
  } catch {
    // Not persisted, but the theme still applies for this visit
  }
}

export function useTheme() {
  // Writable computed (system | light | dark); the switcher uses toggleTheme
  const theme = computed({
    get: () => choice.value,
    set: (value) => {
      if (!CHOICES.includes(value)) return
      choice.value = value
      applyChoice(value)
    }
  })

  // The single-button switcher flips whatever scheme is on screen. 'system' is
  // the initial state (follow the OS until the first press). Landing on the
  // scheme the OS already prefers returns to 'system' rather than pinning an
  // explicit choice, so a press-and-press-back never stops following the OS.
  const toggleTheme = () => {
    const next = scheme.value === 'dark' ? 'light' : 'dark'
    const osScheme = osPrefersDark() ? 'dark' : 'light'
    theme.value = next === osScheme ? 'system' : next
  }

  return { theme, scheme, toggleTheme }
}
