<template>
  <div>
    <h2 class="text-2xl font-semibold text-gray-800 mb-4">Create New Project</h2>
    <div v-if="scriptSamples.length" class="flex flex-col gap-4">
      <h2 class="font-bold text-2xl">Select script</h2>
      <div class="flex flex-col gap-2">
        <div 
          class="border p-2 rounded-sm"
          v-for="(sample, index) in scriptSamples"
          :key="index"
        >
          <label class="block text-sm font-medium text-gray-600">Script Sample {{ index + 1 }} (Estimated time: {{ sample.estimated_time }} seconds)</label>
          <textarea
            v-model="scriptSamples[index]"
            type="number"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500 min-h-[250px]"
            placeholder="Already gathered data"
          />
          <button class="bg-blue-500 font-bold p-2 rounded text-xs" @click="selectScript(index)">
            Select Script Sample {{ index + 1 }}
          </button>
        </div>
      </div>
    </div>

    
    <div v-else class="bg-white p-6 rounded-lg shadow-sm">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-600">Topic</label>
          <input
            v-model="scriptPrompt.topic"
            type="text"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter topic..."
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600">Description</label>
          <input
            v-model="scriptPrompt.description"
            type="text"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter description..."
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600">Film Duration (seconds)</label>
          <input
            v-model="scriptPrompt.duration"
            type="number"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter duration..."
          />
        </div>
        <div class="flex gap-2 items-center">
          <label class="block text-sm font-medium text-gray-600">Gather Data</label>
          <input
            v-model="scriptPrompt.gather_data"
            type="checkbox"
            class="p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600">Data (optional)</label>
          <textarea
            v-model="scriptPrompt.data"
            type="number"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500 min-h-[250px]"
            placeholder="Already gathered data"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600">Reference stories (optional)</label>
          <textarea
            v-model="scriptPrompt.reference_stories"
            type="number"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500 min-h-[250px]"
            placeholder="Paste refernce stories"
          />
        </div>
        <div class="flex gap-2 items-center">
          <label class="block text-sm font-medium text-gray-600">Persistant characters</label>
          <input
            v-model="scriptPrompt.persistant_characters"
            type="checkbox"
            class="p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          @click="createScripts"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Generate Script
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const scriptPrompt = reactive({
  topic: '',
  description: '',
  duration: 60,
  data: null,
  persistant_characters: false,
  gather_data: false,
  reference_stories: '',
});

const projectPrompt = reactive({
  script: '',
  topic: '',
})

const createProject = async () => {
  console.log(projectPrompt);
  console.log('Creating project with:', projectPrompt);
  await axios.post('http://localhost:8000/projects/create-project', projectPrompt)
    .then(response => {
      console.log('Project created:', response.data);
        router.push(`/projects/${response.data.project_id}`);
    })
    .catch(error => {
      console.error('Error creating project:', error);
    });
}


const selectScript = (index) => {
  projectPrompt.script = scriptSamples.value[index];
  projectPrompt.topic = scriptPrompt.topic;
  console.log('Selected script:', projectPrompt);
  createProject();
};

const scriptSamples = ref([]);

const createScripts = async () => {
  console.log('Creating project with:', scriptPrompt);
  await axios.post('http://localhost:8000/projects/generate-script', scriptPrompt)
    .then(response => {
      console.log(response.data)
      response.data.scripts.forEach(sample => {
        scriptSamples.value.push(sample);
      });
    })
    .catch(error => {
      console.error('Error generating script:', error);
    });
};
</script>