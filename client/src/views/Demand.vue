<template>
  <div class="demand">
    <div class="page-header">
      <div>
        <h1>{{ t('demand.title') }}</h1>
        <p>{{ t('demand.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="demand-trend-cards">
        <section class="trend-card increasing-card">
          <div class="trend-header">
            <div class="trend-icon" aria-hidden="true">↑</div>
            <div>
              <h2 class="trend-label">{{ t('demand.increasingDemand') }}</h2>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('increasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('increasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">+{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('increasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('increasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </section>

        <section class="trend-card stable-card">
          <div class="trend-header">
            <div class="trend-icon" aria-hidden="true">→</div>
            <div>
              <h2 class="trend-label">{{ t('demand.stableDemand') }}</h2>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('stable').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('stable').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change neutral">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('stable').length > 5" class="more-items">
              +{{ getForecastsByTrend('stable').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </section>

        <section class="trend-card decreasing-card">
          <div class="trend-header">
            <div class="trend-icon" aria-hidden="true">↓</div>
            <div>
              <h2 class="trend-label">{{ t('demand.decreasingDemand') }}</h2>
              <div class="trend-count">{{ t('demand.itemsCount', { count: getForecastsByTrend('decreasing').length }) }}</div>
            </div>
          </div>
          <div class="trend-items">
            <div v-for="item in getForecastsByTrend('decreasing').slice(0, 5)" :key="item.id" class="trend-item">
              <span class="item-name">{{ item.item_name }}</span>
              <span class="item-change">{{ getChangePercent(item) }}%</span>
            </div>
            <div v-if="getForecastsByTrend('decreasing').length > 5" class="more-items">
              +{{ getForecastsByTrend('decreasing').length - 5 }} {{ t('demand.more') }}
            </div>
          </div>
        </section>
      </div>

      <div class="card card--flush">
        <div class="card-header">
          <h2 class="card-title">{{ t('demand.demandForecasts') }}</h2>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('demand.table.sku') }}</th>
                <th scope="col">{{ t('demand.table.itemName') }}</th>
                <th scope="col" class="num">{{ t('demand.table.currentDemand') }}</th>
                <th scope="col" class="num">{{ t('demand.table.forecastedDemand') }}</th>
                <th scope="col" class="num">{{ t('demand.table.change') }}</th>
                <th scope="col">{{ t('demand.table.trend') }}</th>
                <th scope="col">{{ t('demand.table.period') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="forecast in forecasts" :key="forecast.id">
                <td><strong>{{ forecast.item_sku }}</strong></td>
                <td>{{ forecast.item_name }}</td>
                <td class="num">{{ forecast.current_demand }}</td>
                <td class="num"><strong>{{ forecast.forecasted_demand }}</strong></td>
                <td class="num">
                  <span :style="{ color: getChangeColor(forecast) }">
                    {{ getChangePercent(forecast) }}%
                  </span>
                </td>
                <td>
                  <span :class="['badge', forecast.trend]">
                    {{ t(`trends.${forecast.trend}`) }}
                  </span>
                </td>
                <td>{{ translatePeriod(forecast.period) }}</td>
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

export default {
  name: 'Demand',
  setup() {
    const { t } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const allForecasts = ref([])
    const inventoryItems = ref([])

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Filter forecasts based on inventory filters
    const forecasts = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allForecasts.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allForecasts.value.filter(f => validSkus.has(f.item_sku))
    })

    const loadForecasts = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [forecastsData, inventoryData] = await Promise.all([
          api.getDemandForecasts(),
          api.getInventory({
            warehouse: filters.warehouse,
            category: filters.category
          })
        ])

        allForecasts.value = forecastsData
        inventoryItems.value = inventoryData
      } catch (err) {
        error.value = 'Failed to load demand forecasts: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadForecasts()
    })

    const getForecastsByTrend = (trend) => {
      return forecasts.value.filter(f => f.trend === trend)
    }

    const getChangePercent = (forecast) => {
      const change = ((forecast.forecasted_demand - forecast.current_demand) / forecast.current_demand * 100).toFixed(1)
      return change > 0 ? `+${change}` : change
    }

    const getChangeColor = (forecast) => {
      const change = forecast.forecasted_demand - forecast.current_demand
      const changePercent = Math.abs((change / forecast.current_demand) * 100)

      // If change is within ±2%, consider it stable and show blue
      if (changePercent <= 2) {
        return 'var(--color-info)' // Blue for stable
      }

      if (change > 0) return 'var(--color-success)' // Green for increasing
      if (change < 0) return 'var(--color-danger)' // Red for decreasing
      return 'var(--color-info)' // Blue for no change
    }

    const translatePeriod = (period) => {
      // Period values like "Next 3 months", "Q1 2025", "30 days", etc.
      const { currentLocale } = useI18n()
      if (currentLocale.value === 'ja') {
        return period
          .replace(/Next\s+/i, '次の')
          .replace(/\s+months/i, 'か月')
          .replace(/\s+month/i, 'か月')
          .replace(/\s+days/i, '日間')
          .replace(/\s+day/i, '日')
          .replace('Q1', '第1四半期')
          .replace('Q2', '第2四半期')
          .replace('Q3', '第3四半期')
          .replace('Q4', '第4四半期')
      }
      return period
    }

    onMounted(loadForecasts)

    return {
      t,
      loading,
      error,
      forecasts,
      getForecastsByTrend,
      getChangePercent,
      getChangeColor,
      translatePeriod
    }
  }
}
</script>

<style scoped>
.demand-trend-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(20rem, 100%), 1fr));
  gap: var(--space-6);
  margin-block-end: var(--space-8);
}

.trend-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
  min-inline-size: 0;
  transition: box-shadow var(--duration) var(--ease-out);
}

.trend-card:hover {
  box-shadow: var(--shadow-md);
}

.increasing-card { border-inline-start: 4px solid var(--chart-2); }
.stable-card { border-inline-start: 4px solid var(--chart-1); }
.decreasing-card { border-inline-start: 4px solid var(--chart-4); }

.trend-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-block-end: var(--space-4);
  padding-block-end: var(--space-4);
  border-block-end: 1px solid var(--color-border);
}

.trend-icon {
  inline-size: 3rem;
  block-size: 3rem;
  display: grid;
  place-items: center;
  border-radius: var(--radius-md);
  font-size: var(--text-xl);
  font-weight: 700;
  flex-shrink: 0;
}

.increasing-card .trend-icon {
  background: var(--color-success-soft);
  color: var(--color-on-success-soft);
}

.stable-card .trend-icon {
  background: var(--color-info-soft);
  color: var(--color-on-info-soft);
}

.decreasing-card .trend-icon {
  background: var(--color-danger-soft);
  color: var(--color-on-danger-soft);
}

.trend-label {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trend-count {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
  margin-block-start: var(--space-1);
}

.trend-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.trend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  transition: background-color var(--duration) var(--ease-out);
}

.trend-item:hover {
  background: var(--color-surface-hover);
}

.item-name {
  font-size: var(--text-base);
  color: var(--color-text);
  font-weight: 500;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-inline-end: var(--space-4);
}

.item-change {
  font-size: var(--text-sm);
  font-weight: 700;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.increasing-card .item-change { color: var(--color-success); }
.stable-card .item-change { color: var(--color-info); }
.decreasing-card .item-change { color: var(--color-danger); }
.item-change.neutral { color: var(--color-text-subtle); }

.more-items {
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
  font-style: italic;
  text-align: center;
  padding: var(--space-2);
}
</style>
