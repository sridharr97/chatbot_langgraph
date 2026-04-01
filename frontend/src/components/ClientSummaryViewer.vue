<script setup>
defineProps({
  htmlContent: {
    type: String,
    required: true
  },
  clientName: {
    type: String,
    default: 'Client'
  },
  isLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])
</script>

<template>
  <div class="summary-viewer">
    <div class="summary-header">
      <h3 class="summary-title">Summary: {{ clientName }}</h3>
      <button class="close-btn" @click="$emit('close')" aria-label="Close Summary">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    </div>

    <div class="summary-content-wrapper">
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Fetching details...</p>
      </div>
      <div 
        v-else 
        class="html-container" 
        v-html="htmlContent"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.summary-viewer {
  background: var(--salt-color-white);
  border-radius: 1rem;
  box-shadow: 0 20px 25px -5px rgba(46, 25, 5, 0.1), 0 10px 10px -5px rgba(46, 25, 5, 0.04);
  border: 1px solid var(--salt-color-brown-200);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.summary-header {
  padding: 1rem 1.5rem;
  background-color: var(--salt-color-brown-100);
  border-bottom: 1px solid var(--salt-color-brown-200);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--salt-color-brown-900);
}

.close-btn {
  background: none;
  border: none;
  color: var(--salt-color-brown-500);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background-color: var(--salt-color-brown-200);
  color: var(--salt-color-brown-800);
}

.summary-content-wrapper {
  padding: 2rem;
  min-height: 200px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  gap: 1rem;
  color: var(--salt-color-brown-500);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--salt-color-brown-100);
  border-top-color: var(--salt-color-brown-600);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.html-container {
  color: var(--salt-color-black);
  line-height: 1.6;
}

/* Ensure injected HTML looks okay */
:deep(h1), :deep(h2), :deep(h3) {
  color: var(--salt-color-brown-900);
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(p) {
  margin-bottom: 1rem;
}
</style>
