<script setup>
/**
 * ChatDrawer.vue
 * A slide-out container (drawer) for the chatbot.
 * It remains in the DOM (using v-show) to preserve the conversation state.
 */
defineProps({
  isOpen: {
    type: Boolean,
    required: true // Controls visibility of the drawer
  }
})

// Emit event to notify parent (App.vue) to close the drawer
defineEmits(['close'])
</script>

<template>
  <div class="drawer-wrapper">
    <!-- Dim Background Overlay: Closes the drawer when clicked -->
    <transition name="fade">
      <div v-show="isOpen" class="drawer-overlay" @click="$emit('close')"></div>
    </transition>
    
    <!-- Drawer Container: Slides in from the right -->
    <transition name="slide">
      <div v-show="isOpen" class="drawer-container">
        <!-- Drawer Header: Contains the close button -->
        <div class="drawer-header">
          <button @click="$emit('close')" class="close-arrow-btn" title="Close Chatbot">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
        </div>
        
        <!-- Drawer Content: Slot for the Chatbot component -->
        <div class="drawer-content">
          <slot></slot>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
/* --- Component Styles --- */

.drawer-wrapper {
  z-index: 1000; /* Ensure it stays above main content */
}

/* Darkened background when drawer is open */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(46, 25, 5, 0.4); 
  z-index: 1000;
}

/* The actual side panel */
.drawer-container {
  position: fixed;
  top: 0;
  right: 0;
  width: 50%; /* Default width for desktop */
  height: 100vh;
  background-color: var(--salt-color-white);
  box-shadow: -4px 0 20px rgba(46, 25, 5, 0.1);
  z-index: 1001;
  display: flex;
  flex-direction: column;
}

/* Responsive widths for different screen sizes */
@media (max-width: 1200px) { .drawer-container { width: 35%; } }
@media (max-width: 768px)  { .drawer-container { width: 80%; } }
@media (max-width: 480px)  { .drawer-container { width: 100%; } }

.drawer-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--salt-color-brown-200);
  display: flex;
  justify-content: flex-start;
  align-items: center;
  background: var(--salt-color-brown-100);
}

.close-arrow-btn {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--salt-color-brown-600);
  padding: 0.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-arrow-btn:hover {
  background-color: var(--salt-color-brown-200);
  color: var(--salt-color-brown-800);
  transform: translateX(2px);
}

.drawer-content {
  flex: 1;
  overflow: hidden; /* Important for the chatbot internal scroll */
  display: flex;
  flex-direction: column;
}

/* --- Animation Transitions --- */

/* Slide from right to left */
.slide-enter-from, .slide-leave-to { transform: translateX(100%); }
.slide-enter-active, .slide-leave-active { transition: transform 0.3s ease-in-out; }

/* Fade in for the overlay */
.fade-enter-from, .fade-leave-to { opacity: 0; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease-in-out; }
</style>
