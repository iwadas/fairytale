<template>
  <div>
    <h2 class="text-2xl font-semibold text-gray-800 mb-4">Create New Project</h2>
    <div class="bg-white p-6 rounded-lg shadow-sm">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-600">Topic</label>
          <input
            v-model="projectPrompt.topic"
            type="text"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter topic..."
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600">Film Duration (seconds)</label>
          <input
            v-model="projectPrompt.duration"
            type="number"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter duration..."
          />
        </div>
        <button
          @click="createProject"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Generate Script
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue';
// import { useRouter } from 'vue-router';
import axios from 'axios';

// const router = useRouter();
const projectPrompt = reactive({
  topic: '',
  duration: 120,
});

const createProject = async () => {
  console.log('Creating project with:', projectPrompt);
  await axios.post('http://localhost:8000/generators/generate-script', projectPrompt);

  // const newProjectId = response.data.project_id;
  // console.log('Project created with ID:', response.data);
  // router.push(`/projects/${newProjectId}`);

};
</script>