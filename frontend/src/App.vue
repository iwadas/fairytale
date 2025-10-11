<template>
  <div class="flex h-screen bg-gray-100 font-sans">
    <!-- Sidebar -->
    <div class="w-64 bg-white shadow-md">
      <div class="p-4">
        <h1 class="text-xl font-semibold text-gray-800">f<span class="text-blue-500 font-bold">ai</span>ry tale</h1>
      </div>
      <nav class="mt-4">
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
      </nav>
    </div>

    <!-- Main Content -->
    <div class="flex-1 p-6 overflow-auto">
      <router-view />
    </div>
  </div>
</template>

<script setup>

const tabs = [
  { name: 'Create New Project', path: '/create-project' },
  { name: 'Select Project', path: '/select-project' },
  { name: 'Characters List', path: '/characters-list' },
];
</script>