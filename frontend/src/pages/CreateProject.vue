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
      <div class="space-y-8"> 
        <div class="space-y-5">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <form-input 
              v-model="scriptPrompt.topic" 
              label="Topic"
              type="text"
              placeholder="E.g., The History of Rome"
              class="w-full"
            />

            <form-input 
              v-model="scriptPrompt.duration" 
              label="Film Duration (seconds)"
              type="number"
              placeholder="60"
              class="w-full"
            />
          </div>

          <form-input 
            v-model="scriptPrompt.style" 
            label="Description"
            type="textarea"
            placeholder="Briefly describe what happens in the script..."
            class="w-full"
          />  
        </div>

        <hr class="border-[var(--light-gray)]" />

        <div class="flex flex-wrap gap-6">
          <form-input
            v-model="scriptPrompt.gather_data" 
            label="Gather External Data"
            type="checkbox"
          />
          <form-input
            v-model="scriptPrompt.persistant_characters" 
            label="Persistent Characters"
            type="checkbox"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <form-input 
            v-model="scriptPrompt.data" 
            :optional="true"
            label="Existing Data"
            type="textarea"
            placeholder="Paste any pre-gathered data here..."
            class="w-full"
          />
          <form-input 
            v-model="scriptPrompt.reference_stories" 
            :optional="true"
            label="Reference Stories"
            type="textarea"
            placeholder="Paste any reference stories or style guides here..."
            class="w-full"
          />

        </div>

        <div class="pt-2 flex justify-center gap-4">
          <form-button
            @clicked="createScripts"
            button_style="primary"
            :show_status="true"
            :loading="generatingScripts"
            label="Generate Script Samples"
          />

          <form-button
            @clicked="skipGeneratingScripts"
            button_style="secondary"
            label="I already have a script"
          />
        

          <!-- <button
            @click="createScripts"
            class="w-full sm:w-auto px-10 py-3 bg-[var(--primary)] text-white font-bold rounded-[10px] hover:bg-[var(--primary-dark)] transition-all duration-300 shadow-lg hover:shadow-red-500/25 flex justify-center items-center gap-2"
          >
            Generate Script
          </button> -->
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
import FormButton from '@/components/FormButton.vue';
import FormInput from '@/components/FormInput.vue';

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
const generatingScripts = ref(false);

const createScripts = async () => {
  if(generatingScript.value) return;
  console.log('Creating project with:', scriptPrompt);
  generatingScripts.value = true;
  await axios.post('http://localhost:8000/projects/generate-script', scriptPrompt)
    .then(response => {
      console.log(response.data)
      response.data.scripts.forEach(sample => {
        scriptSamples.value.push(sample);
      });
    })
    .catch(error => {
      console.error('Error generating script:', error);
    })
    .finally(() => {
      generatingScripts.value = false;
    });
};

const skipGeneratingScripts = () => {
  if(!scriptPrompt.topic) {
    alert('Please enter a topic for your project before proceeding.');
    return;
  }
  projectPrompt.script = scriptPrompt.description;
  projectPrompt.topic = scriptPrompt.topic;
  scriptSamples.value = ["Insert your script here..."];
  console.log('Skipping script generation. Creating project with:', projectPrompt);
}

</script>