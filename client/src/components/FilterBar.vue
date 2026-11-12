<template>
  <search class="filters-bar">
    <form class="filters-form" :aria-label="t('shell.filters')" @submit.prevent>
      <div class="filters-grid">
        <div class="filter-group">
          <label for="filter-period">{{ t('filters.timePeriod') }}</label>
          <select id="filter-period" v-model="selectedPeriod" class="select filter-select">
              <option value="all">{{ t('filters.allMonths') }}</option>
              <option value="2025-01">{{ t('months.january') }}</option>
              <option value="2025-02">{{ t('months.february') }}</option>
              <option value="2025-03">{{ t('months.march') }}</option>
              <option value="2025-04">{{ t('months.april') }}</option>
              <option value="2025-05">{{ t('months.may') }}</option>
              <option value="2025-06">{{ t('months.june') }}</option>
              <option value="2025-07">{{ t('months.july') }}</option>
              <option value="2025-08">{{ t('months.august') }}</option>
              <option value="2025-09">{{ t('months.september') }}</option>
              <option value="2025-10">{{ t('months.october') }}</option>
              <option value="2025-11">{{ t('months.november') }}</option>
              <option value="2025-12">{{ t('months.december') }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label for="filter-location">{{ t('filters.location') }}</label>
          <select id="filter-location" v-model="selectedLocation" class="select filter-select">
              <option value="all">{{ t('filters.all') }}</option>
              <option value="San Francisco">{{ t('warehouses.sanFrancisco') }}</option>
              <option value="London">{{ t('warehouses.london') }}</option>
              <option value="Tokyo">{{ t('warehouses.tokyo') }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label for="filter-category">{{ t('filters.category') }}</label>
          <select id="filter-category" v-model="selectedCategory" class="select filter-select">
              <option value="all">{{ t('filters.all') }}</option>
              <option value="circuit boards">{{ t('categories.circuitBoards') }}</option>
              <option value="sensors">{{ t('categories.sensors') }}</option>
              <option value="actuators">{{ t('categories.actuators') }}</option>
              <option value="controllers">{{ t('categories.controllers') }}</option>
              <option value="power supplies">{{ t('categories.powerSupplies') }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label for="filter-status">{{ t('filters.orderStatus') }}</label>
          <select id="filter-status" v-model="selectedStatus" class="select filter-select">
              <option value="all">{{ t('filters.all') }}</option>
              <option value="delivered">{{ t('status.delivered') }}</option>
              <option value="shipped">{{ t('status.shipped') }}</option>
              <option value="processing">{{ t('status.processing') }}</option>
              <option value="backordered">{{ t('status.backordered') }}</option>
          </select>
        </div>
      </div>
      <button
        type="button"
        class="icon-btn reset-filters-btn"
        :disabled="!hasActiveFilters"
        :title="t('filters.reset')"
        :aria-label="t('filters.reset')"
        @click="resetFilters"
      >
        <svg class="reset-icon" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
          <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
        </svg>
      </button>
    </form>
  </search>
</template>

<script>
import { useFilters } from '../composables/useFilters'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'FilterBar',
  setup() {
    const {
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    } = useFilters()

    const { t } = useI18n()

    return {
      t,
      selectedPeriod,
      selectedLocation,
      selectedCategory,
      selectedStatus,
      hasActiveFilters,
      resetFilters
    }
  }
}
</script>

<style scoped>
/* AppShell owns the bar's background, padding and stickiness; this only
   arranges the controls inside it. */
.filters-bar {
  display: block;
  flex: 1;
  min-inline-size: 0;
}

.filters-form {
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
}

/* Wraps onto extra rows on narrow screens instead of scrolling sideways */
.filters-grid {
  display: flex;
  flex: 1;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-4);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-inline-size: 0;
}

.filter-group label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
}

.filter-select {
  min-inline-size: 8.75rem;
  max-inline-size: 100%;
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
}

.reset-filters-btn {
  flex-shrink: 0;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
}

.reset-filters-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.reset-icon {
  inline-size: 1.125rem;
  block-size: 1.125rem;
}

/* Phones: two filters per row, label above each select */
@media (width < 40rem) {
  .filters-form {
    align-items: flex-start;
  }

  .filters-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .filter-group {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-1);
  }

  .filter-select {
    min-inline-size: 0;
    inline-size: 100%;
  }
}
</style>
