<template>
  <div class="restocking">
    <div class="page-header">
      <div>
        <h1>{{ t('restocking.title') }}</h1>
        <p>{{ t('restocking.description') }}</p>
      </div>
    </div>

    <div v-if="initializing" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="initError" class="error">{{ initError }}</div>
    <div v-else>
      <div class="card">
        <div class="slider-block">
          <div class="slider-header">
            <label for="restocking-budget" class="slider-label">{{ t('restocking.budgetSlider') }}</label>
            <span class="slider-value">{{ formatCurrency(budget, currentCurrency) }}</span>
          </div>
          <input
            id="restocking-budget"
            class="budget-slider"
            type="range"
            min="0"
            :max="maxBudget"
            :step="STEP"
            :value="budget"
            :aria-valuetext="formatCurrency(budget, currentCurrency)"
            @input="onSliderInput"
          />
          <div class="slider-bounds">
            <span>{{ formatCurrency(0, currentCurrency) }}</span>
            <span>{{ formatCurrency(maxBudget, currentCurrency) }}</span>
          </div>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.budget') }}</div>
          <div class="stat-value">{{ formatCurrency(budget, currentCurrency) }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('restocking.plannedSpend') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(totalCost, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card success">
          <div class="stat-label">{{ t('restocking.remaining') }}</div>
          <div class="stat-value">{{ formatCurrencyWithDecimals(remainingBudget, currentCurrency, 2) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('restocking.items') }}</div>
          <div class="stat-value">{{ items.length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('restocking.longestLeadTime') }}</div>
          <div class="stat-value">{{ longestLeadTime === null ? '—' : t('restocking.days', { count: longestLeadTime }) }}</div>
        </div>
      </div>

      <div v-if="orderResult" class="alert alert--success" role="status">
        <span>{{ t('restocking.orderSuccess', { orderNumber: orderResult.order_number, date: formatDate(orderResult.expected_delivery) }) }}</span>
        <router-link to="/orders" class="banner-link">{{ t('restocking.viewInOrders') }}</router-link>
      </div>
      <div v-if="orderError" class="error" role="alert">{{ orderError }}</div>
      <div v-if="loadError" class="error" role="alert">{{ loadError }}</div>

      <div class="card card--flush">
        <div class="card-header">
          <h2 class="card-title">
            {{ t('restocking.recommendations') }}
            <span v-if="refreshing || isStale" class="refreshing">{{ t('restocking.refreshing') }}</span>
          </h2>
          <button
            type="button"
            class="btn btn--primary"
            :disabled="items.length === 0 || submitting || refreshing || isStale || orderResult !== null"
            @click="placeOrder"
          >
            {{ submitting ? t('restocking.placingOrder') : t('restocking.placeOrder') }}
          </button>
        </div>

        <div v-if="items.length === 0" class="empty-state">{{ t('restocking.emptyState') }}</div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('restocking.table.sku') }}</th>
                <th scope="col">{{ t('restocking.table.item') }}</th>
                <th scope="col">{{ t('restocking.table.trend') }}</th>
                <th scope="col" class="num">{{ t('restocking.table.forecast') }}</th>
                <th scope="col" class="num">{{ t('restocking.table.recommended') }}</th>
                <th scope="col" class="num">{{ t('restocking.table.unitCost') }}</th>
                <th scope="col" class="num">{{ t('restocking.table.lineTotal') }}</th>
                <th scope="col">{{ t('restocking.table.supplier') }}</th>
                <th scope="col" class="num">{{ t('restocking.table.leadTime') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in items" :key="item.sku">
                <td><strong>{{ item.sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td>
                  <span :class="['badge', trendBadgeClass(item.trend)]">
                    {{ t(`trends.${item.trend}`) }}
                  </span>
                </td>
                <td class="num">{{ item.forecasted_demand.toLocaleString() }}</td>
                <td class="num">
                  <strong>{{ item.recommended_quantity.toLocaleString() }}</strong>
                  <span v-if="item.is_partial" class="partial-tag" :title="t('restocking.partialHint')">{{ t('restocking.partial') }}</span>
                </td>
                <td class="num">{{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</td>
                <td class="num"><strong>{{ formatCurrencyWithDecimals(item.line_total, currentCurrency, 2) }}</strong></td>
                <td>{{ item.supplier }}</td>
                <td class="num">{{ t('restocking.days', { count: item.lead_time_days }) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { api } from '../api'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Restocking forecasts have no warehouse/category mapping, so this page
// intentionally ignores the global FilterBar filters (useFilters is not used).

const STEP = 500
const DEBOUNCE_MS = 250

export default {
  name: 'Restocking',
  setup() {
    const { t, currentCurrency, currentLocale, translateProductName } = useI18n()

    const initializing = ref(true)
    const initError = ref(null)
    const maxBudget = ref(0)
    // Budget is always held in USD; conversion happens only at display time.
    const budget = ref(0)

    const items = ref([])
    const loadedBudget = ref(0) // budget the current `items` were computed for
    const totalCost = ref(0)
    const remainingBudget = ref(0)
    const refreshing = ref(false)
    const loadError = ref(null)

    const submitting = ref(false)
    const orderResult = ref(null)
    const orderError = ref(null)

    // The slider updates `budget` immediately but recommendations are fetched after a
    // debounce, so for a moment the table belongs to an older budget. Treat that window
    // as stale so the user can't place an order for numbers they aren't looking at.
    const isStale = computed(() => budget.value !== loadedBudget.value)

    const longestLeadTime = computed(() => {
      if (items.value.length === 0) return null
      return Math.max(...items.value.map(i => i.lead_time_days))
    })

    // Monotonic request id: the slider can fire several fetches in quick succession
    // and responses may arrive out of order. Only the response belonging to the most
    // recent request may update state, otherwise a slow earlier response could
    // overwrite newer results and show data that doesn't match the slider.
    let latestRequestId = 0
    let debounceTimer = null

    const applyRecommendations = (data) => {
      loadedBudget.value = data.budget
      items.value = data.items
      totalCost.value = data.total_cost
      remainingBudget.value = data.remaining_budget
    }

    const fetchRecommendations = async () => {
      const requestId = ++latestRequestId
      refreshing.value = true
      try {
        const data = await api.getRestockingRecommendations(budget.value)
        if (requestId !== latestRequestId) return // stale response, ignore
        applyRecommendations(data)
        loadError.value = null
      } catch (err) {
        if (requestId !== latestRequestId) return
        loadError.value = t('restocking.loadFailed')
        console.error('Failed to load recommendations:', err)
      } finally {
        if (requestId === latestRequestId) refreshing.value = false
      }
    }

    const onSliderInput = (event) => {
      budget.value = Number(event.target.value)
      // The displayed numbers no longer match a previously placed order's budget.
      orderResult.value = null
      orderError.value = null
      clearTimeout(debounceTimer)
      debounceTimer = setTimeout(fetchRecommendations, DEBOUNCE_MS)
    }

    const placeOrder = async () => {
      if (items.value.length === 0 || submitting.value || isStale.value) return
      submitting.value = true
      orderResult.value = null
      orderError.value = null
      try {
        // Send the budget the displayed items were computed for (not the live slider
        // value, which may be ahead of the table while a debounced fetch is pending);
        // otherwise the server could reject the order as exceeding the budget.
        orderResult.value = await api.createRestockingOrder({
          budget: loadedBudget.value,
          items: items.value.map(i => ({ sku: i.sku, quantity: i.recommended_quantity }))
        })
      } catch (err) {
        // FastAPI 400s carry a string detail; 422 validation errors carry an array of objects
        const detail = err.response?.data?.detail
        orderError.value = typeof detail === 'string' ? detail : t('restocking.orderFailed')
        console.error('Failed to place order:', err)
      } finally {
        submitting.value = false
      }
    }

    const trendBadgeClass = (trend) => {
      const map = { increasing: 'success', stable: 'info', decreasing: 'danger' }
      return map[trend] || 'info'
    }

    const formatDate = (dateString) => {
      // JS parses a bare "YYYY-MM-DD" as UTC midnight, which renders as the previous
      // day in timezones west of UTC. Pin date-only strings to local midnight instead.
      const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(dateString)
      const date = new Date(isDateOnly ? `${dateString}T00:00:00` : dateString)
      if (isNaN(date.getTime())) return dateString
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, { year: 'numeric', month: 'short', day: 'numeric' })
    }

    const init = async () => {
      try {
        // A zero budget returns no items but still reports full_cost, which
        // defines the slider range.
        const probe = await api.getRestockingRecommendations(0)
        // Round up to the next 1000 (at least 1000 so the slider is never degenerate).
        maxBudget.value = Math.max(1000, Math.ceil(probe.full_cost / 1000) * 1000)
        // Default to half the range, snapped to the slider step.
        budget.value = Math.round(maxBudget.value / 2 / STEP) * STEP
        initializing.value = false
        await fetchRecommendations()
      } catch (err) {
        initError.value = t('restocking.loadFailed')
        console.error('Failed to initialize restocking:', err)
        initializing.value = false
      }
    }

    onMounted(init)
    onBeforeUnmount(() => clearTimeout(debounceTimer))

    return {
      t,
      STEP,
      currentCurrency,
      translateProductName,
      formatCurrency,
      formatCurrencyWithDecimals,
      formatDate,
      trendBadgeClass,
      initializing,
      initError,
      maxBudget,
      budget,
      items,
      totalCost,
      remainingBudget,
      refreshing,
      isStale,
      loadError,
      longestLeadTime,
      submitting,
      orderResult,
      orderError,
      onSliderInput,
      placeOrder
    }
  }
}
</script>

<style scoped>
.slider-block {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.slider-header {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: baseline;
  gap: var(--space-2);
}

.slider-label {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.slider-value {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  font-variant-numeric: tabular-nums;
}

.budget-slider {
  inline-size: 100%;
  accent-color: var(--color-primary);
  cursor: pointer;
}

.slider-bounds {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
}

.num {
  white-space: nowrap;
}

.partial-tag {
  display: inline-block;
  margin-inline-start: var(--space-2);
  padding: 0.125rem var(--space-2);
  border-radius: var(--radius-sm);
  background: var(--color-warning-soft);
  color: var(--color-on-warning-soft);
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.refreshing {
  margin-inline-start: var(--space-3);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text-subtle);
}

.alert .banner-link {
  color: inherit;
  font-weight: 600;
  text-decoration: underline;
  white-space: nowrap;
}
</style>
