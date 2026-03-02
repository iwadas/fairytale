<template>
  <div class="w-full">
    {{ actualDuration }}
    <div v-if="loading">
      <div class="flex rounded overflow-hidden">
        <div v-if="fistSceneImg">
          <img :src="fistSceneImg" class="w-[54px] min-w-[54px] h-[54px] object-cover" />
        </div>
        <div 
          v-for="n in (NUMBER_OF_FRAMES - (fistSceneImg ? 1 : 0))" 
          :key="n" 
          class="w-[54px] min-w-[54px] h-[54px] flex justify-center items-center"
          :class="{
            'bg-stone-300' : n % 3 == 0,
            'bg-[var(--light-gray)]' : n % 3 == 1,
            'bg-stone-400' : n % 3 == 2,
          }"
        >
          <font-awesome-icon icon="image"></font-awesome-icon>
        </div>
      </div>
    </div>
    
    <div v-else>
      <div class="flex rounded overflow-hidden">
        <img 
          v-for="(thumbUrl, index) in displayedThumbnails" 
          :key="index" 
          :src="thumbUrl" 
          class="w-[54px] min-w-[54px] h-[54px] object-cover"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onBeforeUnmount, watch } from 'vue';
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

const fistSceneImg = computed(()=>{
  if(props.scene.video_src){
    return null;
  }
  if(props.scene.images.length > 0){
    if(props.scene.images[0].src){
      return `http://localhost:8000/${props.scene.images[0].src}`;
    }
  }
  return null;
})

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


const loadThumbnails = async () => {
  loading.value = true;
  if(!props.scene.video_src) {
    console.warn("No video source provided for the scene.");
    return;
  }
  try {
    
    const response = await fetch(`http://localhost:8000/${props.scene.video_src}`);
    const blob = await response.blob();
    
    const metadata = await getMetadata(blob);
    const duration = metadata.duration;
    
    const intervalTime = duration / (NUMBER_OF_FRAMES + 1);
    
    const generatedThumbnails = await getThumbnails(blob, {
      start: intervalTime,
      end: duration - intervalTime,
      interval: intervalTime,
      quality: 0.1, 
      scale: 0.1, 
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
}

onMounted(async () => {
  await loadThumbnails();
});

watch(() => props.scene.video_src, async (newSrc, oldSrc) => {
  if (newSrc !== oldSrc) {
    thumbnails.value.forEach(url => URL.revokeObjectURL(url));
    thumbnails.value = [];
    await loadThumbnails();
  }
});

onBeforeUnmount(() => {
  thumbnails.value.forEach(url => URL.revokeObjectURL(url));
});


</script>