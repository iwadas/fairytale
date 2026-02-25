<template>

  <background-pattern
    class="fixed inset-0 z-[-1]"
  />
  <div class="flex h-screen"  
  >
    <!-- Sidebar -->
    <side-bar
      class="p-6"
      :tabs=tabs
    />

    <!-- Main Content -->
    <div class="flex-1 py-6 px-10 overflow-auto">
      <router-view />
    </div>

    <background-tasks
      :notifications=notifications
    />

    <div class="fixed bottom-4 right-4 width-[300px] h-[100px] shadow-lg rounded-lg p-1">
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import BackgroundTasks from './components/BackgroundTasks.vue';
import BackgroundPattern from './components/main_layout/BackgroundPattern.vue';
import SideBar from './components/main_layout/SideBar.vue';

const tabs = [
  { 
    name: 'Create Project',
    icon: 'fa-square-plus',
    sub_paths: [
      { 
        name: 'From Script', 
        path: '/create-project',
        icon: 'fa-video',
      },
      { 
        name: 'Photo Dump', 
        path: '/create-photo-dump',
        icon: 'fa-images'
      },
    ] 
  },
  { name: 'Projects', path: '/select-project', icon: 'fa-photo-film' },
  { name: 'Characters', path: '/characters-list', icon: 'fa-mask' },
  { name: 'Settings', path: '/settings', icon: 'fa-cog' },
];

let socket = null;
const notifications = ref([]);

onMounted(() => {
  // 1. Connect to your FastAPI WebSocket route
  // Make sure the port (8000) and path (/ws) match your backend configuration
  socket = new WebSocket("ws://localhost:8000/ws");

  // 2. Listener: Connection Opened
  socket.onopen = () => {
    console.log("✅ WebSocket Connected");
  };

  // 3. Listener: Receiving Messages (This is what you asked for)
  socket.onmessage = (event) => {
    try {
      const jsonData = JSON.parse(event.data);
      console.log(jsonData.message);
      console.log(jsonData);
      notifications.value.push(jsonData);
    } catch (e) {
      // It's just a text string
    }
  };

  // 4. Listener: Errors
  socket.onerror = (error) => {
    console.error("❌ WebSocket Error:", error);
  };
});

onUnmounted(() => {
  // Close connection if the component unmounts to prevent memory leaks
  if (socket) {
    socket.close();
  }
});
</script>