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

watch(messages, (newVal, oldVal) => {
  if (newVal.length > oldVal.length) {
    scrollToBottom()
  }
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
  <div class="chatbot-container">
    <header class="header">
      <h1>LangGraph DB Chatbot</h1>
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
                    <div class="data-actions">
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

<style scoped>
.chatbot-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: var(--salt-color-brown-100);
}

.header {
  background: var(--salt-color-white);
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(46, 25, 5, 0.05);
  border-bottom: 1px solid var(--salt-color-brown-200);
}
.header h1 {
  margin: 0;
  font-size: 1.15rem;
  color: var(--salt-color-brown-900);
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.message-wrapper {
  display: flex;
  width: 100%;
}
.message-wrapper.user { justify-content: flex-end; }
.message-wrapper.assistant { justify-content: flex-start; }

.message-bubble {
  max-width: 90%;
  padding: 0.875rem 1rem;
  border-radius: 0.75rem;
  font-size: 0.925rem;
  position: relative;
  line-height: 1.5;
}
.message-bubble.user {
  background-color: var(--salt-color-brown-200);
  border: 1px solid var(--salt-color-brown-200);
  color: var(--salt-color-black);
}
.message-bubble.assistant {
  background-color: var(--salt-color-white);
  border: 1px solid var(--salt-color-brown-200);
  color: var(--salt-color-black);
  box-shadow: 0 2px 4px rgba(46, 25, 5, 0.03);
}

.user-message-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

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
  color: var(--salt-color-brown-400);
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}
.copy-icon-btn:hover {
  background-color: var(--salt-color-brown-100);
  color: var(--salt-color-brown-600);
}
.copy-icon-btn.inline { margin-top: -2px; }
.copy-icon-btn.absolute {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
}

.status-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}

.status-tool {
  font-weight: 600;
  color: var(--salt-color-black);
}
.status-node {
  font-size: 0.8rem;
  color: var(--salt-color-brown-500);
  font-style: italic;
}

.footer {
  background: var(--salt-color-white);
  padding: 1rem;
  border-top: 1px solid var(--salt-color-brown-200);
}
.input-form {
  display: flex;
  align-items: flex-end;
  gap: 0.625rem;
}

.input-container {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.chat-input {
  flex: 1;
  background-color: var(--salt-color-brown-100);
  border: 1px solid var(--salt-color-brown-200);
  border-radius: 0.5rem;
  padding: 0.75rem 2.5rem 0.75rem 0.875rem;
  outline: none;
  transition: all 0.2s;
  resize: vertical;
  min-height: 40px;
  max-height: 150px;
  font-family: inherit;
  font-size: 0.925rem;
  color: var(--salt-color-black);
}
.chat-input:focus {
  border-color: var(--salt-color-brown-400);
  background-color: var(--salt-color-white);
  box-shadow: 0 0 0 3px rgba(184, 138, 103, 0.1);
}

.stop-button {
  position: absolute;
  right: 0.5rem;
  bottom: 0.5rem;
  background: none;
  border: none;
  color: #c2410c; 
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  border-radius: 4px;
}

.send-button {
  background-color: var(--salt-color-brown-700);
  color: var(--salt-color-white);
  padding: 0.625rem 1.25rem;
  border-radius: 0.5rem;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  height: 40px;
}
.send-button:hover:not(:disabled) {
  background-color: var(--salt-color-brown-800);
}
.send-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Tabbed Container Styles */
.tabbed-container { display: flex; flex-direction: column; }
.tabs-header {
  display: flex;
  border-bottom: 1px solid var(--salt-color-brown-100);
  margin-bottom: 0.875rem;
}
.tab-btn {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  color: var(--salt-color-black);
  font-weight: 600;
  transition: all 0.2s;
  opacity: 0.6;
}
.tab-btn:hover { opacity: 1; }
.tab-btn.active {
  opacity: 1;
  border-bottom-color: var(--salt-color-brown-700);
}

.tab-content { min-height: 80px; }

.processing-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100px;
  color: var(--salt-color-brown-400);
  gap: 0.5rem;
}

.bounce-dots { display: flex; gap: 0.25rem; }
.bounce-dots span {
  width: 0.4rem;
  height: 0.4rem;
  background-color: var(--salt-color-brown-300);
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
  background-color: var(--salt-color-brown-600);
  color: var(--salt-color-white);
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  text-decoration: none;
  font-size: 0.8rem;
  font-weight: 600;
}

.table-wrapper {
  overflow-x: auto;
  overflow-y: auto;
  max-height: 400px;
  border: 1px solid var(--salt-color-brown-200);
  border-radius: 0.375rem;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.825rem;
  color: var(--salt-color-black);
}

th, td { padding: 0.625rem 0.875rem; border-bottom: 1px solid var(--salt-color-brown-100); }
th {
  background-color: var(--salt-color-brown-100);
  font-weight: 700;
  color: var(--salt-color-black);
  position: sticky;
  top: 0;
  z-index: 10;
}

/* SQL Query Styles */
.sql-wrapper {
  position: relative;
  background-color: var(--salt-color-black);
  border-radius: 0.5rem;
  padding: 1rem;
  color: var(--salt-color-brown-100);
  font-size: 0.825rem;
  overflow: hidden;
}
.sql-wrapper pre { margin: 0; overflow-x: auto; }
.sql-wrapper code { white-space: pre-wrap; word-break: break-all; }
</style>
