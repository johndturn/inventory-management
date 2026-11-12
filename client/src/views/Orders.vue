<template>
  <div class="orders">
    <div class="page-header">
      <div>
        <h1>{{ t('orders.title') }}</h1>
        <p>{{ t('orders.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="stats-grid">
        <div class="stat-card success">
          <div class="stat-label">{{ t('status.delivered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Delivered').length }}</div>
        </div>
        <div class="stat-card info">
          <div class="stat-label">{{ t('status.shipped') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Shipped').length }}</div>
        </div>
        <div class="stat-card warning">
          <div class="stat-label">{{ t('status.processing') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Processing').length }}</div>
        </div>
        <div class="stat-card danger">
          <div class="stat-label">{{ t('status.backordered') }}</div>
          <div class="stat-value">{{ getOrdersByStatus('Backordered').length }}</div>
        </div>
      </div>

      <div class="card card--flush">
        <div class="card-header">
          <h2 class="card-title">{{ t('orders.submittedOrders.title') }} ({{ restockingOrders.length }})</h2>
        </div>
        <div v-if="restockingError" class="error">{{ restockingError }}</div>
        <div v-else-if="restockingOrders.length === 0" class="empty-state">
          {{ t('orders.submittedOrders.empty') }}
          <router-link to="/restocking" class="empty-link">{{ t('orders.submittedOrders.goToRestocking') }}</router-link>
        </div>
        <div v-else class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th scope="col" class="col-order-number">{{ t('orders.submittedOrders.orderNumber') }}</th>
                <th scope="col" class="col-date">{{ t('orders.submittedOrders.submitted') }}</th>
                <th scope="col" class="col-items">{{ t('orders.submittedOrders.items') }}</th>
                <th scope="col" class="col-value num">{{ t('orders.submittedOrders.total') }}</th>
                <th scope="col" class="col-date">{{ t('orders.submittedOrders.leadTime') }}</th>
                <th scope="col" class="col-date">{{ t('orders.submittedOrders.expectedDelivery') }}</th>
                <th scope="col" class="col-status">{{ t('orders.submittedOrders.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in restockingOrders" :key="order.id">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-date"><time :datetime="order.submitted_date">{{ formatDate(order.submitted_date) }}</time></td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-list">
                      <div v-for="item in order.items" :key="item.sku" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.item_name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ formatCurrencyWithDecimals(item.unit_cost, currentCurrency, 2) }}</span>
                        <span class="item-meta">{{ item.supplier }} · {{ t('orders.submittedOrders.days', { count: item.lead_time_days }) }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-value num"><strong>{{ formatCurrency(order.total_cost, currentCurrency) }}</strong></td>
                <td class="col-date">{{ t('orders.submittedOrders.days', { count: order.lead_time_days }) }}</td>
                <td class="col-date"><time :datetime="order.expected_delivery">{{ formatDate(order.expected_delivery) }}</time></td>
                <td class="col-status">
                  <span class="badge info">{{ t('orders.submittedOrders.statusSubmitted') }}</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="card card--flush">
        <div class="card-header">
          <h2 class="card-title">{{ t('orders.allOrders') }} ({{ orders.length }})</h2>
        </div>
        <div class="table-container">
          <table class="orders-table">
            <thead>
              <tr>
                <th scope="col" class="col-order-number">{{ t('orders.table.orderNumber') }}</th>
                <th scope="col" class="col-customer">{{ t('orders.table.customer') }}</th>
                <th scope="col" class="col-items">{{ t('orders.table.items') }}</th>
                <th scope="col" class="col-status">{{ t('orders.table.status') }}</th>
                <th scope="col" class="col-date">{{ t('orders.table.orderDate') }}</th>
                <th scope="col" class="col-date">{{ t('orders.table.expectedDelivery') }}</th>
                <th scope="col" class="col-value num">{{ t('orders.table.totalValue') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="order in orders" :key="order.id">
                <td class="col-order-number"><strong>{{ order.order_number }}</strong></td>
                <td class="col-customer">{{ translateCustomerName(order.customer) }}</td>
                <td class="col-items">
                  <details class="items-details">
                    <summary class="items-summary">
                      {{ t('orders.itemsCount', { count: order.items.length }) }}
                    </summary>
                    <div class="items-list">
                      <!-- An order can list the same SKU twice, so sku alone is not unique; position disambiguates -->
                      <div v-for="(item, idx) in order.items" :key="`${item.sku}-${idx}`" class="item-entry">
                        <span class="item-name">{{ translateProductName(item.name) }}</span>
                        <span class="item-meta">{{ t('orders.quantity') }}: {{ item.quantity }} @ {{ formatCurrencyWithDecimals(item.unit_price, currentCurrency, 2) }}</span>
                      </div>
                    </div>
                  </details>
                </td>
                <td class="col-status">
                  <span :class="['badge', getOrderStatusClass(order.status)]">
                    {{ t(`status.${order.status.toLowerCase()}`) }}
                  </span>
                </td>
                <td class="col-date"><time :datetime="order.order_date">{{ formatDate(order.order_date) }}</time></td>
                <td class="col-date"><time :datetime="order.expected_delivery">{{ formatDate(order.expected_delivery) }}</time></td>
                <td class="col-value num"><strong>{{ formatCurrencyWithDecimals(order.total_value, currentCurrency, 2) }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

export default {
  name: 'Orders',
  setup() {
    const { t, currentCurrency, translateProductName, translateCustomerName } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const orders = ref([])
    const restockingOrders = ref([])
    const restockingError = ref(null)

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const loadOrders = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        const fetchedOrders = await api.getOrders(filters)

        // Sort orders by order_date (earliest first)
        orders.value = fetchedOrders.sort((a, b) => {
          const dateA = new Date(a.order_date)
          const dateB = new Date(b.order_date)
          return dateA - dateB
        })
      } catch (err) {
        error.value = 'Failed to load orders: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadOrders()
    })

    const getOrdersByStatus = (status) => {
      return orders.value.filter(order => order.status === status)
    }

    const getOrderStatusClass = (status) => {
      const statusMap = {
        'Delivered': 'success',
        'Shipped': 'info',
        'Processing': 'warning',
        'Backordered': 'danger'
      }
      return statusMap[status] || 'info'
    }

    const formatDate = (dateString) => {
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      // JS parses a bare "YYYY-MM-DD" (restocking orders) as UTC midnight, which renders
      // as the previous day west of UTC. Pin date-only strings to local midnight instead.
      const isDateOnly = /^\d{4}-\d{2}-\d{2}$/.test(dateString)
      const date = new Date(isDateOnly ? `${dateString}T00:00:00` : dateString)
      if (isNaN(date.getTime())) return dateString || ''
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    }

    // Restocking orders are loaded once and deliberately NOT reloaded on global
    // filter changes: they have no warehouse/status/month, so those filters don't apply.
    // Errors are kept local so a failure here never breaks the main orders table.
    const loadRestockingOrders = async () => {
      try {
        restockingError.value = null
        restockingOrders.value = await api.getRestockingOrders()
      } catch (err) {
        restockingError.value = t('orders.submittedOrders.loadFailed')
        console.error('Failed to load restocking orders:', err)
      }
    }

    onMounted(() => {
      loadOrders()
      loadRestockingOrders()
    })

    return {
      t,
      loading,
      error,
      orders,
      getOrdersByStatus,
      getOrderStatusClass,
      formatDate,
      currentCurrency,
      restockingOrders,
      restockingError,
      formatCurrency,
      formatCurrencyWithDecimals,
      translateProductName,
      translateCustomerName
    }
  }
}
</script>

<style scoped>
/* Fixed layout keeps columns from shifting; the min width makes the container
   scroll sideways on narrow screens instead of crushing the columns */
.orders-table {
  table-layout: fixed;
  inline-size: 100%;
  min-inline-size: 64rem;
}

.col-order-number { inline-size: 8.5rem; }
.col-customer { inline-size: 11rem; }
.col-items { inline-size: 14rem; }
.col-status { inline-size: 8.5rem; }
.col-date { inline-size: 9rem; }
.col-value { inline-size: 8rem; }

.items-summary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  color: var(--color-primary);
  font-weight: 500;
  list-style: none;
  user-select: none;
}

.items-summary::-webkit-details-marker {
  display: none;
}

/* Border chevron; rotates when open */
.items-summary::before {
  content: '';
  inline-size: 0.4rem;
  block-size: 0.4rem;
  border-inline-end: 2px solid currentColor;
  border-block-end: 2px solid currentColor;
  rotate: -45deg;
  transition: rotate var(--duration) var(--ease-out);
}

.items-details[open] .items-summary::before {
  rotate: 45deg;
}

.items-summary:hover {
  text-decoration: underline;
}

.items-summary:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
  border-radius: 2px;
}

/* Expands in normal flow inside the cell. A floating dropdown (position:absolute;
   top:100%) is clipped by .table-container's overflow, so the list grows the row
   instead - no JS, no anchor positioning, nothing to clip. */
.items-list {
  margin-block-start: var(--space-2);
  padding: var(--space-1) var(--space-2);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
}

.item-entry {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-2);
  border-block-end: 1px solid var(--color-border);
  white-space: normal;
}

.item-entry:last-child {
  border-block-end: none;
}

.item-name {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-text);
}

.item-meta {
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
}

.empty-link {
  margin-inline-start: var(--space-2);
  color: var(--color-primary);
  font-weight: 500;
}
</style>
