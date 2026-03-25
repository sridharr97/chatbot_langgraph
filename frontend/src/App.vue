<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'

const messages = ref([
  { 
    role: 'assistant', 
    content: 'Hello! I am your database assistant. How can I help you today?',
    logs: [],
    outputData: [],
    isComplete: true
  }
])
const input = ref('')
const isLoading = ref(false)
const messagesEndRef = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesEndRef.value) {
    messagesEndRef.value.scrollIntoView({ behavior: "smooth" })
  }
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

const handleSendMessage = async () => {
  if (!input.value.trim()) return

  const userMessage = { role: 'user', content: input.value }
  messages.value.push(userMessage)
  
  const currentInput = input.value
  input.value = ''
  isLoading.value = true

  const assistantMessageId = Date.now()
  const newMessage = { 
    id: assistantMessageId,
    role: 'assistant', 
    logs: [], 
    outputData: [],
    content: '', 
    isComplete: false,
    activeTab: 'processing',
    hasAutoSwitched: false
  }
  messages.value.push(newMessage)

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: currentInput }),
    })

    if (!response.body) throw new Error('ReadableStream not supported')

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || '' 

      for (const line of lines) {
        if (!line.trim()) continue
        try {
          const data = JSON.parse(line)
          
          const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
          if (msgIndex !== -1) {
            const msg = messages.value[msgIndex]
            if (data.type === 'log') {
              msg.logs.push(data.content)
            } else if (data.type === 'data') {
              msg.outputData = data.content
            } else if (data.type === 'result') {
              msg.content = data.content
              msg.isComplete = true
              // Auto-switch tab
              if (!msg.hasAutoSwitched) {
                const isLargeResult = msg.content.includes("more than 100 records");
                msg.activeTab = isLargeResult ? 'data' : 'answer';
                msg.hasAutoSwitched = true
              }
            } else if (data.type === 'error') {
              msg.content = `Error: ${data.content}`
              msg.isComplete = true
              msg.activeTab = 'answer'
            }
          }
        } catch (e) {
          console.error('Error parsing JSON line:', e)
        }
      }
    }
  } catch (error) {
    console.error('Error sending message:', error)
    const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
    if (msgIndex !== -1) {
      messages.value[msgIndex].content = 'Sorry, I encountered an error connecting to the server.'
      messages.value[msgIndex].isComplete = true
      messages.value[msgIndex].activeTab = 'answer'
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="app-container">
    <header class="header">
      <h1>LangGraph DB Chatbot (Vue)</h1>
    </header>

    <main class="messages-area">
      <div v-for="(msg, index) in messages" :key="index" :class="['message-wrapper', msg.role]">
        <div :class="['message-bubble', msg.role]">
          <!-- USER MESSAGE -->
          <template v-if="msg.role === 'user'">
            <p class="content-text">{{ msg.content }}</p>
          </template>

          <!-- ASSISTANT MESSAGE -->
          <template v-else>
            <div class="assistant-content">
              <!-- Initial Greeting (no tabs) -->
              <div v-if="!msg.id">
                <p class="content-text">{{ msg.content }}</p>
              </div>

              <!-- Chat Responses (with tabs) -->
              <div v-else class="tabbed-container">
                <div class="tabs-header">
                  <button 
                    @click="msg.activeTab = 'processing'" 
                    :class="{ active: msg.activeTab === 'processing' }"
                    class="tab-btn"
                  >
                    Query Processing
                  </button>
                  <button 
                    @click="msg.activeTab = 'answer'" 
                    :class="{ active: msg.activeTab === 'answer' }"
                    class="tab-btn"
                  >
                    Answer
                  </button>
                  <button 
                    @click="msg.activeTab = 'data'" 
                    :class="{ active: msg.activeTab === 'data' }"
                    class="tab-btn"
                    v-if="msg.outputData && msg.outputData.length > 0"
                  >
                    Output Data
                  </button>
                </div>
                
                <div class="tab-content">
                  <!-- Processing Logs Tab -->
                  <div v-if="msg.activeTab === 'processing'" class="logs-container">
                    <div v-if="msg.logs.length > 0" class="logs-list">
                      <div v-for="(log, i) in msg.logs" :key="i" class="log-entry">
                        {{ log }}
                      </div>
                    </div>
                    <div v-else class="waiting-logs">
                      <div class="ping-dot"></div>
                      <span>Waiting for process logs...</span>
                    </div>
                  </div>
                  
                  <!-- Final Answer Tab -->
                  <div v-else-if="msg.activeTab === 'answer'" class="output-container">
                    <p v-if="msg.content" class="content-text">{{ msg.content }}</p>
                    <div v-else class="processing-placeholder">
                      <div class="bounce-dots">
                        <span>.</span><span>.</span><span>.</span>
                      </div>
                      <span>Processing final answer...</span>
                    </div>
                  </div>

                  <!-- Output Data Tab -->
                  <div v-else-if="msg.activeTab === 'data'" class="data-container">
                    <div class="data-actions" v-if="index === messages.length - 1">
                        <a href="/api/download" download="query_result.csv" class="download-btn">
                            Download CSV
                        </a>
                    </div>
                    <div class="table-wrapper" v-if="msg.outputData && msg.outputData.length > 0">
                        <table>
                            <thead>
                                <tr>
                                    <th v-for="(value, key) in msg.outputData[0]" :key="key">{{ key }}</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(row, i) in msg.outputData" :key="i">
                                    <td v-for="(value, key) in row" :key="key">{{ value }}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    <div v-else class="no-data">
                        No data available.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div v-if="isLoading" class="loading-indicator">
        <span class="processing-text">Processing...</span>
      </div>
      <div ref="messagesEndRef"></div>
    </main>

    <footer class="footer">
      <form @submit.prevent="handleSendMessage" class="input-form">
        <input
          v-model="input"
          type="text"
          placeholder="Ask about your data..."
          class="chat-input"
          :disabled="isLoading"
        />
        <button
          type="submit"
          :disabled="isLoading || !input.trim()"
          class="send-button"
        >
          Send
        </button>
      </form>
    </footer>
  </div>
</template>

<style>
/* Global styles */
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  background-color: #f9fafb;
  color: #1f2937;
}
body { margin: 0; }
</style>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background-color: #f9fafb;
}

.header {
  background: white;
  padding: 1rem;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  border-bottom: 1px solid #e5e7eb;
}
.header h1 {
  margin: 0;
  font-size: 1.25rem;
  color: #374151;
  font-weight: 600;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.message-wrapper {
  display: flex;
  width: 100%;
}
.message-wrapper.user { justify-content: flex-end; }
.message-wrapper.assistant { justify-content: flex-start; }

.message-bubble {
  max-width: 85%;
  padding: 1rem;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  font-size: 0.95rem;
}
.message-bubble.user {
  background-color: #eff6ff;
  border: 1px solid #dbeafe;
  color: #1e40af;
}
.message-bubble.assistant {
  background-color: white;
  border: 1px solid #e5e7eb;
  color: #374151;
  width: 100%;
}

.assistant-content {
  width: 100%;
}

.content-text {
  white-space: pre-wrap;
  margin: 0;
}

.loading-indicator {
  display: flex;
  justify-content: flex-start;
  padding-left: 0.5rem;
}
.processing-text {
  font-size: 0.875rem;
  color: #9ca3af;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .5; }
}

.footer {
  background: white;
  padding: 1.25rem;
  border-top: 1px solid #e5e7eb;
}
.input-form {
  max-width: 56rem;
  margin: 0 auto;
  display: flex;
  gap: 0.75rem;
}

.chat-input {
  flex: 1;
  background-color: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.75rem 1rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.chat-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.send-button {
  background-color: #2563eb;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
}
.send-button:hover:not(:disabled) {
  background-color: #1d4ed8;
}
.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Tabbed Container Styles */
.tabbed-container {
  display: flex;
  flex-direction: column;
}
.tabs-header {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1rem;
}
.tab-btn {
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  color: #6b7280;
  font-weight: 500;
  transition: color 0.2s, border-color 0.2s;
}
.tab-btn:hover {
  color: #374151;
}
.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

.tab-content {
  min-height: 120px;
}

.logs-container {
  background-color: #f3f4f6;
  padding: 1rem;
  border-radius: 0.5rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.75rem;
  color: #4b5563;
  max-height: 350px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
}
.log-entry {
  margin-bottom: 0.375rem;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 0.375rem;
  line-height: 1.4;
}
.log-entry:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.waiting-logs {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  color: #9ca3af;
  font-style: italic;
  justify-content: center;
  height: 80px;
}
.ping-dot {
  width: 0.5rem;
  height: 0.5rem;
  background-color: #3b82f6;
  border-radius: 9999px;
  position: relative;
}
.ping-dot::after {
  content: "";
  position: absolute;
  width: 100%;
  height: 100%;
  background-color: inherit;
  border-radius: inherit;
  animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

@keyframes ping {
  75%, 100% { transform: scale(2.5); opacity: 0; }
}

.output-container {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.processing-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: #9ca3af;
  font-style: italic;
  gap: 0.5rem;
}

.bounce-dots {
  display: flex;
  gap: 0.25rem;
}
.bounce-dots span {
  width: 0.4rem;
  height: 0.4rem;
  background-color: #d1d5db;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.bounce-dots span:nth-child(1) { animation-delay: -0.32s; }
.bounce-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); }
}

/* Data Table Styles */
.data-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.data-actions {
  display: flex;
  justify-content: flex-end;
}

.download-btn {
  background-color: #10b981;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s;
}
.download-btn:hover {
  background-color: #059669;
}

.table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  max-height: 400px;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  text-align: left;
}

th, td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #e5e7eb;
}

th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}

tr:last-child td {
  border-bottom: none;
}
</style>
