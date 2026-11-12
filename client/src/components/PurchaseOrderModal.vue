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
        <h2 :id="titleId" class="modal-title">
          {{ mode === 'view' ? t('purchaseOrder.viewTitle') : t('purchaseOrder.createTitle') }}
        </h2>
        <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- Create mode -->
      <form v-if="mode === 'create'" novalidate @submit.prevent="submit">
        <div class="modal-body">
          <dl class="detail-grid po-context">
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.item') }}</dt>
              <dd class="detail-value">{{ translateProductName(backlogItem.item_name) }} ({{ backlogItem.item_sku }})</dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.shortage') }}</dt>
              <dd class="detail-value">{{ shortage }}</dd>
            </div>
          </dl>

          <div class="po-form">
            <div class="field">
              <label :for="ids.supplier">{{ t('purchaseOrder.supplier') }} *</label>
              <input
                :id="ids.supplier"
                v-model="form.supplier"
                type="text"
                class="input"
                required
                maxlength="200"
                :placeholder="t('purchaseOrder.supplierPlaceholder')"
              />
            </div>

            <div class="po-row">
              <div class="field">
                <label :for="ids.quantity">{{ t('purchaseOrder.quantity') }} *</label>
                <input :id="ids.quantity" v-model.number="form.quantity" type="number" class="input" min="1" step="1" required />
              </div>
              <div class="field">
                <label :for="ids.unitCost">{{ t('purchaseOrder.unitCost') }} (USD) *</label>
                <input :id="ids.unitCost" v-model.number="form.unitCost" type="number" class="input" min="0.01" step="0.01" required />
              </div>
            </div>

            <div class="field">
              <label :for="ids.date">{{ t('purchaseOrder.expectedDelivery') }} *</label>
              <input :id="ids.date" v-model="form.expectedDelivery" type="date" class="input" :min="today" required />
            </div>

            <div class="field">
              <label :for="ids.notes">{{ t('purchaseOrder.notes') }}</label>
              <textarea
                :id="ids.notes"
                v-model="form.notes"
                class="input po-notes"
                rows="3"
                maxlength="1000"
                :placeholder="t('purchaseOrder.notesPlaceholder')"
              ></textarea>
            </div>

            <div class="po-total">
              <span class="detail-label">{{ t('purchaseOrder.total') }}</span>
              <strong>{{ formatCurrencyWithDecimals(total, currentCurrency, 2) }}</strong>
            </div>

            <div v-if="submitError" class="error" role="alert">{{ submitError }}</div>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
          <button type="submit" class="btn btn--primary" :disabled="submitting || !isValid">
            {{ submitting ? t('purchaseOrder.submitting') : t('purchaseOrder.submit') }}
          </button>
        </div>
      </form>

      <!-- View mode -->
      <template v-else>
        <div class="modal-body">
          <div v-if="loadingPO" class="loading">{{ t('purchaseOrder.loading') }}</div>
          <div v-else-if="loadError" class="error" role="alert">{{ loadError }}</div>
          <dl v-else-if="po" class="detail-grid">
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.poNumber') }}</dt>
              <dd class="detail-value">{{ po.id }}</dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.status') }}</dt>
              <dd class="detail-value"><span class="badge warning">{{ statusLabel }}</span></dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.supplier') }}</dt>
              <dd class="detail-value">{{ po.supplier_name }}</dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.quantity') }}</dt>
              <dd class="detail-value">{{ po.quantity }}</dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.unitCost') }}</dt>
              <dd class="detail-value">{{ formatCurrencyWithDecimals(po.unit_cost, currentCurrency, 2) }}</dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.total') }}</dt>
              <dd class="detail-value">{{ formatCurrencyWithDecimals(po.quantity * po.unit_cost, currentCurrency, 2) }}</dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.expectedDelivery') }}</dt>
              <dd class="detail-value">{{ formatDate(po.expected_delivery_date) }}</dd>
            </div>
            <div>
              <dt class="detail-label">{{ t('purchaseOrder.createdDate') }}</dt>
              <dd class="detail-value">{{ formatDate(po.created_date) }}</dd>
            </div>
            <div v-if="po.notes">
              <dt class="detail-label">{{ t('purchaseOrder.notes') }}</dt>
              <dd class="detail-value">{{ po.notes }}</dd>
            </div>
          </dl>
        </div>

        <div class="modal-footer">
          <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
        </div>
      </template>
    </template>
  </dialog>
</template>

<script>
import { computed, reactive, ref, watch, onMounted, useId } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

// Local (not UTC) YYYY-MM-DD, so "today" matches the user's calendar day
const localToday = () => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export default {
  name: 'PurchaseOrderModal',
  props: {
    isOpen: { type: Boolean, default: false },
    backlogItem: { type: Object, default: null },
    mode: { type: String, default: 'create' }
  },
  emits: ['close', 'po-created'],
  setup(props, { emit }) {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const titleId = useId()
    const baseId = useId()
    const ids = {
      supplier: `${baseId}-supplier`,
      quantity: `${baseId}-quantity`,
      unitCost: `${baseId}-unit-cost`,
      date: `${baseId}-date`,
      notes: `${baseId}-notes`
    }
    const dialogEl = ref(null)

    const today = ref(localToday())
    const form = reactive({ supplier: '', quantity: 1, unitCost: null, expectedDelivery: '', notes: '' })
    const submitting = ref(false)
    const submitError = ref(null)

    const po = ref(null)
    const loadingPO = ref(false)
    const loadError = ref(null)

    const shortage = computed(() => {
      if (!props.backlogItem) return 0
      return Math.max(props.backlogItem.quantity_needed - props.backlogItem.quantity_available, 1)
    })

    const total = computed(() => {
      const q = Number(form.quantity)
      const c = Number(form.unitCost)
      return Number.isFinite(q) && Number.isFinite(c) ? q * c : 0
    })

    const isValid = computed(() =>
      form.supplier.trim().length > 0 &&
      Number.isInteger(form.quantity) && form.quantity >= 1 &&
      typeof form.unitCost === 'number' && form.unitCost >= 0.01 &&
      form.expectedDelivery !== '' && form.expectedDelivery >= today.value
    )

    const statusLabel = computed(() =>
      po.value?.status === 'Pending' ? t('purchaseOrder.statusPending') : (po.value?.status || '')
    )

    const resetForm = () => {
      today.value = localToday()
      form.supplier = ''
      form.quantity = shortage.value
      form.unitCost = null
      form.expectedDelivery = ''
      form.notes = ''
      submitting.value = false
      submitError.value = null
    }

    const loadPO = async () => {
      po.value = null
      loadError.value = null
      loadingPO.value = true
      try {
        po.value = await api.getPurchaseOrderByBacklogItem(props.backlogItem.id)
      } catch (err) {
        loadError.value = t('purchaseOrder.loadFailed')
      } finally {
        loadingPO.value = false
      }
    }

    // Reset or fetch each time the modal opens
    const onOpen = () => {
      if (!props.backlogItem) return
      if (props.mode === 'view') loadPO()
      else resetForm()
    }

    // Drive the native dialog from isOpen; showModal() gives focus trap, Escape and inert page
    watch(() => props.isOpen, (open) => {
      if (open) onOpen()
      const d = dialogEl.value
      if (!d) return
      if (open && !d.open) d.showModal()
      else if (!open && d.open) d.close()
    })
    onMounted(() => {
      if (props.isOpen) {
        onOpen()
        dialogEl.value?.showModal()
      }
    })

    // Native 'close' fires for Escape and dialog.close(); only tell the parent if it still thinks we're open
    const onClose = () => { if (props.isOpen) emit('close') }

    // Backdrop click: target is the dialog itself, not its children
    const onDialogClick = (e) => { if (e.target === dialogEl.value) dialogEl.value.close() }

    const close = () => { dialogEl.value?.close() }

    const submit = async () => {
      if (!isValid.value || submitting.value) return
      submitting.value = true
      submitError.value = null
      try {
        // Unit cost is sent in USD regardless of display currency
        const created = await api.createPurchaseOrder({
          backlog_item_id: props.backlogItem.id,
          supplier_name: form.supplier.trim(),
          quantity: form.quantity,
          unit_cost: form.unitCost,
          expected_delivery_date: form.expectedDelivery,
          notes: form.notes.trim() || null
        })
        emit('po-created', created)
        close()
      } catch (err) {
        const detail = err.response?.data?.detail
        submitError.value = typeof detail === 'string' ? detail : t('purchaseOrder.createFailed')
      } finally {
        submitting.value = false
      }
    }

    // Parse YYYY-MM-DD as local midnight; new Date('YYYY-MM-DD') is UTC and shows the previous day in the Americas
    const formatDate = (value) => {
      if (!value) return '-'
      const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value)
      if (isNaN(date.getTime())) return '-'
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric', month: 'long', day: 'numeric'
      })
    }

    return {
      t, currentCurrency, translateProductName, formatCurrencyWithDecimals,
      titleId, ids, dialogEl, today, form, submitting, submitError,
      po, loadingPO, loadError, shortage, total, isValid, statusLabel,
      onClose, onDialogClick, close, submit, formatDate
    }
  }
}
</script>

<style scoped>
dd {
  margin: 0;
}

.po-context {
  margin-block-end: var(--space-5);
}

.po-form {
  display: grid;
  gap: var(--space-4);
}

.po-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(10rem, 100%), 1fr));
  gap: var(--space-4);
}

.po-notes {
  padding-block: var(--space-2);
  resize: vertical;
}

.po-total {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-block-start: var(--space-3);
  border-block-start: 1px solid var(--color-border);
  font-size: var(--text-lg);
  color: var(--color-text);
}
</style>
