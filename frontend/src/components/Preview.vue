<template>
  <div class="flex flex-col gap-3 w-full max-w-4xl mx-auto mb-6 select-none">
    
    <div class="relative w-full aspect-video bg-dark rounded-[10px] overflow-hidden shadow-2xl flex items-center justify-center">
      
      <template v-for="clip in sortedActiveElements" :key="clip.id">
        <video
          v-if="clip.type === 'scene' && clip.video_src"
          :src="getSrc(clip.video_src)"
          :ref="el => setMediaRef(el, clip.id)"
          class="absolute top-0 left-0 w-full h-full object-contain pointer-events-none"
          playsinline
        ></video>
        
        <audio
          v-else-if="AUDIO_TYPES.includes(clip.type) && clip.src"
          :src="getSrc(clip.src)"
          :ref="el => setMediaRef(el, clip.id)"
        ></audio>
      </template>

      <div v-if="!activeElements.length" class="text-gray-700 font-medium tracking-widest uppercase text-sm">
        No Media
      </div>
    </div>

    <div class="flex items-center justify-between text-light">

      <p class="font-mono opacity-0 select-none">
        {{ formattedTime }}
      </p>

      <div class="flex justify-center items-center">
        <button class="p-3 text-xs"
          @click="stepBackward"
        >
          <font-awesome-icon icon="backward-step" />
        </button>
        <button class="p-4 text-lg"
          @click="togglePlay"
        >
          <font-awesome-icon :icon="isPlaying ? 'pause' : 'play'" />
        </button>
        <button class="p-3 text-xs"
          @click="stepForward"
        >
          <font-awesome-icon icon="forward-step" />
        </button>

      </div>

      <p class="font-mono">
        {{ formattedTime }}
      </p>

      <!-- <button 
        @click="togglePlay" 
        class="flex items-center justify-center w-24 py-2 rounded-md font-semibold text-sm transition-all"
        :class="isPlaying ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30' : 'bg-white text-black hover:bg-gray-200'"
      >
        {{ isPlaying ? 'Pause' : 'Play' }}
      </button>

      <div class="font-mono text-gray-300 text-lg tracking-wider bg-black px-3 py-1 rounded border border-gray-800">
        {{ formattedTime }}
      </div> -->
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onUnmounted } from 'vue'
import getSrc from '@/utils/getSrc' // Utility to construct full media URLs

const props = defineProps({
  currentTime: { type: Number, required: true },
  isPlaying: { type: Boolean, required: true },
  timelineElements: { type: Array, required: true }
})

const AUDIO_TYPES = ['voiceover', 'music']


const emit = defineEmits(['update:currentTime', 'update:isPlaying'])

// --- MEDIA REF MANAGEMENT ---
const mediaRefs = ref(new Map())

const setMediaRef = (el, id) => {
  if (el) {
    mediaRefs.value.set(id, el)
  } else {
    // Clean up unmounted DOM elements when clips leave the active playhead area
    mediaRefs.value.delete(id) 
  }
}

// --- ACTIVE ELEMENT DETECTION ---
const activeElements = computed(() => {
  return props.timelineElements.filter(clip => {
    const visibleDuration = clip.duration - clip.cut_start - clip.cut_end
    return props.currentTime >= clip.start_time && props.currentTime < (clip.start_time + visibleDuration)
  })
})

// Visual stacking: Layer 4 is bottom (render first), Layer 1 is top (render last)
const sortedActiveElements = computed(() => {
  return [...activeElements.value].sort((a, b) => b.layer - a.layer)
})

// --- TIMECODE FORMATTER ---
const formattedTime = computed(() => {
  const mins = Math.floor(props.currentTime / 60).toString().padStart(2, '0')
  const secs = Math.floor(props.currentTime % 60).toString().padStart(2, '0')
  const ms = Math.floor((props.currentTime % 1) * 10).toString()
  return `${mins}:${secs}.${ms}`
})

// --- PLAYBACK ENGINE ---
let animationFrameId = null
let lastTimestamp = null

const togglePlay = () => {
  emit('update:isPlaying', !props.isPlaying)
}

const stepBackward = () => {
  const newTime = Math.max(0, props.currentTime - 5)
  emit('update:currentTime', newTime)
}

const stepForward = () => {
  // If you have a max duration variable available, you could clamp this similarly:
  // const newTime = Math.min(maxDuration, props.currentTime + 5)
  const newTime = props.currentTime + 5
  emit('update:currentTime', newTime)
}


const loop = (timestamp) => {
  if (!props.isPlaying) return

  if (!lastTimestamp) lastTimestamp = timestamp
  const delta = (timestamp - lastTimestamp) / 1000 // Convert ms to seconds

  const newTime = props.currentTime + delta
  emit('update:currentTime', newTime)

  syncMediaElements(newTime, true)

  lastTimestamp = timestamp
  animationFrameId = requestAnimationFrame(loop)
}

// Watch for Play/Pause toggles
watch(() => props.isPlaying, (playing) => {
  if (playing) {
    lastTimestamp = null
    animationFrameId = requestAnimationFrame(loop)
    syncMediaElements(props.currentTime, true)
  } else {
    cancelAnimationFrame(animationFrameId)
    syncMediaElements(props.currentTime, false)
  }
})

// Watch for manual scrubbing (when paused but time changes)
watch(() => props.currentTime, (newTime) => {
  if (!props.isPlaying) {
    syncMediaElements(newTime, false)
  }
})

// --- STRICT MEDIA SYNCING ---
const syncMediaElements = (globalTime, isPlaying) => {
  activeElements.value.forEach(clip => {
    const mediaEl = mediaRefs.value.get(clip.id)
    if (!mediaEl) return

    // Calculate exactly where the media's internal clock should be
    const expectedLocalTime = clip.cut_start + (globalTime - clip.start_time)

    // Sync Drift Logic: 
    // If we are playing, only force-update if it drifts by > 0.1s to prevent stuttering.
    // If we are scrubbing (paused), force-update every time.
    if (!isPlaying || Math.abs(mediaEl.currentTime - expectedLocalTime) > 0.1) {
      mediaEl.currentTime = expectedLocalTime
    }

    // Play/Pause state syncing
    if (isPlaying && mediaEl.paused) {
      const playPromise = mediaEl.play()
      if (playPromise !== undefined) {
        playPromise.catch(error => {
          // Catch autoplay/interact policies errors without crashing the loop
          console.warn("Playback blocked or interrupted:", error)
        })
      }
    } else if (!isPlaying && !mediaEl.paused) {
      mediaEl.pause()
    }
  })
}

onUnmounted(() => {
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
})
</script>