<script setup>
import { ref } from 'vue'
import ChatDrawer from './components/ChatDrawer.vue'
import Chatbot from './components/Chatbot.vue'

const isChatOpen = ref(false)

const toggleChat = () => {
  isChatOpen.value = !isChatOpen.value
}
</script>

<template>
  <div class="main-app">
    <!-- Main Content Area (will be blurred when chat is open) -->
    <main :class="['main-content', { 'is-blurred': isChatOpen }]">
      <div class="homepage-placeholder">
        <!-- Content will be added here later -->
      </div>
    </main>

    <!-- Vertical Chatbot Button -->
    <button 
      @click="toggleChat" 
      class="chatbot-vertical-tab"
      aria-label="Toggle Chatbot"
    >
      <span class="tab-text">Chatbot</span>
    </button>

    <!-- Chatbot Drawer -->
    <ChatDrawer :isOpen="isChatOpen" @close="isChatOpen = false">
      <Chatbot />
    </ChatDrawer>
  </div>
</template>

<style>
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  
  /* Permitted Color Palette */
  --salt-color-white: rgb(255, 255, 255);
  --salt-color-black: rgb(0, 0, 0);
  --salt-color-brown-100: rgb(243, 238, 232);
  --salt-color-brown-200: rgb(237, 229, 216);
  --salt-color-brown-300: rgb(215, 186, 157);
  --salt-color-brown-400: rgb(184, 138, 103);
  --salt-color-brown-500: rgb(153, 108, 72);
  --salt-color-brown-600: rgb(125, 83, 47);
  --salt-color-brown-700: rgb(103, 63, 27);
  --salt-color-brown-800: rgb(66, 36, 7);
  --salt-color-brown-900: rgb(46, 25, 5);

  background-color: var(--salt-color-brown-100);
  color: var(--salt-color-black);
}

body {
  margin: 0;
  overflow-x: hidden;
  color: var(--salt-color-black);
}
</style>

<style scoped>
.main-app {
  position: relative;
  min-height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--salt-color-brown-100);
}

.main-content {
  min-height: 100vh;
  width: 100%;
  transition: filter 0.3s ease-in-out;
}

.main-content.is-blurred {
  filter: blur(8px);
  pointer-events: none;
}

.homepage-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: var(--salt-color-brown-100);
}

.chatbot-vertical-tab {
  position: fixed;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  background-color: var(--salt-color-brown-700);
  color: var(--salt-color-white);
  border: none;
  border-radius: 8px 0 0 8px;
  padding: 1.25rem 0.625rem;
  cursor: pointer;
  z-index: 999;
  box-shadow: -2px 0 12px rgba(46, 25, 5, 0.15);
  transition: all 0.2s ease-in-out;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chatbot-vertical-tab:hover {
  background-color: var(--salt-color-brown-800);
  padding-right: 0.875rem;
}

.tab-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-weight: 600;
  font-size: 0.9rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  transform: rotate(180deg);
}
</style>
