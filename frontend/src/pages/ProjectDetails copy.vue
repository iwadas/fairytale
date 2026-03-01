<template>
  <div class="container mx-auto">

    <!-- REGENERATING PROMPT -->
 


    <div class="preview mb-4 h-[550px]">
      <div
        class="flex gap-10 h-full justify-center"
      >
        <!-- PREVIEW -->
        <div class="relative min-w-[400px] overflow-hidden">
          <div class="size-[400px] rounded-[10px] overflow-hidden relative">
            <video
              v-for="index in 3"
              :key="index"
              :ref="el => setVideoRef(el, index - 1)"
              class="absolute object-cover w-full h-full bg-dark"
              width="400"
              height="400"
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

          <!-- Hidden audio for music -->
          <audio
            v-for="index in 2"
            :key="'music' + index"
            :ref="el => musicEls[index - 1] = el"
            preload="auto"
            @canplaythrough="onMusicReady(index - 1)"
            @ended="onMusicEnded(index - 1)"
            style="display: none;"
          ></audio>

          <div class="mt-4 text-lg">
            <div class="flex gap-3 items-center justify-center">
              <button class="size-6 rounded-md grid place-items-center text-light-hover" @click="move(-10)">
                <font-awesome-icon icon="backward" />
              </button>
              <button class="size-12 rounded-md grid place-items-center text-light-hover text-3xl" @click="togglePlay">
                <font-awesome-icon icon="play" v-if="!isPlaying"/>
                <font-awesome-icon icon="stop" v-else/>
              </button>
               <button class="size-6 rounded-md grid place-items-center text-light-hover" @click="move(10)">
                <font-awesome-icon icon="forward" />
              </button>
            </div>
            <!-- <p class="text-center mt-3">Time: {{ currentTime.toFixed(2) }}s</p> -->
          </div>
        </div>


        <!-- EDIT SCENE -->
        <scene-editor
          v-if="typeof(selectedSceneIndex) == 'number'"
          v-model:scene="scenes[selectedSceneIndex]"
          v-model:scene_tasks="sceneTasks"
          :project-id="projectId"
          :voiceovers="voiceovers"

        />
        <!-- v-model:reference_images="referenceImages"
          v-model:generating_video="generating" -->
        <!-- VOICEOVER EDIT -->
        <voiceover-editor
          v-else-if="typeof(selectedVoiceoverIndex) == 'number'"
          v-model:voiceover="voiceovers[selectedVoiceoverIndex]"
          v-model:voiceover_tasks="voiceoverTasks"
        />

        <music-editor
          v-else-if="typeof(selectedMusicIndex) == 'number'"
          v-model:music="backgroundMusic[selectedMusicIndex]"
        />



      </div>

      
    </div>

    <!-- Timeline Section -->
    <div class="flex gap-2 items-center mb-2">
      <button class="button-secondary text-xs text-light">
        <font-awesome-icon icon="video"/>
        <font-awesome-icon icon="plus-circle" class="text-primary"/>
      </button>
      <button class="button-secondary text-xs text-light">
        <font-awesome-icon icon="image"/>
        <font-awesome-icon icon="plus-circle" class="text-primary"/>
      </button>
      <button class="button-secondary text-xs text-light">
        <font-awesome-icon icon="microphone"/>
        <font-awesome-icon icon="plus-circle" class="text-primary"/>
      </button>
      <button class="button-secondary text-xs text-light"
        @click="addMusic"
      >
        <font-awesome-icon icon="music"/>
        <font-awesome-icon icon="plus-circle" class="text-primary"/>
      </button>
    </div>
    <div
      class="text-light container-background w-full text-xs"
    >
      <!-- <div class="mb-2 flex justify-end *:w-32 gap-2">
          <form-button label="Add scene" @clicked="addScene"/>
          <form-button label="Add voiceover" @clicked="addVoiceover"/>
      </div> -->
      <div class="flex w-full" ref="containerRef"> 
        <div class="min-w-[100px] flex flex-col -mr-10 relative z-30">
          <div class="mt-[60px] h-[70px] w-full flex justify-center items-center bg-medium">
            <font-awesome-icon icon="video"/>
          </div>
          <div class="h-[70px] w-full flex justify-center items-center bg-light-gray">
            <font-awesome-icon icon="image"/>
          </div>
          <div class="h-[70px] w-full flex justify-center items-center bg-medium">
            <font-awesome-icon icon="microphone"/>
          </div>
          <div class="h-[70px] w-full flex justify-center items-center bg-light-gray">
            <font-awesome-icon icon="music"/>
          </div>
        </div>

        <div class="overflow-x-auto relative px-10">
          <div class="relative" :style="{ width: `${totalWidth}px`, minWidth: '100%' }">
            <!-- Timeline Background with Time Markers -->
            <div class="relative w-full h-5 rounded">
              <!-- Time Markers -->
              <div class="flex text-xs text-gray-400">
                <div v-for="tick in timeTicks" :key="tick" class="absolute flex flex-col items-center -translate-x-1/2" :style="{ left: `${tick.time * pixelsPerSecond}px` }">
                  <div :class="tick.label ? 'h-6' : 'h-2'" class="w-[1px] bg-[var(--light-gray)]"></div>
                  <span class="h-5 text-xs text-light">
                    {{ tick.label }}
                  </span>
                </div>
              </div>
            </div>
  
            <div class="h-10 w-full relative z-20 -mt-5">
              <div class="w-full h-full" @click="handleTimeChange($event)"></div>
              <div class="absolute h-[400px] z-40 top-0"
                :style="{ left: `${currentTime * pixelsPerSecond}px` }"
              >
                <div class="relative h-full">
                  <font-awesome-icon
                    icon="caret-down"
                    class="text-[var(--primary)] text-3xl absolute -translate-x-1/2 top-0 -translate-y-3 left-1/2"
                  />
                  <div class="h-full bg-primary w-1">
                  </div>
                </div>
              </div>
            </div>
            <!-- Scenes Track -->
            <div class="relative h-[70px] bg-medium mt-5 z-0" ref="scenesTrack">
              <div
                v-for="(scene, index) in scenes"
                :key="scene.id"
                class="absolute rounded-[10px] cursor-pointer select-none flex flex-col border-[2px] justify-between mt-[10px] overflow-hidden"
                :class="{
                  'border-[var(--primary)]' : index == selectedSceneIndex,
                  'border-transparent' : index != selectedSceneIndex,
                }"
                :style="{
                  left: `${scene.start_time * pixelsPerSecond}px`,
                  width: `${sceneActualDuration[scene.id] * pixelsPerSecond}px`,
                  zIndex: Math.round(scene.start_time * 100),
                }"
                @click="selectScene(scene.id)"
                @mousedown="startDragging($event, 'scene', scene, index, $refs.scenesTrack)"
              >
                <video-element
                  :scene="scene"
                  :numberOfFramesToDisplay="Math.ceil(scene.duration * pixelsPerSecond / 50)"
                />
              </div>
            </div>
  
            <!-- PHOTODUMP TRACK -->
            <div class="relative h-[70px] bg-light-gray" >
              
            </div>

            <div class="relative h-[70px] bg-medium" ref="voiceoversTrack">
              <div
                v-for="(voiceover, index) in voiceovers"
                :key="voiceover.id"
                class="absolute h-[50px] rounded-[10px] cursor-pointer select-none flex flex-col border-[2px] justify-between mt-[10px]"
                :style="{
                  left: `${voiceover.start_time * pixelsPerSecond}px`,
                  width: `${voiceover.duration * pixelsPerSecond}px`,
                }"
                :class="{
                  'border-[var(--primary)]' : index == selectedVoiceoverIndex,
                  'border-transparent' : index != selectedVoiceoverIndex,
                }"
                @click="selectVoiceover(voiceover.id)"
                @mousedown="startDragging($event, 'voiceover', voiceover, index, $refs.voiceoversTrack)"
              >
                
                <audio-element :voiceover="voiceover" class="bg-light-gray"/>
              </div>
            </div>
            <div class="relative h-[70px] bg-light-gray" ref="musicTrack">
              <div
                v-for="(music, index) in backgroundMusic"
                :key="music.id"
                class="absolute h-[50px] rounded-[10px] cursor-pointer select-none flex flex-col border-[2px] justify-between mt-[10px]"
                :style="{
                  left: `${music.start_time * pixelsPerSecond}px`,
                  width: `${music.duration * pixelsPerSecond}px`,
                }"
                :class="{
                  'border-[var(--primary)]' : index == selectedMusicIndex,
                  'border-transparent' : index != selectedMusicIndex,
                }"
                @click="selectMusic(music.id)"
                @mousedown="startDragging($event, 'music', music, index, $refs.musicTrack)"
              >
                
                <audio-element :music="music" class="bg-medium"/>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- <form-button label="Generate one long voiceover" @clicked="combineVoiceovers"/>
    <form-button label="Save project" @clicked="saveProjectChanges"/> -->
    
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue';
import axios from 'axios'
import FormInput from '@/components/FormInput.vue'
import FormButton from '@/components/FormButton.vue'
import VideoSubtitles from '@/components/VideoSubtitles.vue'
import ReferenceImage from '@/components/ReferenceImage.vue'
import Modal from '@/components/ModalContainer.vue'
import getSrc from '../utils/getSrc.js'
import VideoElement from '@/components/project_details/VideoElement.vue'
import AudioElement from '@/components/project_details/AudioElement.vue'
import SceneEditor from '@/components/project_details/SceneEditor.vue'
import VoiceoverEditor from '@/components/project_details/VoiceoverEditor.vue'
import MusicEditor from '@/components/project_details/MusicEditor.vue'


const route = 'http://localhost:8000/'
let projectId = null;

const scenes = ref([]);
const voiceovers = ref([]);
const backgroundMusic = ref([]);
const characters = ref([]);

const timelineDuration = 220; // Total duration of the timeline in seconds (adjust as needed)
const pixelsPerSecond = ref(50); // 100px per second
const totalWidth = computed(()=>{
  return timelineDuration * pixelsPerSecond.value;
});

const selectedSceneIndex = ref(null);
const selectedVoiceoverIndex = ref(null);
const selectedMusicIndex = ref(null);
const generateImageLowkey = ref(true);
const voiceoverTimestamps = ref([])
const selectedSceneImageIndex = ref(null);


const sceneTasks = ref({
  fixing_image_prompt: {},
  generating_video: {},
  generating_image: {},
  generating_prompt: {},
});


const getSelectedSceneId = () => {
  return scenes.value[selectedSceneIndex.value].id
}

const getSelectedVoiceoverId = () => {
  return voiceovers.value[selectedVoiceoverIndex.value].id
}

// ADD SCENE
const addScene = async () => {
  const response = await axios.post(`${route}scenes/${projectId}`);
  let newScene = response.data;
  newScene["start_time"] = currentTime.value;
  newScene["images"] = [{src: '', prompt: ''}, {src: '', prompt: ''}]; // start and end images
  newScene["characters"] = []; // characters array
  scenes.value.push(newScene);
}

// COMBINE VOICEOVERS
const combineVoiceovers = async () => {
  await axios.post(`${route}voiceovers/combine/${projectId}`);
}

const addMusic = async () => {
  const response = await axios.post(`${route}music/${projectId}`);
  backgroundMusic.value.push(response.data.music);
}

// ADD VOICEOVER
const addVoiceover = async () => {
  const response = await axios.post(`${route}voiceovers/${projectId}`);
  voiceovers.value.push(response.data);
}


// SET TIME
const handleTimeChange = (event) => {
  if (!containerRef.value) return;

  const containerRect = containerRef.value.getBoundingClientRect();
  const scrollLeft = containerRef.value.querySelector('.overflow-x-auto').scrollLeft;

  // 40 because of padding
  const clickX = event.clientX - containerRect.left + scrollLeft - 100;

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
// const voiceoversVersion = ref({})
// const videosVersion = ref({})
// const imagesVersion = ref({})

// const initializeVersions = (ref, values) => {
//   let result = {}
//   values.forEach(el => result[el.id] = 0)
//   ref.value = result
//   console.log(voiceoversVersion.value)
// }


// PREVIEW LOGIC
const videoEls = ref([]) // [video0, video1, video2]
const isPlaying = ref(false)
const currentTime = ref(0)
const rafId = ref(null)

const audioEls = ref([])  // [audio0, audio1]
const activeAudioLayer = ref(0)
const audioReady = ref([false, false])
const audioSources = ref(['', ''])  // track current src per layer

const musicEls = ref([])
const activeMusicLayer = ref(0)
const musicReady = ref([false, false])
const musicSources = ref(['', ''])  // track current src per layer

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

const onMusicReady = (index) => {
  musicReady.value[index] = true
}

const onAudioEnded = (index) => {
  // Auto-switch back to layer 0 when this one finishes (optional)
  if (activeAudioLayer.value === index) {
    activeAudioLayer.value = 0
  }
}

const onMusicEnded = (index) => {
  if (activeMusicLayer.value === index) {
    activeMusicLayer.value = 0
  }
}



// Performance
let playbackStartTime = 0
let playbackStartTimestamp = 0

// Throttling

const orderedScenes = computed(()=>{
  return [...scenes.value].sort((a, b) => a.start_time - b.start_time)
}, {deep: true})

const orderedScenesIdToIndex = computed(()=>{
  let mapping = {}
  orderedScenes.value.forEach((scene, index) => {
    mapping[scene.id] = index
  })
  return mapping
})

const sceneActualDuration = computed(()=>{
  let mapping = {}
  orderedScenes.value.forEach((scene) => {
    const nextScene = orderedScenes.value.find(s => s.start_time > scene.start_time)
    const endTime = Math.min(nextScene ? nextScene.start_time : 10000, scene.start_time + scene.duration)
    mapping[scene.id] = endTime - scene.start_time
  })
  return mapping
})


// ================ SCENE LOGIC ================
const activeScene = computed(() => {
  const time = currentTime.value

  // Since orderedScenes is sorted by start_time (ascending),
  // iterating backwards finds the most recently started scene that is still active.
  // This naturally handles overlapping scenes correctly (later-started wins).
  for (let i = orderedScenes.value.length - 1; i >= 0; i--) {
    const s = orderedScenes.value[i]
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

const activeMusic = computed(() => {
  const time = currentTime.value
  for (const music of backgroundMusic.value) {
    if (time >= music.start_time && time < music.start_time + music.duration) {
      return music
    }
  }
  return null
})

const nextScene = computed(() => {
  const current = activeScene.value
  if (!current) return null
  const index = orderedScenes.value.findIndex(s => s === current)
  return orderedScenes.value[index + 1] || null
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
  const index = orderedScenes.value.findIndex(s => s === next)
  return orderedScenes.value[index + 1] || null
})

const nextMusic = computed(() => {
  const current = activeMusic.value
  if (!current) return null
  const index = backgroundMusic.value.findIndex(m => m === current)
  return backgroundMusic.value[index + 1] || null
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

const updateMusicLayers = async (time) => {
  const music = activeMusic.value
  const next_music = nextMusic.value

  const currentLayer = activeMusicLayer.value
  const nextLayer = 1 - currentLayer  // toggle between 0 and 1

  // 1. Current music
  if (music) {
    const localTime = time - music.start_time
    const fullSrc = (route + music.src).replaceAll("\\", "/")

    // FIX 1: Check musicSources, not audioSources
    if (musicSources.value[currentLayer] !== fullSrc) {
      // Load into current layer
      // FIX 2: Renamed inner variable to musicEl to prevent shadowing
      const musicEl = musicEls.value[currentLayer]

      musicEl.pause()
      musicEl.src = fullSrc
      musicEl.currentTime = localTime
      musicEl.load()
      musicSources.value[currentLayer] = fullSrc
      musicReady.value[currentLayer] = false
    } else {
      // Same source → just sync time
      const musicEl = musicEls.value[currentLayer]
      if (Math.abs(musicEl.currentTime - localTime) > 0.1) {
        musicEl.currentTime = localTime
      }
    }

    // Auto-switch to this layer when ready
    if (musicReady.value[currentLayer] && activeMusicLayer.value !== currentLayer) {
      activeMusicLayer.value = currentLayer
    }

    // Play if playing
    if (isPlaying.value && musicEls.value[currentLayer].paused && musicReady.value[currentLayer]) {
      musicEls.value[currentLayer].play().catch(() => {})
    }
  }

  // 2. Preload NEXT music (if exists and not too far)
  if (next_music && next_music.start_time - time < 2.0) {  // preload 2s early
    const fullSrc = (route + next_music.src).replaceAll("\\", "/")
    if (musicSources.value[nextLayer] !== fullSrc) {

      const musicEl = musicEls.value[nextLayer]
      musicEl.pause()
      musicEl.src = fullSrc
      musicEl.currentTime = 0
      musicEl.load()
      musicSources.value[nextLayer] = fullSrc
      musicReady.value[nextLayer] = false
    }
  }

  // 3. Auto-switch on boundary
  if (next_music && time >= next_music.start_time - 0.05) {
    if (musicReady.value[nextLayer]) {
      activeMusicLayer.value = nextLayer
    }
  }

  // 4. Stop inactive layer
  const inactiveLayer = 1 - activeMusicLayer.value
  if (musicEls.value[inactiveLayer].src && inactiveLayer !== currentLayer) {
    musicEls.value[inactiveLayer].pause()
  }
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
  if (next && time >= next.start_time) {
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
  updateMusicLayers(currentTime.value)

  // Sync active video
  if (activeScene.value && videoEls.value[activeLayer.value]) {
    const video = videoEls.value[activeLayer.value]
    const expected = currentTime.value - activeScene.value.start_time
    if (Math.abs(video.currentTime - expected) > 0.5) {
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
  musicEls.value.forEach(m => m.pause())
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

const move = (seconds) => {
  seekTo(Math.max(0, currentTime.value + seconds));
}

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


// REGENERATE IMAGE PROMPT
const generatingNewImagePrompts = ref(false);

const newImagePromptForm = ref({
  scene_id: null,
  scene_image_id: null,
  full_voiceover_text: null,
  additional_info: null,
  start_word_idx: null,
  end_word_idx: null,
  options: [],
})






// GENERATING VIDEO
const fixingVideoPrompt = ref(false);
const fixVideoPrompt = async () => {
  try {
    fixingVideoPrompt.value = true;
    const response = await axios
      .post('http://localhost:8000/generators/fix-scene-video-prompt', { 
        image_prompt: scenes.value[selectedSceneIndex.value].images[0].prompt,
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
  } finally {
    fixingVideoPrompt.value = false;
  }
}

// GENERATING IMAGE




const removeImage = async (sceneImageId) => {
  if(!sceneImageId) return
  await axios.delete(`${route}scenes/remove-image/${sceneImageId}`);
  scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value].src = null;
}




// REQUESTS
const voiceoverTasks = ref({
  generating_voiceover: {},
});


// Time markers (every 10 seconds)
const timeTicks = computed(()=>{
  const ticks = [];
  for(let t = 0; t <= timelineDuration; t++){
    if(t % 5 == 0){
      ticks.push({
        time: t,
        label: formatTime(t)
      })
    } else {
      ticks.push({
        time: t,
        label: '',
      });
    }
  }
  return ticks
})

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
  if(index != selectedSceneIndex.value && type === 'scene') return;
  if(index != selectedVoiceoverIndex.value && type === 'voiceover') return;
  if(index != selectedMusicIndex.value && type === 'music') return;
  
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
    } else if (type === 'music') {
      backgroundMusic.value[index].start_time = newStartTime;
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
  deselectAll();
  selectedSceneIndex.value = scenes.value.findIndex(el => el.id == sceneId);
  filterSceneImages();
};

const selectMusic = (musicId) => {
  deselectAll();
  selectedMusicIndex.value = backgroundMusic.value.findIndex(el => el.id == musicId);
};

const deselectAll = () => {
  selectedSceneIndex.value = null;
  selectedVoiceoverIndex.value = null;
  selectedMusicIndex.value = null;
  selectedSceneImageIndex.value = 0;
}


// Function filters scene images based on their time (image has time which is enum - start, mid, end) (start -> 0, mid -> 1, end -> 2);
// If there are more than one image per time, it keeps the first one -> others are moved to next time slot (if free)
// If there are more than 3 scene images, extra ones are ignored
const filterSceneImages = () => {
  console.log('initial scenes');
  console.log(scenes.value[selectedSceneIndex.value]);
  if(typeof(selectedSceneIndex.value) != 'number') return;
  const scene = scenes.value[selectedSceneIndex.value];
  // const timeSlots = [null, null, null]; // start, mid, end
  const timeSlots = [null, null]; // start, mid, end
  scene.images.forEach(img => {
    console.log('processing img:');
    console.log(img);
    let slotIndex = 0;
    // if(img.time == 'mid') slotIndex = 1;
    if(img.time == 'end') slotIndex = 1;

    // Try to place in the desired slot or next available
    for(let i = slotIndex; i < 2; i++) {
      if(!timeSlots[i]) {
        timeSlots[i] = img;
        console.log('placed in slot ' + i);
        break;
      }
    }
    // fill empty timeslots with basic image data
  });
  for(let i = 0; i < 3; i++) {
    if(!timeSlots[i]) {
      timeSlots[i] = {
        id: null,
        scene_id: scene.id,
        src: null,
        time: i == 0 ? 'start' : 'end',
        prompt: 'Change camera angle / add action description',
      };
    }
  }

  scenes.value[selectedSceneIndex.value].images = timeSlots;


}

// Select voiceover for preview
const selectVoiceover = (voiceoverId) => {
  deselectAll();
  selectedVoiceoverIndex.value = voiceovers.value.findIndex(el => el.id == voiceoverId);
};


onMounted(async () => {
  projectId = window.location.pathname.split('/').pop();
  const response = await fetch(`http://localhost:8000/projects/${projectId}`);
  const project = await response.json();

  // initializeVersions(voiceoversVersion, project.voiceovers)
  // initializeVersions(videosVersion, project.voiceovers)
  // initializeVersions(imagesVersion, project.voiceovers)
  // Wait for the next tick to ensure DOM is updated with voiceover elements
  voiceovers.value = project.voiceovers
  scenes.value = project.scenes
  characters.value = project.characters
  backgroundMusic.value = project.background_music

  console.log(project.background_music);

  console.log('project');
  console.log(project);

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
/* video {
  transition: opacity 0.1s ease;
} */

</style>