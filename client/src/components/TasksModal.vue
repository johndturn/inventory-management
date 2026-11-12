<template>
  <dialog
    ref="dialogEl"
    class="modal-container modal-container--lg"
    :aria-labelledby="titleId"
    @close="onClose"
    @click="onDialogClick"
  >
    <div class="modal-header">
      <h2 :id="titleId" class="modal-title">{{ t('tasks.title') }}</h2>
      <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
        <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
    </div>

    <div class="modal-body">
      <!-- Add Task Form -->
      <form class="task-form" @submit.prevent="handleAddTask">
        <div class="field">
          <label for="task-title">{{ t('tasks.taskTitle') }}</label>
          <input
            id="task-title"
            v-model="newTask.title"
            type="text"
            class="input"
            :placeholder="t('tasks.taskTitlePlaceholder')"
          />
        </div>

        <div class="form-row">
          <div class="field">
            <label for="task-priority">{{ t('tasks.priority') }}</label>
            <select id="task-priority" v-model="newTask.priority" class="select">
              <option value="high">{{ t('priority.high') }}</option>
              <option value="medium">{{ t('priority.medium') }}</option>
              <option value="low">{{ t('priority.low') }}</option>
            </select>
          </div>

          <div class="field">
            <label for="task-due-date">{{ t('tasks.dueDate') }}</label>
            <input id="task-due-date" v-model="newTask.dueDate" type="date" class="input" />
          </div>

          <button
            type="submit"
            class="btn-primary task-add-btn"
            :disabled="!newTask.title.trim() || !newTask.dueDate"
          >
            {{ t('tasks.addTask') }}
          </button>
        </div>
      </form>

      <!-- Tasks List -->
      <p v-if="sortedTasks.length === 0" class="no-tasks">
        {{ t('tasks.noTasks') }}
      </p>

      <ul v-else role="list" class="tasks-list">
        <li
          v-for="task in sortedTasks"
          :key="task.id"
          class="task-item"
          :class="[`priority-${task.priority}`, { completed: task.status === 'completed' }]"
        >
          <div class="task-header">
            <label class="task-check-title">
              <input
                type="checkbox"
                class="task-checkbox"
                :checked="task.status === 'completed'"
                @change="$emit('toggle-task', task.id)"
              />
              <span class="task-title">{{ task.title }}</span>
            </label>
            <button
              type="button"
              class="icon-btn task-delete-btn"
              :title="t('tasks.deleteTask')"
              :aria-label="t('tasks.deleteTask')"
              @click="$emit('delete-task', task.id)"
            >
              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </div>

          <div class="task-footer">
            <span class="priority-badge" :class="task.priority">
              {{ translatePriority(task.priority) }}
            </span>
            <span class="task-due-date">
              <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
                <rect x="4" y="5" width="16" height="15" rx="2" />
                <path d="M8 3v4M16 3v4M4 10h16" />
              </svg>
              {{ formatDueDate(task.dueDate) }}
            </span>
            <span class="status-badge" :class="getStatusClass(task.dueDate, task.status)">
              {{ getStatusText(task.dueDate, task.status) }}
            </span>
          </div>
        </li>
      </ul>
    </div>

    <div class="modal-footer">
      <button type="button" class="btn-secondary" @click="close">{{ t('profileDetails.close') }}</button>
    </div>
  </dialog>
</template>

<script>
import { ref, computed, watch, onMounted, useId } from 'vue'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'TasksModal',
  props: {
    isOpen: {
      type: Boolean,
      required: true
    },
    tasks: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'add-task', 'delete-task', 'toggle-task'],
  setup(props, { emit }) {
    const { t, currentLocale } = useI18n()
    const newTask = ref({
      title: '',
      priority: 'medium',
      dueDate: ''
    })

    const sortedTasks = computed(() => {
      // Don't sort - just return tasks in their current order (newest first)
      return [...props.tasks]
    })

    const dialogEl = ref(null)
    const titleId = `tasks-title-${useId()}`

    // Drive the native dialog from the isOpen prop; showModal() gives focus trap, Escape and inert page for free
    watch(() => props.isOpen, (open) => {
      const d = dialogEl.value
      if (!d) return
      if (open && !d.open) d.showModal()
      else if (!open && d.open) d.close()
    })
    onMounted(() => {
      if (props.isOpen) dialogEl.value?.showModal()
    })

    // The native 'close' event fires for Escape and dialog.close(); only tell the parent if it still thinks we're open
    const onClose = () => {
      if (props.isOpen) emit('close')
    }

    // Backdrop tap: clicks on the dialog element itself (not its children) are outside the content box
    const onDialogClick = (e) => {
      if (e.target === dialogEl.value) dialogEl.value.close()
    }

    const close = () => dialogEl.value?.close()

    const handleAddTask = () => {
      if (newTask.value.title.trim() && newTask.value.dueDate) {
        emit('add-task', {
          title: newTask.value.title.trim(),
          priority: newTask.value.priority,
          dueDate: newTask.value.dueDate
        })
        newTask.value = {
          title: '',
          priority: 'medium',
          dueDate: ''
        }
      }
    }

    const formatDueDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return ''
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const dueDate = new Date(date)
      dueDate.setHours(0, 0, 0, 0)

      const diffTime = dueDate - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      const isJapanese = currentLocale.value === 'ja'

      if (diffDays === 0) return isJapanese ? '今日' : 'today'
      if (diffDays === 1) return isJapanese ? '明日' : 'tomorrow'
      if (diffDays === -1) return isJapanese ? '昨日' : 'yesterday'
      if (diffDays < 0) return isJapanese ? `${Math.abs(diffDays)}日前` : `${Math.abs(diffDays)} days ago`
      if (diffDays < 7) return isJapanese ? `${diffDays}日後` : `in ${diffDays} days`

      const locale = isJapanese ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        month: 'short',
        day: 'numeric',
        year: date.getFullYear() !== today.getFullYear() ? 'numeric' : undefined
      })
    }

    const getStatusClass = (dueDate, status) => {
      if (status === 'completed') return 'completed'

      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const due = new Date(dueDate)
      due.setHours(0, 0, 0, 0)

      const diffTime = due - today
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

      if (diffDays < 0) return 'overdue'
      if (diffDays <= 1) return 'urgent'
      return 'upcoming'
    }

    const getStatusText = (dueDate, status) => {
      const isJapanese = currentLocale.value === 'ja'

      if (status === 'completed') return isJapanese ? '完了' : 'Completed'

      const statusClass = getStatusClass(dueDate, status)
      if (statusClass === 'overdue') return isJapanese ? '期限超過' : 'Overdue'
      if (statusClass === 'urgent') return isJapanese ? 'もうすぐ期限' : 'Due Soon'
      return isJapanese ? '予定' : 'Upcoming'
    }

    const translatePriority = (priority) => {
      const priorityMap = {
        'high': t('priority.high'),
        'medium': t('priority.medium'),
        'low': t('priority.low')
      }
      return priorityMap[priority] || priority
    }

    return {
      t,
      dialogEl,
      titleId,
      onClose,
      onDialogClick,
      newTask,
      sortedTasks,
      close,
      handleAddTask,
      formatDueDate,
      getStatusClass,
      getStatusText,
      translatePriority
    }
  }
}
</script>

<style scoped>
/* Add-task form */
.task-form {
  display: grid;
  gap: var(--space-4);
  margin-block-end: var(--space-5);
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(10rem, 100%), 1fr));
  gap: var(--space-4);
  align-items: end;
}

.task-add-btn {
  white-space: nowrap;
}

.no-tasks {
  padding: var(--space-8);
  text-align: center;
  color: var(--color-text-muted);
  font-style: italic;
}

.tasks-list {
  display: grid;
  gap: var(--space-3);
}

.task-item {
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-inline-start-width: 4px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.task-item:hover {
  border-color: var(--color-border-strong);
}

/* Priority stripe */
.task-item.priority-high { border-inline-start-color: var(--color-danger); }
.task-item.priority-medium { border-inline-start-color: var(--color-warning); }
.task-item.priority-low { border-inline-start-color: var(--color-info); }

.task-item.completed {
  opacity: 0.65;
}

.task-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  margin-block-end: var(--space-2);
}

.task-check-title {
  display: flex;
  flex: 1;
  align-items: center;
  gap: var(--space-3);
  min-inline-size: 0;
  cursor: pointer;
}

.task-checkbox {
  inline-size: 1.25rem;
  block-size: 1.25rem;
  flex-shrink: 0;
  accent-color: var(--color-primary);
  cursor: pointer;
}

.task-title {
  font-weight: 600;
  line-height: var(--leading-tight);
  overflow-wrap: anywhere;
}

.task-item.completed .task-title {
  text-decoration: line-through;
  color: var(--color-text-subtle);
}

.task-delete-btn:hover {
  background: var(--color-danger-soft);
  color: var(--color-on-danger-soft);
}

.task-footer {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-2) var(--space-4);
}

.task-due-date {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.task-due-date .icon {
  inline-size: 0.875rem;
  block-size: 0.875rem;
}

.priority-badge,
.status-badge {
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  font-size: var(--text-xs);
  font-weight: 600;
}

.priority-badge {
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.status-badge {
  margin-inline-start: auto;
}

.priority-badge.high,
.status-badge.overdue {
  background: var(--color-danger-soft);
  color: var(--color-on-danger-soft);
}

.priority-badge.medium,
.status-badge.urgent {
  background: var(--color-warning-soft);
  color: var(--color-on-warning-soft);
}

.priority-badge.low,
.status-badge.upcoming {
  background: var(--color-info-soft);
  color: var(--color-on-info-soft);
}

.status-badge.completed {
  background: var(--color-success-soft);
  color: var(--color-on-success-soft);
}
</style>
