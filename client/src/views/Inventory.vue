<template>
  <div class="inventory">
    <div class="page-header">
      <div>
        <h1>{{ t('inventory.title') }}</h1>
        <p>{{ t('inventory.description') }}</p>
      </div>
    </div>

    <div v-if="loading" class="loading">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else>
      <div class="card card--flush">
        <div class="card-header">
          <h2 class="card-title">{{ t('inventory.stockLevels') }} ({{ filteredItems.length }} {{ t('inventory.skus') }})</h2>
          <div class="search-box">
            <svg class="icon search-icon" viewBox="0 0 20 20" aria-hidden="true">
              <circle cx="9" cy="9" r="5.5" />
              <path d="M13 13l4 4" />
            </svg>
            <input
              v-model="searchQuery"
              type="search"
              :placeholder="t('inventory.searchPlaceholder')"
              :aria-label="t('inventory.searchPlaceholder')"
              class="input search-input"
            />
            <button
              v-if="searchQuery"
              type="button"
              @click="searchQuery = ''"
              class="icon-btn clear-search"
              :aria-label="t('inventory.clearSearch')"
              :title="t('inventory.clearSearch')"
            >
              <svg class="icon" viewBox="0 0 20 20" aria-hidden="true">
                <path d="M15 5L5 15M5 5l10 10" />
              </svg>
            </button>
          </div>
        </div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th scope="col">{{ t('inventory.table.sku') }}</th>
                <th scope="col">{{ t('inventory.table.itemName') }}</th>
                <th scope="col">{{ t('inventory.table.category') }}</th>
                <th scope="col" class="num">{{ t('inventory.table.quantityOnHand') }}</th>
                <th scope="col" class="num">{{ t('inventory.table.reorderPoint') }}</th>
                <th scope="col" class="num">{{ t('inventory.table.unitCost') }}</th>
                <th scope="col" class="num">{{ t('inventory.table.totalValue') }}</th>
                <th scope="col">{{ t('inventory.table.location') }}</th>
                <th scope="col">{{ t('inventory.table.status') }}</th>
              </tr>
            </thead>
            <tbody>
              <!-- Row click is a mouse convenience; the SKU button is the keyboard/AT entry point -->
              <tr
                v-for="item in filteredItems"
                :key="item.id"
                class="clickable-row"
                @click="showItemDetail(item)"
              >
                <td><button type="button" class="row-link" @click.stop="showItemDetail(item)">{{ item.sku }}</button></td>
                <td>{{ translateProductName(item.name) }}</td>
                <td>{{ translateCategory(item.category) }}</td>
                <td class="num"><strong>{{ item.quantity_on_hand }}</strong></td>
                <td class="num">{{ item.reorder_point }}</td>
                <td class="num">{{ currencySymbol }}{{ item.unit_cost.toFixed(2) }}</td>
                <td class="num"><strong>{{ currencySymbol }}{{ (item.quantity_on_hand * item.unit_cost).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) }}</strong></td>
                <td>{{ translateWarehouse(item.location) }}</td>
                <td>
                  <span :class="['badge', getStockStatusClass(item)]">
                    {{ getStockStatus(item) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <InventoryDetailModal
      :is-open="showItemModal"
      :inventory-item="selectedItem"
      @close="showItemModal = false"
    />
  </div>
</template>

<script>
import { ref, onMounted, watch, computed } from 'vue'
import { api } from '../api'
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'
import InventoryDetailModal from '../components/InventoryDetailModal.vue'

export default {
  name: 'Inventory',
  components: {
    InventoryDetailModal
  },
  setup() {
    const { t, currentCurrency, translateProductName, translateWarehouse } = useI18n()

    const currencySymbol = computed(() => {
      return currentCurrency.value === 'JPY' ? '¥' : '$'
    })

    const loading = ref(true)
    const error = ref(null)
    const items = ref([])
    const searchQuery = ref('')

    // Modal state
    const showItemModal = ref(false)
    const selectedItem = ref(null)

    // Use shared filters
    const { selectedLocation, selectedCategory, getCurrentFilters } = useFilters()

    // Stock status order for sorting (using status keys)
    const STATUS_ORDER = { 'lowStock': 0, 'adequate': 1, 'inStock': 2 }

    // Get stock status key (for sorting and translation)
    const getStockStatusKey = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'lowStock'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'adequate'
      } else {
        return 'inStock'
      }
    }

    // Computed property to filter items by search query and sort by stock status
    const filteredItems = computed(() => {
      let filtered = items.value

      // Apply search filter if query exists
      if (searchQuery.value.trim()) {
        const query = searchQuery.value.toLowerCase().trim()
        filtered = filtered.filter(item =>
          item.name.toLowerCase().includes(query)
        )
      }

      // Sort by stock status: Low Stock first, then Adequate, then In Stock
      // Always create a copy to avoid mutating the original array
      return filtered.slice().sort((a, b) => {
        const statusA = getStockStatusKey(a)
        const statusB = getStockStatusKey(b)
        return STATUS_ORDER[statusA] - STATUS_ORDER[statusB]
      })
    })

    const loadInventory = async () => {
      try {
        loading.value = true
        const filters = getCurrentFilters()
        // Inventory doesn't support month/status filters, only warehouse and category
        items.value = await api.getInventory({
          warehouse: filters.warehouse,
          category: filters.category
        })
      } catch (err) {
        error.value = 'Failed to load inventory: ' + err.message
      } finally {
        loading.value = false
      }
    }

    // Watch for filter changes and reload data
    watch([selectedLocation, selectedCategory], () => {
      loadInventory()
    })

    const getStockStatus = (item) => {
      const key = getStockStatusKey(item)
      return t(`status.${key}`)
    }

    const getStockStatusClass = (item) => {
      if (item.quantity_on_hand <= item.reorder_point) {
        return 'danger'
      } else if (item.quantity_on_hand <= item.reorder_point * 1.5) {
        return 'warning'
      } else {
        return 'success'
      }
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

    const showItemDetail = (item) => {
      selectedItem.value = item
      showItemModal.value = true
    }

    onMounted(loadInventory)

    return {
      t,
      loading,
      error,
      items,
      searchQuery,
      filteredItems,
      getStockStatus,
      getStockStatusClass,
      translateCategory,
      showItemModal,
      selectedItem,
      showItemDetail,
      currencySymbol,
      translateProductName,
      translateWarehouse
    }
  }
}
</script>

<style scoped>
.search-box {
  position: relative;
  display: flex;
  align-items: center;
  inline-size: min(20rem, 100%);
}

.search-icon {
  position: absolute;
  inset-inline-start: var(--space-3);
  inline-size: 1.125rem;
  block-size: 1.125rem;
  color: var(--color-text-subtle);
  pointer-events: none;
}

.search-input {
  inline-size: 100%;
  padding-inline: var(--space-10);
  font-size: var(--text-base);
}

.search-input::placeholder {
  color: var(--color-text-subtle);
}

.clear-search {
  position: absolute;
  inset-inline-end: var(--space-1);
  inline-size: calc(var(--control-h) - var(--space-2));
  block-size: calc(var(--control-h) - var(--space-2));
}

.clickable-row {
  cursor: pointer;
}
</style>
