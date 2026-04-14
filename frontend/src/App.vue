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
    <div class="flex-1 py-6 px-10 max-h-screen overflow-y-auto">
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
import { onMounted } from 'vue';
import BackgroundTasks from './components/BackgroundTasks.vue';
import BackgroundPattern from './components/main_layout/BackgroundPattern.vue';
import SideBar from './components/main_layout/SideBar.vue';
import { useWebSockets, notifications } from '@/utils/useWebSocket';

const { connectGlobalWS, connectResponsesWS } = useWebSockets();

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

onMounted(() => {
  connectGlobalWS();
  connectResponsesWS();
});


</script>