<template>
  <AppShell
    :nav-label="t('nav.primary')"
    :open-nav-label="t('shell.openMenu')"
    :close-nav-label="t('shell.closeMenu')"
    :skip-label="t('shell.skipToContent')"
  >
    <template #sidebar>
      <AppSidebar>
        <template #brand>
          <div class="brand">
            <span class="brand__name">{{ t('nav.companyName') }}</span>
            <span class="brand__subtitle">{{ t('nav.subtitle') }}</span>
          </div>
        </template>

        <SidebarNav :items="navItems" :label="t('nav.primary')" />

        <template #footer>
          <div class="sidebar-tools">
            <LanguageSwitcher />
            <ThemeSwitcher />
          </div>
          <ProfileMenu
            @show-profile-details="showProfileDetails = true"
            @show-tasks="showTasks = true"
          />
        </template>
      </AppSidebar>
    </template>

    <template #topbar>
      <FilterBar />
    </template>

    <router-view />
  </AppShell>

  <ProfileDetailsModal
    :is-open="showProfileDetails"
    @close="showProfileDetails = false"
  />

  <TasksModal
    :is-open="showTasks"
    :tasks="tasks"
    @close="showTasks = false"
    @add-task="addTask"
    @delete-task="deleteTask"
    @toggle-task="toggleTask"
  />
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { api } from './api'
import { useAuth } from './composables/useAuth'
import { useI18n } from './composables/useI18n'
import FilterBar from './components/FilterBar.vue'
import ProfileMenu from './components/ProfileMenu.vue'
import ProfileDetailsModal from './components/ProfileDetailsModal.vue'
import TasksModal from './components/TasksModal.vue'
import LanguageSwitcher from './components/LanguageSwitcher.vue'
import AppShell from './components/shell/AppShell.vue'
import AppSidebar from './components/shell/AppSidebar.vue'
import SidebarNav from './components/shell/SidebarNav.vue'
import ThemeSwitcher from './components/shell/ThemeSwitcher.vue'
import { useNavItems } from './composables/useNavItems'

export default {
  name: 'App',
  components: {
    FilterBar,
    ProfileMenu,
    ProfileDetailsModal,
    TasksModal,
    LanguageSwitcher,
    AppShell,
    AppSidebar,
    SidebarNav,
    ThemeSwitcher
  },
  setup() {
    const { currentUser } = useAuth()
    const { t } = useI18n()
    // Sidebar items come from route meta.nav; recomputes when the locale changes
    const navItems = useNavItems(t)
    const showProfileDetails = ref(false)
    const showTasks = ref(false)
    const apiTasks = ref([])

    // Merge mock tasks from currentUser with API tasks
    const tasks = computed(() => {
      return [...currentUser.value.tasks, ...apiTasks.value]
    })

    const loadTasks = async () => {
      try {
        apiTasks.value = await api.getTasks()
      } catch (err) {
        console.error('Failed to load tasks:', err)
      }
    }

    const addTask = async (taskData) => {
      try {
        const newTask = await api.createTask(taskData)
        // Add new task to the beginning of the array
        apiTasks.value.unshift(newTask)
      } catch (err) {
        console.error('Failed to add task:', err)
      }
    }

    const deleteTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const isMockTask = currentUser.value.tasks.some(t => t.id === taskId)

        if (isMockTask) {
          // Remove from mock tasks
          const index = currentUser.value.tasks.findIndex(t => t.id === taskId)
          if (index !== -1) {
            currentUser.value.tasks.splice(index, 1)
          }
        } else {
          // Remove from API tasks
          await api.deleteTask(taskId)
          apiTasks.value = apiTasks.value.filter(t => t.id !== taskId)
        }
      } catch (err) {
        console.error('Failed to delete task:', err)
      }
    }

    const toggleTask = async (taskId) => {
      try {
        // Check if it's a mock task (from currentUser)
        const mockTask = currentUser.value.tasks.find(t => t.id === taskId)

        if (mockTask) {
          // Toggle mock task status
          mockTask.status = mockTask.status === 'pending' ? 'completed' : 'pending'
        } else {
          // Toggle API task
          const updatedTask = await api.toggleTask(taskId)
          const index = apiTasks.value.findIndex(t => t.id === taskId)
          if (index !== -1) {
            apiTasks.value[index] = updatedTask
          }
        }
      } catch (err) {
        console.error('Failed to toggle task:', err)
      }
    }

    onMounted(loadTasks)

    return {
      t,
      navItems,
      showProfileDetails,
      showTasks,
      tasks,
      addTask,
      deleteTask,
      toggleTask
    }
  }
}
</script>

<style scoped>
/* Brand block only; layout belongs to AppShell/AppSidebar */
.brand {
  display: grid;
  gap: var(--space-1);
  min-inline-size: 0;
}

.brand__name {
  font-size: var(--text-lg);
  font-weight: 700;
  letter-spacing: -0.025em;
  line-height: var(--leading-tight);
}

.brand__subtitle {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
}

/* Sidebar footer row: language picker fills the row, theme button sits at the
   inline-end. minmax(0, 1fr) lets the picker's label truncate instead of
   pushing the button out. */
.sidebar-tools {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--space-2);
  align-items: center;
}
</style>
