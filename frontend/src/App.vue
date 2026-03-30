<script setup>
import { ref, onMounted, nextTick, watch } from 'vue'

const messages = ref([
  { 
    role: 'assistant', 
    content: 'Hello! I am your database assistant. How can I help you today?',
    outputData: [],
    sqlQuery: '',
    isComplete: true
  }
])
const input = ref('')
const isLoading = ref(false)
const currentStatusTool = ref('')
const currentStatusNode = ref('')
const messagesEndRef = ref(null)
const sessionThreadId = ref('')
let abortController = null

// Generate a unique thread ID for this browser session/refresh
const generateThreadId = () => {
  return 'thread_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9)
}

onMounted(() => {
  sessionThreadId.value = generateThreadId()
  console.log('Session initialized with thread ID:', sessionThreadId.value)
})

const scrollToBottom = async () => {
  await nextTick()
  if (messagesEndRef.value) {
    messagesEndRef.value.scrollIntoView({ behavior: "smooth" })
  }
}

watch(messages, () => {
  scrollToBottom()
}, { deep: true })

const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    console.log('Copied to clipboard');
  }).catch(err => {
    console.error('Failed to copy text: ', err);
  });
}

const formatValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/.test(value)) {
    return value.split('T')[0]
  }
  if (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value
  }
  if (typeof value === 'number') {
    return value.toLocaleString()
  }
  return value
}

const handleStopProcess = () => {
  if (abortController) {
    abortController.abort()
    isLoading.value = false
    currentStatusTool.value = ''
    currentStatusNode.value = 'Process stopped.'
    
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && !lastMsg.isComplete) {
      lastMsg.isComplete = true
      lastMsg.content = lastMsg.content || 'Process stopped by user.'
      lastMsg.activeTab = 'answer'
    }
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSendMessage()
  }
}

const handleSendMessage = async () => {
  if (!input.value.trim() || isLoading.value) return

  const userMessage = { role: 'user', content: input.value }
  messages.value.push(userMessage)
  
  const currentInput = input.value
  input.value = ''
  isLoading.value = true
  currentStatusTool.value = 'Thinking...'
  currentStatusNode.value = ''
  
  abortController = new AbortController()

  const assistantMessageId = Date.now()
  const newMessage = { 
    id: assistantMessageId,
    role: 'assistant', 
    outputData: [],
    sqlQuery: '',
    content: '', 
    isComplete: false,
    activeTab: 'answer',
    hasAutoSwitched: false
  }
  messages.value.push(newMessage)

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message: currentInput,
        thread_id: sessionThreadId.value
      }),
      signal: abortController.signal
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
            
            if (data.type === 'status') {
              const status = data.content
              if (status.includes('Calling SQL QA Tool')) {
                currentStatusTool.value = status
                currentStatusNode.value = ''
              } else if (status.includes('Processing:')) {
                currentStatusNode.value = status
              } else {
                currentStatusTool.value = status
              }
            } else if (data.type === 'data') {
              msg.outputData = data.content
            } else if (data.type === 'query') {
              msg.sqlQuery = data.content
            } else if (data.type === 'result') {
              msg.content = data.content
              msg.isComplete = true
              if (!msg.hasAutoSwitched) {
                const isLargeResult = msg.content.includes("more than 100 records");
                if (isLargeResult) msg.activeTab = 'data';
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
    if (error.name === 'AbortError') {
      console.log('Fetch aborted')
    } else {
      console.error('Error sending message:', error)
      const msgIndex = messages.value.findIndex(m => m.id === assistantMessageId)
      if (msgIndex !== -1) {
        messages.value[msgIndex].content = 'Sorry, I encountered an error connecting to the server.'
        messages.value[msgIndex].isComplete = true
        messages.value[msgIndex].activeTab = 'answer'
      }
    }
  } finally {
    isLoading.value = false
    abortController = null
    currentStatusTool.value = ''
    currentStatusNode.value = ''
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
          <template v-if="msg.role === 'user'">
            <div class="user-message-content">
              <p class="content-text">{{ msg.content }}</p>
              <button class="copy-icon-btn" @click="copyToClipboard(msg.content)" title="Copy Query">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              </button>
            </div>
          </template>

          <template v-else>
            <div class="assistant-content">
              <div v-if="!msg.id">
                <p class="content-text">{{ msg.content }}</p>
              </div>

              <div v-else class="tabbed-container">
                <div class="tabs-header">
                  <button @click="msg.activeTab = 'answer'" :class="{ active: msg.activeTab === 'answer' }" class="tab-btn">Answer</button>
                  <button @click="msg.activeTab = 'data'" :class="{ active: msg.activeTab === 'data' }" class="tab-btn" v-if="msg.outputData && msg.outputData.length > 0">Output Data</button>
                  <button @click="msg.activeTab = 'query'" :class="{ active: msg.activeTab === 'query' }" class="tab-btn" v-if="msg.sqlQuery">SQL Query</button>
                </div>
                
                <div class="tab-content">
                  <div v-if="msg.activeTab === 'answer'" class="output-container">
                    <div v-if="msg.content" class="answer-with-copy">
                      <p class="content-text">{{ msg.content }}</p>
                      <button class="copy-icon-btn inline" @click="copyToClipboard(msg.content)" title="Copy Answer">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                      </button>
                    </div>
                    <div v-else class="processing-placeholder">
                      <div class="bounce-dots"><span>.</span><span>.</span><span>.</span></div>
                      <div class="status-stack">
                        <span class="status-tool">{{ currentStatusTool || 'Thinking...' }}</span>
                        <span v-if="currentStatusNode" class="status-node">{{ currentStatusNode }}</span>
                      </div>
                    </div>
                  </div>

                  <div v-else-if="msg.activeTab === 'data'" class="data-container">
                    <div class="data-actions" v-if="index === messages.length - 1">
                        <a href="/api/download" download="query_result.csv" class="download-btn">Download CSV</a>
                    </div>
                    <div class="table-wrapper" v-if="msg.outputData && msg.outputData.length > 0">
                        <table>
                            <thead><tr><th v-for="(value, key) in msg.outputData[0]" :key="key">{{ key }}</th></tr></thead>
                            <tbody><tr v-for="(row, i) in msg.outputData" :key="i"><td v-for="(value, key) in row" :key="key">{{ formatValue(value) }}</td></tr></tbody>
                        </table>
                    </div>
                    <div v-else class="no-data">No data available.</div>
                  </div>

                  <div v-else-if="msg.activeTab === 'query'" class="query-container">
                    <div class="sql-wrapper">
                      <pre><code>{{ msg.sqlQuery }}</code></pre>
                      <button class="copy-icon-btn absolute" @click="copyToClipboard(msg.sqlQuery)" title="Copy SQL">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
      <div v-if="isLoading" class="loading-indicator">
        <div class="status-stack mini">
          <span class="processing-text">{{ currentStatusTool || 'Processing...' }}</span>
          <span v-if="currentStatusNode" class="processing-text sub">{{ currentStatusNode }}</span>
        </div>
      </div>
      <div ref="messagesEndRef"></div>
    </main>

    <footer class="footer">
      <form @submit.prevent="handleSendMessage" class="input-form">
        <div class="input-container">
          <textarea
            v-model="input"
            @keydown="handleKeydown"
            placeholder="Ask about your data..."
            class="chat-input"
            :disabled="isLoading"
            rows="1"
          ></textarea>
          <button
            v-if="isLoading"
            type="button"
            @click="handleStopProcess"
            class="stop-button"
            title="Stop Process"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2" ry="2"></rect></svg>
          </button>
        </div>
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
  position: relative;
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
}

.user-message-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.assistant-content { }

.content-text {
  white-space: pre-wrap;
  margin: 0;
}

.answer-with-copy {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.copy-icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: #9ca3af;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.copy-icon-btn:hover {
  background-color: #f3f4f6;
  color: #374151;
}
.copy-icon-btn.inline { margin-top: -2px; }
.copy-icon-btn.absolute {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
}

.loading-indicator {
  display: flex;
  justify-content: flex-start;
  padding-left: 0.5rem;
}

.status-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}
.status-stack.mini { align-items: flex-start; }

.status-tool {
  font-weight: 600;
  color: #374151;
}
.status-node {
  font-size: 0.85rem;
  color: #6b7280;
  font-style: italic;
}

.processing-text {
  font-size: 0.875rem;
  color: #9ca3af;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
.processing-text.sub {
  font-size: 0.75rem;
  animation-delay: 0.5s;
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
  align-items: flex-end;
  gap: 0.75rem;
}

.input-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.chat-input {
  flex: 1;
  background-color: #f9fafb;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  padding: 0.75rem 3rem 0.75rem 1rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  resize: vertical;
  min-height: 44px;
  max-height: 200px;
  font-family: inherit;
  font-size: 0.95rem;
  line-height: 1.4;
}
.chat-input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.stop-button {
  position: absolute;
  right: 0.75rem;
  bottom: 0.75rem;
  background: none;
  border: none;
  color: #ef4444;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 4px;
  transition: background-color 0.2s;
}
.stop-button:hover { background-color: #fee2e2; }

.send-button {
  background-color: #2563eb;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: background-color 0.2s;
  height: 44px;
}
.send-button:hover:not(:disabled) { background-color: #1d4ed8; }
.send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Tabbed Container Styles */
.tabbed-container { display: flex; flex-direction: column; }
.tabs-header {
  display: flex;
  border-bottom: 1px solid #e5e7eb;
  margin-bottom: 1rem;
  overflow-x: auto;
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
  white-space: nowrap;
}
.tab-btn:hover { color: #374151; }
.tab-btn.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

.tab-content { min-height: 120px; }

.output-container { animation: fadeIn 0.3s ease-out; }

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

.bounce-dots { display: flex; gap: 0.25rem; }
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
.data-container { display: flex; flex-direction: column; gap: 1rem; }
.data-actions { display: flex; justify-content: flex-end; }
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
.download-btn:hover { background-color: #059669; }

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

th, td { padding: 0.75rem 1rem; border-bottom: 1px solid #e5e7eb; }
th {
  background-color: #f9fafb;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}
tr:last-child td { border-bottom: none; }

/* SQL Query Styles */
.sql-wrapper {
  position: relative;
  background-color: #1e293b;
  border-radius: 0.5rem;
  padding: 1rem;
  color: #e2e8f0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  font-size: 0.875rem;
  overflow: hidden;
}
.sql-wrapper pre { margin: 0; overflow-x: auto; }
.sql-wrapper code { white-space: pre-wrap; word-break: break-all; }
</style>
