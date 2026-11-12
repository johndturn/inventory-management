<template>
  <dialog
    ref="dialogEl"
    class="modal-container modal-container--sm"
    :aria-labelledby="titleId"
    @close="onClose"
    @click="onDialogClick"
  >
    <div class="modal-header">
      <h2 :id="titleId" class="modal-title">{{ t('profileDetails.title') }}</h2>
      <button type="button" class="close-button" :aria-label="t('common.close')" @click="close">
        <svg class="icon" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
    </div>

    <div class="modal-body">
      <div class="profile-section">
        <div class="avatar-section">
          <div class="avatar-xl" aria-hidden="true">
            {{ getInitials(currentUser.name) }}
          </div>
          <h3 class="profile-name">{{ currentUser.name }}</h3>
          <p class="profile-job-title">{{ currentUser.jobTitle }}</p>
        </div>

        <dl class="detail-grid">
          <div class="info-item">
            <dt class="detail-label">{{ t('profileDetails.email') }}</dt>
            <dd class="detail-value">{{ currentUser.email }}</dd>
          </div>
          <div class="info-item">
            <dt class="detail-label">{{ t('profileDetails.department') }}</dt>
            <dd class="detail-value">{{ currentUser.department }}</dd>
          </div>
          <div class="info-item">
            <dt class="detail-label">{{ t('profileDetails.location') }}</dt>
            <dd class="detail-value">{{ currentUser.location }}</dd>
          </div>
          <div class="info-item">
            <dt class="detail-label">{{ t('profileDetails.phone') }}</dt>
            <dd class="detail-value">{{ currentUser.phone }}</dd>
          </div>
          <div class="info-item">
            <dt class="detail-label">{{ t('profileDetails.joinDate') }}</dt>
            <dd class="detail-value">{{ formatDate(currentUser.joinDate) }}</dd>
          </div>
          <div class="info-item">
            <dt class="detail-label">{{ t('profileDetails.employeeId') }}</dt>
            <dd class="detail-value">CC-{{ currentUser.id.toString().padStart(5, '0') }}</dd>
          </div>
        </dl>
      </div>
    </div>

    <div class="modal-footer">
      <button type="button" class="btn-secondary" @click="close">{{ t('profileDetails.close') }}</button>
    </div>
  </dialog>
</template>

<script>
import { ref, watch, onMounted, useId } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useI18n } from '../composables/useI18n'

export default {
  name: 'ProfileDetailsModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const { currentUser, getInitials } = useAuth()
    const { t, currentLocale } = useI18n()

    const dialogEl = ref(null)
    const titleId = `profile-title-${useId()}`

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

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      if (isNaN(date.getTime())) return ''
      const locale = currentLocale.value === 'ja' ? 'ja-JP' : 'en-US'
      return date.toLocaleDateString(locale, {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })
    }

    return { t, currentUser, getInitials, dialogEl, titleId, onClose, onDialogClick, close, formatDate }
  }
}
</script>

<style scoped>
.profile-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding-block-end: var(--space-5);
  border-block-end: 1px solid var(--color-border);
}

.avatar-xl {
  display: grid;
  place-items: center;
  inline-size: 6rem;
  block-size: 6rem;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: var(--text-3xl);
  font-weight: 700;
  letter-spacing: 0.025em;
  box-shadow: var(--shadow-md);
}

.profile-name {
  font-size: var(--text-xl);
  font-weight: 700;
}

.profile-job-title {
  color: var(--color-text-muted);
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  min-inline-size: 0;
}

.detail-value {
  overflow-wrap: anywhere;
}
</style>
