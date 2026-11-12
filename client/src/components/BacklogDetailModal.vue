<template>
  <dialog
    ref="dialogEl"
    class="modal-container"
    :aria-labelledby="titleId"
    @close="onClose"
    @click="onDialogClick"
  >
    <template v-if="backlogItem">
      <div class="modal-header">
        <h2 :id="titleId" class="modal-title">Inventory Shortage Details</h2>
        <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="shortage-header">
          <div class="shortage-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <path d="M24 8L24 28M24 34L24 36" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
              <circle cx="24" cy="24" r="18" stroke="currentColor" stroke-width="3"/>
            </svg>
          </div>
          <div class="shortage-title-section">
            <p class="item-name">{{ translateProductName(backlogItem.item_name) }}</p>
            <div class="item-sku">SKU: {{ backlogItem.item_sku }}</div>
          </div>
          <span :class="['badge', backlogItem.priority]">
            {{ backlogItem.priority }} Priority
          </span>
        </div>

        <div class="shortage-summary">
          <div class="summary-card danger">
            <div class="detail-label">Shortage Amount</div>
            <div class="summary-value">{{ shortage }} units</div>
          </div>
          <div class="summary-card warning">
            <div class="detail-label">Days Delayed</div>
            <div class="summary-value">{{ backlogItem.days_delayed }} days</div>
          </div>
        </div>

        <dl class="detail-grid">
          <div>
            <dt class="detail-label">Order ID</dt>
            <dd class="detail-value mono">{{ backlogItem.order_id }}</dd>
          </div>
          <div>
            <dt class="detail-label">Item SKU</dt>
            <dd class="detail-value mono">{{ backlogItem.item_sku }}</dd>
          </div>
          <div>
            <dt class="detail-label">Quantity Needed</dt>
            <dd class="detail-value">{{ backlogItem.quantity_needed }} units</dd>
          </div>
          <div>
            <dt class="detail-label">Quantity Available</dt>
            <dd class="detail-value">{{ backlogItem.quantity_available }} units</dd>
          </div>
          <div>
            <dt class="detail-label">Expected Date</dt>
            <dd class="detail-value">
              <time v-if="backlogItem.expected_date" :datetime="backlogItem.expected_date">{{ formatDate(backlogItem.expected_date) }}</time>
              <template v-else>N/A</template>
            </dd>
          </div>
          <div>
            <dt class="detail-label">Status</dt>
            <dd class="detail-value">
              <span class="badge danger">Backordered</span>
            </dd>
          </div>
        </dl>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
      </div>
    </template>
  </dialog>
</template>

<script setup>
import { computed, ref, watch, onMounted, useId } from 'vue'
import { useI18n } from '../composables/useI18n'

const { t, translateProductName } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  backlogItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const titleId = useId()
const dialogEl = ref(null)

// Drive the native dialog from the isOpen prop; showModal() gives focus trap, Escape and inert page for free
watch(() => props.isOpen, (open) => {
  const d = dialogEl.value
  if (!d) return
  if (open && !d.open) d.showModal()
  else if (!open && d.open) d.close()
})
onMounted(() => { if (props.isOpen) dialogEl.value?.showModal() })

// The native 'close' event fires for Escape and dialog.close(); only tell the parent if it still thinks we're open
const onClose = () => { if (props.isOpen) emit('close') }

// Backdrop tap: clicks on the dialog element itself (not its children) are outside the content box
const onDialogClick = (e) => { if (e.target === dialogEl.value) dialogEl.value.close() }

const shortage = computed(() => {
  if (!props.backlogItem) return 0
  return props.backlogItem.quantity_needed - props.backlogItem.quantity_available
})

const close = () => {
  dialogEl.value?.close()
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  if (isNaN(date.getTime())) return 'N/A'
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.shortage-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding-block-end: var(--space-6);
  margin-block-end: var(--space-6);
  border-block-end: 1px solid var(--color-border);
}

.shortage-icon {
  display: grid;
  place-items: center;
  inline-size: 4rem;
  block-size: 4rem;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.shortage-title-section {
  flex: 1;
  min-inline-size: 0;
}

.item-name {
  margin-block-end: var(--space-2);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
}

.item-sku {
  font-size: var(--text-base);
  color: var(--color-text-subtle);
  font-family: var(--font-mono);
}

.shortage-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
  gap: var(--space-4);
  margin-block-end: var(--space-8);
}

.summary-card {
  padding: var(--space-5);
  border: 1px solid;
  border-radius: var(--radius-md);
}

.summary-card.danger {
  border-color: var(--color-danger-soft);
  background: var(--color-danger-bg);
}

.summary-card.warning {
  border-color: var(--color-warning-soft);
  background: var(--color-warning-soft);
}

.summary-value {
  margin-block-start: var(--space-2);
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
}

.summary-card.danger .summary-value {
  color: var(--color-danger);
}

.summary-card.warning .summary-value {
  color: var(--color-on-warning-soft);
}

.detail-value.mono {
  font-family: var(--font-mono);
  color: var(--color-primary);
}

dd {
  margin: 0;
}
</style>
