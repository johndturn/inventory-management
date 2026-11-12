<template>
  <div class="reports">
    <div class="page-header">
      <div>
        <h1>{{ t('reports.title') }}</h1>
        <p>{{ t('reports.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('reports.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="isEmpty" class="empty-state">{{ t('reports.empty') }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <section class="card card--flush" aria-labelledby="quarterly-title">
        <div class="card-header">
          <h2 id="quarterly-title" class="card-title">{{ t('reports.quarterlyPerformance') }}</h2>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('reports.table.quarter') }}</th>
                <th scope="col" class="num">{{ t('reports.table.totalOrders') }}</th>
                <th scope="col" class="num">{{ t('reports.table.totalRevenue') }}</th>
                <th scope="col" class="num">{{ t('reports.table.avgOrderValue') }}</th>
                <th scope="col" class="num">{{ t('reports.table.fulfillmentRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <th scope="row" class="row-header">{{ formatQuarter(q.quarter) }}</th>
                <td class="num">{{ formatCount(q.total_orders) }}</td>
                <td class="num">{{ formatCurrency(q.total_revenue, currentCurrency) }}</td>
                <td class="num">{{ formatCurrencyWithDecimals(q.avg_order_value, currentCurrency, 2) }}</td>
                <td class="num">
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ formatPercent(q.fulfillment_rate) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Monthly Trends Chart -->
      <section class="card" aria-labelledby="trend-title">
        <div class="card-header">
          <h2 id="trend-title" class="card-title">{{ t('reports.monthlyRevenueTrend') }}</h2>
        </div>
        <div class="chart-container">
          <!-- The month-over-month table below carries the same data in text form -->
          <div
            class="bar-chart"
            role="img"
            :aria-label="t('reports.chartLabel', { count: monthlyData.length })"
          >
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="formatCurrency(month.revenue, currentCurrency)"
                ></div>
              </div>
              <div class="bar-label">{{ formatMonth(month.month) }}</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Month-over-Month Comparison -->
      <section class="card card--flush" aria-labelledby="mom-title">
        <div class="card-header">
          <h2 id="mom-title" class="card-title">{{ t('reports.monthOverMonth') }}</h2>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('reports.table.month') }}</th>
                <th scope="col" class="num">{{ t('reports.table.orders') }}</th>
                <th scope="col" class="num">{{ t('reports.table.revenue') }}</th>
                <th scope="col" class="num">{{ t('reports.table.change') }}</th>
                <th scope="col" class="num">{{ t('reports.table.growthRate') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in monthRows" :key="row.month">
                <th scope="row" class="row-header"><time :datetime="row.month">{{ formatMonth(row.month) }}</time></th>
                <td class="num">{{ formatCount(row.order_count) }}</td>
                <td class="num">{{ formatCurrency(row.revenue, currentCurrency) }}</td>
                <td class="num">
                  <span v-if="row.previous !== null" :class="getChangeClass(row.change)">
                    {{ formatChange(row.change) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td class="num">
                  <span v-if="row.previous !== null" :class="getChangeClass(row.change)">
                    {{ formatGrowthRate(row.change, row.previous) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Summary Stats -->
      <div class="stats-grid stats-grid--wide">
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(totalRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.avgMonthlyRevenue') }}</div>
          <div class="stat-value">{{ formatCurrency(avgMonthlyRevenue, currentCurrency) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.totalOrders') }}</div>
          <div class="stat-value">{{ formatCount(totalOrders) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">{{ t('reports.summary.bestQuarter') }}</div>
          <div class="stat-value">{{ bestQuarter ? formatQuarter(bestQuarter) : t('reports.notApplicable') }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency, formatCurrencyWithDecimals } from '../utils/currency'

// Tallest bar in px; matches .bar-container block-size
const MAX_BAR_HEIGHT = 200

export default {
  name: 'Reports',
  setup() {
    const { t, currentLocale, currentCurrency } = useI18n()

    const loading = ref(true)
    const error = ref(null)
    const quarterlyData = ref([])
    const monthlyData = ref([])

    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    // BCP 47 tag for Intl formatters; follows the language switcher
    const intlLocale = computed(() => (currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'))

    // Filters can change faster than the API responds. Only the newest request may
    // write state, otherwise a slow earlier response could overwrite newer data.
    let latestRequestId = 0

    const loadData = async () => {
      const requestId = ++latestRequestId
      loading.value = true
      error.value = null
      try {
        const filters = getCurrentFilters()
        const [quarterly, monthly] = await Promise.all([
          api.getQuarterlyReport(filters),
          api.getMonthlyTrends(filters)
        ])
        if (requestId !== latestRequestId) return // stale response, ignore
        quarterlyData.value = quarterly
        monthlyData.value = monthly
      } catch (err) {
        if (requestId !== latestRequestId) return
        error.value = t('reports.loadFailed')
        console.error('Failed to load reports:', err)
      } finally {
        if (requestId === latestRequestId) loading.value = false
      }
    }

    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(loadData)

    const isEmpty = computed(() => quarterlyData.value.length === 0 && monthlyData.value.length === 0)

    // Summary stats and chart scale are derived once per data change, not per render
    const totalRevenue = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + (Number(m.revenue) || 0), 0)
    )
    const avgMonthlyRevenue = computed(() =>
      monthlyData.value.length > 0 ? totalRevenue.value / monthlyData.value.length : 0
    )
    const totalOrders = computed(() =>
      monthlyData.value.reduce((sum, m) => sum + (Number(m.order_count) || 0), 0)
    )
    const bestQuarter = computed(() => {
      let best = null
      for (const q of quarterlyData.value) {
        if (best === null || q.total_revenue > best.total_revenue) best = q
      }
      return best && best.total_revenue > 0 ? best.quarter : null
    })
    const maxRevenue = computed(() =>
      monthlyData.value.reduce((max, m) => Math.max(max, Number(m.revenue) || 0), 0)
    )

    // Each month paired with its predecessor so the template doesn't index into the array
    const monthRows = computed(() =>
      monthlyData.value.map((m, i) => {
        const previous = i > 0 ? monthlyData.value[i - 1].revenue : null
        return { ...m, previous, change: previous === null ? 0 : m.revenue - previous }
      })
    )

    const getBarHeight = (revenue) => {
      if (maxRevenue.value === 0) return 0
      return (revenue / maxRevenue.value) * MAX_BAR_HEIGHT
    }

    const getFulfillmentClass = (rate) => {
      if (rate >= 90) return 'badge success'
      if (rate >= 75) return 'badge warning'
      return 'badge danger'
    }

    // "Q1-2025" -> localized label via reports.quarterLabel
    const formatQuarter = (value) => {
      const match = /^Q(\d)-(\d{4})$/.exec(value || '')
      if (!match) return value || ''
      return t('reports.quarterLabel', { quarter: match[1], year: match[2] })
    }

    // "YYYY-MM" -> locale month name. Built from parts (not parsed from a string)
    // so timezone offsets can't shift it into the neighbouring month.
    const formatMonth = (monthStr) => {
      const [year, month] = String(monthStr).split('-').map(Number)
      const date = new Date(year, month - 1, 1)
      if (!year || !month || isNaN(date.getTime())) return monthStr
      return new Intl.DateTimeFormat(intlLocale.value, { year: 'numeric', month: 'short' }).format(date)
    }

    const formatCount = (n) => new Intl.NumberFormat(intlLocale.value).format(n)

    const formatPercent = (n) =>
      `${new Intl.NumberFormat(intlLocale.value, { maximumFractionDigits: 1 }).format(n)}%`

    // Signed currency delta: sign is added here, the formatter gets the absolute value
    const formatChange = (change) => {
      const formatted = formatCurrency(Math.abs(change), currentCurrency.value)
      if (change > 0) return `+${formatted}`
      if (change < 0) return `−${formatted}`
      return formatted
    }

    const getChangeClass = (change) => {
      if (change > 0) return 'positive-change'
      if (change < 0) return 'negative-change'
      return ''
    }

    const formatGrowthRate = (change, previous) => {
      if (!previous) return t('reports.notApplicable') // growth from zero is undefined
      const rate = (change / previous) * 100
      const formatted = new Intl.NumberFormat(intlLocale.value, {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
        signDisplay: 'exceptZero'
      }).format(rate)
      return `${formatted}%`
    }

    return {
      t,
      currentCurrency,
      loading,
      error,
      isEmpty,
      quarterlyData,
      monthlyData,
      monthRows,
      totalRevenue,
      avgMonthlyRevenue,
      totalOrders,
      bestQuarter,
      getBarHeight,
      getFulfillmentClass,
      formatQuarter,
      formatMonth,
      formatCount,
      formatPercent,
      formatChange,
      getChangeClass,
      formatGrowthRate,
      formatCurrency,
      formatCurrencyWithDecimals
    }
  }
}
</script>

<style scoped>
/* Row header cells read like the old bold first column, not like column headings */
.row-header {
  padding: var(--space-2) var(--space-3);
  border-block: 0;
  border-block-start: 1px solid var(--color-border);
  background: transparent;
  text-align: start;
  font-size: var(--text-base);
  font-weight: 600;
  text-transform: none;
  letter-spacing: normal;
  color: var(--color-text);
}

.chart-container {
  padding: var(--space-8) var(--space-4);
  min-block-size: 300px;
  overflow-x: auto;
}

.bar-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-around;
  block-size: 250px;
  gap: var(--space-2);
}

.bar-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  max-inline-size: 80px;
}

.bar-container {
  block-size: 200px;
  display: flex;
  align-items: flex-end;
  inline-size: 100%;
}

.bar {
  inline-size: 100%;
  background: var(--chart-1);
  border-radius: 4px 4px 0 0;
  transition: opacity var(--duration) var(--ease-out);
}

.bar:hover {
  opacity: 0.8;
}

.bar-label {
  margin-block-start: var(--space-6);
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  text-align: center;
  transform: rotate(-45deg);
  white-space: nowrap;
}

.positive-change {
  color: var(--color-success);
  font-weight: 600;
}

.negative-change {
  color: var(--color-danger);
  font-weight: 600;
}
</style>
