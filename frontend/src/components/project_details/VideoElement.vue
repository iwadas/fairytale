<template>
  <div class="w-full">
    {{ actualDuration }}
    <div v-if="loading">
       <div class="flex rounded overflow-hidden">
        <div 
          v-for="n in NUMBER_OF_FRAMES" 
          :key="n" 
          class="w-[50px] min-w-[50px] h-[50px]"
          :class="{
            'bg-gray-200' : n % 3 == 0,
            'bg-gray-300' : n % 3 == 1,
            'bg-gray-400' : n % 3 == 2,
          }"
        ></div>
      </div>
    </div>
    
    <div v-else>
      <div class="flex rounded overflow-hidden">
        <img 
          v-for="(thumbUrl, index) in displayedThumbnails" 
          :key="index" 
          :src="thumbUrl" 
          class="w-[50px] min-w-[50px] h-[50px] object-cover"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount } from 'vue';
import { getMetadata, getThumbnails } from 'video-metadata-thumbnails';


const NUMBER_OF_FRAMES = 8;

const props = defineProps({
  scene: Object,
  numberOfFramesToDisplay: {
    type: Number,
    default: 6
  },
  actualDuration: Number,
});

// State
const loading = ref(true);
const thumbnails = ref([]);
const scrubberRef = ref(null);


const displayedThumbnails = computed(()=>{
  const result = [];
  if(thumbnails.value.length === 0) return result;
  for (let i = 0; i < props.numberOfFramesToDisplay; i++) {
    const index = Math.floor(i * NUMBER_OF_FRAMES / props.numberOfFramesToDisplay);
    if (thumbnails.value[index]) {
      result.push(thumbnails.value[index]);
    } else {
      console.warn(`Thumbnail at index ${index} is missing.`);
    }
  }
  return result;
})


onMounted(async () => {


  try {
    loading.value = true;
    
    const response = await fetch(`http://localhost:8000/${props.scene.video_src}`);
    const blob = await response.blob();
    
    const metadata = await getMetadata(blob);
    const duration = metadata.duration;
    
    const intervalTime = duration / (NUMBER_OF_FRAMES + 1);
    
    const generatedThumbnails = await getThumbnails(blob, {
      start: intervalTime,
      end: duration - intervalTime,
      interval: intervalTime,
      quality: 0.2,   
    });
    
    thumbnails.value = generatedThumbnails.map(item => {
      const imageBlob = item.blob ? item.blob : item; 
      return URL.createObjectURL(imageBlob);
    }).slice(0, NUMBER_OF_FRAMES); 
    
  } catch (error) {
    console.error("Failed to generate thumbnails:", error);
  } finally {
    loading.value = false;
      if(thumbnails.value.length === 0) {
        console.warn("No thumbnails were generated.");
      } else {
          if (!scrubberRef.value || thumbnails.value.length === 0) return;
      }
  }
});

onBeforeUnmount(() => {
  thumbnails.value.forEach(url => URL.revokeObjectURL(url));
});


</script>