<script setup>
import { computed } from 'vue'

const props = defineProps({
  client: {
    type: Object,
    required: true
  },
  isActive: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])

// Identification of primary fields
const titleField = 'name'
const badgeField = 'flag'

// Metrics list excluding title, badge, and ALWAYS excluding 'id'
const metrics = computed(() => {
  return Object.entries(props.client).filter(([key]) => {
    // Explicitly exclude 'id' from display as per requirements
    return key.toLowerCase() !== 'id' && key !== titleField && key !== badgeField
  })
})

const getBadgeClass = (value) => {
  if (!value) return ''
  const val = String(value).toLowerCase()
  // Generic mapping for common flags
  if (val.includes('vh') || val.includes('very high')) return 'vh'
  if (val.includes('h') || val === 'high') return 'h'
  if (val.includes('m') || val === 'medium') return 'm'
  if (val.includes('l') || val === 'low') return 'l'
  return ''
}
</script>

<template>
  <div 
    :class="['client-row', { active: isActive }]" 
    @click="$emit('select', client)"
  >
    <div class="row-main">
      <div class="title-group">
        <span class="client-title">{{ client[titleField] }}</span>
        <span v-if="client[badgeField]" :class="['status-badge', getBadgeClass(client[badgeField])]">
          {{ client[badgeField] }}
        </span>
      </div>
      
      <div class="metrics-group">
        <div v-for="[key, value] in metrics" :key="key" class="metric-item">
          <span class="metric-label">{{ key.replace(/_/g, ' ') }}:</span>
          <span class="metric-value">{{ value }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.client-row {
  background: var(--salt-color-white);
  border: 1px solid var(--salt-color-brown-200);
  border-radius: 0.5rem;
  padding: 1rem 1.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 2rem;
  margin-bottom: 0.75rem;
  width: fit-content;
  min-width: 400px;
}

.client-row:hover {
  border-color: var(--salt-color-brown-400);
  background-color: var(--salt-color-white);
  box-shadow: 0 4px 12px rgba(46, 25, 5, 0.05);
  transform: translateX(4px);
}

.client-row.active {
  border-color: var(--salt-color-brown-700);
  background-color: var(--salt-color-brown-100);
  box-shadow: inset 4px 0 0 var(--salt-color-brown-700);
}

.row-main {
  display: flex;
  align-items: center;
  gap: 3rem;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 1rem;
  min-width: 200px;
}

.client-title {
  font-weight: 700;
  font-size: 1.05rem;
  color: var(--salt-color-black);
  text-transform: capitalize;
  white-space: nowrap;
}

.status-badge {
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Dynamic Badge Colors */
.status-badge.vh { background-color: #fee2e2; color: #991b1b; }
.status-badge.h { background-color: #ffedd5; color: #9a3412; }
.status-badge.m { background-color: #fef9c3; color: #854d0e; }
.status-badge.l { background-color: #f0fdf4; color: #166534; }

.metrics-group {
  display: flex;
  gap: 2rem;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  white-space: nowrap;
}

.metric-label {
  color: var(--salt-color-brown-500);
  font-weight: 500;
  text-transform: capitalize;
}

.metric-value {
  color: var(--salt-color-black);
  font-weight: 600;
}

@media (max-width: 992px) {
  .client-row {
    width: 100%;
    min-width: unset;
  }
  .row-main {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  .title-group {
    min-width: unset;
  }
  .metrics-group {
    gap: 1rem;
    flex-wrap: wrap;
  }
}
</style>
