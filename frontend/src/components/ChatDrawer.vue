<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    required: true
  }
})

defineEmits(['close'])
</script>

<template>
  <div class="drawer-wrapper">
    <!-- Dim Background Overlay -->
    <transition name="fade">
      <div v-show="isOpen" class="drawer-overlay" @click="$emit('close')"></div>
    </transition>
    
    <!-- Drawer Content -->
    <transition name="slide">
      <div v-show="isOpen" class="drawer-container">
        <div class="drawer-header">
          <button @click="$emit('close')" class="close-arrow-btn" title="Close Chatbot">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12"></line>
              <polyline points="12 5 19 12 12 19"></polyline>
            </svg>
          </button>
        </div>
        <div class="drawer-content">
          <slot></slot>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.drawer-wrapper {
  z-index: 1000;
}

.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(46, 25, 5, 0.4); /* Based on brown-900 */
  z-index: 1000;
}

.drawer-container {
  position: fixed;
  top: 0;
  right: 0;
  width: 50%;
  height: 100vh;
  background-color: var(--salt-color-white);
  box-shadow: -4px 0 20px rgba(46, 25, 5, 0.1);
  z-index: 1001;
  display: flex;
  flex-direction: column;
}

@media (max-width: 1200px) {
  .drawer-container {
    width: 35%;
  }
}

@media (max-width: 768px) {
  .drawer-container {
    width: 80%;
  }
}

@media (max-width: 480px) {
  .drawer-container {
    width: 100%;
  }
}

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
  overflow: hidden;
  display: flex;
  flex-direction: column;
}


/* Transitions */
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease-in-out;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease-in-out;
}
</style>
