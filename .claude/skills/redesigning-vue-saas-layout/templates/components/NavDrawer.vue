<!--
  NavDrawer: mobile navigation built on a modal <dialog>.

  The platform handles: focus trap, inert page behind it, Escape to close,
  focus returning to the menu button, top-layer stacking (no z-index), and,
  together with base.css, scroll lock.

  JS handles three things:
    1. Closing after a route change (following a link never closes a dialog).
    2. Closing if the viewport grows to the wide layout while open. Hiding an
       open modal with CSS would leave the page inert.
    3. Backdrop-click dismissal on Safari, which lacks closedby="any".
-->
<template>
  <dialog
    :id="id"
    ref="dialog"
    class="nav-drawer"
    closedby="any"
    :aria-label="label"
    @click="dismissOnBackdrop"
  >
    <div class="nav-drawer__panel">
      <button
        type="button"
        class="icon-btn nav-drawer__close"
        :commandfor="id"
        command="close"
        :aria-label="closeLabel"
      >
        <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
      <slot />
    </div>
  </dialog>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const props = defineProps({
  id: { type: String, required: true },
  label: { type: String, required: true },
  closeLabel: { type: String, default: 'Close navigation' }
})

const dialog = ref(null)
const close = () => dialog.value?.close()

const route = useRoute()
watch(() => route.fullPath, close)

// Keep in sync with the 64rem breakpoint in AppShell.vue
let wide
const closeWhenWide = (event) => {
  if (event.matches) close()
}
onMounted(() => {
  wide = window.matchMedia('(width >= 64rem)')
  wide.addEventListener('change', closeWhenWide)
})
onBeforeUnmount(() => wide?.removeEventListener('change', closeWhenWide))

// The panel fills the whole dialog box, so a click whose target is the
// <dialog> element itself can only have landed on ::backdrop
const dismissOnBackdrop = (event) => {
  if (event.target === dialog.value) close()
}

defineExpose({ close, id: props.id })
</script>

<style scoped>
.nav-drawer {
  /* Override the UA's centered modal: pin full-height to the inline-start edge */
  inset-block: 0;
  inset-inline: 0 auto;
  margin: 0;
  padding: 0;
  border: 0;
  inline-size: min(var(--sidebar-w), 85vw);
  max-inline-size: none;
  block-size: 100dvh;
  max-block-size: none;
  background: var(--color-surface);
  color: var(--color-text);
  box-shadow: var(--shadow-lg);
  translate: -100% 0;
  /* allow-discrete keeps the dialog rendered during its exit transition;
     `overlay` is Chromium-only and harmless elsewhere */
  transition:
    translate var(--duration) var(--ease-out),
    display var(--duration) allow-discrete,
    overlay var(--duration) allow-discrete;
}

.nav-drawer[open] {
  translate: 0 0;
}

/* The state the entry transition starts from */
@starting-style {
  .nav-drawer[open] {
    translate: -100% 0;
  }
}

.nav-drawer::backdrop {
  background: oklch(0% 0 0 / 0%);
  transition:
    background-color var(--duration) var(--ease-out),
    display var(--duration) allow-discrete,
    overlay var(--duration) allow-discrete;
}

.nav-drawer[open]::backdrop {
  background: oklch(0% 0 0 / 45%);
}

@starting-style {
  .nav-drawer[open]::backdrop {
    background: oklch(0% 0 0 / 0%);
  }
}

/* RTL: slide in from the other edge */
.nav-drawer:dir(rtl) {
  translate: 100% 0;
}

.nav-drawer:dir(rtl)[open] {
  translate: 0 0;
}

.nav-drawer__panel {
  position: relative;
  display: flex;
  flex-direction: column;
  block-size: 100%;
  padding-block: env(safe-area-inset-top) env(safe-area-inset-bottom);
}

.nav-drawer__close {
  position: absolute;
  inset-block-start: calc(env(safe-area-inset-top) + var(--space-3));
  inset-inline-end: var(--space-3);
}
</style>
