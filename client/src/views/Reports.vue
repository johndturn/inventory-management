<template>
  <div class="reports">
    <div class="page-header">
      <div>
        <h1>Performance Reports</h1>
        <p>View quarterly performance metrics and monthly trends</p>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading reports...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <!-- Quarterly Performance -->
      <section class="card card--flush" aria-labelledby="quarterly-title">
        <div class="card-header">
          <h2 id="quarterly-title" class="card-title">Quarterly Performance</h2>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Quarter</th>
                <th scope="col" class="num">Total Orders</th>
                <th scope="col" class="num">Total Revenue</th>
                <th scope="col" class="num">Avg Order Value</th>
                <th scope="col" class="num">Fulfillment Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="q in quarterlyData" :key="q.quarter">
                <th scope="row" class="row-header">{{ q.quarter }}</th>
                <td class="num">{{ q.total_orders }}</td>
                <td class="num">${{ formatNumber(q.total_revenue) }}</td>
                <td class="num">${{ formatNumber(q.avg_order_value) }}</td>
                <td class="num">
                  <span :class="getFulfillmentClass(q.fulfillment_rate)">
                    {{ q.fulfillment_rate }}%
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
          <h2 id="trend-title" class="card-title">Monthly Revenue Trend</h2>
        </div>
        <div class="chart-container">
          <!-- The month-over-month table below carries the same data in text form -->
          <div class="bar-chart" role="img" aria-label="Monthly Revenue Trend">
            <div v-for="month in monthlyData" :key="month.month" class="bar-wrapper">
              <div class="bar-container">
                <div
                  class="bar"
                  :style="{ height: getBarHeight(month.revenue) + 'px' }"
                  :title="'$' + formatNumber(month.revenue)"
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
          <h2 id="mom-title" class="card-title">Month-over-Month Analysis</h2>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">Month</th>
                <th scope="col" class="num">Orders</th>
                <th scope="col" class="num">Revenue</th>
                <th scope="col" class="num">Change</th>
                <th scope="col" class="num">Growth Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(month, index) in monthlyData" :key="month.month">
                <th scope="row" class="row-header"><time :datetime="month.month">{{ formatMonth(month.month) }}</time></th>
                <td class="num">{{ month.order_count }}</td>
                <td class="num">${{ formatNumber(month.revenue) }}</td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getChangeValue(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
                <td class="num">
                  <span v-if="index > 0" :class="getChangeClass(month.revenue, monthlyData[index - 1].revenue)">
                    {{ getGrowthRate(month.revenue, monthlyData[index - 1].revenue) }}
                  </span>
                  <span v-else>-</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Summary Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total Revenue (YTD)</div>
          <div class="stat-value">${{ formatNumber(totalRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Avg Monthly Revenue</div>
          <div class="stat-value">${{ formatNumber(avgMonthlyRevenue) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Orders (YTD)</div>
          <div class="stat-value">{{ totalOrders }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Best Performing Quarter</div>
          <div class="stat-value">{{ bestQuarter }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Reports',
  data() {
    return {
      loading: true,
      error: null,
      quarterlyData: [],
      monthlyData: [],
      totalRevenue: 0,
      avgMonthlyRevenue: 0,
      totalOrders: 0,
      bestQuarter: ''
    }
  },
  mounted() {
    console.log('Reports component mounted')
    this.loadData()
  },
  methods: {
    async loadData() {
      console.log('Loading reports data...')
      try {
        this.loading = true

        // Fetch quarterly data
        console.log('Fetching quarterly data...')
        const quarterlyResponse = await axios.get('http://localhost:8001/api/reports/quarterly')
        this.quarterlyData = quarterlyResponse.data
        console.log('Quarterly data:', this.quarterlyData)

        // Fetch monthly data
        console.log('Fetching monthly data...')
        const monthlyResponse = await axios.get('http://localhost:8001/api/reports/monthly-trends')
        this.monthlyData = monthlyResponse.data
        console.log('Monthly data:', this.monthlyData)

        // Calculate summary stats
        console.log('Calculating summary stats...')
        this.calculateSummaryStats()
        console.log('Summary stats calculated')

      } catch (err) {
        console.log('Error loading reports:', err)
        this.error = 'Failed to load reports: ' + err.message
      } finally {
        this.loading = false
        console.log('Loading complete')
      }
    },

    calculateSummaryStats() {
      // Calculate total revenue
      var total = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        total = total + this.monthlyData[i].revenue
      }
      this.totalRevenue = total

      // Calculate average monthly revenue
      if (this.monthlyData.length > 0) {
        this.avgMonthlyRevenue = total / this.monthlyData.length
      } else {
        this.avgMonthlyRevenue = 0
      }

      // Calculate total orders
      var orders = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        orders = orders + this.monthlyData[i].order_count
      }
      this.totalOrders = orders

      // Find best quarter
      var bestQ = ''
      var bestRevenue = 0
      for (var i = 0; i < this.quarterlyData.length; i++) {
        if (this.quarterlyData[i].total_revenue > bestRevenue) {
          bestRevenue = this.quarterlyData[i].total_revenue
          bestQ = this.quarterlyData[i].quarter
        }
      }
      this.bestQuarter = bestQ
    },

    formatNumber(num) {
      console.log('Formatting number:', num)
      // Format number with commas
      var str = num.toString()
      var parts = str.split('.')
      var intPart = parts[0]
      var decPart = parts.length > 1 ? parts[1] : '00'

      var formatted = ''
      var count = 0
      for (var i = intPart.length - 1; i >= 0; i--) {
        if (count > 0 && count % 3 === 0) {
          formatted = ',' + formatted
        }
        formatted = intPart[i] + formatted
        count++
      }

      if (decPart.length === 1) {
        decPart = decPart + '0'
      }
      if (decPart.length > 2) {
        decPart = decPart.substring(0, 2)
      }

      return formatted + '.' + decPart
    },

    formatMonth(monthStr) {
      console.log('Formatting month:', monthStr)
      // Convert YYYY-MM to readable format
      var parts = monthStr.split('-')
      var year = parts[0]
      var month = parts[1]

      var monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
      var monthIndex = parseInt(month) - 1

      return monthNames[monthIndex] + ' ' + year
    },

    getBarHeight(revenue) {
      console.log('Calculating bar height for revenue:', revenue)
      // Calculate bar height (max height 200px)
      var maxRevenue = 0
      for (var i = 0; i < this.monthlyData.length; i++) {
        if (this.monthlyData[i].revenue > maxRevenue) {
          maxRevenue = this.monthlyData[i].revenue
        }
      }

      if (maxRevenue === 0) {
        return 0
      }

      var height = (revenue / maxRevenue) * 200
      return height
    },

    getFulfillmentClass(rate) {
      if (rate >= 90) {
        return 'badge success'
      } else if (rate >= 75) {
        return 'badge warning'
      } else {
        return 'badge danger'
      }
    },

    getChangeValue(current, previous) {
      var change = current - previous
      if (change > 0) {
        return '+$' + this.formatNumber(change)
      } else if (change < 0) {
        return '-$' + this.formatNumber(Math.abs(change))
      } else {
        return '$0.00'
      }
    },

    getChangeClass(current, previous) {
      var change = current - previous
      if (change > 0) {
        return 'positive-change'
      } else if (change < 0) {
        return 'negative-change'
      } else {
        return ''
      }
    },

    getGrowthRate(current, previous) {
      if (previous === 0) {
        return 'N/A'
      }

      var rate = ((current - previous) / previous) * 100
      var sign = rate > 0 ? '+' : ''

      return sign + rate.toFixed(1) + '%'
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
