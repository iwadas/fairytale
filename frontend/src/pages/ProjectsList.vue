<template>
  <div class="w-full min-h-screen">

    <div 
      v-if="activeMenu" 
      @click="activeMenu = null" 
      class="fixed inset-0 z-10"
    ></div>

    <div class="flex flex-wrap gap-4 justify-center container">

      <div
        v-for="project in projects"
        :key="project.id"
        @click="selectProject(project)"
        class="flex flex-col gap-4 transition-all duration-300 border border-transparent w-full sm:w-80 cursor-pointer relative group overflow-hidden"
        :class="activeMenu === project.id ? 'z-20 container-background' : 'z-0 container-background-hover'"
      >
        
        <button 
          @click.stop="toggleMenu(project.id)"
          class="absolute top-2 right-2 z-20 p-1 bg-black/40 hover:bg-black/60 rounded-[10px] transition-colors text-white"
        >
          <font-awesome-icon icon="ellipsis-v" />
        </button>

        <div 
          v-if="activeMenu === project.id"
          class="absolute top-10 right-2 z-30 bg-[#1a1a1a] border border-white/10 rounded-[8px] shadow-xl flex flex-col min-w-[120px] overflow-hidden"
        >
          <button
            @click.stop="downloadProject(project.id); activeMenu = null"
            class="px-4 py-2 text-left text-sm text-light hover:bg-white/5 transition-colors"
          >
            <font-awesome-icon icon="download" class="mr-1" />
            Download
          </button>
          <button
            @click.stop="copyProject(project.id); activeMenu = null"
            class="px-4 py-2 text-left text-sm text-light hover:bg-white/5 transition-colors"
          >
            <font-awesome-icon icon="copy" class="mr-1" />
            Copy
          </button>
          <button
            @click.stop="addTranslations(project.id); activeMenu = null"
            class="px-4 py-2 text-left text-sm text-light hover:bg-white/5 transition-colors"
          >
            <font-awesome-icon icon="language" class="mr-1" />
            Translate
          </button>
          <div class="h-px bg-white/10 w-full"></div>
          <button
            @click.stop="deleteProject(project.id); activeMenu = null"
            class="px-4 py-2 text-left text-sm text-red-400 hover:bg-red-400/10 transition-colors"
          >
            <font-awesome-icon icon="trash" class="mr-1" />
            Delete
          </button>
        </div>

        <div class="w-full h-40 relative overflow-hidden">
          <img 
            v-if="project.thumbnail"
            :src="getSrc(project.thumbnail)" 
            alt="Project Thumbnail"
            class="w-full h-full object-cover bg-black/20 shadow-inner group-hover:scale-105 transition-transform duration-300"
          />
          <div 
            v-else 
            class="w-full h-full bg-black/20 flex items-center justify-center text-light-hover text-[10px] uppercase tracking-wider shadow-inner"
          >
            No Image
          </div>
        </div>

        <div class="flex flex-col gap-1 p-4 pt-0">
          <p class="text-light font-medium text-lg truncate">{{ project.name }}</p>
          <p class="text-[10px] text-light-hover font-medium uppercase tracking-wider">
            Created: {{ new Date(project.created_at).toLocaleDateString() }}
          </p>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import getSrc from '../utils/getSrc.js'

const router = useRouter();
const projects = ref([]);
const activeMenu = ref(null); // State to track which dropdown is open

const toggleMenu = (projectId) => {
  // Toggle the menu off if it's already open, otherwise open it
  activeMenu.value = activeMenu.value === projectId ? null : projectId;
};

const selectProject = (project) => {
  if(project.type === 'PHOTO_DUMP' || project.name.toLowerCase().includes('photo dump')){
    router.push(`/photo-dump-projects/${project.id}`);
    return;
  }
  router.push(`/projects/${project.id}`);
};

const copyProject = (projectId) => {
  axios.post(`http://localhost:8000/projects/copy/${projectId}`)
    .then(res => console.log(res))
}

const addTranslations = (projectId) => {
  axios.post(`http://localhost:8000/projects/add-translations/${projectId}`)
    .then(res => console.log(res))
}

const deleteProject = (projectId) => {
  axios.delete(`http://localhost:8000/projects/${projectId}`)
    .then(res => {
        console.log(res);
        // Clean up UI instantly without refresh
        projects.value = projects.value.filter(p => p.id !== projectId);
    })
}

const downloadProject = (projectId) => {
  axios.post(`http://localhost:8000/projects/download/${projectId}`)
    .then(res => console.log(res))
}

onMounted(() => {
  axios.get('http://localhost:8000/projects').then(response => {
    console.log(response.data)
    projects.value = response.data
  })
})
</script>