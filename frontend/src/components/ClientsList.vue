<script setup>
import { ref, onMounted, nextTick } from 'vue'
import ClientRow from './ClientRow.vue'
import ClientSummaryViewer from './ClientSummaryViewer.vue'

const clients = ref([])
const selectedClient = ref(null)
const htmlSummary = ref('')
const isSummaryVisible = ref(false)
const isLoadingSummary = ref(false)
const summaryRef = ref(null)

const fetchClients = async () => {
  try {
    const response = await fetch('/api/clients')
    if (!response.ok) throw new Error('Failed to fetch clients')
    clients.value = await response.json()
  } catch (err) {
    console.error('Error fetching clients:', err)
  }
}

const handleSelectClient = async (client) => {
  selectedClient.value = client
  isSummaryVisible.value = true
  isLoadingSummary.value = true
  htmlSummary.value = ''

  try {
    const response = await fetch(`/api/client-summary/${client.id}`)
    if (!response.ok) throw new Error('Failed to fetch summary')
    htmlSummary.value = await response.text()
    
    // Scroll into view once summary is loaded
    await nextTick()
    if (summaryRef.value) {
      summaryRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  } catch (err) {
    console.error('Error fetching summary:', err)
    htmlSummary.value = '<p class="error">Failed to load summary content.</p>'
  } finally {
    isLoadingSummary.value = false
  }
}

const handleCloseSummary = () => {
  isSummaryVisible.value = false
  selectedClient.value = null
  htmlSummary.value = ''
}

// Utility to get a display name for the summary header
const getDisplayName = (client) => {
  if (!client) return ''
  return client.name || client.id
}

onMounted(fetchClients)
</script>

<template>
  <div class="dashboard-container">
    <section class="list-section">
      <div class="section-header">
        <h2 class="section-title">Dashboard</h2>
        <p class="section-subtitle">Select an item to view detailed summary</p>
      </div>

      <div class="list-scroll-wrapper">
        <div class="clients-list">
          <ClientRow
            v-for="client in clients"
            :key="client.id"
            :client="client"
            :isActive="selectedClient?.id === client.id"
            @select="handleSelectClient"
          />
        </div>
      </div>
    </section>

    <section v-if="isSummaryVisible" ref="summaryRef" class="summary-section">
      <ClientSummaryViewer
        :htmlContent="htmlSummary"
        :clientName="getDisplayName(selectedClient)"
        :isLoading="isLoadingSummary"
        @close="handleCloseSummary"
      />
    </section>
  </div>
</template>

<style scoped>
.dashboard-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 2.25rem;
  font-weight: 800;
  color: var(--salt-color-brown-900);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
}

.section-subtitle {
  color: var(--salt-color-brown-600);
  font-size: 1.1rem;
  margin: 0;
}

.list-scroll-wrapper {
  max-height: 400px;
  overflow-y: auto;
  padding-right: 0.75rem;
  /* Standard Properties */
  scrollbar-width: thin;
  scrollbar-color: var(--salt-color-brown-300) var(--salt-color-brown-100);
}

/* Custom Scrollbar Styling (Always Visible) */
.list-scroll-wrapper::-webkit-scrollbar {
  width: 8px;
  display: block;
}

.list-scroll-wrapper::-webkit-scrollbar-track {
  background: var(--salt-color-brown-100);
  border-radius: 10px;
}

.list-scroll-wrapper::-webkit-scrollbar-thumb {
  background-color: var(--salt-color-brown-300);
  border-radius: 10px;
  border: 2px solid var(--salt-color-brown-100); /* Adds spacing effect */
}

.list-scroll-wrapper::-webkit-scrollbar-thumb:hover {
  background-color: var(--salt-color-brown-500);
}

.clients-list {
  display: flex;
  flex-direction: column;
  width: max-content;
  min-width: 100%;
}

.summary-section {
  margin-top: 1rem;
  padding-bottom: 3rem; /* Extra space at bottom */
}

@media (max-width: 768px) {
  .dashboard-container {
    padding: 2rem 1.25rem;
  }
  
  .section-title {
    font-size: 1.75rem;
  }
  
  .list-scroll-wrapper {
    max-height: 350px;
  }
}
</style>
