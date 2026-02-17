<template>
  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar -->
    <div class="duration-500 bg-white shadow-md w-64" v-if="showTab">
      <div class="p-4">
        <h1 class="text-xl font-semibold text-gray-800">f<span class="text-blue-500 font-bold">ai</span>ry tale</h1>
      </div>
      <nav class="mt-4 flex flex-col pb-24" style="height: calc(100vh - 90px)">
        <router-link
          v-for="tab in tabs"
          :key="tab.name"
          :to="tab.path"
          class="block px-4 py-2 text-left"
          :class="{
            'bg-blue-100 text-blue-600': $route.path === tab.path,
            'text-gray-600 hover:bg-gray-100': $route.path !== tab.path,
          }"
        >
          {{ tab.name }}
        </router-link>
        <button @click="showTab = false" class="mt-auto text-center font-bold">
          &lt;
        </button>
      </nav>
    </div>
    <div v-else class="mt-4 flex flex-col justify-center w-10" style="height: 100vh">
      <button class="text-center font-bold" @click="showTab = true">
        &gt;
      </button>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 overflow-auto">
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
const showTab = ref(true)

const tabs = [
  { name: 'Create New Project', path: '/create-project' },
  { name: 'Select Project', path: '/select-project' },
  { name: 'Characters List', path: '/characters-list' },
  { name: 'Create Photo Dump', path: '/create-photo-dump' },
];

// --- WebSocket Logic ---
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