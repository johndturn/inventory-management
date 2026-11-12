<template>
  <dialog
    ref="dialogEl"
    class="modal-container"
    :aria-labelledby="titleId"
    @close="onClose"
    @click="onDialogClick"
  >
    <template v-if="product">
      <div class="modal-header">
        <h2 :id="titleId" class="modal-title">Product Details</h2>
        <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="product-header">
          <div class="product-icon">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true">
              <rect x="8" y="12" width="32" height="28" rx="2" stroke="currentColor" stroke-width="2.5"/>
              <path d="M16 8V16M32 8V16M8 20H40" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="product-title-section">
            <p class="product-name">{{ product.name }}</p>
            <div class="product-sku">SKU: {{ product.sku }}</div>
          </div>
          <span :class="['badge', getStockBadgeClass(product.stockLevel)]">
            {{ product.stockLevel }}
          </span>
        </div>

        <dl class="detail-grid">
          <div>
            <dt class="detail-label">Category</dt>
            <dd class="detail-value">{{ product.category }}</dd>
          </div>
          <div>
            <dt class="detail-label">Warehouse</dt>
            <dd class="detail-value">{{ product.warehouse }}</dd>
          </div>
          <div>
            <dt class="detail-label">Units Ordered</dt>
            <dd class="detail-value">{{ product.unitsOrdered }}</dd>
          </div>
          <div>
            <dt class="detail-label">Total Revenue</dt>
            <dd class="detail-value">{{ formatCurrency(product.revenue, currentCurrency) }}</dd>
          </div>
          <div>
            <dt class="detail-label">Current Stock</dt>
            <dd class="detail-value">{{ product.quantityOnHand }} units</dd>
          </div>
          <div>
            <dt class="detail-label">Reorder Point</dt>
            <dd class="detail-value">{{ product.reorderPoint }} units</dd>
          </div>
          <div>
            <dt class="detail-label">First Order Date</dt>
            <dd class="detail-value">
              <time v-if="product.firstOrderDate" :datetime="product.firstOrderDate">{{ formatDate(product.firstOrderDate) }}</time>
              <template v-else>N/A</template>
            </dd>
          </div>
          <div>
            <dt class="detail-label">Stock Status</dt>
            <dd class="detail-value">
              <span :class="['badge', getStockBadgeClass(product.stockLevel)]">
                {{ product.stockLevel }}
              </span>
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
import { formatCurrency } from '../utils/currency'

const { t, currentCurrency } = useI18n()

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  product: {
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

const getStockBadgeClass = (stockLevel) => {
  if (stockLevel === 'In Stock') return 'success'
  if (stockLevel === 'Low Stock') return 'warning'
  if (stockLevel === 'Out of Stock') return 'danger'
  return 'info'
}
</script>

<style scoped>
.product-header {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding-block-end: var(--space-6);
  margin-block-end: var(--space-6);
  border-block-end: 1px solid var(--color-border);
}

.product-icon {
  display: grid;
  place-items: center;
  inline-size: 4rem;
  block-size: 4rem;
  flex-shrink: 0;
  border-radius: var(--radius-md);
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.product-title-section {
  flex: 1;
  min-inline-size: 0;
}

.product-name {
  margin-block-end: var(--space-2);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
}

.product-sku {
  font-size: var(--text-base);
  color: var(--color-text-subtle);
  font-family: var(--font-mono);
}

dd {
  margin: 0;
}
</style>
