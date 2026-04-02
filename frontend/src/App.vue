<script setup>
/**
 * App.vue
 * This is the root component of the application.
 * It manages the overall layout, including the main content area,
 * the vertical chatbot trigger, and the slide-out ChatDrawer.
 */
import { ref } from 'vue'
import ChatDrawer from './components/ChatDrawer.vue'
import Chatbot from './components/Chatbot.vue'
import ClientsList from './components/ClientsList.vue'

// --- State Management ---
const isChatOpen = ref(false) // Controls whether the chatbot drawer is visible

/**
 * Toggles the visibility of the chatbot drawer.
 */
const toggleChat = () => {
  isChatOpen.value = !isChatOpen.value
}
</script>

<template>
  <div class="main-app">
    <!-- 
      Main Content Area: 
      Displays the Dashboard (ClientsList).
      When the chatbot is open, this area gets blurred and disabled for interaction.
    -->
    <main :class="['main-content', { 'is-blurred': isChatOpen }]">
      <div class="homepage-content">
        <ClientsList />
      </div>
    </main>

    <!-- 
      Vertical Chatbot Button:
      Fixed to the right side of the screen. 
      Clicking it opens the slide-out drawer.
    -->
    <button 
      @click="toggleChat" 
      class="chatbot-vertical-tab"
      aria-label="Toggle Chatbot"
    >
      <span class="tab-text">Assistant</span>
    </button>

    <!-- 
      Chatbot Drawer:
      Slide-out panel containing the actual Chatbot interface.
      Uses v-show internally to keep the chatbot state alive even when closed.
    -->
    <ChatDrawer :isOpen="isChatOpen" @close="isChatOpen = false">
      <Chatbot />
    </ChatDrawer>
  </div>
</template>

<style>
/* --- Global Styles --- */

:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  
  /* Permitted Color Palette (Salt Theme) */
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
  overflow-x: hidden; /* Prevent horizontal scroll on body */
  color: var(--salt-color-black);
}
</style>

<style scoped>
/* --- Component Specific Styles --- */

.main-app {
  position: relative;
  min-height: 100vh;
  width: 100vw;
  background-color: var(--salt-color-brown-100);
}

.main-content {
  min-height: 100vh;
  width: 100%;
  transition: filter 0.3s ease-in-out; /* Smooth blur transition */
}

/* Blurring effect for the dashboard when drawer is open */
.main-content.is-blurred {
  filter: blur(8px);
  pointer-events: none; /* Disables clicking on background while drawer is active */
}

.homepage-content {
  width: 100%;
  min-height: 100vh;
  overflow-y: auto;
  background-color: var(--salt-color-brown-100);
}

/* Vertical Tab Styling (Right Side) */
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
  padding-right: 0.875rem; /* Slight expansion on hover */
}

.tab-text {
  writing-mode: vertical-rl;
  text-orientation: mixed;
  font-weight: 600;
  font-size: 0.9rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  transform: rotate(180deg); /* Flip text orientation */
}
</style>
