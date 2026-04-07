<script setup>
/**
 * ClientSummaryViewer.vue
 * This component renders the detailed HTML summary for a specific client.
 * It's displayed in a full-page view when a row is clicked in the dashboard.
 */
defineProps({
  htmlContent: {
    type: String,
    default: '' // The raw HTML content from the backend
  },
  clientName: {
    type: String,
    default: '' // The name of the client to display in the header
  },
  isLoading: {
    type: Boolean,
    default: false // Show a loading spinner while fetching the content
  }
})

// Emit event to return to the dashboard view
defineEmits(['close'])
</script>

<template>
  <div class="summary-viewer">
    <!-- Header: Shows the client name -->
    <header class="summary-header">
      <div class="header-main">
        <h2 class="client-name">{{ clientName }}</h2>
        <span class="view-tag">Summary</span>
      </div>
    </header>

    <!-- Content Area -->
    <div class="summary-body">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>Generating summary analysis...</p>
      </div>

      <!-- Rendered HTML Content -->
      <div 
        v-else 
        class="html-content" 
        v-html="htmlContent"
      ></div>
    </div>
  </div>
</template>

<style scoped>
/* --- Component Styles --- */

.summary-viewer {
  background-color: var(--salt-color-white);
  border-radius: 1rem;
  border: 1px solid var(--salt-color-brown-200);
  box-shadow: 0 10px 30px rgba(46, 25, 5, 0.08);
  overflow: hidden;
  min-height: 600px;
}

.summary-header {
  padding: 2rem;
  background-color: var(--salt-color-brown-100);
  border-bottom: 1px solid var(--salt-color-brown-200);
}

.header-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.client-name {
  font-size: 2rem;
  font-weight: 800;
  color: var(--salt-color-brown-900);
  margin: 0;
}

.view-tag {
  background-color: var(--salt-color-brown-700);
  color: var(--salt-color-white);
  padding: 0.25rem 0.75rem;
  border-radius: 2rem;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.summary-body {
  padding: 2.5rem;
  color: var(--salt-color-black);
  line-height: 1.6;
}

/* Styles for the injected HTML content from backend */
:deep(.html-content) {
  font-size: 1.05rem;
}

:deep(.html-content h1, .html-content h2, .html-content h3) {
  color: var(--salt-color-brown-900);
  margin-top: 2rem;
  margin-bottom: 1rem;
}

:deep(.html-content p) { margin-bottom: 1.25rem; }

:deep(.html-content ul, .html-content ol) {
  margin-bottom: 1.5rem;
  padding-left: 1.5rem;
}

:deep(.html-content li) { margin-bottom: 0.5rem; }

/* Loading Spinner */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 0;
  color: var(--salt-color-brown-500);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--salt-color-brown-100);
  border-top-color: var(--salt-color-brown-700);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
