<template>
  <PopoverMenu :label="t('shell.language')">
    <template #trigger>
      <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18M12 3c-3 3-3 15 0 18M12 3c3 3 3 15 0 18" />
      </svg>
      <span class="language-label truncate">{{ localeName }}</span>
      <svg class="icon chevron" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 15l6-6 6 6" />
      </svg>
    </template>

    <template #default="{ close }">
      <button
        v-for="locale in availableLocales"
        :key="locale"
        type="button"
        class="popover-menu__item language-item"
        :aria-current="currentLocale === locale ? 'true' : undefined"
        @click="selectLanguage(locale, close)"
      >
        <span class="language-name">{{ getLanguageName(locale) }}</span>
        <svg v-if="currentLocale === locale" class="icon check-icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M5 12l5 5 9-10" />
        </svg>
      </button>
    </template>
  </PopoverMenu>
</template>

<script>
import { useI18n } from '../composables/useI18n'
import PopoverMenu from './shell/PopoverMenu.vue'

const languageNames = {
  en: 'English',
  ja: '日本語'
}

export default {
  name: 'LanguageSwitcher',
  components: { PopoverMenu },
  setup() {
    const { t, currentLocale, setLocale, availableLocales, localeName } = useI18n()

    const getLanguageName = (locale) => languageNames[locale] || locale

    const selectLanguage = (locale, close) => {
      setLocale(locale)
      close()
    }

    return { t, currentLocale, availableLocales, localeName, getLanguageName, selectLanguage }
  }
}
</script>

<style scoped>
.language-label {
  flex: 1;
  min-inline-size: 0;
  font-size: var(--text-sm);
  font-weight: 500;
}

.chevron {
  color: var(--color-text-subtle);
}

.popover-menu__item .icon {
  color: var(--color-text-muted);
}

.language-item {
  justify-content: space-between;
}

.language-item[aria-current='true'] {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.language-item[aria-current='true'] .icon {
  color: var(--color-primary);
}
</style>
