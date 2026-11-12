<template>
  <dialog
    ref="dialogEl"
    class="modal-container"
    :aria-labelledby="titleId"
    @close="onClose"
    @click="onDialogClick"
  >
    <template v-if="inventoryItem">
      <div class="modal-header">
        <h2 :id="titleId" class="modal-title">Inventory Item Details</h2>
        <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
          <svg class="icon" viewBox="0 0 20 20" aria-hidden="true">
            <path d="M15 5L5 15M5 5L15 15" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="item-header">
          <div class="item-icon" :class="getStockIconClass()" aria-hidden="true">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
              <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
              <path d="M16 28H32M16 34H24" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="item-title-section">
            <h3 class="item-name">{{ translateProductName(inventoryItem.name) }}</h3>
            <div class="item-sku">SKU: {{ inventoryItem.sku }}</div>
          </div>
          <span class="badge" :class="getStockStatusClass()">
            {{ getStockStatus() }}
          </span>
        </div>

        <div class="stock-summary">
          <div class="summary-card primary">
            <div class="summary-label">Quantity on Hand</div>
            <div class="summary-value">{{ inventoryItem.quantity_on_hand }} units</div>
          </div>
          <div class="summary-card" :class="getSummaryCardClass()">
            <div class="summary-label">Stock Level</div>
            <div class="summary-value">{{ stockPercentage }}%</div>
            <div class="summary-subtitle">vs. reorder point</div>
          </div>
        </div>

        <dl class="detail-grid">
          <div>
            <dt class="detail-label">Category</dt>
            <dd class="detail-value">{{ inventoryItem.category }}</dd>
          </div>

          <div>
            <dt class="detail-label">Location</dt>
            <dd class="detail-value">{{ inventoryItem.location }}</dd>
          </div>

          <div>
            <dt class="detail-label">Reorder Point</dt>
            <dd class="detail-value">{{ inventoryItem.reorder_point }} units</dd>
          </div>

          <div>
            <dt class="detail-label">Units Remaining</dt>
            <dd class="detail-value" :class="inventoryItem.quantity_on_hand <= inventoryItem.reorder_point ? 'text-danger' : 'text-success'">
              {{ inventoryItem.quantity_on_hand - inventoryItem.reorder_point }} units
            </dd>
          </div>

          <div>
            <dt class="detail-label">Unit Cost</dt>
            <dd class="detail-value">{{ formatCurrencyWithDecimals(inventoryItem.unit_cost, currentCurrency, 2) }}</dd>
          </div>

          <div>
            <dt class="detail-label">Total Value</dt>
            <dd class="detail-value total-value">
              {{ formatCurrencyWithDecimals(totalValue, currentCurrency, 2) }}
            </dd>
          </div>

          <div>
            <dt class="detail-label">Warehouse</dt>
            <dd class="detail-value">{{ translateWarehouse(inventoryItem.location) }}</dd>
          </div>

          <div>
            <dt class="detail-label">Status</dt>
            <dd class="detail-value">
              <span :class="['badge', getStockStatusClass()]">
                {{ getStockStatus() }}
              </span>
            </dd>
          </div>
        </dl>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="close">{{ t('common.close') }}</button>
      </div>
    </template>
  </dialog>
</template>

<script setup>
import { computed, ref, watch, onMounted, useId } from 'vue'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  inventoryItem: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['close'])

const totalValue = computed(() => {
  if (!props.inventoryItem) return 0
  return props.inventoryItem.quantity_on_hand * props.inventoryItem.unit_cost
})

const stockPercentage = computed(() => {
  if (!props.inventoryItem || props.inventoryItem.reorder_point === 0) return 0
  return Math.round((props.inventoryItem.quantity_on_hand / props.inventoryItem.reorder_point) * 100)
})

const titleId = useId()
const dialogEl = ref(null)

// Drive the native dialog from the isOpen prop; showModal() gives focus trap, Escape and inert page for free
watch(() => props.isOpen, (open) => { const d = dialogEl.value; if (!d) return; if (open && !d.open) d.showModal(); else if (!open && d.open) d.close() })
onMounted(() => { if (props.isOpen) dialogEl.value?.showModal() })

// The native 'close' event fires for Escape and dialog.close(); only tell the parent if it still thinks we're open
const onClose = () => { if (props.isOpen) emit('close') }

// Backdrop tap: clicks on the dialog element itself (not its children) are outside the content box
const onDialogClick = (e) => { if (e.target === dialogEl.value) dialogEl.value.close() }

// Footer button closes through the dialog so the native close event drives the parent
const close = () => { dialogEl.value?.close() }

const getStockStatus = () => {
  if (!props.inventoryItem) return 'Unknown'
  if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point) {
    return 'Low Stock'
  } else if (props.inventoryItem.quantity_on_hand <= props.inventoryItem.reorder_point * 1.5) {
    return 'Adequate'
  } else {
    return 'In Stock'
  }
}

const getStockStatusClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger'
  if (status === 'Adequate') return 'warning'
  return 'success'
}

const getStockIconClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger-icon'
  if (status === 'Adequate') return 'warning-icon'
  return 'success-icon'
}

const getSummaryCardClass = () => {
  const status = getStockStatus()
  if (status === 'Low Stock') return 'danger-card'
  if (status === 'Adequate') return 'warning-card'
  return 'success-card'
}
</script>

<style scoped>
.item-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-5);
  padding-block-end: var(--space-6);
  border-block-end: 1px solid var(--color-border);
  margin-block-end: var(--space-6);
}

.item-icon {
  inline-size: 4rem;
  block-size: 4rem;
  border-radius: var(--radius-md);
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

/* Soft tint + status foreground keeps contrast in both themes */
.item-icon.success-icon {
  background: var(--color-success-soft);
  color: var(--color-on-success-soft);
}

.item-icon.warning-icon {
  background: var(--color-warning-soft);
  color: var(--color-on-warning-soft);
}

.item-icon.danger-icon {
  background: var(--color-danger-soft);
  color: var(--color-on-danger-soft);
}

.item-title-section {
  flex: 1;
  min-inline-size: 0;
}

.item-name {
  font-size: var(--text-xl);
  font-weight: 700;
  margin-block-end: var(--space-2);
}

.item-sku {
  font-size: var(--text-base);
  color: var(--color-text-subtle);
  font-family: var(--font-mono);
}

.stock-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(12rem, 100%), 1fr));
  gap: var(--space-4);
  margin-block-end: var(--space-8);
}

.summary-card {
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
}

.summary-card.primary {
  background: var(--color-info-soft);
}

.summary-card.success-card {
  background: var(--color-success-soft);
}

.summary-card.warning-card {
  background: var(--color-warning-soft);
}

.summary-card.danger-card {
  background: var(--color-danger-soft);
}

.summary-label {
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
  margin-block-end: var(--space-2);
}

.summary-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--color-text);
}

.summary-subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  margin-block-start: var(--space-1);
}

.detail-value.total-value {
  font-size: var(--text-lg);
  color: var(--color-primary);
  font-weight: 700;
}

.text-danger {
  color: var(--color-danger);
}

.text-success {
  color: var(--color-success);
}
</style>
