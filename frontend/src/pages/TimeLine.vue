<template>

  <div>
    <PreviewPlayer 
      v-model:currentTime="currentTime"
      v-model:isPlaying="isPlaying"
      :timelineElements="timelineElements"
    />

    <div 
      ref="scrollContainer"
      @wheel="handleWheel"
      class="container-background w-full overflow-x-auto overflow-y-hidden relative select-none text-light"
    >
      <div class="relative" :style="{ width: `${timelineDuration * pixelsPerSecond}px`, minWidth: '100%', height: `${maxLayers * trackHeight + rulerHeight}px` }">
        <div 
          class="absolute top-0 bottom-0 w-px bg-primary z-50 pointer-events-none shadow-[0_0_12px_rgba(220,38,38,1)] flex flex-col items-center transition-all duration-75" 
          :style="{ left: `${currentTime * pixelsPerSecond}px` }"
        >
          <div class="w-3 h-4 bg-primary rounded-b-sm -mt-0.5"></div>
        </div>

        <div @mousedown="handleRulerClick" class="absolute top-0 left-0 w-full z-30 cursor-text" :style="{ height: `${rulerHeight}px` }">             
            <div v-for="i in timelineDuration + 1" :key="'tick-'+(i-1)" class="absolute bottom-0 border-l border-[var(--light-gray)]" :style="{ left: `${(i-1) * pixelsPerSecond}px`, height: (i-1) % 5 === 0 ? '12px' : '6px' }">
              <span v-if="(i-1) % 5 === 0 && i > 0" class="absolute bottom-full mb-1 -translate-x-1/2 text-[10px] text-[var(--light)] font-medium">
                {{ i - 1 }}s
              </span>
            </div>
        </div>

        <div v-for="layer in maxLayers" :key="'bg-'+layer" class="absolute w-full border-t border-[var(--light-gray)] box-border pointer-events-none" :style="{ top: `${rulerHeight + (layer - 1) * trackHeight}px`, height: `${trackHeight}px` }">
          <span class="absolute left-2 top-2 text-gray-600 text-[10px] font-bold uppercase z-0 tracking-wider">Layer {{ layer }}</span>
        </div>

        <div v-if="snapLine !== null" class="absolute bottom-0 w-px bg-primary z-50 pointer-events-none shadow-[0_0_12px_rgba(220,38,38,1)]" :style="{ top: `${rulerHeight}px`, left: `${snapLine * pixelsPerSecond}px` }"></div>

        <div
          v-for="segment in timelineElements"
          :key="segment.id"
          @mousedown.stop="startDrag($event, segment, 'move')"
          :style="getSegmentStyle(segment)"
          :class="[
            'absolute rounded-md shadow-md flex items-center overflow-hidden border border-black/50 transition-shadow text-sm font-medium z-10 box-border',
            segment.type === 'audio' ? 'bg-gray-700 text-blue-50' : 'bg-gray-400 text-emerald-50',
            dragState.activeId === segment.id && dragState.action === 'move' ? 'opacity-80 ring-2 ring-[var(--primary)] scale-[1.02] cursor-grabbing z-50' : 'cursor-grab hover:brightness-110'
          ]"
        >
          <div class="relative w-full h-full overflow-hidden">
            <div @mousedown.stop="startDrag($event, segment, 'trimLeft')" class="absolute left-0 h-full flex items-center bottom-0 w-2 text-[var(--primary)] hover:text-[var(--primary-dark)] cursor-ew-resize z-20 border-l-[3px] border-[var(--primary)] hover:border-[var(--primary-dark)]">
              <font-awesome-icon icon="caret-right" class="-ml-1 text-2xl"/>
            </div>

            <!-- TIME ELEMENT BACKGROUND -->
            <div class="absolute h-full -z-10"
              :style="getSegmentBackgroundStyle(segment)"
            >
                <video-element
                  v-if="segment.type === 'scene'"
                  :scene="segment"
                  :numberOfFramesToDisplay="Math.ceil((segment.duration + segment.cut_start + segment.cut_end) * pixelsPerSecond / 50)"
                />
                <audio-element
                  v-else-if="segment.type === 'audio'"
                  :voiceover="segment"
                />  
            </div>

            <span class="truncate pointer-events-none select-none text-xs ">
              {{ getVisibleDuration(segment).toFixed(1) }}s
              {{ segment.cut_end }}
              {{ segment.cut_start }}
            </span>
  
            <div @mousedown.stop="startDrag($event, segment, 'trimRight')" class="absolute right-0 h-full flex items-center bottom-0 w-2 text-[var(--primary)] hover:text-[var(--primary-dark)] cursor-ew-resize z-20 border-r-[3px] border-[var(--primary)] hover:border-[var(--primary-dark)]">
              <font-awesome-icon icon="caret-left" class="-ml-[2px] text-2xl"/>
            </div>
            
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted, onMounted } from 'vue'
import AudioElement from '@/components/project_details/AudioElement.vue'
import VideoElement from '@/components/project_details/VideoElement.vue'
import PreviewPlayer from '@/components/Preview.vue' // Adjust path as needed
const currentTime = ref(0)
const isPlaying = ref(false)

const projectId = "e62759f7-0e81-4094-8f22-03b3dab77261"

const handleRulerClick = (e) => {
  const rect = e.currentTarget.getBoundingClientRect()
  const clickX = e.clientX - rect.left
  
  // Calculate the time based on the click position and current zoom level
  const newTime = Math.max(0, clickX / pixelsPerSecond.value)
  currentTime.value = newTime
}

// --- REFS FOR DOM ELEMENTS ---
const scrollContainer = ref(null) // Allows us to manipulate the scrollbar mathematically

// --- CONSTANTS & REACTIVE STATE ---
const pixelsPerSecond = ref(40) 
const trackHeight = 70 
const maxLayers = 4    
const rulerHeight = 32 
const snapThreshold = 0.1

const timelineElements = ref([])

// --- WHEEL/SCROLL ENGINE ---
const handleWheel = (e) => {
  // If holding Ctrl (Windows) or Cmd (Mac)
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault() // Prevents the whole browser tab from zooming
    
    // Smooth out the scroll delta (trackpads spin much faster than mouse wheels)
    const zoomDelta = e.deltaY * -0.1 
    
    // Apply zoom within bounds (10px to 150px per second)
    const newZoom = pixelsPerSecond.value + zoomDelta
    pixelsPerSecond.value = Math.max(10, Math.min(150, newZoom))
    
  } else {
    // If NOT holding Ctrl, map standard vertical scroll to horizontal panning
    // This is a massive NLE quality-of-life feature
    e.preventDefault()
    if (scrollContainer.value) {
      scrollContainer.value.scrollLeft += e.deltaY
    }
  }
}


const getLayerBoundaries = (segmentId, targetLayer, proposedStart, duration) => {
  let minTime = 0
  let maxTime = Infinity
  const proposedMid = proposedStart + (duration / 2)

  timelineElements.value.forEach(seg => {
    if (seg.layer === targetLayer && seg.id !== segmentId) {
      const segMid = seg.start_time + (getVisibleDuration(seg) / 2)

      // If the segment's center is to the left of our proposed center
      if (segMid <= proposedMid) {
        minTime = Math.max(minTime, getEndTime(seg))
      } 
      // If the segment's center is to the right
      else {
        maxTime = Math.min(maxTime, seg.start_time)
      }
    }
  })
  
  return { minTime, maxTime }
}


// Dynamically calculate the total seconds the timeline should display
const timelineDuration = computed(() => {
  let max = 30 
  timelineElements.value.forEach(seg => {
    const end = seg.start_time + (seg.duration - seg.cut_start - seg.cut_end)
    if (end > max) max = end
  })
  return Math.ceil(max + 10) 
})

// Engine State
const snapLine = ref(null)
const dragState = ref({ activeId: null, action: null, startX: 0, startY: 0, initialClip: null })

// --- HELPERS ---
const getVisibleDuration = (seg) => seg.duration - seg.cut_start - seg.cut_end
const getEndTime = (seg) => seg.start_time + getVisibleDuration(seg)


const getSegmentBackgroundStyle = (segment) => {
  return {
    left: `${-segment.cut_start * pixelsPerSecond.value}px`,
    width: `${(getVisibleDuration(segment) + segment.cut_start + segment.cut_end) * pixelsPerSecond.value}px`,
    top: `0 px`,
  }
}

const getSegmentStyle = (segment) => {
  return {
    left: `${segment.start_time * pixelsPerSecond.value}px`,
    width: `${getVisibleDuration(segment) * pixelsPerSecond.value}px`,
    top: `${rulerHeight + (segment.layer - 1) * trackHeight + 8}px`,
    height: `${trackHeight - 16}px`
  }
}

const getSnapPoints = (excludeId) => {
  const points = new Set([0])
  timelineElements.value.forEach(seg => {
    if (seg.id !== excludeId) {
      points.add(seg.start_time)
      points.add(getEndTime(seg))
    }
  })
  return Array.from(points)
}

// --- CORE INTERACTIVITY ---
const startDrag = (e, segment, action) => {
  dragState.value = {
    activeId: segment.id,
    action: action,
    startX: e.clientX,
    startY: e.clientY,
    initialClip: { ...segment } 
  }
  window.addEventListener('mousemove', onDrag)
  window.addEventListener('mouseup', stopDrag)
}

const onDrag = (e) => {
  if (!dragState.value.activeId) return
  const segment = timelineElements.value.find(s => s.id === dragState.value.activeId)
  const initial = dragState.value.initialClip
  
  const deltaX = (e.clientX - dragState.value.startX) / pixelsPerSecond.value
  const snapPoints = getSnapPoints(segment.id)
  snapLine.value = null

  if (dragState.value.action === 'move') {
    const deltaY = e.clientY - dragState.value.startY
    let proposedLayer = Math.max(1, Math.min(maxLayers, initial.layer + Math.round(deltaY / trackHeight)))
    
    let proposedStart = initial.start_time + deltaX
    const duration = getVisibleDuration(initial)

    // 1. Get bounds for the PROPOSED layer based on current mouse position
    let bounds = getLayerBoundaries(segment.id, proposedLayer, proposedStart, duration)

    // 2. CRITICAL: Check if the segment actually fits in the new layer's gap!
    // If the space between clips is smaller than our clip, block the layer change.
    if (bounds.maxTime - bounds.minTime < duration) {
      proposedLayer = initial.layer // Fallback to the original layer
      bounds = getLayerBoundaries(segment.id, proposedLayer, proposedStart, duration) // Recalculate safe bounds
    }

    segment.layer = proposedLayer

    // 3. Apply snapping
    let newStart = proposedStart
    let newEnd = newStart + duration
    for (let point of snapPoints) {
      if (Math.abs(newStart - point) < snapThreshold) { newStart = point; snapLine.value = point; break; }
      if (Math.abs(newEnd - point) < snapThreshold) { newStart = point - duration; snapLine.value = point; break; }
    }

    // 4. Clamp within the valid bounds so it slides against other clips
    if (newStart < bounds.minTime) newStart = bounds.minTime
    if (newStart + duration > bounds.maxTime) newStart = bounds.maxTime - duration
    
    segment.start_time = Math.max(0, newStart)

  } else if (dragState.value.action === 'trimLeft') {
    let proposedTimeChange = deltaX
    const maxCutStart = initial.duration - initial.cut_end - 0.5 
    
    // Pass the required parameters to the updated getLayerBoundaries
    const duration = getVisibleDuration(initial)
    const bounds = getLayerBoundaries(segment.id, segment.layer, initial.start_time, duration)
    
    for (let point of snapPoints) {
      if (Math.abs((initial.start_time + proposedTimeChange) - point) < snapThreshold) {
        proposedTimeChange = point - initial.start_time
        snapLine.value = point
        break
      }
    }

    let newCutStart = initial.cut_start + proposedTimeChange
    if (newCutStart < 0) newCutStart = 0
    if (newCutStart > maxCutStart) newCutStart = maxCutStart
    if (initial.start_time + (newCutStart - initial.cut_start) < bounds.minTime) {
      newCutStart = initial.cut_start + (bounds.minTime - initial.start_time)
    }

    segment.cut_start = newCutStart
    segment.start_time = initial.start_time + (newCutStart - initial.cut_start)

  } else if (dragState.value.action === 'trimRight') {
    let proposedTimeChange = deltaX
    const maxCutEnd = initial.duration - initial.cut_start - 0.5 
    
    // Pass the required parameters to the updated getLayerBoundaries
    const duration = getVisibleDuration(initial)
    const bounds = getLayerBoundaries(segment.id, segment.layer, initial.start_time, duration)

    for (let point of snapPoints) {
      if (Math.abs((getEndTime(initial) + proposedTimeChange) - point) < snapThreshold) {
        proposedTimeChange = point - getEndTime(initial)
        snapLine.value = point
        break
      }
    }

    let newCutEnd = initial.cut_end - proposedTimeChange
    if (newCutEnd < 0) newCutEnd = 0
    if (newCutEnd > maxCutEnd) newCutEnd = maxCutEnd
    if (getEndTime(initial) + (initial.cut_end - newCutEnd) > bounds.maxTime) {
       newCutEnd = initial.cut_end - (bounds.maxTime - getEndTime(initial))
    }
    segment.cut_end = newCutEnd
  }
}


const voiceovers = ref([])
const scenes = ref([])
const backgroundMusic = ref(null)

onMounted(async () => {
  const response = await fetch(`http://localhost:8000/projects/${projectId}`);
  const project = await response.json();
  
  voiceovers.value = project.voiceovers
  console.log('voiceovers');
  console.log(project.voiceovers);

  scenes.value = project.scenes
  console.log('scenes');
  console.log(project.scenes);

  backgroundMusic.value = project.background_music
  console.log('background music');
  console.log(project.background_music);

  timelineElements.value = parseProjectData(scenes.value, voiceovers.value)
  
});


const parseProjectData = () => {
  const parsedElements = []

  // 1. Parse Scenes (Main Visual Track -> Layer 1)
  scenes.value.forEach(scene => {
    scene.cut_start = scene.cut_start || 0;
    scene.cut_end = scene.cut_end || 0;
    scene.layer = scene.layer || 2;
    scene.type = "scene";
    parsedElements.push(scene);
  })

  // 2. Parse Voiceovers (Audio Track -> Layer 2)
  let currentAudioTime = 0 // Fallback tracker if start_time is missing

  voiceovers.value.forEach((vo, index) => {
    // If your real data eventually includes start_time/duration, use it. 
    // Otherwise, fallback to chaining them sequentially.
    vo.cut_start = vo.cut_start || 0;
    vo.cut_end = vo.cut_end || 0;
    vo.layer = vo.layer || 3;
    vo.type = "audio";
    parsedElements.push(vo)

    // Advance the fallback timer for the next audio clip
  })

  backgroundMusic.value.forEach((music, index) => {
    music.cut_start = music.cut_start || 0;
    music.cut_end = music.cut_end || 0;
    music.layer = music.layer || 4;
    music.type = "audio";

    parsedElements.push(music)
  })

  return parsedElements
}

// --- INITIALIZE TIMELINE STATE ---
// We replace the hardcoded array with our new parser



const stopDrag = () => {
  dragState.value.activeId = null
  dragState.value.action = null
  snapLine.value = null 
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
}

onUnmounted(() => {
  window.removeEventListener('mousemove', onDrag)
  window.removeEventListener('mouseup', stopDrag)
})
</script>