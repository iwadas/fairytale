<template>
  <div>
    <h2 class="text-2xl font-semibold text-gray-800 mb-4">Select Project</h2>
    <div class="grid grid-cols-1 gap-4">
      <div
        v-for="project in projects"
        :key="project.id"
        class="bg-white p-4 rounded-lg shadow-sm flex justify-between items-center"
      >
        <div>
          <p class="text-gray-800 font-medium">{{ project.name }}</p>
          <p class="text-sm text-gray-600">Created: {{ new Date(project.created_at).toLocaleDateString() }}</p>
        </div>
        <button
          @click="selectProject(project.id)"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Open
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';


const router = useRouter();
const projects = ref([]);

const selectProject = (projectId) => {
  router.push(`/projects/${projectId}`);
};

onMounted(()=>{
  axios.get('http://localhost:8000/projects').then(response=>{
    console.log(response.data)
    projects.value = response.data
  })
})

</script>