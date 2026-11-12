<template>
  <dialog
    ref="dialogEl"
    class="modal-container"
    :aria-labelledby="titleId"
    @close="onClose"
    @click="onDialogClick"
  >
    <template v-if="costData">
      <div class="modal-header">
        <h2 :id="titleId" class="modal-title">{{ costData.month }} Cost Breakdown</h2>
        <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M15 5L5 15M5 5L15 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <div class="summary-card">
          <div class="summary-label">Total Costs</div>
          <div class="summary-value">{{ currencySymbol }}{{ totalCosts.toLocaleString() }}</div>
        </div>

        <ul class="cost-breakdown" role="list">
          <li v-for="item in costItems" :key="item.key" class="cost-item" :class="item.key">
            <div class="cost-header">
              <div class="cost-icon">
                <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
                  <path v-for="d in item.paths" :key="d" :d="d" />
                </svg>
              </div>
              <div class="cost-info">
                <div class="cost-name">{{ item.label }}</div>
                <div class="cost-amount">{{ currencySymbol }}{{ item.amount.toLocaleString() }}</div>
              </div>
            </div>
            <div class="cost-percentage">{{ item.percentage }}% of total</div>
          </li>
        </ul>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn" @click="close">{{ t('common.close') }}</button>
      </div>
    </template>
  </dialog>
</template>

<script>
import { ref, computed, watch, onMounted, useId } from 'vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'CostDetailModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    },
    costData: {
      type: Object,
      default: null
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const { t, currentCurrency } = useI18n()
    const titleId = useId()
    const dialogEl = ref(null)

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const totalCosts = computed(() => {
      if (!props.costData) return 0
      return props.costData.procurement + props.costData.operational +
             props.costData.labor + props.costData.overhead
    })

    const percentageOf = (value) => {
      if (totalCosts.value === 0) return 0
      return ((value / totalCosts.value) * 100).toFixed(1)
    }

    // Icon path data per category (stroke icons, drawn with the shared .icon class)
    const costItems = computed(() => {
      if (!props.costData) return []
      const data = props.costData
      return [
        {
          key: 'procurement',
          label: 'Procurement',
          amount: data.procurement,
          percentage: percentageOf(data.procurement),
          paths: ['M6 6H18A2 2 0 0 1 20 8V18A2 2 0 0 1 18 20H6A2 2 0 0 1 4 18V8A2 2 0 0 1 6 6Z', 'M8 6V4M16 6V4M4 10H20']
        },
        {
          key: 'operational',
          label: 'Operational',
          amount: data.operational,
          percentage: percentageOf(data.operational),
          paths: ['M12 4A8 8 0 1 0 12 20A8 8 0 1 0 12 4Z', 'M12 8V12L15 15']
        },
        {
          key: 'labor',
          label: 'Labor',
          amount: data.labor,
          percentage: percentageOf(data.labor),
          paths: ['M12 4A4 4 0 1 0 12 12A4 4 0 1 0 12 4Z', 'M6 20C6 16.7 8.7 14 12 14C15.3 14 18 16.7 18 20']
        },
        {
          key: 'overhead',
          label: 'Overhead',
          amount: data.overhead,
          percentage: percentageOf(data.overhead),
          paths: ['M3 12L12 3L21 12', 'M5 10V20H19V10', 'M9 20V14H15V20']
        }
      ]
    })

    // Drive the native dialog from the isOpen prop; showModal() gives focus trap, Escape and inert page for free
    watch(() => props.isOpen, (open) => {
      const d = dialogEl.value
      if (!d) return
      if (open && !d.open) d.showModal()
      else if (!open && d.open) d.close()
    })

    onMounted(() => {
      if (props.isOpen) dialogEl.value?.showModal()
    })

    // The native 'close' event fires for Escape and dialog.close(); only tell the parent if it still thinks we're open
    const onClose = () => {
      if (props.isOpen) emit('close')
    }

    // Backdrop tap: clicks on the dialog element itself (not its children) are outside the content box
    const onDialogClick = (e) => {
      if (e.target === dialogEl.value) dialogEl.value.close()
    }

    const close = () => {
      dialogEl.value?.close()
    }

    return {
      t,
      titleId,
      dialogEl,
      currencySymbol,
      totalCosts,
      costItems,
      onClose,
      onDialogClick,
      close
    }
  }
}
</script>

<style scoped>
.summary-card {
  margin-block-end: var(--space-6);
  padding: var(--space-6);
  border-radius: var(--radius-md);
  text-align: center;
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.summary-label {
  margin-block-end: var(--space-2);
  font-size: var(--text-base);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-value {
  font-size: var(--text-3xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.cost-breakdown {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin: 0;
  padding: 0;
  list-style: none;
}

/* --accent drives the tinted card and icon chip; series match the Spending charts */
.cost-item {
  --accent: var(--chart-1);
  padding: var(--space-5);
  border-radius: var(--radius-md);
  border: 1px solid color-mix(in srgb, var(--accent) 45%, transparent);
  background: color-mix(in srgb, var(--accent) 10%, transparent);
}

.cost-item.procurement { --accent: var(--chart-1); }
.cost-item.operational { --accent: var(--chart-5); }
.cost-item.labor { --accent: var(--chart-2); }
.cost-item.overhead { --accent: var(--chart-3); }

.cost-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-block-end: var(--space-2);
}

.cost-icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  inline-size: 3rem;
  block-size: 3rem;
  border-radius: var(--radius-md);
  background: var(--accent);
  color: var(--color-on-primary);
}

.cost-icon .icon {
  inline-size: 1.5rem;
  block-size: 1.5rem;
  stroke-width: 2;
}

.cost-info {
  flex: 1;
}

.cost-name {
  margin-block-end: var(--space-1);
  font-size: var(--text-md);
  font-weight: 600;
  color: var(--color-text);
}

.cost-amount {
  font-size: var(--text-xl);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
}

.cost-percentage {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-text-subtle);
}
</style>
