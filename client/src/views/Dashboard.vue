<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>{{ t('dashboard.title') }}</h1>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error" role="alert">{{ error }}</div>
    <div v-else>
      <!-- Key Performance Indicators -->
      <section class="kpi-section">
        <h2 class="section-title">{{ t('dashboard.kpi.title') }}</h2>
        <div class="kpi-grid">
          <div class="stat-card">
            <div class="stat-label">{{ t('dashboard.kpi.inventoryTurnover') }}</div>
            <div class="stat-value">4.2</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 4.5 (-6.67%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" style="width: 93.33%"></div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-label">{{ t('dashboard.kpi.ordersFulfilled') }}</div>
            <div class="stat-value">{{ ordersData.fulfilled }}</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: {{ ordersData.goal }} ({{ calculatePercentage(ordersData.fulfilled, ordersData.goal) }}%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" :style="{ width: calculatePercentage(ordersData.fulfilled, ordersData.goal) + '%' }"></div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-label">{{ t('dashboard.kpi.orderFillRate') }}</div>
            <div class="stat-value">{{ fillRate }}%</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 95% ({{ fillRate - 95 > 0 ? '+' : '' }}{{ (fillRate - 95).toFixed(2) }}%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress success" :style="{ width: (fillRate / 95 * 100) + '%' }"></div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-label">{{ t(selectedPeriod === 'all' ? 'dashboard.kpi.revenueYTD' : 'dashboard.kpi.revenueMTD') }}</div>
            <div class="stat-value">{{ formatCurrency(Math.round(summary.total_orders_value), selectedCurrency) }}</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: {{ formatCurrency(revenueGoal, selectedCurrency) }} ({{ summary.total_orders_value > revenueGoal ? '+' : '' }}{{ ((summary.total_orders_value / revenueGoal - 1) * 100).toFixed(1) }}%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress" :style="{ width: Math.min((summary.total_orders_value / revenueGoal * 100), 100) + '%' }"></div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-label">{{ t('dashboard.kpi.avgProcessingTime') }}</div>
            <div class="stat-value">2.8</div>
            <div class="kpi-goal">{{ t('dashboard.kpi.goal') }}: 3.0 (-6.67%)</div>
            <div class="kpi-progress-bar">
              <div class="kpi-progress success" style="width: 93.33%"></div>
            </div>
          </div>
        </div>
      </section>

      <!-- Summary Section -->
      <h2 class="section-title">{{ t('dashboard.summary.title') }}</h2>

      <div class="grid-2">
        <!-- Order Health Dashboard -->
        <section class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.orderHealth.title') }}</h3>
          </div>
          <div class="order-health-container">
            <!-- Left: Donut Chart -->
            <div class="order-health-chart">
              <svg viewBox="0 0 200 200" class="donut-svg-compact" role="img" :aria-label="t('dashboard.orderHealth.title')">
                <circle class="donut-track" cx="100" cy="100" r="65" fill="none" stroke-width="25"/>
                <circle class="donut-seg seg-delivered" cx="100" cy="100" r="65" fill="none" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.delivered)} 408`"
                  stroke-dashoffset="0" transform="rotate(-90 100 100)"/>
                <circle class="donut-seg seg-shipped" cx="100" cy="100" r="65" fill="none" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.shipped)} 408`"
                  :stroke-dashoffset="`-${getCircleSegment(statusData.delivered)}`"
                  transform="rotate(-90 100 100)"/>
                <circle class="donut-seg seg-processing" cx="100" cy="100" r="65" fill="none" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.processing)} 408`"
                  :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped)}`"
                  transform="rotate(-90 100 100)"/>
                <circle class="donut-seg seg-backordered" cx="100" cy="100" r="65" fill="none" stroke-width="25"
                  :stroke-dasharray="`${getCircleSegment(statusData.backordered)} 408`"
                  :stroke-dashoffset="`-${getCircleSegment(statusData.delivered) + getCircleSegment(statusData.shipped) + getCircleSegment(statusData.processing)}`"
                  transform="rotate(-90 100 100)"/>
                <text x="100" y="90" text-anchor="middle" class="donut-center-label">{{ t('dashboard.orderHealth.total') }}</text>
                <text x="100" y="120" text-anchor="middle" class="donut-center-value">{{ orderHealthMetrics.totalOrders }}</text>
              </svg>
              <ul class="donut-legend-compact" role="list">
                <li class="legend-item-compact"><span class="legend-dot" style="background: var(--chart-2)"></span>{{ t('status.delivered') }}</li>
                <li class="legend-item-compact"><span class="legend-dot" style="background: var(--chart-1)"></span>{{ t('status.shipped') }}</li>
                <li class="legend-item-compact"><span class="legend-dot" style="background: var(--chart-3)"></span>{{ t('status.processing') }}</li>
                <li class="legend-item-compact"><span class="legend-dot" style="background: var(--chart-4)"></span>{{ t('status.backordered') }}</li>
              </ul>
            </div>

            <!-- Right: Health Metrics -->
            <div class="order-health-metrics">
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.revenue') }}</div>
                <div class="health-metric-value">{{ formatCurrency(orderHealthMetrics.totalValue, selectedCurrency) }}</div>
              </div>
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.avgOrderValue') }}</div>
                <div class="health-metric-value">{{ formatCurrency(orderHealthMetrics.avgOrderValue, selectedCurrency) }}</div>
              </div>
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.onTimeRate') }}</div>
                <div class="health-metric-value" :class="{ 'metric-good': orderHealthMetrics.onTimeRate >= 90, 'metric-warning': orderHealthMetrics.onTimeRate < 90 && orderHealthMetrics.onTimeRate >= 75, 'metric-bad': orderHealthMetrics.onTimeRate < 75 }">
                  {{ orderHealthMetrics.onTimeRate.toFixed(1) }}%
                </div>
              </div>
              <div class="health-metric">
                <div class="health-metric-label">{{ t('dashboard.orderHealth.avgFulfillmentDays') }}</div>
                <div class="health-metric-value">{{ orderHealthMetrics.avgFulfillmentDays.toFixed(1) }}</div>
              </div>
            </div>
          </div>
        </section>

        <!-- Inventory by Category -->
        <section class="card">
          <div class="card-header">
            <h3 class="card-title">{{ t('dashboard.inventoryValue.title') }}</h3>
          </div>
          <div class="horizontal-bar-chart" v-if="categoryData.length > 0">
            <div v-for="cat in categoryData" :key="cat.name" class="h-bar-item">
              <div class="h-bar-label">{{ translateCategory(cat.name) }}</div>
              <div class="h-bar-container">
                <div class="h-bar" :style="{ width: (cat.value / maxCategoryValue * 100) + '%', background: cat.color }">
                  <span class="h-bar-value">{{ selectedCurrency === 'JPY' ? formatCurrency(cat.value, selectedCurrency) : `$${(cat.value / 1000).toFixed(1)}K` }}</span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">{{ t('dashboard.inventoryShortages.noData') }}</div>
        </section>
      </div>

      <!-- Inventory Shortages -->
      <section class="card card--flush">
        <div class="card-header">
          <h3 class="card-title">{{ t('dashboard.inventoryShortages.title') }} ({{ backlogItems.length }})</h3>
        </div>
        <div v-if="backlogItems.length === 0" class="no-backlog">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="success-icon" aria-hidden="true">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
          </svg>
          <p class="no-backlog-text">{{ t('dashboard.inventoryShortages.noShortages') }}</p>
        </div>
        <div v-else class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('dashboard.inventoryShortages.orderId') }}</th>
                <th scope="col">{{ t('dashboard.inventoryShortages.sku') }}</th>
                <th scope="col">{{ t('dashboard.inventoryShortages.itemName') }}</th>
                <th scope="col" class="num">{{ t('dashboard.inventoryShortages.quantityNeeded') }}</th>
                <th scope="col" class="num">{{ t('dashboard.inventoryShortages.quantityAvailable') }}</th>
                <th scope="col">{{ t('dashboard.inventoryShortages.shortage') }}</th>
                <th scope="col" class="num">{{ t('dashboard.inventoryShortages.daysDelayed') }}</th>
                <th scope="col">{{ t('dashboard.inventoryShortages.priority') }}</th>
                <th scope="col">Actions</th>
              </tr>
            </thead>
            <tbody>
              <!-- Row click is a mouse convenience; the .row-link button is the keyboard/AT entry point -->
              <tr
                v-for="item in backlogItems"
                :key="item.id"
                class="clickable-row"
                @click="showBacklogDetail(item)"
              >
                <td><button type="button" class="row-link" @click.stop="showBacklogDetail(item)">{{ item.order_id }}</button></td>
                <td><strong>{{ item.item_sku }}</strong></td>
                <td>{{ translateProductName(item.item_name) }}</td>
                <td class="num">{{ item.quantity_needed }}</td>
                <td class="num">{{ item.quantity_available }}</td>
                <td>
                  <span class="badge danger">
                    {{ Math.abs(item.quantity_needed - item.quantity_available) }} {{ t('dashboard.inventoryShortages.unitsShort') }}
                  </span>
                </td>
                <td class="num">
                  <span :class="['days-delayed', item.days_delayed > 7 ? 'days-late' : 'days-warn']">
                    {{ item.days_delayed }} {{ t('dashboard.inventoryShortages.days') }}
                  </span>
                </td>
                <td>
                  <span :class="['badge', item.priority]">
                    {{ translatePriority(item.priority) }}
                  </span>
                </td>
                <td>
                  <button
                    v-if="!item.purchase_order_id"
                    type="button"
                    @click.stop="openPOModal(item)"
                    class="btn btn--sm btn--primary"
                  >
                    Create PO
                  </button>
                  <button
                    v-else
                    type="button"
                    @click.stop="viewPO(item)"
                    class="btn btn--sm"
                  >
                    View PO
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Top Products Table -->
      <section class="card card--flush">
        <div class="card-header">
          <h3 class="card-title">{{ t('dashboard.topProducts.title') }}</h3>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('dashboard.topProducts.product') }}</th>
                <th scope="col">{{ t('dashboard.topProducts.sku') }}</th>
                <th scope="col">{{ t('dashboard.topProducts.category') }}</th>
                <th scope="col" class="num">{{ t('dashboard.topProducts.unitsOrdered') }}</th>
                <th scope="col" class="num">{{ t('dashboard.topProducts.revenue') }}</th>
                <th scope="col">{{ t('dashboard.topProducts.firstOrder') }}</th>
                <th scope="col">{{ t('dashboard.topProducts.stockStatus') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="item in topProducts"
                :key="item.sku"
                class="clickable-row"
                @click="showProductDetail(item)"
              >
                <td><button type="button" class="row-link" @click.stop="showProductDetail(item)">{{ translateProductName(item.name) }}</button></td>
                <td>{{ item.sku }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td class="num">{{ item.unitsOrdered }}</td>
                <td class="num"><strong>{{ formatCurrency(item.revenue, selectedCurrency) }}</strong></td>
                <td>
                  <time v-if="item.firstOrderDate" :datetime="item.firstOrderDate">{{ formatDate(item.firstOrderDate) }}</time>
                  <template v-else>-</template>
                </td>
                <td>
                  <span :class="['badge', getStockBadge(item.stockLevel)]">
                    {{ translateStockLevel(item.stockLevel) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <ProductDetailModal
      :is-open="showProductModal"
      :product="selectedProduct"
      @close="showProductModal = false"
    />

    <BacklogDetailModal
      :is-open="showBacklogModal"
      :backlog-item="selectedBacklogItem"
      @close="showBacklogModal = false"
    />

    <PurchaseOrderModal
      :is-open="showPOModal"
      :backlog-item="selectedBacklogForPO"
      :mode="poModalMode"
      @close="showPOModal = false"
      @po-created="handlePOCreated"
    />
  </div>
</template>

<script>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import { formatCurrency } from '../utils/currency'
import ProductDetailModal from '../components/ProductDetailModal.vue'
import BacklogDetailModal from '../components/BacklogDetailModal.vue'

export default {
  name: 'Dashboard',
  components: {
    ProductDetailModal,
    BacklogDetailModal,
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()
    const loading = ref(true)
    const error = ref(null)
    const summary = ref({})
    const allOrders = ref([])
    const inventoryItems = ref([])

    // Modal state
    const showProductModal = ref(false)
    const selectedProduct = ref(null)
    const showBacklogModal = ref(false)
    const selectedBacklogItem = ref(null)
    const showPOModal = ref(false)
    const selectedBacklogForPO = ref(null)
    const poModalMode = ref('create')

    // Use shared filters
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      getCurrentFilters
    } = useFilters()

    const ordersData = ref({ fulfilled: 187, goal: 200 })
    const fillRate = ref(96.8)

    const revenueGoal = computed(() => {
      // $800K per month, so if looking at all months (12 months), goal is 12 * 800K = 9.6M
      const monthlyGoal = 800000
      if (selectedPeriod.value === 'all') {
        return monthlyGoal * 12 // $9,600,000 for the full year
      }
      return monthlyGoal // $800,000 for a single month
    })

    const revenueGoalDisplay = computed(() => {
      if (revenueGoal.value >= 1000000) {
        return `$${(revenueGoal.value / 1000000).toFixed(1)}M`
      }
      return `$${(revenueGoal.value / 1000).toFixed(0)}K`
    })

    const statusData = computed(() => {
      const counts = { delivered: 0, shipped: 0, processing: 0, backordered: 0 }
      allOrders.value.forEach(order => {
        const status = order.status.toLowerCase()
        if (counts[status] !== undefined) counts[status]++
      })
      return counts
    })

    const orderHealthMetrics = computed(() => {
      const totalOrders = allOrders.value.length
      const totalValue = allOrders.value.reduce((sum, order) => sum + (order.total_value || 0), 0)
      const avgOrderValue = totalOrders > 0 ? totalValue / totalOrders : 0

      // Calculate on-time delivery rate (delivered orders that arrived on or before expected date)
      const deliveredOrders = allOrders.value.filter(o => o.status.toLowerCase() === 'delivered')
      const onTimeDeliveries = deliveredOrders.filter(o => {
        if (o.actual_delivery && o.expected_delivery) {
          return new Date(o.actual_delivery) <= new Date(o.expected_delivery)
        }
        return false
      }).length
      const onTimeRate = deliveredOrders.length > 0 ? (onTimeDeliveries / deliveredOrders.length) * 100 : 0

      // Calculate average fulfillment speed (days from order to delivery for delivered orders)
      let totalDays = 0
      let countWithDates = 0
      deliveredOrders.forEach(o => {
        if (o.order_date && o.actual_delivery) {
          const orderDate = new Date(o.order_date)
          const deliveryDate = new Date(o.actual_delivery)
          const days = Math.round((deliveryDate - orderDate) / (1000 * 60 * 60 * 24))
          totalDays += days
          countWithDates++
        }
      })
      const avgFulfillmentDays = countWithDates > 0 ? totalDays / countWithDates : 0

      return {
        totalOrders,
        totalValue,
        avgOrderValue,
        onTimeRate,
        avgFulfillmentDays
      }
    })

    const categoryData = computed(() => {
      // Group inventory by category and calculate values
      // Filter inventory items to only include those with orders in the selected period
      const categoryMap = {}

      // Use a single neutral slate/gray color for all categories
      const singleColor = 'var(--chart-5)' // Neutral slate chart token (theme-aware)

      // Get SKUs from orders in the filtered time period
      const orderedSkus = new Set()
      allOrders.value.forEach(order => {
        if (order.items) {
          order.items.forEach(item => {
            orderedSkus.add(item.sku)
          })
        }
      })

      // Only include inventory items that have orders in the selected period
      // If no period is selected (all), include all inventory items
      const itemsToInclude = selectedPeriod.value === 'all'
        ? inventoryItems.value
        : inventoryItems.value.filter(item => orderedSkus.has(item.sku))

      itemsToInclude.forEach(item => {
        const cat = item.category.toLowerCase()
        if (!categoryMap[cat]) {
          categoryMap[cat] = {
            name: item.category,
            value: 0,
            color: singleColor,
            category: cat,
            count: 0
          }
        }
        categoryMap[cat].value += item.quantity_on_hand * item.unit_cost
        categoryMap[cat].count += 1
      })

      return Object.values(categoryMap)
    })

    const maxCategoryValue = computed(() => {
      if (categoryData.value.length === 0) return 1
      return Math.max(...categoryData.value.map(c => c.value))
    })

    const orderTrendData = computed(() => {
      // Group orders by month from the actual data
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

      // Initialize all months with 0 orders
      const monthMap = {}
      monthNames.forEach(month => {
        monthMap[month] = { month, orders: 0 }
      })

      // Count orders for each month
      if (Array.isArray(allOrders.value)) {
        allOrders.value.forEach(order => {
          if (order && order.order_date) {
            const date = new Date(order.order_date)
            const monthIndex = date.getMonth()
            // Check if monthIndex is valid (0-11)
            if (!isNaN(monthIndex) && monthIndex >= 0 && monthIndex <= 11) {
              const monthName = monthNames[monthIndex]
              monthMap[monthName].orders++
            }
          }
        })
      }

      // Return all months in order
      return monthNames.map(month => monthMap[month])
    })

    const maxOrderCount = computed(() => {
      if (orderTrendData.value.length === 0) return 10
      const max = Math.max(...orderTrendData.value.map(d => d.orders))
      // Round up to nearest 10 for cleaner axis, minimum 10
      return Math.max(10, Math.ceil(max / 10) * 10)
    })

    const topProducts = computed(() => {
      // Calculate top products from filtered order data
      const productMap = {}

      // allOrders is already filtered by API based on: month, warehouse, category, status
      allOrders.value.forEach(order => {
        if (order.items) {
          order.items.forEach(item => {
            const sku = item.sku

            // Find matching inventory item to get full product details
            // Note: inventoryItems is also filtered by API based on: warehouse, category
            const invItem = inventoryItems.value.find(i => i.sku === sku)

            // Skip products that don't match current inventory filters
            // (e.g., if filtering by warehouse A, don't show products from warehouse B)
            if (!invItem && (selectedLocation.value !== 'all' || selectedCategory.value !== 'all')) {
              return // Skip this product as it doesn't match inventory filters
            }

            if (!productMap[sku]) {
              productMap[sku] = {
                name: item.name,
                sku: sku,
                category: invItem?.category || 'Unknown',
                warehouse: invItem?.warehouse || 'Unknown',
                unitsOrdered: 0,
                revenue: 0,
                stockLevel: invItem ? (invItem.quantity_on_hand > invItem.reorder_point ? 'In Stock' : 'Low Stock') : 'Unknown',
                firstOrderDate: order.order_date
              }
            } else {
              // Update to EARLIEST order date (to show January at top when selecting All Months)
              if (order.order_date && (!productMap[sku].firstOrderDate || order.order_date < productMap[sku].firstOrderDate)) {
                productMap[sku].firstOrderDate = order.order_date
              }
            }
            productMap[sku].unitsOrdered += item.quantity
            productMap[sku].revenue += item.quantity * item.unit_price
          })
        }
      })

      // Convert to array, sort by first order date (earliest first = January at top), then by revenue, and take top 12
      return Object.values(productMap)
        .sort((a, b) => {
          // Sort by first order date (earliest first)
          // This ensures products first ordered in January appear before those first ordered in December
          const dateA = new Date(a.firstOrderDate || '9999-12-31')
          const dateB = new Date(b.firstOrderDate || '9999-12-31')
          if (dateA.getTime() !== dateB.getTime()) {
            return dateA.getTime() - dateB.getTime() // Earlier dates come first
          }
          // If dates are equal, sort by revenue (highest first)
          return b.revenue - a.revenue
        })
        .slice(0, 12)
    })

    const allBacklogItems = ref([])

    // Filter backlog based on inventory filters
    const backlogItems = computed(() => {
      if (selectedLocation.value === 'all' && selectedCategory.value === 'all') {
        return allBacklogItems.value
      }

      // Get SKUs of items that match the filters
      const validSkus = new Set(inventoryItems.value.map(item => item.sku))
      return allBacklogItems.value.filter(b => validSkus.has(b.item_sku))
    })

    const loadData = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()

        const [summaryData, ordersData, inventoryData, backlogData] = await Promise.all([
          api.getDashboardSummary(filters),
          api.getOrders(filters),
          api.getInventory(filters),
          api.getBacklog()
        ])

        summary.value = summaryData
        allOrders.value = ordersData
        inventoryItems.value = inventoryData
        allBacklogItems.value = backlogData
      } catch (err) {
        error.value = 'Failed to load dashboard data: ' + err.message
      } finally {
        loading.value = false
      }
    }

    const calculatePercentage = (value, goal) => {
      return ((value / goal) * 100).toFixed(2)
    }

    // Compute total orders once for efficiency
    const totalOrders = computed(() => {
      return statusData.value.delivered + statusData.value.shipped +
             statusData.value.processing + statusData.value.backordered
    })

    const getCircleSegment = (value) => {
      return totalOrders.value > 0 ? (value / totalOrders.value) * 440 : 0
    }

    const getStockBadge = (level) => {
      if (level === 'In Stock') return 'success'
      if (level === 'Low Stock') return 'warning'
      return 'danger'
    }

    const translateCategory = (category) => {
      const categoryMap = {
        'Circuit Boards': t('categories.circuitBoards'),
        'Sensors': t('categories.sensors'),
        'Actuators': t('categories.actuators'),
        'Controllers': t('categories.controllers'),
        'Power Supplies': t('categories.powerSupplies')
      }
      return categoryMap[category] || category
    }

    const translateStockLevel = (stockLevel) => {
      const stockMap = {
        'In Stock': t('status.inStock'),
        'Low Stock': t('status.lowStock')
      }
      return stockMap[stockLevel] || stockLevel
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low'),
        'High': t('priority.high'),
        'Medium': t('priority.medium'),
        'Low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    const formatDate = (dateString) => {
      if (!dateString) return '-'
      const { currentLocale } = useI18n()
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      const date = new Date(dateString)
      return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' })
    }

    const showProductDetail = (product) => {
      selectedProduct.value = product
      showProductModal.value = true
    }

    const showBacklogDetail = (item) => {
      selectedBacklogItem.value = item
      showBacklogModal.value = true
    }

    const openPOModal = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'create'
      showPOModal.value = true
    }

    const viewPO = (item) => {
      selectedBacklogForPO.value = item
      poModalMode.value = 'view'
      showPOModal.value = true
    }

    const handlePOCreated = (poData) => {
      // Update the backlog item with the new PO ID
      const item = allBacklogItems.value.find(b => b.id === poData.backlog_item_id)
      if (item) {
        item.purchase_order_id = poData.id
        item.purchase_order = poData
      }
      showPOModal.value = false
    }

    // Watch for filter changes and reload data
    watch([selectedPeriod, selectedLocation, selectedCategory, selectedStatus], () => {
      loadData()
    })

    onMounted(loadData)

    return {
      t,
      loading,
      error,
      summary,
      ordersData,
      fillRate,
      statusData,
      orderHealthMetrics,
      categoryData,
      maxCategoryValue,
      orderTrendData,
      maxOrderCount,
      topProducts,
      backlogItems,
      calculatePercentage,
      getCircleSegment,
      getStockBadge,
      translateCategory,
      translateStockLevel,
      translatePriority,
      formatDate,
      revenueGoal,
      revenueGoalDisplay,
      showProductModal,
      selectedProduct,
      showProductDetail,
      showBacklogModal,
      selectedBacklogItem,
      showBacklogDetail,
      selectedPeriod,
      selectedCurrency: currentCurrency,
      formatCurrency,
      Math,
      translateProductName,
      translateWarehouse,
      showPOModal,
      selectedBacklogForPO,
      poModalMode,
      openPOModal,
      viewPO,
      handlePOCreated
    }
  }
}
</script>

<style scoped>
.kpi-section {
  margin-block-end: var(--space-6);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(13.75rem, 100%), 1fr));
  gap: var(--space-4);
}

.kpi-goal {
  margin-block: var(--space-2) var(--space-3);
  font-size: var(--text-sm);
  color: var(--color-text-subtle);
}

.kpi-progress-bar {
  block-size: 6px;
  border-radius: 3px;
  background: var(--chart-track);
  overflow: hidden;
}

.kpi-progress {
  block-size: 100%;
  border-radius: 3px;
  background: var(--chart-1);
  transition: width 0.6s ease;
}

.kpi-progress.success {
  background: var(--chart-2);
}

/* Order health donut */
.order-health-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(14rem, 100%), 1fr));
  gap: var(--space-6);
  align-items: center;
}

.order-health-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
}

.donut-svg-compact {
  inline-size: min(12.5rem, 100%);
  block-size: auto;
  aspect-ratio: 1;
}

.donut-track {
  stroke: var(--chart-track);
}

.seg-delivered { stroke: var(--chart-2); }
.seg-shipped { stroke: var(--chart-1); }
.seg-processing { stroke: var(--chart-3); }
.seg-backordered { stroke: var(--chart-4); }

.donut-center-label {
  font-size: 12px;
  font-weight: 500;
  fill: var(--chart-axis);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.donut-center-value {
  font-size: 36px;
  font-weight: 700;
  fill: var(--color-text);
}

.donut-legend-compact {
  display: grid;
  grid-template-columns: repeat(2, auto);
  gap: var(--space-2) var(--space-5);
  list-style: none;
  padding: 0;
  margin: 0;
}

.legend-item-compact {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--color-text-muted);
}

.legend-dot {
  inline-size: 10px;
  block-size: 10px;
  border-radius: 2px;
  flex-shrink: 0;
}

.order-health-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
  justify-content: center;
  align-items: center;
}

.health-metric {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  inline-size: 100%;
  text-align: center;
}

.health-metric-label {
  font-size: var(--text-xs);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-subtle);
}

.health-metric-value {
  font-size: var(--text-xl);
  font-weight: 700;
  letter-spacing: -0.025em;
  color: var(--color-text);
}

.metric-good { color: var(--color-success); }
.metric-warning { color: var(--color-warning); }
.metric-bad { color: var(--color-danger); }

/* Inventory by category bars */
.horizontal-bar-chart {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.h-bar-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.h-bar-label {
  inline-size: 7.5rem;
  flex-shrink: 0;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-muted);
}

.h-bar-container {
  flex: 1;
  min-inline-size: 0;
  block-size: 2rem;
  border-radius: var(--radius-sm);
  background: var(--chart-track);
  overflow: hidden;
}

.h-bar {
  block-size: 100%;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-inline-end: var(--space-3);
  transition: width 0.6s ease;
}

.h-bar-value {
  font-size: var(--text-sm);
  font-weight: 700;
  /* On-primary flips with the theme, matching the lighter dark-mode bar */
  color: var(--color-on-primary);
}

/* Shortages */
.no-backlog {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-12);
  text-align: center;
}

.success-icon {
  inline-size: 3rem;
  block-size: 3rem;
  color: var(--color-success);
}

.no-backlog-text {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-success);
}

.days-delayed {
  font-weight: 600;
}

.days-late { color: var(--color-danger); }
.days-warn { color: var(--color-warning); }

.clickable-row {
  cursor: pointer;
}
</style>
