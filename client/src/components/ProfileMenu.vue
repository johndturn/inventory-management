<template>
  <PopoverMenu :label="currentUser.name">
    <template #trigger>
      <span class="avatar" aria-hidden="true">{{ getInitials(currentUser.name) }}</span>
      <span class="profile-name truncate">{{ currentUser.name }}</span>
      <svg class="icon chevron" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M6 15l6-6 6 6" />
      </svg>
    </template>

    <template #default="{ close }">
      <div class="profile-header">
        <span class="avatar avatar--lg" aria-hidden="true">{{ getInitials(currentUser.name) }}</span>
        <div class="user-info">
          <div class="user-name truncate">{{ currentUser.name }}</div>
          <div class="user-email truncate">{{ currentUser.email }}</div>
        </div>
      </div>
      <hr class="divider" />
      <button type="button" class="popover-menu__item" @click="showProfileDetails(close)">
        <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-3.3 3.6-6 8-6s8 2.7 8 6" />
        </svg>
        {{ t('profile.profileDetails') }}
      </button>
      <button type="button" class="popover-menu__item" @click="showTasks(close)">
        <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <path d="M8 12l3 3 5-6" />
        </svg>
        {{ t('profile.myTasks') }}
        <span v-if="pendingTaskCount > 0" class="task-badge">{{ pendingTaskCount }}</span>
      </button>
      <hr class="divider" />
      <button type="button" class="popover-menu__item logout" @click="handleLogout(close)">
        <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M10 20H5a1 1 0 01-1-1V5a1 1 0 011-1h5M15 8l4 4-4 4M19 12H9" />
        </svg>
        {{ t('profile.logout') }}
      </button>
    </template>
  </PopoverMenu>
</template>

<script>
import { computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'
import PopoverMenu from './shell/PopoverMenu.vue'

export default {
  name: 'ProfileMenu',
  components: { PopoverMenu },
  emits: ['show-profile-details', 'show-tasks'],
  setup(props, { emit }) {
    const { currentUser, logout, getInitials } = useAuth()
    const { t } = useI18n()

    const pendingTaskCount = computed(() =>
      currentUser.value.tasks.filter(task => task.status === 'pending').length
    )

    // The popover is light-dismiss, but item clicks stay inside it, so each
    // action closes it explicitly via the slot's close()
    const showProfileDetails = (close) => {
      close()
      emit('show-profile-details')
    }
    const showTasks = (close) => {
      close()
      emit('show-tasks')
    }
    const handleLogout = (close) => {
      close()
      logout()
    }

    return {
      t,
      currentUser,
      getInitials,
      pendingTaskCount,
      showProfileDetails,
      showTasks,
      handleLogout
    }
  }
}
</script>

<style scoped>
.avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  inline-size: 2rem;
  block-size: 2rem;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.025em;
}

.avatar--lg {
  inline-size: 3rem;
  block-size: 3rem;
  font-size: var(--text-md);
  font-weight: 700;
}

.profile-name {
  flex: 1;
  min-inline-size: 0;
  font-size: var(--text-sm);
  font-weight: 500;
}

.chevron {
  color: var(--color-text-subtle);
}

.profile-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
}

.user-info {
  flex: 1;
  min-inline-size: 0;
}

.user-name {
  font-weight: 600;
}

.user-email {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.divider {
  margin-block: var(--space-1);
  border: 0;
  border-block-start: 1px solid var(--color-border);
}

.popover-menu__item .icon {
  color: var(--color-text-muted);
}

.popover-menu__item.logout,
.popover-menu__item.logout .icon {
  color: var(--color-danger);
}

.task-badge {
  margin-inline-start: auto;
  min-inline-size: 1.25rem;
  padding: 0 var(--space-2);
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: var(--text-xs);
  font-weight: 600;
  text-align: center;
}
</style>
