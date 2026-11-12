import './styles/index.css'
import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import Dashboard from './views/Dashboard.vue'
import Inventory from './views/Inventory.vue'
import Orders from './views/Orders.vue'
import Demand from './views/Demand.vue'
import Spending from './views/Spending.vue'
import Reports from './views/Reports.vue'
import Restocking from './views/Restocking.vue'

// Sidebar items are built from meta.nav by useNavItems(), so the router is the
// single source of truth for navigation. `icon` is SVG path data for a 24x24
// stroke icon (rendered by SidebarNav); `order` is the sidebar position.
// Backlog.vue is intentionally unrouted: the Dashboard's shortage table covers it.
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: Dashboard,
      meta: { nav: { labelKey: 'nav.overview', order: 1, icon: 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z' } }
    },
    {
      path: '/inventory',
      component: Inventory,
      meta: { nav: { labelKey: 'nav.inventory', order: 2, icon: 'M21 8 12 3 3 8v8l9 5 9-5zM3 8l9 5 9-5M12 13v8' } }
    },
    {
      path: '/orders',
      component: Orders,
      meta: { nav: { labelKey: 'nav.orders', order: 3, icon: 'M9 4h6v3H9zM9 5.5H6v15h12v-15h-3M9 12h6M9 16h4' } }
    },
    {
      path: '/spending',
      component: Spending,
      meta: { nav: { labelKey: 'nav.finance', order: 4, icon: 'M3 6h18v12H3zM3 10h18M7 15h3' } }
    },
    {
      path: '/demand',
      component: Demand,
      meta: { nav: { labelKey: 'nav.demandForecast', order: 5, icon: 'M3 17l6-6 4 4 8-8M15 7h6v6' } }
    },
    {
      path: '/restocking',
      component: Restocking,
      meta: { nav: { labelKey: 'nav.restocking', order: 6, icon: 'M2 6h12v10H2zM14 9h4l4 4v3h-8M6 19.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3M18 19.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3' } }
    },
    {
      path: '/reports',
      component: Reports,
      meta: { nav: { labelKey: 'nav.reports', order: 7, icon: 'M4 20V10M10 20V4M16 20v-7M2 20h20' } }
    }
  ]
})

// Mark "just arrived on a page" for a moment after each navigation. The dark
// terminal skin plays its chart reveal only under this flag (terminal.css):
// views remount their content on every filter change, and replaying the reveal
// then would hide data that is already there. 1.2s covers a normal data load;
// if the API is slower the chart simply appears without the reveal.
const ROUTE_ENTER_MS = 1200
let routeEnterTimer
router.afterEach(() => {
  const root = document.documentElement
  root.dataset.routeEnter = ''
  clearTimeout(routeEnterTimer)
  routeEnterTimer = setTimeout(() => delete root.dataset.routeEnter, ROUTE_ENTER_MS)
})

const app = createApp(App)
app.use(router)
app.mount('#app')
