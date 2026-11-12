<template>
  <div class="spending">
    <div class="page-header">
      <div>
        <h1>{{ t('finance.title') }}</h1>
        <p>{{ t('finance.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Revenue & Financial KPIs -->
      <div class="stats-grid">
        <div class="stat-card revenue-card">
          <div class="stat-label">{{ t('finance.totalRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.totalRevenue) }}</div>
          <div class="stat-change positive">
            <span class="change-icon" aria-hidden="true">↑</span>
            {{ t('finance.fromOrders', { count: revenueMetrics.orderCount }) }}
          </div>
        </div>
        <div class="stat-card cost-card">
          <div class="stat-label">{{ t('finance.totalCosts') }}</div>
          <div class="stat-value">{{ formatCurrency(totalCosts) }}</div>
          <div class="stat-meta">{{ t('finance.costBreakdown') }}</div>
        </div>
        <div class="stat-card profit-card">
          <div class="stat-label">{{ t('finance.netProfit') }}</div>
          <div class="stat-value">{{ formatCurrency(netProfit) }}</div>
          <div class="stat-meta">{{ profitMargin }}% {{ t('finance.margin') }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('finance.avgOrderValue') }}</div>
          <div class="stat-value">{{ formatCurrency(revenueMetrics.avgOrderValue) }}</div>
          <div class="stat-meta">{{ t('finance.perOrderRevenue') }}</div>
        </div>
      </div>

      <!-- Monthly Revenue vs Cost Chart -->
      <section class="card" aria-labelledby="revenue-costs-title">
        <div class="card-header">
          <h2 id="revenue-costs-title" class="card-title">{{ t('finance.revenueVsCosts.title') }}</h2>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot revenue-color"></span>{{ t('finance.revenueVsCosts.revenue') }}</span>
            <span class="legend-item"><span class="legend-dot cost-color"></span>{{ t('finance.revenueVsCosts.costs') }}</span>
          </div>
        </div>
        <div class="chart-container">
          <div class="bar-chart" role="img" :aria-label="t('finance.revenueVsCosts.title')">
            <div class="y-axis" aria-hidden="true">
              <span>{{ currencySymbol }}{{ maxRevenueValue }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.75) }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.5) }}K</span>
              <span>{{ currencySymbol }}{{ Math.round(maxRevenueValue * 0.25) }}K</span>
              <span>{{ currencySymbol }}0</span>
            </div>
            <div class="chart-area">
              <div v-for="month in monthlyRevenue" :key="month.month" class="bar-group-revenue">
                <div class="revenue-bars">
                  <div class="revenue-bar" :style="{ height: getRevenueBarHeight(month.revenue) + '%' }" :title="`Revenue: ${currencySymbol}${month.revenue.toLocaleString()}`"></div>
                  <div class="cost-bar" :style="{ height: getRevenueBarHeight(month.costs) + '%' }" :title="`Costs: ${currencySymbol}${month.costs.toLocaleString()}`"></div>
                </div>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Monthly Cost Flow Chart -->
      <section class="card" aria-labelledby="cost-flow-title">
        <div class="card-header">
          <h2 id="cost-flow-title" class="card-title">{{ t('finance.monthlyCostFlow.title') }}</h2>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot procurement"></span>{{ t('finance.monthlyCostFlow.procurement') }}</span>
            <span class="legend-item"><span class="legend-dot operational"></span>{{ t('finance.monthlyCostFlow.operational') }}</span>
            <span class="legend-item"><span class="legend-dot labor"></span>{{ t('finance.monthlyCostFlow.labor') }}</span>
            <span class="legend-item"><span class="legend-dot overhead"></span>{{ t('finance.monthlyCostFlow.overhead') }}</span>
          </div>
        </div>
        <div class="chart-container">
          <!-- role="group", not "img": each month's stacked bar is a button and must stay exposed -->
          <div class="bar-chart" role="group" :aria-label="t('finance.monthlyCostFlow.title')">
            <div class="y-axis" aria-hidden="true">
              <span>{{ currencySymbol }}25K</span>
              <span>{{ currencySymbol }}20K</span>
              <span>{{ currencySymbol }}15K</span>
              <span>{{ currencySymbol }}10K</span>
              <span>{{ currencySymbol }}5K</span>
              <span>{{ currencySymbol }}0</span>
            </div>
            <div class="chart-area">
              <div v-for="month in monthlySpending" :key="month.month" class="bar-group">
                <button
                  type="button"
                  class="stacked-bar"
                  :aria-label="`${translateMonth(month.month)} - ${t('finance.monthlyCostFlow.title')}`"
                  @click="showCostDetail(month)"
                >
                  <span class="bar-segment procurement" :style="{ height: getBarHeight(month.procurement) + '%' }" :title="`Procurement: ${currencySymbol}${month.procurement.toLocaleString()}`"></span>
                  <span class="bar-segment operational" :style="{ height: getBarHeight(month.operational) + '%' }" :title="`Operational: ${currencySymbol}${month.operational.toLocaleString()}`"></span>
                  <span class="bar-segment labor" :style="{ height: getBarHeight(month.labor) + '%' }" :title="`Labor: ${currencySymbol}${month.labor.toLocaleString()}`"></span>
                  <span class="bar-segment overhead" :style="{ height: getBarHeight(month.overhead) + '%' }" :title="`Overhead: ${currencySymbol}${month.overhead.toLocaleString()}`"></span>
                </button>
                <span class="bar-label">{{ translateMonth(month.month) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="grid-2">
        <!-- Category Spending Breakdown -->
        <section class="card" aria-labelledby="category-title">
          <div class="card-header">
            <h2 id="category-title" class="card-title">{{ t('finance.categorySpending.title') }}</h2>
          </div>
          <div class="category-list">
            <div v-for="category in categorySpending" :key="category.category" class="category-item">
              <div class="category-info">
                <div class="category-name">{{ translateCategory(category.category) }}</div>
                <div class="category-amount">{{ currencySymbol }}{{ category.amount.toLocaleString() }}</div>
              </div>
              <div class="category-bar-container">
                <div class="category-bar" :style="{ width: category.percentage + '%' }"></div>
              </div>
              <div class="category-meta">
                <span class="percentage">{{ category.percentage }}% {{ t('finance.categorySpending.ofTotal') }}</span>
                <span class="change" :class="{ positive: category.change > 0, negative: category.change < 0 }">
                  {{ category.change > 0 ? '+' : '' }}{{ category.change }}%
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- Recent Transactions -->
        <section class="card card--flush" aria-labelledby="transactions-title">
          <div class="card-header">
            <h2 id="transactions-title" class="card-title">{{ t('finance.transactions.title') }}</h2>
          </div>
          <div class="table-container transactions-scroll">
            <table class="table--sticky-first">
              <thead>
                <tr>
                  <th scope="col">{{ t('finance.transactions.id') }}</th>
                  <th scope="col">{{ t('finance.transactions.description') }}</th>
                  <th scope="col">{{ t('finance.transactions.vendor') }}</th>
                  <th scope="col">{{ t('finance.transactions.date') }}</th>
                  <th scope="col" class="num">{{ t('finance.transactions.amount') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="transaction in recentTransactions" :key="transaction.id">
                  <td class="transaction-id">
                    <button type="button" class="row-link" @click="handleTransactionClick(transaction)">
                      {{ transaction.id.toString().padStart(3, '0') }}
                    </button>
                  </td>
                  <td class="transaction-description">{{ transaction.description }}</td>
                  <td>{{ transaction.vendor }}</td>
                  <td class="transaction-date"><time :datetime="transaction.date">{{ formatDateShort(transaction.date) }}</time></td>
                  <td class="num transaction-amount">{{ currencySymbol }}{{ transaction.amount.toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>

    <CostDetailModal
      :is-open="showCostModal"
      :cost-data="selectedCostData"
      @close="showCostModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency as formatCurrencyUtil } from '../utils/currency'
import CostDetailModal from '../components/CostDetailModal.vue'

export default {
  name: 'Spending',
  components: {
    CostDetailModal
  },
  setup() {
    const { t, currentCurrency } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allMonthlySpending = ref([])
    const allCategorySpending = ref([])
    const allTransactions = ref([])
    const summaryData = ref({})
    const allOrders = ref([])

    // Modal state
    const showCostModal = ref(false)
    const selectedCostData = ref(null)

    // Use shared filters
    const { selectedPeriod, getCurrentFilters } = useFilters()

    // Monthly spending chart always shows all months (not filtered)
    const monthlySpending = computed(() => {
      return allMonthlySpending.value
    })

    // Filtered monthly spending for summary calculations only
    const filteredMonthlySpending = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allMonthlySpending.value
      }

      // Extract month name from YYYY-MM format
      const monthMap = {
        '01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
        '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
        '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'
      }
      const selectedMonth = monthMap[selectedPeriod.value.split('-')[1]]
      return allMonthlySpending.value.filter(m => m.month === selectedMonth)
    })

    const categorySpending = computed(() => {
      return allCategorySpending.value
    })

    const recentTransactions = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allTransactions.value
      }
      // Filter transactions by selected month
      return allTransactions.value.filter(t => {
        const transactionMonth = new Date(t.date).toISOString().slice(0, 7)
        return transactionMonth === selectedPeriod.value
      })
    })

    const summary = computed(() => {
      // Recalculate summary based on filteredMonthlySpending (not the chart data)
      if (filteredMonthlySpending.value.length === 0) {
        return summaryData.value
      }

      const totals = filteredMonthlySpending.value.reduce((acc, month) => ({
        procurement: acc.procurement + month.procurement,
        operational: acc.operational + month.operational,
        labor: acc.labor + month.labor,
        overhead: acc.overhead + month.overhead
      }), { procurement: 0, operational: 0, labor: 0, overhead: 0 })

      return {
        total_procurement_cost: totals.procurement,
        total_operational_cost: totals.operational,
        total_labor_cost: totals.labor,
        total_overhead: totals.overhead,
        procurement_change: summaryData.value.procurement_change || 0,
        operational_change: summaryData.value.operational_change || 0,
        labor_change: summaryData.value.labor_change || 0,
        overhead_change: summaryData.value.overhead_change || 0
      }
    })

    // Filtered orders based on selected period
    const filteredOrders = computed(() => {
      if (selectedPeriod.value === 'all') {
        return allOrders.value
      }

      // Filter orders by selected month
      return allOrders.value.filter(order => {
        const orderMonth = new Date(order.order_date).toISOString().slice(0, 7)
        return orderMonth === selectedPeriod.value
      })
    })

    // Revenue metrics from filtered orders
    const revenueMetrics = computed(() => {
      const totalRevenue = filteredOrders.value.reduce((sum, order) => sum + (order.total_value || 0), 0)
      const orderCount = filteredOrders.value.length
      const avgOrderValue = orderCount > 0 ? totalRevenue / orderCount : 0

      return {
        totalRevenue,
        orderCount,
        avgOrderValue,
        revenueGrowth: 15.3 // Placeholder - could calculate from historical data
      }
    })

    // Total costs from summary
    const totalCosts = computed(() => {
      return summary.value.total_procurement_cost +
             summary.value.total_operational_cost +
             summary.value.total_labor_cost +
             summary.value.total_overhead
    })

    // Net profit
    const netProfit = computed(() => {
      return revenueMetrics.value.totalRevenue - totalCosts.value
    })

    // Profit margin percentage
    const profitMargin = computed(() => {
      if (revenueMetrics.value.totalRevenue === 0) return 0
      return ((netProfit.value / revenueMetrics.value.totalRevenue) * 100).toFixed(1)
    })

    // Monthly revenue data for chart
    const monthlyRevenue = computed(() => {
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months
      const revenueByMonth = monthNames.map(month => ({
        month,
        revenue: 0,
        costs: 0
      }))

      // Calculate revenue from orders
      allOrders.value.forEach(order => {
        const orderDate = new Date(order.order_date)
        const monthIndex = orderDate.getMonth()
        if (monthIndex >= 0 && monthIndex < 12) {
          revenueByMonth[monthIndex].revenue += order.total_value || 0
        }
      })

      // Add costs from spending data
      allMonthlySpending.value.forEach(spending => {
        const monthIndex = monthNames.indexOf(spending.month)
        if (monthIndex >= 0) {
          revenueByMonth[monthIndex].costs = spending.procurement + spending.operational + spending.labor + spending.overhead
        }
      })

      return revenueByMonth
    })

    // Max value for chart scaling
    const maxRevenueValue = computed(() => {
      const maxRevenue = Math.max(...monthlyRevenue.value.map(m => m.revenue))
      const maxCost = Math.max(...monthlyRevenue.value.map(m => m.costs))
      const max = Math.max(maxRevenue, maxCost)
      return Math.ceil(max / 1000) // Return in K
    })

    const loadData = async () => {
      try {
        loading.value = true
        const [summaryRes, monthlyRes, categoryRes, transactionsRes, ordersRes] = await Promise.all([
          api.getSpendingSummary(),
          api.getMonthlySpending(),
          api.getCategorySpending(),
          api.getTransactions(),
          api.getOrders()
        ])

        summaryData.value = summaryRes
        allMonthlySpending.value = monthlyRes
        allCategorySpending.value = categoryRes
        allTransactions.value = transactionsRes
        allOrders.value = ordersRes
      } catch (err) {
        error.value = 'Failed to load financial data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for period filter changes
    watch([selectedPeriod], () => {
      // Data will automatically update via computed properties
    })

    const formatCurrency = (value) => {
      return formatCurrencyUtil(value, currentCurrency.value)
    }

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const getBarHeight = (value) => {
      const maxValue = 25000
      return (value / maxValue) * 100
    }

    const getRevenueBarHeight = (value) => {
      const maxValue = maxRevenueValue.value * 1000
      return (value / maxValue) * 100
    }

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      })
    }

    const formatDateShort = (dateString) => {
      const date = new Date(dateString)
      const month = (date.getMonth() + 1).toString().padStart(2, '0')
      const day = date.getDate().toString().padStart(2, '0')
      const year = date.getFullYear().toString().slice(-2)
      return `${month}/${day}/${year}`
    }

    const translateMonth = (month) => {
      const monthMap = {
        'Jan': t('months.jan'),
        'Feb': t('months.feb'),
        'Mar': t('months.mar'),
        'Apr': t('months.apr'),
        'May': t('months.may'),
        'Jun': t('months.jun'),
        'Jul': t('months.jul'),
        'Aug': t('months.aug'),
        'Sep': t('months.sep'),
        'Oct': t('months.oct'),
        'Nov': t('months.nov'),
        'Dec': t('months.dec')
      }
      return monthMap[month] || month
    }

    const translateCategory = (category) => {
      // First try spending categories
      const spendingCategoryMap = {
        'Raw Materials': t('spendingCategories.rawMaterials'),
        'Components': t('spendingCategories.components'),
        'Equipment': t('spendingCategories.equipment'),
        'Consumables': t('spendingCategories.consumables')
      }

      // Then try product categories
      const productCategoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }

      return spendingCategoryMap[category] || productCategoryMap[category] || category
    }

    const handleTransactionClick = (transaction) => {
      console.log('Transaction clicked:', transaction)
      alert(`Transaction Details:\n\nID: ${transaction.id}\nDescription: ${transaction.description}\nVendor: ${transaction.vendor}\nDate: ${formatDateShort(transaction.date)}\nAmount: $${transaction.amount.toLocaleString()}`)
    }

    const showCostDetail = (monthData) => {
      selectedCostData.value = monthData
      showCostModal.value = true
    }

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      summary,
      monthlySpending,
      categorySpending,
      recentTransactions,
      revenueMetrics,
      totalCosts,
      netProfit,
      profitMargin,
      monthlyRevenue,
      maxRevenueValue,
      formatCurrency,
      currencySymbol,
      getBarHeight,
      getRevenueBarHeight,
      formatDate,
      formatDateShort,
      translateMonth,
      translateCategory,
      handleTransactionClick,
      showCostModal,
      selectedCostData,
      showCostDetail,
      Math
    }
  }
}
</script>

<style scoped>
/* Left accent on the KPI cards; colors come from the chart tokens */
.revenue-card { border-inline-start: 4px solid var(--chart-2); }
.cost-card { border-inline-start: 4px solid var(--chart-4); }
.profit-card { border-inline-start: 4px solid var(--chart-1); }

.stat-change {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-block-start: var(--space-3);
  font-size: var(--text-base);
}

.stat-change.positive { color: var(--color-success); }

.change-icon {
  font-weight: 700;
  font-size: 1rem;
}

.stat-meta {
  margin-block-start: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
}

/* Side-by-side cards must be allowed to shrink so the table scrolls inside its container */
.grid-2 > * {
  min-width: 0;
}

/* ---- Charts ---- */
.chart-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-6);
  font-size: var(--text-base);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-subtle);
}

.legend-dot {
  inline-size: 0.75rem;
  block-size: 0.75rem;
  border-radius: 3px;
}

/* Series colors, shared by the legend dots and the bar segments.
   There is no purple chart token, so operational uses the neutral series. */
.legend-dot.procurement,
.bar-segment.procurement { background: var(--chart-1); }
.legend-dot.operational,
.bar-segment.operational { background: var(--chart-5); }
.legend-dot.labor,
.bar-segment.labor { background: var(--chart-2); }
.legend-dot.overhead,
.bar-segment.overhead { background: var(--chart-3); }
.legend-dot.revenue-color,
.revenue-bar { background: var(--chart-2); }
.legend-dot.cost-color,
.cost-bar { background: var(--chart-4); }

.chart-container {
  padding-block: var(--space-6);
}

.bar-chart {
  display: flex;
  gap: var(--space-6);
  block-size: 22rem;
}

.y-axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding-inline-end: var(--space-4);
  font-size: var(--text-xs);
  color: var(--chart-axis);
  border-inline-end: 1px solid var(--chart-grid);
}

.chart-area {
  flex: 1;
  min-inline-size: 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  gap: var(--space-2);
}

.bar-group-revenue,
.bar-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  min-inline-size: 0;
  block-size: 100%;
}

.revenue-bars {
  inline-size: 100%;
  max-inline-size: 5rem;
  display: flex;
  gap: 6px;
  justify-content: center;
  align-items: flex-end;
  block-size: 100%;
  padding-block-end: var(--space-8);
}

.revenue-bar,
.cost-bar {
  inline-size: 50%;
  max-inline-size: 30px;
  min-block-size: 4px;
  border-radius: 6px 6px 0 0;
  transition: opacity var(--duration) var(--ease-out);
}

.revenue-bar:hover,
.cost-bar:hover {
  opacity: 0.8;
}

/* Real button so the month's cost detail is keyboard reachable */
.stacked-bar {
  inline-size: 100%;
  max-inline-size: 60px;
  block-size: 100%;
  display: flex;
  flex-direction: column-reverse;
  align-items: stretch;
  padding: 0 0 var(--space-8);
  border: 0;
  background: transparent;
  cursor: pointer;
  transition: opacity var(--duration) var(--ease-out);
}

.stacked-bar:hover {
  opacity: 0.85;
}

.stacked-bar:focus-visible {
  outline: 2px solid var(--color-focus);
  outline-offset: 2px;
}

.bar-segment {
  display: block;
  inline-size: 100%;
}

.bar-segment:first-child { border-radius: 0 0 6px 6px; }
.bar-segment:last-child { border-radius: 6px 6px 0 0; }

.bar-label {
  margin-block-start: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-subtle);
}

/* ---- Category breakdown ---- */
.category-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.category-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-3);
}

.category-name {
  font-weight: 600;
  color: var(--color-text);
}

.category-amount {
  font-weight: 700;
  font-size: var(--text-lg);
  color: var(--color-primary);
}

.category-bar-container {
  inline-size: 100%;
  block-size: 8px;
  background: var(--chart-track);
  border-radius: 4px;
  overflow: hidden;
}

.category-bar {
  block-size: 100%;
  background: var(--chart-1);
  border-radius: 4px;
  transition: width 0.6s var(--ease-out);
}

.category-meta {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  font-size: var(--text-sm);
}

.percentage { color: var(--color-text-subtle); }

.change { font-weight: 600; }
.change.positive { color: var(--color-success); }
.change.negative { color: var(--color-danger); }

/* ---- Transactions ---- */
/* Scrolls vertically too; the shared th background keeps the sticky header opaque */
.transactions-scroll {
  max-block-size: 25rem;
  overflow-y: auto;
}

.transactions-scroll thead th {
  position: sticky;
  inset-block-start: 0;
  z-index: var(--z-sticky);
}

/* Corner cell must stay above both the sticky header row and the sticky first column */
.transactions-scroll thead th:first-child {
  z-index: calc(var(--z-sticky) + 1);
}

.transaction-id {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.transaction-description {
  font-weight: 500;
  color: var(--color-text);
}

.transaction-date {
  font-size: var(--text-sm);
  white-space: nowrap;
}

.transaction-amount {
  font-weight: 700;
  color: var(--color-text);
}
</style>
