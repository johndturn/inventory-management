<!--
  PopoverMenu: an anchored dropdown with no open/close state in JS.

  popover + popovertarget provide toggling, light dismiss, Escape,
  aria-expanded on the trigger, and top-layer stacking (no z-index, so it is
  never clipped by a sticky sidebar).
  CSS anchor positioning places the panel below the trigger. It flips above
  automatically when there is no room, as in the sidebar footer, so no
  placement prop is needed.

  Usage:
    <PopoverMenu :label="t('profile.menu')">
      <template #trigger>avatar + name</template>
      <template #default="{ close }">
        <button type="button" class="popover-menu__item" @click="openProfile(); close()">Profile</button>
      </template>
    </PopoverMenu>

  The items are plain buttons and links. Do not add role="menu" unless you
  also implement arrow-key navigation; a wrong role is worse than none.
-->
<template>
  <div class="popover-menu" :style="{ '--anchor': anchorName }">
    <button
      type="button"
      class="popover-menu__trigger"
      :popovertarget="panelId"
      :aria-label="label"
    >
      <slot name="trigger" />
    </button>
    <div :id="panelId" ref="panel" popover class="popover-menu__panel">
      <slot :close="close" />
    </div>
  </div>
</template>

<script setup>
import { ref, useId } from 'vue'

defineProps({
  // Accessible name for the trigger when its content is not descriptive text
  label: { type: String, default: undefined }
})

// The component can render twice (sidebar and drawer). Popover ids and
// anchor names must be unique per instance, so derive both from useId().
const uid = useId().replace(/[^\w-]/g, '-')
const panelId = `popover-${uid}`
const anchorName = `--anchor-${uid}`

const panel = ref(null)
const close = () => panel.value?.hidePopover()
</script>

<style scoped>
.popover-menu__trigger {
  anchor-name: var(--anchor);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  inline-size: 100%;
  min-height: var(--control-h);
  padding: var(--space-2);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  text-align: start;
}

.popover-menu__trigger:hover {
  background: var(--color-surface-hover);
}

.popover-menu__panel {
  position-anchor: var(--anchor);
  /* Below the trigger, start-aligned; flip when out of room */
  position-area: block-end span-inline-end;
  position-try-fallbacks: flip-block, flip-inline, flip-block flip-inline;
  /* Undo the UA's centered popover inset and margin */
  inset: auto;
  margin: var(--space-1) 0;
  min-inline-size: 14rem;
  max-inline-size: min(20rem, calc(100vw - 2 * var(--space-4)));
  padding: var(--space-1);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
  color: var(--color-text);
  box-shadow: var(--shadow-lg);
  opacity: 0;
  transition:
    opacity var(--duration) var(--ease-out),
    display var(--duration) allow-discrete,
    overlay var(--duration) allow-discrete;
}

.popover-menu__panel:popover-open {
  opacity: 1;
}

@starting-style {
  .popover-menu__panel:popover-open {
    opacity: 0;
  }
}

/* Item styling for slotted buttons and links */
.popover-menu__panel :slotted(.popover-menu__item) {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  inline-size: 100%;
  min-height: var(--control-h);
  padding-inline: var(--space-3);
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  text-align: start;
  text-decoration: none;
}

.popover-menu__panel :slotted(.popover-menu__item:hover) {
  background: var(--color-surface-hover);
}
</style>
