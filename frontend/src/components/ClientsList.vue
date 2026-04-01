<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import ClientSummaryViewer from './ClientSummaryViewer.vue'

const clients = ref([])
const selectedClient = ref(null)
const htmlSummary = ref('')
const currentView = ref('dashboard') // 'dashboard' or 'summary'
const isLoadingSummary = ref(false)
const summaryRef = ref(null)

// Filters State
const nameSearch = ref('')
const selectedMonth = ref('')

const fetchClients = async () => {
  try {
    const response = await fetch('/api/clients')
    if (!response.ok) throw new Error('Failed to fetch clients')
    clients.value = await response.json()
  } catch (err) {
    console.error('Error fetching clients:', err)
  }
}

// Computed property for filtered clients
const filteredClients = computed(() => {
  return clients.value.filter(client => {
    const matchesName = !nameSearch.value || 
      (client.name && client.name.toLowerCase().includes(nameSearch.value.toLowerCase()))
    
    const matchesMonth = !selectedMonth.value || 
      client.month === selectedMonth.value
      
    return matchesName && matchesMonth
  })
})

// Extract unique months from client data for the dropdown
const uniqueMonths = computed(() => {
  const months = clients.value.map(c => c.month).filter(Boolean)
  return [...new Set(months)].sort((a, b) => {
    // Simple chronological sort if possible, otherwise alphabetical
    return a.localeCompare(b)
  })
})

const handleRowClick = async (client) => {
  selectedClient.value = client
  currentView.value = 'summary'
  isLoadingSummary.value = true
  htmlSummary.value = ''

  try {
    const response = await fetch(`/api/client-summary/${client.id}`)
    if (!response.ok) throw new Error('Failed to fetch summary')
    htmlSummary.value = await response.text()
    
    await nextTick()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (err) {
    console.error('Error fetching summary:', err)
    htmlSummary.value = '<p class="error">Failed to load summary content.</p>'
  } finally {
    isLoadingSummary.value = false
  }
}

const goBack = () => {
  currentView.value = 'dashboard'
  selectedClient.value = null
  htmlSummary.value = ''
}

const tableHeaders = computed(() => {
  if (clients.value.length === 0) return []
  return Object.keys(clients.value[0]).filter(key => key.toLowerCase() !== 'id')
})

const getDisplayName = (client) => {
  if (!client) return ''
  return client.name || client.id
}

const getBadgeClass = (value) => {
  if (!value) return ''
  const val = String(value).toLowerCase()
  if (val.includes('vh') || val.includes('very high')) return 'vh'
  if (val.includes('h') || val === 'high') return 'h'
  if (val.includes('m') || val === 'medium') return 'm'
  if (val.includes('l') || val === 'low') return 'l'
  return ''
}

onMounted(fetchClients)
</script>

<template>
  <div class="dashboard-wrapper">
    <!-- DASHBOARD VIEW -->
    <div v-if="currentView === 'dashboard'" class="dashboard-layout">
      <!-- SIDEBAR (20%) -->
      <aside class="sidebar">
        <div class="sidebar-header">
          <h3 class="sidebar-title">Filters</h3>
        </div>
        
        <div class="filter-group">
          <label for="name-search" class="filter-label">Search Name</label>
          <div class="input-wrapper">
            <input 
              id="name-search"
              v-model="nameSearch" 
              type="text" 
              placeholder="Type to filter..." 
              class="filter-input"
            />
          </div>
        </div>

        <div class="filter-group">
          <label for="month-filter" class="filter-label">Select Month</label>
          <div class="input-wrapper">
            <select 
              id="month-filter"
              v-model="selectedMonth" 
              class="filter-select"
            >
              <option value="">All Months</option>
              <option v-for="month in uniqueMonths" :key="month" :value="month">
                {{ month }}
              </option>
            </select>
          </div>
        </div>

        <div class="sidebar-footer">
          <button @click="nameSearch = ''; selectedMonth = ''" class="reset-btn">
            Clear Filters
          </button>
        </div>
      </aside>

      <!-- MAIN CONTENT (80%) -->
      <main class="main-dashboard">
        <header class="view-header">
          <h2 class="view-title">Dashboard</h2>
          <p class="view-subtitle">Showing {{ filteredClients.length }} records</p>
        </header>

        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th v-for="header in tableHeaders" :key="header">
                  {{ header.replace(/_/g, ' ') }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="client in filteredClients" 
                :key="client.id" 
                @click="handleRowClick(client)"
                class="clickable-row"
              >
                <td v-for="header in tableHeaders" :key="header">
                  <template v-if="header === 'flag'">
                    <span :class="['status-badge', getBadgeClass(client[header])]">
                      {{ client[header] }}
                    </span>
                  </template>
                  <template v-else>
                    {{ client[header] }}
                  </template>
                </td>
              </tr>
              <tr v-if="filteredClients.length === 0">
                <td :colspan="tableHeaders.length" class="no-results">
                  No matching records found.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>
    </div>

    <!-- SUMMARY VIEW (Full Page Overlay) -->
    <div v-else class="view-container summary-page">
      <div class="navigation-bar">
        <button class="back-btn" @click="goBack">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
          Back to Dashboard
        </button>
      </div>

      <section ref="summaryRef" class="summary-section">
        <ClientSummaryViewer
          :htmlContent="htmlSummary"
          :clientName="getDisplayName(selectedClient)"
          :isLoading="isLoadingSummary"
          @close="goBack"
        />
      </section>
    </div>
  </div>
</template>

<style scoped>
.dashboard-wrapper {
  width: 100%;
  min-height: 100vh;
  background-color: var(--salt-color-brown-100);
}

/* 2-Section Layout */
.dashboard-layout {
  display: flex;
  min-height: 100vh;
}

/* SIDEBAR (20%) */
.sidebar {
  width: 20%;
  background-color: var(--salt-color-white);
  border-right: 1px solid var(--salt-color-brown-200);
  padding: 3rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  position: sticky;
  top: 0;
  height: 100vh;
}

.sidebar-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--salt-color-brown-900);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--salt-color-brown-500);
}

.filter-input, .filter-select {
  width: 100%;
  box-sizing: border-box;
  display: block;
  padding: 0.75rem;
  border: 1px solid var(--salt-color-brown-200);
  border-radius: 0.5rem;
  background-color: var(--salt-color-brown-100);
  color: var(--salt-color-black);
  font-size: 0.9rem;
  transition: all 0.2s;
}

.filter-input:focus, .filter-select:focus {
  outline: none;
  border-color: var(--salt-color-brown-400);
  background-color: var(--salt-color-white);
  box-shadow: 0 0 0 3px rgba(184, 138, 103, 0.1);
}

.reset-btn {
  background: none;
  border: 1px solid var(--salt-color-brown-300);
  color: var(--salt-color-brown-600);
  padding: 0.5rem 1rem;
  border-radius: 0.4rem;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.reset-btn:hover {
  background-color: var(--salt-color-brown-100);
  color: var(--salt-color-brown-900);
}

/* MAIN CONTENT (80%) */
.main-dashboard {
  width: 80%;
  padding: 3rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.view-header {
  margin-bottom: 0.5rem;
}

.view-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--salt-color-brown-900);
  margin: 0 0 0.5rem 0;
  letter-spacing: -0.02em;
}

.view-subtitle {
  color: var(--salt-color-brown-600);
  font-size: 1.1rem;
  margin: 0;
}

/* Table Styles */
.table-container {
  background: var(--salt-color-white);
  border-radius: 0.75rem;
  border: 1px solid var(--salt-color-brown-200);
  box-shadow: 0 4px 6px -1px rgba(46, 25, 5, 0.05);
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.95rem;
}

.data-table th {
  background-color: var(--salt-color-brown-100);
  padding: 1.25rem 1.5rem;
  font-weight: 700;
  color: var(--salt-color-brown-800);
  text-transform: capitalize;
  border-bottom: 2px solid var(--salt-color-brown-200);
  white-space: nowrap;
}

.data-table td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--salt-color-brown-200);
  color: var(--salt-color-black);
  white-space: nowrap;
}

.clickable-row {
  cursor: pointer;
  transition: background-color 0.2s;
}

.clickable-row:hover {
  background-color: var(--salt-color-brown-100);
}

.no-results {
  text-align: center;
  padding: 3rem;
  color: var(--salt-color-brown-400);
  font-style: italic;
}

/* Badge Styles */
.status-badge {
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: inline-block;
}

.status-badge.vh { background-color: #fee2e2; color: #991b1b; }
.status-badge.h { background-color: #ffedd5; color: #9a3412; }
.status-badge.m { background-color: #fef9c3; color: #854d0e; }
.status-badge.l { background-color: #f0fdf4; color: #166534; }

/* SUMMARY VIEW PAGE */
.view-container.summary-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.navigation-bar { margin-bottom: 1rem; }
.back-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: none;
  border: none;
  color: var(--salt-color-brown-600);
  font-weight: 600;
  cursor: pointer;
  padding: 0.5rem 0;
}
.back-btn:hover { color: var(--salt-color-brown-900); }

@media (max-width: 1200px) {
  .sidebar { width: 250px; }
  .main-dashboard { width: calc(100% - 250px); }
}

@media (max-width: 768px) {
  .dashboard-layout { flex-direction: column; }
  .sidebar { 
    width: 100%; 
    height: auto; 
    position: relative; 
    padding: 2rem 1.25rem;
  }
  .main-dashboard { width: 100%; padding: 2rem 1.25rem; }
}
</style>
