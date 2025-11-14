<template>
  <div class="container mx-auto p-4">
    <!-- Preview Section -->
    <div class="preview bg-gray-800 rounded-lg p-4 mb-4 h-[580px]">
      <div
        class="flex gap-2 items-center h-full"
      >
        <!-- TODO -->
        <!-- TODO -->
        <!-- TODO -->
        <!-- PREVIEW -->
        <div class="relative min-w-[270px] rounded-lg overflow-hidden">
          <div class="h-[480px] relative">
            <video
              v-for="index in 3"
              :key="index"
              :ref="el => setVideoRef(el, index - 1)"
              class="absolute inset-0 w-full object-cover top-0 left-0"
              width="270"
              height="480"
              muted
              playsinline
              preload="auto"
              @canplaythrough="onCanPlayThrough(index - 1)"
            ></video>
          </div>

          <video-subtitles 
            v-if="activeVoiceover && activeVoiceover?.text_with_pauses && voiceoverTimestamps"
            class="absolute top-20 w-[60%] left-1/2 -translate-x-1/2 z-20"
            :timestamps="voiceoverTimestamps"
            :time="currentTime - activeVoiceover?.start_time"
            :pauses="activeVoiceover?.text_with_pauses"
          />

          <!-- Hidden audio for voiceovers -->
          <audio
            v-for="index in 2"
            :key="'audio' + index"
            :ref="el => audioEls[index - 1] = el"
            preload="auto"
            @canplaythrough="onAudioReady(index - 1)"
            @ended="onAudioEnded(index - 1)"
            style="display: none;"
          ></audio>

          <div class="flex flex-col gap-2 text-white mt-2">
            <form-button @clicked="togglePlay" :label="isPlaying ? 'Pause' : 'Play'" />
            <form-button @clicked="reset" label="Reset" />
            <span class="text-center">Time: {{ currentTime.toFixed(2) }}s</span>
          </div>
        </div>

        <!-- Divider -->
        <div class="h-full w-1 bg-white"></div>

        <div 
          class="text-gray-300 w-fit mx-auto flex gap-6 items-center" 
          v-if="typeof(selectedSceneIndex) == 'number'"
        >
          <div>
            <div class="flex gap-6">
              <div>
                <div class="size-[200px] min-w-[200px] bg-gray-400 rounded-lg mx-auto relative">
                  <p class="absolute top-4 left-1/2 -translate-x-1/2 text-white fonr-bold z-10">Image</p>
                 
                  <img
                    v-if="scenes[selectedSceneIndex].image_src"
                    :src="getSrc(scenes[selectedSceneIndex].image_src)"
                    alt="Scene Image"
                    class="w-full h-full object-cover"
                  />
                  
                </div>
                <div class="flex flex-col gap-1">
                  <form-button v-if="scenes[selectedSceneIndex].image_src" label="Generate Image" @clicked="generateImage"/>
                  <form-button v-else label="Regenerate Image" @clicked="generateImage"/>
                  <div class="flex justify-center">
                    <p>Lowkey</p>
                    <input type="checkbox" class="border" v-model="generateImageLowkey">
                  </div>
                  <input type="file" class="w-[200px] text-white bg-gray-800 border p-1 rounded-sm text-xs" @input="handleSceneImageUpload">
                </div>
              </div>
              <div>
                <div class="size-[200px] min-w-[200px] bg-gray-400 rounded-lg mx-auto relative">
                  <p class="absolute top-4 left-1/2 -translate-x-1/2 text-white fonr-bold z-10">Video</p>
                  <video 
                    v-if="scenes[selectedSceneIndex].video_src" 
                    :src="`http://localhost:8000/${scenes[selectedSceneIndex].video_src}?v=1}`"
                    alt="Scene Video"
                    class="w-full h-full object-cover rounded-md border" 
                    controls 
                  />
                </div>
                <div class="flex flex-col gap-1">
                  <form-button v-if="scenes[selectedSceneIndex].video_src" label="Regenerate Video" @click="generateVideo"/>
                  <form-button v-else label="Generate Video" @click="generateVideo"/>
                </div>
              </div>
            </div>
            <div class="flex gap-6 mt-8">
              <div class="flex-1">
                <p>
                  Image references:
                </p>
                <div class="overflow-y-auto flex gap-1">
                  <reference-image
                    v-for="referenceImg in addedReferenceImages"
                    :key="referenceImg.src"
                    :name="referenceImg.name"
                    :src="referenceImg.src"
                    @remove="removeReferenceImage"
                    :added="true"
                  />
                </div>
              </div>
              <div class="flex-1">
                <p>
                  Image references:
                </p>
                <div class="overflow-y-auto flex gap-1" v-if="availableReferenceImages.length > 0">
                  <reference-image
                    v-for="refImg in availableReferenceImages"
                    :key="refImg.name"
                    :name="refImg.name"
                    :src="refImg.src"
                    @add="addReferenceImage"
                    :added="false"
                  />
                </div>
              </div>
            </div>
          </div>
          <div class="flex flex-col gap-5">
            <div class="flex gap-4 justify-center">
              <form-input label="Start Time">
                <input type="text" class="w-[200px] text-white bg-gray-800 border p-1 rounded-sm" v-model="scenes[selectedSceneIndex].start_time">
              </form-input>
              <form-input label="Duration">
                <input type="text" class="w-[200px] text-white bg-gray-800 border p-1 rounded-sm" v-model="scenes[selectedSceneIndex].duration">
              </form-input>
            </div>
            <div class="flex gap-2 items-center">
              <form-input label="Image Style" class="w-full">
                <select v-model="imageGenerationStyle" class="text-white bg-gray-800 border-white rounded-sm w-full border">
                  <option value="" default>Auto style</option>
                  <option value="lifelaps">LifeLaps style</option>
                  <option value="lifelaps_science">LifeLaps style (with_science_shit)</option>
                  <option value="criminal">Criminal style</option>
                </select>
              </form-input>
              <div v-if="imageGenerationStylePower" class="w-full">
                <label for="stylePower" class="text-sm text-gray-300">
                  Style Intensity: <span class="font-semibold text-white">{{ imageGenerationStylePower }}</span>/10
                </label>
                <input
                  id="stylePower"
                  v-model="imageGenerationStylePower"
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  class="w-full accent-indigo-500 cursor-pointer"
                />
              </div>
            </div>

            <form-input label="Image Prompt" class="w-[416px]">
              <textarea class="w-[416px] text-white bg-gray-800 border p-1 rounded-sm h-32" v-model="scenes[selectedSceneIndex].image_prompt"></textarea>
              <form-button label="Fix Prompt" @clicked="fixImagePrompt"/>
            </form-input>
            <form-input label="Video Prompt" class="w-[416px]">
              <textarea class="w-[416px] text-white bg-gray-800 border p-1 rounded-sm h-32" v-model="scenes[selectedSceneIndex].video_prompt"></textarea>
              <form-button label="Fix Prompt" @clicked="fixVideoPrompt"/>
            </form-input>

            <form-button label="Delete scene" @clicked="deleteScene"/>
          </div>

        </div>

        <div
          v-else-if="typeof(selectedVoiceoverIndex) == 'number'"
          class="flex flex-col gap-6 items-center text-white w-fit mx-auto"
        >
          <div class="flex gap-4 justify-center">
            <form-input label="Start Time" class="w-[200px]">
              <input type="text" class="w-[200px] text-white bg-gray-800 border p-1 rounded-sm" v-model="voiceovers[selectedVoiceoverIndex].start_time">
            </form-input>
            <form-input label="Duration" class="w-[200px]">
              <input type="text" class="text-white w-[200px] bg-gray-800 border p-1 rounded-sm" v-model="voiceovers[selectedVoiceoverIndex].duration">
            </form-input>
          </div>
          <form-input label="Text">
            <textarea class="w-[416px] text-white bg-gray-800 border p-1 rounded-sm h-32" v-model="voiceovers[selectedVoiceoverIndex].text"></textarea>
          </form-input>
          <form-input label="Text With Breakes">
            <textarea class="w-[416px] text-white bg-gray-800 border p-1 rounded-sm h-32" v-model="voiceovers[selectedVoiceoverIndex].text_with_pauses"></textarea>
          </form-input>

          <div v-if="voiceovers[selectedVoiceoverIndex].src" class="w-[416px]">
            <form-button  label="Regenrate Voiceover" @clicked="generateVoiceover"/>
            <audio :src="`http://localhost:8000/${voiceovers[selectedVoiceoverIndex].src}?v=${voiceoversVersion[voiceovers[selectedVoiceoverIndex].id]}`" controls class="w-full mt-2"></audio>
          </div>
          <form-button v-else label="Generate Voiceover" @clicked="generateVoiceover"/>
          <form-button label="Delete voiceover" @clicked="deleteVoiceover"/>
        </div>

      </div>

      
    </div>

    <!-- Timeline Section -->
    <div class="timeline bg-gray-900 rounded-lg p-4" ref="containerRef"> 
      <div class="overflow-x-auto relative">
        <div class="relative" :style="{ width: `${totalWidth}px`, minWidth: '100%' }">
          <!-- Timeline Background with Time Markers -->
          <div class="relative w-full h-5 bg-gray-800 rounded">
            <!-- Time Markers -->
            <div class="flex text-xs text-gray-400">
              <span v-for="tick in timeTicks" :key="tick" class="absolute " :style="{ left: `${tick * pixelsPerSecond}px` }">
                {{ formatTime(tick) }}
              </span>
            </div>
          </div>

          <div class="h-3 w-full relative z-20 bg-gray-800">
            <div class="w-full h-full" @click="handleTimeChange($event)"></div>
            <div class="absolute h-[400px] z-40 top-0"
              :style="{ left: `${currentTime * pixelsPerSecond}px` }"
            >
              <div class="w-10 h-3 bg-red-500 -ml-5"></div>
              <div class="h-full bg-red-500 w-1">
              </div>
            </div>
          </div>




          <!-- Scenes Track -->
          <div class="relative h-40 mt-1 z-0" ref="scenesTrack">
            <div
              v-for="(scene, index) in scenes"
              :key="scene.id"
              class="absolute h-full bg-blue-500 rounded cursor-pointer select-none border flex flex-col justify-between"
              :style="{
                left: `${scene.start_time * pixelsPerSecond}px`,
                width: `${scene.duration * pixelsPerSecond}px`,
                zIndex: Math.round(scene.start_time * 100)
              }"
              @click="selectScene(scene.id)"
            >
              <span class="text-xs text-white p-2">{{ scene.image_prompt }}</span>
              <div class="w-full text-center bg-gray-800 z-20 text-white text-xs font-bold cursor-move"
                @mousedown="startDragging($event, 'scene', scene, index, $refs.scenesTrack)"
              >
                move
              </div>
            </div>
          </div>

          <!-- Voiceovers Track -->
          <div class="relative h-28" ref="voiceoversTrack">
            <div
              v-for="(voiceover, index) in voiceovers"
              :key="voiceover.id"
              class="absolute h-20 mt-1 bg-green-500 rounded cursor-pointer select-none flex flex-col justify-between border border-white"
              :style="{
                left: `${voiceover.start_time * pixelsPerSecond}px`,
                width: `${voiceover.duration * pixelsPerSecond}px`,
              }"
              @click="selectVoiceover(voiceover.id)"
            >
              <span class="text-xs text-white truncate p-2" :style="`max-width: ${voiceover.duration * pixelsPerSecond}px`">{{ voiceover.text }} </span>
              <div class="w-full text-center bg-gray-800 z-20 text-white text-xs font-bold cursor-move"
                @mousedown="startDragging($event, 'voiceover', voiceover, index, $refs.voiceoversTrack)"
              >
                move
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <form-button label="Save project" @clicked="saveProjectChanges"/>
    
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue';
import axios from 'axios'
import FormInput from './FormInput.vue'
import FormButton from './FormButton.vue'
import VideoSubtitles from './VideoSubtitles.vue'
import ReferenceImage from './ReferenceImage.vue'
import getSrc from '../utils/getSrc.js'


const route = 'http://localhost:8000/'
let projectId = null;

const scenes = ref([]);
const voiceovers = ref([]);
const characters = ref([]);

const timelineDuration = 100; // Total duration of the timeline in seconds (adjust as needed)
const pixelsPerSecond = ref(50); // 100px per second
const totalWidth = computed(()=>{
  return timelineDuration * pixelsPerSecond.value;
});

const selectedSceneIndex = ref(null);
const selectedVoiceoverIndex = ref(null);
const generateImageLowkey = ref(true);
const voiceoverTimestamps = ref([])

const getSelectedSceneId = () => {
  return scenes.value[selectedSceneIndex.value].id
}

const getSelectedVoiceoverId = () => {
  return voiceovers.value[selectedVoiceoverIndex.value].id
}

// SET TIME
const handleTimeChange = (event) => {
  if (!containerRef.value) return;

  const containerRect = containerRef.value.getBoundingClientRect();
  const scrollLeft = containerRef.value.querySelector('.overflow-x-auto').scrollLeft;

  // Calculate how far from the start of the timeline the user clicked (in pixels)
  const clickX = event.clientX - containerRect.left + scrollLeft - 12;

  // Convert pixels to seconds
  const clickedTime = clickX / pixelsPerSecond.value;

  // Clamp to timeline duration
  const clampedTime = Math.max(0, Math.min(clickedTime, timelineDuration));
  currentTime.value = clampedTime;
  seekTo(clampedTime)
};


// DELETE SCENE
const deleteScene = () => {
  const sceneId = getSelectedSceneId();
  axios.delete(`${route}scenes/${sceneId}`)
  if(selectedSceneIndex.value == scenes.value.length - 1){
    selectedSceneIndex.value--
  }
  scenes.value = scenes.value.filter(el => el.id != sceneId)
}

const deleteVoiceover = () => {
  const voId = getSelectedVoiceoverId();
  axios.delete(`${route}voiceovers/${voId}`)
  if(selectedVoiceoverIndex.value == voiceovers.value.length - 1){
    selectedVoiceoverIndex.value--
  }
  voiceovers.value = voiceovers.value.filter(el => el.id != voId)
}



// VERSIONS - TO UPDATE MEDIA
const voiceoversVersion = ref({})
const videosVersion = ref({})
const imagesVersion = ref({})

const initializeVersions = (ref, values) => {
  let result = {}
  values.forEach(el => result[el.id] = 0)
  ref.value = result
  console.log(voiceoversVersion.value)
}


// PREVIEW LOGIC
const videoEls = ref([]) // [video0, video1, video2]
const isPlaying = ref(false)
const currentTime = ref(0)
const rafId = ref(null)

const audioEls = ref([])  // [audio0, audio1]
const activeAudioLayer = ref(0)
const audioReady = ref([false, false])
const audioSources = ref(['', ''])  // track current src per layer

// Track which layer is visible
const activeLayer = ref(0)
// Preloading state per layer
const layerReady = ref([false, false, false])
const layerSources = ref(['', '', '']) // current src per layer

// Set refs for multiple videos
const setVideoRef = (el, index) => {
  if (el) videoEls.value[index] = el
}

const onAudioReady = (index) => {
  audioReady.value[index] = true
}

const onAudioEnded = (index) => {
  // Auto-switch back to layer 0 when this one finishes (optional)
  if (activeAudioLayer.value === index) {
    activeAudioLayer.value = 0
  }
}



// Performance
let playbackStartTime = 0
let playbackStartTimestamp = 0

// Throttling

// ================ SCENE LOGIC ================
const activeScene = computed(() => {
  const time = currentTime.value
  for (let i = scenes.value.length - 1; i >= 0; i--) {
    const s = scenes.value[i]
    if (time >= s.start_time && time < s.start_time + s.duration) {
      return s
    }
  }
  return null
})

const activeVoiceover = computed(() => {
  const time = currentTime.value
  for (const vo of voiceovers.value) {
    if (time >= vo.start_time && time < vo.start_time + vo.duration) {
      return vo
    }
  }
  return null
})

const nextScene = computed(() => {
  const current = activeScene.value
  if (!current) return null
  const index = scenes.value.findIndex(s => s === current)
  return scenes.value[index + 1] || null
})

const nextVoiceover = computed(() => {
  const current = activeVoiceover.value
  if (!current) return null
  const index = voiceovers.value.findIndex(vo => vo === current)
  return voiceovers.value[index + 1] || null
})

const nextNextScene = computed(() => {
  const next = nextScene.value
  if (!next) return null
  const index = scenes.value.findIndex(s => s === next)
  return scenes.value[index + 1] || null
})

// ================ LAYER MANAGEMENT ================
const getNextLayer = () => {
  return (activeLayer.value + 1) % 3
}

const getNextNextLayer = () => {
  return (activeLayer.value + 2) % 3
}

const showLayer = (layerIndex) => {
  videoEls.value.forEach((video, i) => {
    video.style.zIndex = i === layerIndex ? 10 : 1
    video.style.opacity = i === layerIndex ? 1 : 0
  })
  activeLayer.value = layerIndex
}

const preloadVideo = async (videoEl, src, startOffset = 0) => {
  if (!src) return

  const fullSrc = (route + src).replaceAll("\\", "/")
  if (videoEl.src === fullSrc) {
    videoEl.currentTime = startOffset
    return
  }

  videoEl.pause()
  videoEl.src = fullSrc
  videoEl.currentTime = startOffset
  videoEl.load()
  // We don't await here — we just trigger preload
}

// Called when video is ready to play smoothly
const onCanPlayThrough = (layerIndex) => {
  layerReady.value[layerIndex] = true
}

const updateAudioLayers = async (time) => {
  const vo = activeVoiceover.value
  const nextVo = nextVoiceover.value

  const currentLayer = activeAudioLayer.value
  const nextLayer = 1 - currentLayer  // toggle between 0 and 1

  // 1. Current voiceover
  if (vo) {
    const localTime = time - vo.start_time
    const fullSrc = (route + vo.src).replaceAll("\\", "/")

    if (audioSources.value[currentLayer] !== fullSrc) {
      // Load into current layer
      const audio = audioEls.value[currentLayer]

      voiceoverTimestamps.value = JSON.parse(vo.timestamps)

      audio.pause()
      audio.src = fullSrc
      audio.currentTime = localTime
      audio.load()
      audioSources.value[currentLayer] = fullSrc
      audioReady.value[currentLayer] = false
    } else {
      // Same source → just sync time
      const audio = audioEls.value[currentLayer]
      if (Math.abs(audio.currentTime - localTime) > 0.1) {
        audio.currentTime = localTime
      }
    }

    // Auto-switch to this layer when ready
    if (audioReady.value[currentLayer] && activeAudioLayer.value !== currentLayer) {
      activeAudioLayer.value = currentLayer
    }

    // Play if playing
    if (isPlaying.value && audioEls.value[currentLayer].paused && audioReady.value[currentLayer]) {
      audioEls.value[currentLayer].play().catch(() => {})
    }
  }

  // 2. Preload NEXT voiceover (if exists and not too far)
  if (nextVo && nextVo.start_time - time < 2.0) {  // preload 2s early
    const fullSrc = (route + nextVo.src).replaceAll("\\", "/")
    if (audioSources.value[nextLayer] !== fullSrc) {

      const audio = audioEls.value[nextLayer]
      audio.pause()
      audio.src = fullSrc
      audio.currentTime = 0
      audio.load()
      audioSources.value[nextLayer] = fullSrc
      audioReady.value[nextLayer] = false
    }
  }

  // 3. Auto-switch on boundary
  if (vo && time >= vo.start_time - 0.05) {
    if (audioReady.value[currentLayer]) {
      activeAudioLayer.value = currentLayer
    }
  }

  // 4. Stop inactive layer
  const inactiveLayer = 1 - activeAudioLayer.value
  if (audioEls.value[inactiveLayer].src && inactiveLayer !== currentLayer) {
    audioEls.value[inactiveLayer].pause()
  }
}

// ================ UPDATE LAYERS ================
const updateVideoLayers = async (time) => {
  const scene = activeScene.value
  const next = nextScene.value
  const nextNext = nextNextScene.value

  if (!scene) {
    videoEls.value.forEach(v => v.pause())
    return
  }

  const currentLayer = activeLayer.value
  const nextLayer = getNextLayer()
  const nextNextLayer = getNextNextLayer()

  const localTime = time - scene.start_time

  // 1. Current scene → active layer
  if (layerSources.value[currentLayer] !== scene.video_src) {
    await preloadVideo(videoEls.value[currentLayer], scene.video_src, localTime)
    layerSources.value[currentLayer] = scene.video_src
    showLayer(currentLayer)
  } else if (Math.abs(videoEls.value[currentLayer].currentTime - localTime) > 0.1) {
    videoEls.value[currentLayer].currentTime = localTime
  }

  // 2. Preload next scene
  if (next && layerSources.value[nextLayer] !== next.video_src) {
    layerReady.value[nextLayer] = false
    layerSources.value[nextLayer] = next.video_src
    preloadVideo(videoEls.value[nextLayer], next.video_src, 0)
  }

  // 3. Preload next-next (optional but smooth)
  if (nextNext && layerSources.value[nextNextLayer] !== nextNext.video_src) {
    layerSources.value[nextNextLayer] = nextNext.video_src
    preloadVideo(videoEls.value[nextNextLayer], nextNext.video_src, 0)
  }

  // Auto-switch when next scene starts
  if (next && time >= next.start_time - 0.05) {
    const switchLayer = layerReady.value[nextLayer] ? nextLayer : currentLayer
    showLayer(switchLayer)
    if (switchLayer === nextLayer) {
      activeLayer.value = nextLayer
      // Reset ready flags if needed
    }
  }
}

// ================ PLAYBACK LOOP ================
const tick = () => {
  if (!isPlaying.value) return

  const now = performance.now()
  const elapsed = (now - playbackStartTimestamp) / 1000
  currentTime.value = playbackStartTime + elapsed

  // Update both systems
  updateVideoLayers(currentTime.value)
  updateAudioLayers(currentTime.value)

  // Sync active video (same as before)
  if (activeScene.value && videoEls.value[activeLayer.value]) {
    const video = videoEls.value[activeLayer.value]
    const expected = currentTime.value - activeScene.value.start_time
    if (Math.abs(video.currentTime - expected) > 0.1) {
      video.currentTime = expected
    }
    if (video.paused && layerReady.value[activeLayer.value]) {
      video.play().catch(() => {})
    }
  }

  rafId.value = requestAnimationFrame(tick)
}

// ================ CONTROLS ================
const play = async () => {
  if (isPlaying.value) return

  playbackStartTime = currentTime.value
  playbackStartTimestamp = performance.now()
  isPlaying.value = true

  await updateVideoLayers(currentTime.value)
  updateAudioLayers(currentTime.value)  // preloads current VO

  // Play active ones
  if (videoEls.value[activeLayer.value]?.src) {
    videoEls.value[activeLayer.value].play().catch(() => {})
  }
  if (audioEls.value[activeAudioLayer.value]?.src) {
    audioEls.value[activeAudioLayer.value].play().catch(() => {})
  }

  rafId.value = requestAnimationFrame(tick)
}

const pause = () => {
  isPlaying.value = false
  videoEls.value.forEach(v => v.pause())
  audioEls.value.forEach(a => a.pause())
  cancelAnimationFrame(rafId.value)
}

const seekTo = async (time) => {
  currentTime.value = Math.max(0, time)
  pause()
  
  // Reset everything
  layerReady.value = [false, false, false]
  layerSources.value = ['', '', '']
  audioReady.value = [false, false]
  audioSources.value = ['', '']

  await updateVideoLayers(currentTime.value)
  updateAudioLayers(currentTime.value)

  playbackStartTime = currentTime.value
  playbackStartTimestamp = performance.now()
}

const togglePlay = () => {
  isPlaying.value ? pause() : play()
}

const reset = () => seekTo(0)

// ================ LIFECYCLE ================
onMounted(() => {
  // Initial load after mount
  setTimeout(() => {
    updateVideoLayers(0)
  }, 500)
})

onBeforeUnmount(() => {
  pause()
  cancelAnimationFrame(rafId.value)
})

// SAVE
const saveProjectChanges = async () => {
  // images are saved automatically
  axios.put(`${route}projects/${projectId}`, {
    scenes: scenes.value,
    voiceovers: voiceovers.value,
  })
  .then(e => {
    console.log(e);
  })
}


// GENERATING VIDEO
const fixVideoPrompt = async () => {
  try {
    const response = await axios
      .post('http://localhost:8000/generators/fix-scene-video-prompt', { 
        image_prompt: scenes.value[selectedSceneIndex.value].image_prompt,
        video_prompt: scenes.value[selectedSceneIndex.value].video_prompt
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; // Re-throw the error after logging it
      })
    ;
    scenes.value[selectedSceneIndex.value].video_prompt = response.data.fixed_prompt;
  } catch (error) {
    console.error('Error fixing scene image prompt:', error);
  }
}

const generateVideo = async () => {
  try {
    // Reset the form
    const scene = scenes.value[selectedSceneIndex.value];

    const response = await axios.post(`http://localhost:8000/scenes/generate-scene-video/${scene.id}`, {
      prompt: scene.video_prompt,
    });
    const data = response.data;
    scene.video_src = data.video_url; // Assuming the backend returns the video URL in 'video_url'
    alert('Video generation started. It may take a few minutes to complete. Please refresh the page after some time to see the updated video.');

  } catch (error) {
    console.error('Error generating scene video:', error.response?.data || error.message);
  }
}


// GENERATING IMAGE
const imageGenerationStyle = ref(null);
const imageGenerationStylePower = ref(5);

const fixImagePrompt = async () => {
  try {
    const response = await axios
      .post('http://localhost:8000/generators/fix-scene-image-prompt', { 
        prompt: scenes.value[selectedSceneIndex.value].image_prompt,
        style: imageGenerationStyle.value,
        style_power: imageGenerationStylePower.value
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; // Re-throw the error after logging it
      })
    ;
    scenes.value[selectedSceneIndex.value].image_prompt = response.data.fixed_prompt;
  } catch (error) {
    console.error('Error fixing scene image prompt:', error);
  }
}

const generateImage = async () => {
  const formData = new FormData();
  
  // Helper to convert URL/blob to File
  const urlToFile = async (url, filename) => {
    try {
      // Handle blob: URLs
      url = getSrc(url)
      if (url.startsWith('blob:')) {
        const response = await fetch(url);
        const blob = await response.blob();
        return new File([blob], filename, { type: blob.type });
      }

      // Handle http(s) URLs (including localhost)
      const response = await fetch(url);
      if (!response.ok) throw new Error(`Failed to fetch ${url}`);
      const blob = await response.blob();
      return new File([blob], filename, { type: blob.type || 'image/jpeg' });
    } catch (error) {
      console.error(`Error converting ${url} to File:`, error);
      throw error;
    }
  };

  // Convert reference images to Files and append to formData
  console.log(addedReferenceImages.value);
  for (const img of addedReferenceImages.value) {
    const file = await urlToFile(img.src, `scene_${img.name}`);  // filename: scene_<uuid>
    formData.append("files", file);  // ← NOT reference_images[...]
  }

  formData.append("lowkey", generateImageLowkey.value);
  formData.append("image_prompt", scenes.value[selectedSceneIndex.value].image_prompt);

  // Optional: debug
  console.log("Sending FormData:");
  for (const [k, v] of formData.entries()) {
    if (v instanceof File) {
      console.log(`  ${k} -> File: ${v.name} (${v.size} bytes)`);
    } else {
      console.log(`  ${k} -> ${v}`);
    }
  }

  const response = await axios.post(
    `${route}scenes/generate-image/${scenes.value[selectedSceneIndex.value].id}`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );

  console.log(response.data);
  scenes.value[selectedSceneIndex.value].image_src = response.data.image_url;
};

// MANUAL SCENE LOAD
const handleSceneImageUpload = (event) => {
  const img = event.target.files[0];
  const url = URL.createObjectURL(img);
  console.log(url)
  scenes.value[selectedSceneIndex.value].image_src = url;

  const formData = new FormData();
  formData.append('image', img);

  axios.put(`${route}scenes/upload-image/${scenes.value[selectedSceneIndex.value].id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

// REFERENCE IMAGES
const addedReferenceImages = ref([]);

watch(selectedSceneIndex, ()=>{
  if(typeof(selectedSceneIndex.value) == 'number'){
    console.log(scenes.value[selectedSceneIndex.value].characters)
    if(scenes.value[selectedSceneIndex.value].characters.length > 0) {
      console.log("CHARCTERS");
      console.log(scenes.value[selectedSceneIndex.value].characters)
      addedReferenceImages.value = scenes.value[selectedSceneIndex.value].characters.map(el => ({ name: el.name, src: el.src }))
      return
    }
  }
  addedReferenceImages.value = []
})

const availableReferenceImages = computed(()=>{
  const addedSrcs = addedReferenceImages.value.map(el => el.src)
  if(typeof(selectedSceneIndex.value) == 'number'){
    let result = []
    characters.value.forEach(el => {
      if(!addedSrcs.includes(el.src)){
        result.push({
          name: el.name,
          src: el.src
        })
      }
    })
    scenes.value.forEach(el => {
      if(el.image_src && !addedSrcs.includes(el.image_src)){
        result.push({
          name: 'scene_' + el.id,
          src: el.image_src
        })
      }
    })
    return result
  }
  return []
})

const addReferenceImage = (referenceImg) => {
  addedReferenceImages.value.push(referenceImg)
}

const removeReferenceImage = (referenceImgSrc) => {
  addedReferenceImages.value = addedReferenceImages.value.filter(el => el.src != referenceImgSrc)
  console.log(addedReferenceImages.value)
}


// REQUESTS
const generateVoiceover = async () => {
  const voiceover = voiceovers.value[selectedVoiceoverIndex.value];
  console.log(voiceover)
  const voiceoverResponse = await axios.post(`http://localhost:8000/voiceovers/generate-voiceover/${voiceover.id}`, {
    text: voiceover.text
  });
  voiceovers.value[selectedVoiceoverIndex.value].src = voiceoverResponse.data.voiceover_src
  voiceoversVersion.value[voiceover.id]++
}


// Time markers (every 10 seconds)
const timeTicks = Array.from({ length: Math.ceil(timelineDuration / 5) + 1 }, (_, i) => i * 5);

// Format time in seconds to MM:SS.ss (with milliseconds if needed, but simplified to seconds)
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const millis = Math.floor((seconds % 1) * 10); // Get milliseconds as integer (0–9)

  const millisStr = millis.toString().padStart(3, '0'); // Always 3 digits

  return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${String(millisStr)[2]}`;
};

// Dragging state
const dragging = ref(null);


// Handle dragging
const startDragging = (event, type, item, index, trackRef) => {
  event.preventDefault();
  console.log('start dragging');
  const trackRect = trackRef.getBoundingClientRect();
  dragging.value = { 
    type, 
    item, 
    index, 
    startX: event.clientX, 
    startTime: item.start_time,
    trackLeft: trackRect.left,
    scrollLeft: event.target.closest('.overflow-x-auto').scrollLeft
  };

  const onMouseMove = (e) => {
    if (!dragging.value) return;
    const deltaX = e.clientX - dragging.value.startX;
    const deltaTime = deltaX / pixelsPerSecond.value;
    const newStartTime = Math.max(0, Math.min(dragging.value.startTime + deltaTime, timelineDuration - item.duration));

    if (type === 'scene') {
      scenes.value[index].start_time = newStartTime;
    } else if (type === 'voiceover') {
      voiceovers.value[index].start_time = newStartTime;
    }
  };

  const onMouseUp = () => {
    if (dragging.value) {
      console.log(`${dragging.value.type} ${dragging.value.index} new start_time:`, dragging.value.item.start_time);
      dragging.value = null;
    }
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', onMouseUp);
  };
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
};

const containerRef = ref(null)

const handleWheel = (event) => {
  // Check if Ctrl key is pressed (for zoom-like behavior)
  if (event.ctrlKey) {
    event.preventDefault() // Prevent default browser zoom

    // Calculate zoom change based on scroll delta
    const delta = event.deltaY > 0 ? 1/1.3 : 1.3 
    pixelsPerSecond.value = Math.max(10, Math.min(pixelsPerSecond.value * delta, 400)) // Clamp between 0.5x and 3x
  }
}

// Select scene for preview
const selectScene = (sceneId) => {
  selectedSceneIndex.value = scenes.value.findIndex(el => el.id == sceneId);
  selectedVoiceoverIndex.value = null;
};

// Select voiceover for preview
const selectVoiceover = (voiceoverId) => {
  selectedVoiceoverIndex.value = voiceovers.value.findIndex(el => el.id == voiceoverId);
  selectedSceneIndex.value = null;
};


onMounted(async () => {
  projectId = window.location.pathname.split('/').pop();
  const response = await fetch(`http://localhost:8000/projects/${projectId}`);
  const project = await response.json();

  initializeVersions(voiceoversVersion, project.voiceovers)
  initializeVersions(videosVersion, project.voiceovers)
  initializeVersions(imagesVersion, project.voiceovers)
  // Wait for the next tick to ensure DOM is updated with voiceover elements
  voiceovers.value = project.voiceovers
  scenes.value = project.scenes
  characters.value = project.characters

  console.log(scenes.value)

  selectScene(project.scenes[0].id)

  if (containerRef.value) {
    containerRef.value.addEventListener('wheel', handleWheel, { passive: false })
  }
  nextTick()

});

onBeforeUnmount(() => {
  if (containerRef.value) {
    containerRef.value.removeEventListener('wheel', handleWheel)
  }
})


</script>

<style scoped>
.preview {
  min-height: 200px;
}
.timeline {
  user-select: none; /* Prevent text selection during dragging */
}
.overflow-x-auto {
  overflow-x: auto;
  overflow-y: hidden;
}

div[ref="containerRef"] > div {
  transition: transform 0.1s ease-out;
}
video {
  transition: opacity 0.2s ease;
}

</style>