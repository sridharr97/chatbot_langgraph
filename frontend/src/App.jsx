import { useState, useRef, useEffect } from 'react'

function App() {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Hello! I am your database assistant. How can I help you today?',
      logs: [],
      isComplete: true
      // No id here: ensures greeting renders as simple text
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Add a placeholder assistant message with a unique ID
    const assistantMessageId = Date.now()
    setMessages(prev => [
      ...prev, 
      { 
        id: assistantMessageId,
        role: 'assistant', 
        logs: [], 
        content: '', 
        isComplete: false 
      }
    ])

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
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
            
            setMessages(prev => prev.map(msg => {
              if (msg.id !== assistantMessageId) return msg
              
              if (data.type === 'log') {
                return { ...msg, logs: [...msg.logs, data.content] }
              } else if (data.type === 'result') {
                return { ...msg, content: data.content, isComplete: true }
              } else if (data.type === 'error') {
                 return { ...msg, content: `Error: ${data.content}`, isComplete: true }
              }
              return msg
            }))

          } catch (e) {
            console.error('Error parsing JSON line:', e)
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
      setMessages(prev => prev.map(msg => {
         if (msg.id !== assistantMessageId) return msg
         return { ...msg, content: 'Sorry, I encountered an error connecting to the server.', isComplete: true }
      }))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen w-screen bg-gray-50 text-gray-800 font-sans">
      {/* Header */}
      <header className="bg-white p-4 shadow-sm border-b border-gray-200 sticky top-0 z-10">
        <h1 className="text-xl font-semibold text-gray-700">LangGraph DB Chatbot</h1>
      </header>

      {/* Messages Area */}
      <main className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[90%] md:max-w-[80%] rounded-lg p-4 shadow-sm ${
                msg.role === 'user'
                  ? 'bg-blue-50 text-gray-800 border border-blue-100'
                  : 'bg-white text-gray-800 border border-gray-200 w-full'
              }`}
            >
              {msg.role === 'assistant' ? (
                <AssistantMessageContent message={msg} />
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
           <div className="flex justify-start opacity-50">
             <span className="text-sm text-gray-500 ml-2 animate-pulse">Processing...</span>
           </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      {/* Input Area */}
      <footer className="p-4 bg-white border-t border-gray-200 sticky bottom-0 z-10">
        <form onSubmit={handleSendMessage} className="flex space-x-2 max-w-4xl mx-auto">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your data..."
            className="flex-1 bg-gray-50 text-gray-800 border border-gray-300 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent transition-shadow shadow-inner"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-3 px-6 rounded-lg transition-colors shadow-sm"
          >
            Send
          </button>
        </form>
      </footer>
    </div>
  )
}

function AssistantMessageContent({ message }) {
  const [activeTab, setActiveTab] = useState('processing')
  const [hasAutoSwitched, setHasAutoSwitched] = useState(false)
  
  // Auto-switch to Output tab ONLY once when complete and content exists
  useEffect(() => {
    if (message.isComplete && message.content && !hasAutoSwitched) {
      setActiveTab('output')
      setHasAutoSwitched(true)
    }
  }, [message.isComplete, message.content, hasAutoSwitched])

  // Simple rendering for messages without an ID (like the initial greeting)
  if (!message.id) {
      return <p className="whitespace-pre-wrap">{message.content}</p>
  }

  return (
    <div className="flex flex-col w-full h-full">
      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-3">
        <button
          onClick={() => setActiveTab('processing')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'processing'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Query Processing
        </button>
        <button
          onClick={() => setActiveTab('output')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'output'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          Output
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 min-h-[120px]">
        {activeTab === 'processing' ? (
          <div className="bg-gray-50 p-3 rounded-md font-mono text-[11px] text-gray-600 h-full overflow-x-auto max-h-[400px] overflow-y-auto border border-gray-100 shadow-inner">
            {message.logs && message.logs.length > 0 ? (
              message.logs.map((log, i) => (
                <div key={i} className="mb-1 border-b border-gray-100 pb-1 last:border-0 last:pb-0">
                  {log}
                </div>
              ))
            ) : (
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-ping"></div>
                <span className="italic text-gray-400">Waiting for process logs...</span>
              </div>
            )}
             {/* Auto-scroll to bottom of logs inside the tab */}
             <div ref={(el) => el?.scrollIntoView({ behavior: "smooth" })} />
          </div>
        ) : (
          <div className="prose prose-sm max-w-none text-gray-800 animate-in fade-in duration-500">
            {message.content ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="flex flex-col items-center justify-center h-24 text-gray-400 italic space-y-2">
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce"></div>
                  <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:-.15s]"></div>
                  <div className="w-1.5 h-1.5 bg-gray-300 rounded-full animate-bounce [animation-delay:-.3s]"></div>
                </div>
                <span>Processing final answer...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App
