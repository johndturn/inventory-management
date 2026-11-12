<template>
  <dialog
    ref="dialogEl"
    class="modal-container"
    :aria-labelledby="titleId"
    @close="onClose"
    @click="onDialogClick"
  >
    <template v-if="transaction">
      <div class="modal-header">
        <h2 :id="titleId" class="modal-title">{{ t('transactionDetails.title') }}</h2>
        <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <dl class="detail-grid">
          <div>
            <dt class="detail-label">{{ t('transactionDetails.id') }}</dt>
            <dd class="detail-value">{{ transaction.id }}</dd>
          </div>
          <div>
            <dt class="detail-label">{{ t('transactionDetails.description') }}</dt>
            <dd class="detail-value">{{ transaction.description }}</dd>
          </div>
          <div>
            <dt class="detail-label">{{ t('transactionDetails.vendor') }}</dt>
            <dd class="detail-value">{{ transaction.vendor }}</dd>
          </div>
          <div>
            <dt class="detail-label">{{ t('transactionDetails.category') }}</dt>
            <dd class="detail-value">{{ transaction.category || '-' }}</dd>
          </div>
          <div>
            <dt class="detail-label">{{ t('transactionDetails.warehouse') }}</dt>
            <dd class="detail-value">{{ transaction.warehouse || '-' }}</dd>
          </div>
          <div>
            <dt class="detail-label">{{ t('transactionDetails.type') }}</dt>
            <dd class="detail-value">{{ transaction.type || '-' }}</dd>
          </div>
          <div>
            <dt class="detail-label">{{ t('transactionDetails.date') }}</dt>
            <dd class="detail-value">
              <time :datetime="transaction.date">{{ formattedDate }}</time>
            </dd>
          </div>
          <div>
            <dt class="detail-label">{{ t('transactionDetails.amount') }}</dt>
            <dd class="detail-value">{{ formattedAmount }}</dd>
          </div>
        </dl>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn-secondary" @click="close">{{ t('common.close') }}</button>
      </div>
    </template>
  </dialog>
</template>

<script>
import { computed, ref, watch, onMounted, useId } from 'vue'
import { useI18n } from '../composables/useI18n'
import { formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'TransactionDetailModal',
  props: {
    isOpen: { type: Boolean, default: false },
    transaction: { type: Object, default: null }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const { t, currentCurrency, currentLocale } = useI18n()
    const titleId = useId()
    const dialogEl = ref(null)

    // Drive the native dialog from isOpen; showModal() gives focus trap, Escape and inert page
    watch(() => props.isOpen, (open) => {
      const d = dialogEl.value
      if (!d) return
      if (open && !d.open) d.showModal()
      else if (!open && d.open) d.close()
    })
    onMounted(() => { if (props.isOpen) dialogEl.value?.showModal() })

    // Native 'close' fires for Escape and dialog.close(); only tell the parent if it still thinks we're open
    const onClose = () => { if (props.isOpen) emit('close') }

    // Backdrop click: target is the dialog itself, not its children
    const onDialogClick = (e) => { if (e.target === dialogEl.value) dialogEl.value.close() }

    const close = () => { dialogEl.value?.close() }

    const formattedAmount = computed(() => {
      const amount = Number(props.transaction?.amount)
      return Number.isFinite(amount) ? formatCurrencyWithDecimals(amount, currentCurrency.value, 2) : '-'
    })

    // Parse YYYY-MM-DD as local midnight to avoid the UTC off-by-one
    const formattedDate = computed(() => {
      const value = props.transaction?.date
      if (!value) return '-'
      const date = new Date(/^\d{4}-\d{2}-\d{2}$/.test(value) ? `${value}T00:00:00` : value)
      if (isNaN(date.getTime())) return '-'
      return date.toLocaleDateString(currentLocale.value === 'ja' ? 'ja-JP' : 'en-US', {
        year: 'numeric', month: 'long', day: 'numeric'
      })
    })

    return { t, titleId, dialogEl, onClose, onDialogClick, close, formattedAmount, formattedDate }
  }
}
</script>

<style scoped>
dd {
  margin: 0;
}
</style>
