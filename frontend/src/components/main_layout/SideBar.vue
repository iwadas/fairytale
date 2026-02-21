<template>
  <div class="min-h-screen p-10 pr-0 flex">
    
 

    <nav 
      v-if="showTab" 
      class="w-[100px] container-background rounded-[10px] py-4 flex flex-col items-center gap-8 shadow-2xl transition-all duration-300"
    >

      <div class="flex justify-center -my-4">
        <img :src="logo" alt="Logo">
      </div>

      <div 
        v-for="(tab, index) in tabs" 
        :key="index"
        class="flex flex-col items-center w-full"
      >
        
        <button 
          @click="tab.sub_paths ? toggleTab(index) : goTo(tab.path)"
          class="flex flex-col items-center justify-center gap-2 cursor-pointer group transition-all duration-300 w-full"
          :class="selectedTabIndex === index ? 'text-primary' : 'text-light-hover'"
        >
          <div class="relative flex items-center justify-center">
            <div 
              v-if="selectedTabIndex === index" 
              class="absolute inset-0 bg-primary blur-md opacity-50 rounded-full scale-150"
            ></div>
            <font-awesome-icon :icon="tab.icon" class="text-2xl relative z-10"/>
          </div>
          
          <span class="text-[10px] font-medium text-center leading-tight px-1 mt-1">
            {{ tab.name }}
          </span>
        </button>

        <div 
          v-if="tab.sub_paths && expandedTab === index"
          class="flex flex-col items-center gap-5 mt-5 w-full transition-all duration-300"
        >          
          <button
            v-for="(sub, subIndex) in tab.sub_paths" 
            :key="subIndex"
            @click="goTo(sub.path)"
            class="flex flex-col items-center justify-center gap-1 cursor-pointer text-light hover:text-light-hover transition-colors"
          >
            <font-awesome-icon :icon="sub.icon" class="text-[1.1rem]"/>
            <span class="text-[8px] font-medium text-center leading-tight px-1">
              {{ sub.name }}
            </span>
          </button>
          <div class="w-1/2 h-[1px] bg-[var(--light)] rounded-full mb-1"></div>

        </div>

      </div>
    </nav>
    
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router'; 
import logo from '@/assets/logo.png';

const router = useRouter();

const props = defineProps({
  tabs: {
    type: Array,
    required: true
  }
});

const showTab = ref(true);

// Track which tab is currently expanded (default to 0 to show the first tab's sub-paths)
const expandedTab = ref(0); 

const toggleTab = (index) => {
  // If clicking the already open tab, close it. Otherwise, open the new one.
  expandedTab.value = expandedTab.value === index ? null : index;
};

const selectedTabIndex = computed(() => {
  const currentPath = router.currentRoute.value.path;
  return props.tabs.findIndex(tab => 
    tab.path === currentPath || (tab.sub_paths && tab.sub_paths.some(sub => sub.path === currentPath))
  );
});

const goTo = (path) => {
    if (path) {
        router.push(path);
    }
};

</script>