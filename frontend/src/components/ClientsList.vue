<script setup>
/**
 * ClientsList.vue
 * This component displays the main Dashboard with a list of clients in a table.
 * It includes a sidebar for filtering by name and month, and top summary tiles
 * for filtering by risk category (flagg).
 */
import { ref, onMounted, nextTick, computed } from 'vue'
import ClientSummaryViewer from './ClientSummaryViewer.vue'

// --- State Management ---
const clients = ref([])               // Full list of clients from backend
const selectedClient = ref(null)       // The client currently selected for the summary view
const htmlSummary = ref('')            // The HTML content of the client summary
const currentView = ref('dashboard')   // Tracks if we are in 'dashboard' or 'summary' view
const isLoadingSummary = ref(false)    // Loading state for fetching HTML summaries
const summaryRef = ref(null)           // Reference to the summary section DOM element

// --- Filter State ---
const nameSearch = ref('')             // Bound to the Name search input
const selectedMonth = ref('')          // Bound to the Month dropdown
const selectedFlag = ref('')           // Bound to the interactive Risk tiles (flagg)

// Columns that should have a fixed width and word wrap
const wrappedColumns = ['flagg', 'check', 'checked for important changes']

// Columns that should be rendered as status badges
const badgeColumns = ['flagg', 'check', 'checked for important changes']

/**
 * Fetch all clients from the API on component mount.
 */
const fetchClients = async () => {
  try {
    const response = await fetch('/api/clients')
    if (!response.ok) throw new Error('Failed to fetch clients')
    clients.value = await response.json()
  } catch (err) {
    console.error('Error fetching clients:', err)
  }
}

/**
 * Aggregated counts for the risk tiles.
 * Uses the 'flagg' field from the data.
 */
const flagCounts = computed(() => {
  const counts = { 'Very High': 0, 'High': 0, 'Medium': 0, 'Low': 0 }
  clients.value.forEach(client => {
    const f = client.flagg
    if (f && counts.hasOwnProperty(f)) {
      counts[f]++
    }
  })
  return counts
})

/**
 * Main logic for filtering the clients list.
 * Combines Name search, Month selection, and Risk tile selection.
 */
const filteredClients = computed(() => {
  return clients.value.filter(client => {
    // Name filter (uses 'namee' field)
    const matchesName = !nameSearch.value || 
      (client.namee && client.namee.toLowerCase().includes(nameSearch.value.toLowerCase()))
    
    // Month filter
    const matchesMonth = !selectedMonth.value || 
      client.month === selectedMonth.value

    // Risk category filter (uses 'flagg' field)
    const matchesFlag = !selectedFlag.value ||
      client.flagg === selectedFlag.value
      
    return matchesName && matchesMonth && matchesFlag
  })
})

/**
 * Extracts unique months from the dataset for the dropdown filter.
 */
const uniqueMonths = computed(() => {
  const months = clients.value.map(c => c.month).filter(Boolean)
  return [...new Set(months)].sort((a, b) => a.localeCompare(b))
})

/**
 * Called when a row in the table is clicked.
 * Fetches the HTML summary for the specific client using 'html_id'.
 */
const handleRowClick = async (client) => {
  selectedClient.value = client
  currentView.value = 'summary'
  isLoadingSummary.value = true
  htmlSummary.value = ''

  try {
    const response = await fetch(`/api/client-summary/${client.html_id}`)
    if (!response.ok) throw new Error('Failed to fetch summary')
    htmlSummary.value = await response.text()
    
    // Scroll to top of the page when the summary view opens
    await nextTick()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (err) {
    console.error('Error fetching summary:', err)
    htmlSummary.value = '<p class="error">Summary content not available.</p>'
  } finally {
    isLoadingSummary.value = false
  }
}

/**
 * Switches view back to the main dashboard.
 */
const goBack = () => {
  currentView.value = 'dashboard'
  selectedClient.value = null
  htmlSummary.value = ''
}

/**
 * Toggles the filter for a specific risk category tile.
 */
const toggleFlagFilter = (flag) => {
  if (selectedFlag.value === flag) {
    selectedFlag.value = '' // Unselect if already selected
  } else {
    selectedFlag.value = flag
  }
}

/**
 * Dynamically determines table headers based on the first client object.
 * Excludes the 'html_id' field from display.
 */
const tableHeaders = computed(() => {
  if (clients.value.length === 0) return []
  // Note: Exclude 'html_id' from table columns
  return Object.keys(clients.value[0]).filter(key => key.toLowerCase() !== 'html_id')
})

/**
 * Helper to get a display name for a client.
 */
const getDisplayName = (client) => {
  if (!client) return ''
  // Note: 'name' updated to 'namee'
  return client.namee || client.html_id
}

/**
 * Maps risk categories to CSS classes for badges and tiles.
 */
const getBadgeClass = (value) => {
  if (!value) return ''
  const val = String(value).toLowerCase()
  if (val === 'very high' || val === 'vh') return 'vh'
  if (val === 'high' || val === 'h') return 'h'
  if (val === 'medium' || val === 'm') return 'm'
  if (val === 'low' || val === 'l') return 'l'
  if (val === 'yes') return 'yes'
  if (val === 'no') return 'no'
  return ''
}

// Fetch data when the component is ready
onMounted(fetchClients)
</script>

<template>
  <div class="dashboard-wrapper">
    <!-- FULL-WIDTH MAIN HEADER BAR (Always Visible) -->
    <header class="main-header-bar">
      <h1 class="main-title">Dashboard</h1>
    </header>

    <!-- --- DASHBOARD VIEW --- -->
    <div v-if="currentView === 'dashboard'" class="dashboard-view-container">
      <div class="dashboard-layout">
        
        <!-- SIDEBAR (20% width) - Contains filters -->
        <aside class="sidebar">
          <div class="sidebar-header">
            <h3 class="sidebar-title">Filters</h3>
          </div>
          
          <!-- Name Search Input -->
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

          <!-- Month Dropdown Filter -->
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

          <!-- Clear All Filters Button -->
          <div class="sidebar-footer">
            <button @click="nameSearch = ''; selectedMonth = ''; selectedFlag = ''" class="reset-btn">
              Clear Filters
            </button>
          </div>
        </aside>

        <!-- MAIN DASHBOARD CONTENT (80% width) -->
        <main class="main-dashboard">
          
          <!-- Result Count Information -->
          <div class="view-status">
            <p class="view-subtitle">Showing {{ filteredClients.length }} records</p>
          </div>

          <!-- INTERACTIVE CATEGORY TILES (Risk Summary) -->
          <div class="stat-tiles">
            <div 
              v-for="(count, flag) in flagCounts" 
              :key="flag"
              :class="['stat-tile', getBadgeClass(flag), { active: selectedFlag === flag }]"
              @click="toggleFlagFilter(flag)"
            >
              <span class="tile-label">{{ flag }}</span>
              <span class="tile-value">{{ count }}</span>
            </div>
          </div>

          <!-- DATA TABLE -->
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th 
                    v-for="header in tableHeaders" 
                    :key="header"
                    :class="{ 'fixed-col': wrappedColumns.includes(header) }"
                  >
                    {{ header.replace(/_/g, ' ') }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="client in filteredClients" 
                  :key="client.html_id" 
                  @click="handleRowClick(client)"
                  class="clickable-row"
                >
                  <td 
                    v-for="header in tableHeaders" 
                    :key="header"
                    :class="{ 'fixed-col': wrappedColumns.includes(header) }"
                  >
                    <!-- Custom rendering for columns that show badges -->
                    <template v-if="badgeColumns.includes(header)">
                      <span :class="['status-badge', getBadgeClass(client[header])]">
                        {{ client[header] }}
                      </span>
                    </template>
                    <!-- Default rendering for other columns -->
                    <template v-else>
                      {{ client[header] }}
                    </template>
                  </td>
                </tr>
                <!-- No Results State -->
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
    </div>

    <!-- --- SUMMARY VIEW --- (Full Page) -->
    <div v-else class="view-container summary-page">
      <!-- Top Navigation with Back Button -->
      <div class="navigation-bar">
        <button class="back-btn" @click="goBack">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
          Back to Dashboard
        </button>
      </div>

      <!-- Component to render the detailed HTML summary -->
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
/* --- Layout Styles --- */

.dashboard-wrapper {
  width: 100%;
  min-height: 100vh;
  background-color: var(--salt-color-brown-100);
}

.dashboard-view-container {
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 85px); /* Full height minus header */
}

/* FULL-WIDTH MAIN HEADER BAR */
.main-header-bar {
  width: 100%;
  background-color: var(--salt-color-brown-200); /* Slightly darker shade for the header */
  padding: 1.5rem 3rem;
  border-bottom: 1px solid var(--salt-color-brown-300);
  box-sizing: border-box;
  position: sticky;
  top: 0;
  z-index: 100;
}

.main-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--salt-color-brown-900);
  margin: 0;
  letter-spacing: -0.02em;
}

.dashboard-layout {
  display: flex;
  flex: 1;
}

/* SIDEBAR STYLING */
.sidebar {
  width: 20%;
  background-color: var(--salt-color-white);
  border-right: 1px solid var(--salt-color-brown-200);
  padding: 3rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  position: sticky;
  top: 85px; /* Fixed height of the header */
  height: calc(100vh - 85px);
  box-sizing: border-box;
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
}

/* MAIN CONTENT STYLING */
.main-dashboard {
  width: 80%;
  padding: 2rem 3rem 3rem 3rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.view-status {
  margin-bottom: 0.5rem;
}

.view-subtitle {
  color: var(--salt-color-brown-600);
  font-size: 1.1rem;
  margin: 0;
  font-weight: 500;
}

/* SUMMARY TILES STYLING */
.stat-tiles {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.stat-tile {
  flex: 1;
  background-color: var(--salt-color-white);
  border: 1px solid var(--salt-color-brown-200);
  border-radius: 0.75rem;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 0.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.stat-tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(46, 25, 5, 0.05);
  border-color: var(--salt-color-brown-400);
}

.stat-tile.active {
  border-color: var(--salt-color-brown-700);
  box-shadow: inset 0 0 0 2px var(--salt-color-brown-700);
}

.tile-label {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Risk-specific colors for tiles */
.stat-tile.vh .tile-label, .stat-tile.yes .tile-label { color: #991b1b; }
.stat-tile.h .tile-label { color: #9a3412; }
.stat-tile.m .tile-label { color: #854d0e; }
.stat-tile.l .tile-label, .stat-tile.no .tile-label { color: #166534; }

.tile-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--salt-color-black);
}

/* Mild Tile Background Colors based on risk level */
.stat-tile.vh, .stat-tile.yes { background-color: #fef2f2; border-color: #fee2e2; }
.stat-tile.h { background-color: #fffaf5; border-color: #ffedd5; }
.stat-tile.m { background-color: #fefce8; border-color: #fef9c3; }
.stat-tile.l, .stat-tile.no { background-color: #f0fdf4; border-color: #dcfce7; }

.stat-tile.vh:hover, .stat-tile.yes:hover { border-color: #fca5a5; }
.stat-tile.h:hover { border-color: #fdba74; }
.stat-tile.m:hover { border-color: #fde047; }
.stat-tile.l:hover, .stat-tile.no:hover { border-color: #86efac; }

/* DATA TABLE STYLING */
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
  table-layout: auto; /* Allow columns to adjust naturally */
}

.data-table th {
  background-color: var(--salt-color-brown-100);
  padding: 1.25rem 1.5rem;
  font-weight: 700;
  color: var(--salt-color-brown-800);
  text-transform: capitalize;
  border-bottom: 2px solid var(--salt-color-brown-200);
  white-space: nowrap; /* Default: no wrap */
}

.data-table td {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--salt-color-brown-200);
  color: var(--salt-color-black);
  white-space: nowrap; /* Default: no wrap */
}

/* Specific styling for selected columns with fixed width and wrap */
.fixed-col {
  width: 150px;
  min-width: 150px;
  white-space: normal !important;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.clickable-row:hover { background-color: var(--salt-color-brown-100); }

/* STATUS BADGES (Table) */
.status-badge {
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  display: inline-block;
}

.status-badge.vh, .status-badge.yes { background-color: #fee2e2; color: #991b1b; }
.status-badge.h { background-color: #ffedd5; color: #9a3412; }
.status-badge.m { background-color: #fef9c3; color: #854d0e; }
.status-badge.l, .status-badge.no { background-color: #f0fdf4; color: #166534; }

/* SUMMARY VIEW STYLING */
.view-container.summary-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 3rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  min-height: calc(100vh - 85px);
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
}

/* RESPONSIVE BREAKPOINTS */
@media (max-width: 1200px) {
  .sidebar { width: 250px; }
  .main-dashboard { width: calc(100% - 250px); }
  .stat-tiles { flex-wrap: wrap; }
}

@media (max-width: 768px) {
  .dashboard-layout { flex-direction: column; }
  .sidebar { width: 100%; height: auto; position: relative; padding: 2rem 1.25rem; top: 0; }
  .main-dashboard { width: 100%; padding: 2rem 1.25rem; }
  .main-header-bar { padding: 1rem 1.5rem; }
  .main-title { font-size: 1.75rem; }
}
</style>
