import { computed } from 'vue'
import { useRouter } from 'vue-router'

/*
 * Builds sidebar items from route meta, so the router stays the single source
 * of truth. A new route appears in the nav by declaring meta.nav, and the nav
 * can never link to a route that does not exist.
 *
 *   { path: '/orders', component: Orders,
 *     meta: { nav: { labelKey: 'nav.orders', icon: 'M3 7h18M3 12h18M3 17h18', order: 3 } } }
 *
 * `t` is the app's translate function. The computed re-runs when the locale
 * changes, as long as t() reads a reactive locale ref.
 */
export function useNavItems(t) {
  const router = useRouter()

  return computed(() =>
    router
      .getRoutes()
      .filter((route) => route.meta?.nav)
      .sort((a, b) => (a.meta.nav.order ?? 0) - (b.meta.nav.order ?? 0))
      .map((route) => ({
        to: route.path,
        label: t(route.meta.nav.labelKey),
        icon: route.meta.nav.icon
      }))
  )
}
