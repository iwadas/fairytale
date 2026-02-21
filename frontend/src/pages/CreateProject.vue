<template>
  <div class="w-full max-w-4xl mx-auto">
    <div v-if="scriptSamples.length" class="flex flex-col gap-6">
      <h2 class="font-bold text-xl text-light-hover">Select your preferred script</h2>
      <div class="flex flex-col gap-6">
        <div 
          class="container-background p-6 rounded-[10px] shadow-2xl transition-all duration-300 border border-gray-700/50"
          v-for="(sample, index) in scriptSamples"
          :key="index"
        >
          <label class="block text-sm font-medium text-gray-200 mb-2">
            Script Sample {{ index + 1 }} 
            <span class="text-gray-400 font-normal ml-2" v-if="sample.estimated_time">
              (Estimated time: {{ sample.estimated_time }} seconds)
            </span>
          </label>
          <textarea
            v-model="scriptSamples[index]"
            class="w-full mt-1 p-4 bg-transparent border border-[var(--light-gray)] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all min-h-[250px] resize-y custom-scrollbar"
            placeholder="Review or edit your script..."
          />
          <button 
            class="mt-4 bg-[var(--primary)] text-white font-bold px-6 py-2.5 rounded-[10px] hover:bg-red-500 transition-all duration-300 shadow-lg hover:shadow-red-500/25" 
            @click="selectScript(index)"
          >
            Select Script Sample {{ index + 1 }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="container-background p-8 rounded-[10px] shadow-2xl transition-all duration-300 border border-gray-700/50">
      <div class="space-y-8"> <div class="space-y-5">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Topic</label>
              <input
                v-model="scriptPrompt.topic"
                type="text"
                class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all"
                placeholder="E.g., The History of Rome"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-300 mb-1">Film Duration (seconds)</label>
              <input
                v-model="scriptPrompt.duration"
                type="number"
                class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all"
                placeholder="60"
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Description</label>
            <textarea
              v-model="scriptPrompt.description"
              class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all min-h-[100px] resize-y"
              placeholder="Briefly describe what happens in the script..."
            />
          </div>
        </div>

        <hr class="border-gray-700/50" />

        <div class="flex flex-wrap gap-6">
          <div class="flex gap-3 items-center p-3 rounded-[10px] border border-gray-700/50 hover:bg-white/5 transition-colors cursor-pointer w-full sm:w-auto">
            <input
              v-model="scriptPrompt.gather_data"
              type="checkbox"
              id="gatherData"
              class="w-4 h-4 text-[var(--primary)] bg-transparent border-[var(--light-gray)] rounded focus:ring-[var(--primary)] focus:ring-2 cursor-pointer"
            />
            <label for="gatherData" class="block text-sm font-medium text-gray-300 cursor-pointer select-none">
              Gather External Data
            </label>
          </div>

          <div class="flex gap-3 items-center p-3 rounded-[10px] border border-gray-700/50 hover:bg-white/5 transition-colors cursor-pointer w-full sm:w-auto">
            <input
              v-model="scriptPrompt.persistant_characters"
              type="checkbox"
              id="persistantChars"
              class="w-4 h-4 text-[var(--primary)] bg-transparent border-[var(--light-gray)] rounded focus:ring-[var(--primary)] focus:ring-2 cursor-pointer"
            />
            <label for="persistantChars" class="block text-sm font-medium text-gray-300 cursor-pointer select-none">
              Persistent Characters
            </label>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Existing Data <span class="text-gray-500 font-normal">(Optional)</span></label>
            <textarea
              v-model="scriptPrompt.data"
              class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all min-h-[120px] resize-y"
              placeholder="Paste any pre-gathered data here..."
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Reference Stories <span class="text-gray-500 font-normal">(Optional)</span></label>
            <textarea
              v-model="scriptPrompt.reference_stories"
              class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-[10px] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all min-h-[120px] resize-y"
              placeholder="Paste reference stories or style guides..."
            />
          </div>
        </div>

        <div class="pt-2 flex justify-center">
          <button
            @click="createScripts"
            class="w-full sm:w-auto px-10 py-3 bg-[var(--primary)] text-white font-bold rounded-[10px] hover:bg-red-500 transition-all duration-300 shadow-lg hover:shadow-red-500/25 flex justify-center items-center gap-2"
          >
            Generate Script
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Your existing script remains unchanged, keeping it here for completeness
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