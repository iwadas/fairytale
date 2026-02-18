<template>
  <div class="container mx-auto p-4">

    <!-- REGENERATING PROMPT -->
    <modal v-if="newImagePromptForm.scene_id && newImagePromptForm.full_voiceover_text">
      <div class="flex flex-col gap-4">
        
        <div class="flex justify-end">
          <form-button label="Cancel" class="w-fit" color="red" @clicked="newImagePromptForm.scene_id = null"/>
        </div>
        <h2 class="text-2xl">Regenerate prompt</h2>
        
        <div>
          <p>
            Select the part of the scene description that you want to regenerate.
          </p>
          <p>Set: <span :class="settingWordForStart ? 'text-blue-500' : 'text-red-500'">{{ settingWordForStart ? 'start' : 'end' }}</span></p>
          <div class="flex gap-1 flex-wrap">
            <span v-for="(word, idx) in newImagePromptForm.full_voiceover_text.split(' ')" :key="`${idx}-word`" class="relative cursor-pointer bg-gray-100 p-0.5 rounded-sm" @click="setWordForImageGeneration(idx)">
              {{ word }}
              <span v-if="idx == newImagePromptForm.start_word_idx" class="absolute left-0 h-full w-1 top-0 bg-blue-500"></span>
              <span v-if="idx == newImagePromptForm.end_word_idx" class="absolute right-0 h-full w-1 top-0 bg-red-500"></span>
            </span>
          </div>
        </div>

        <p>Additional information (style or mood)</p>
        <textarea v-model="newImagePromptForm.additional_info"></textarea>


        <form-button label="Generate new prompts" :loading="generatingNewImagePrompts" :show_status="true" @clicked="generateNewImagePrompts"/>
        
        <div v-if="newImagePromptForm.options.length">
          <h3 class="text-xl mb-2">New Scene Description Options:</h3>
          <div class="flex flex-col gap-2 max-h-[400px] overflow-y-auto">
            <div 
              v-for="(option, idx) in newImagePromptForm.options" 
              :key="`option-${idx}`" 
              class="p-2 border rounded hover:bg-gray-100 cursor-pointer"
              @click="applyNewImagePrompt(option)"
            >
              <p>
                <font-awesome-icon icon="image"/>
                {{ option.image_description }}
              </p>
              <br>
              <p>
                <font-awesome-icon icon="circle-play"/>
                {{ option.video_description }}
              </p>
            </div>
          </div>
        </div>


      </div>


    </modal>


    <div class="preview bg-gray-800 rounded-lg p-4 mb-4 h-[660px]">
      <div
        class="flex gap-2 items-center h-full"
      >
        <!-- TODO -->
        <!-- TODO -->
        <!-- TODO -->
        <!-- PREVIEW -->
        <div class="relative min-w-[270px] rounded-lg overflow-hidden">
          <div class="h-[480px]">
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

          <div class="text-white">
            <div class="flex gap-4 items-center mt-2 justify-center text-xl">
              <button class="size-4 rounded-md grid place-items-center" @click="reset">
                <font-awesome-icon icon="backward-fast" />
              </button>
              <button class="size-4 rounded-md grid place-items-center" @click="move(-10)">
                <font-awesome-icon icon="backward" />
              </button>
              <button class="size-4 rounded-md grid place-items-center" @click="togglePlay">
                <font-awesome-icon icon="circle-play" v-if="!isPlaying"/>
                <font-awesome-icon icon="circle-stop" v-else/>
              </button>
               <button class="size-4 rounded-md grid place-items-center" @click="move(10)">
                <font-awesome-icon icon="forward" />
              </button>
               <button class="size-4 rounded-md grid place-items-center opacity-0" >
                <font-awesome-icon icon="forward" />
              </button>
            </div>
            <p class="text-center mt-3">Time: {{ currentTime.toFixed(2) }}s</p>
          </div>
        </div>

        <!-- Divider -->
        <div class="h-full w-1 bg-white"></div>

        <div 
          class="text-gray-300 flex gap-6" 
          v-if="typeof(selectedSceneIndex) == 'number'"
        >
          <!-- SCENE VIDEO -->
          <div>
            <div class="h-[320px] w-[180px] bg-gray-400 rounded-lg mx-auto relative">
              <p class="absolute top-4 left-1/2 -translate-x-1/2 text-white fonr-bold z-10">Video</p>
              <video 
                v-if="scenes[selectedSceneIndex].video_src" 
                :src="`http://localhost:8000/${scenes[selectedSceneIndex].video_src}?v=1}`"
                alt="Scene Video"
                class="w-full h-full object-cover rounded-md border" 
                controls 
              />
            </div>
            <form-input label="Video Prompt" class="w-[180px] mt-6 text-xs">
              <textarea class="w-[180px] text-white bg-gray-800 border p-1 rounded-sm h-24" v-model="scenes[selectedSceneIndex].video_prompt"></textarea>
              <form-button label="Fix Prompt" :show_status="true" :loading="fixingVideoPrompt" @clicked="fixVideoPrompt"/>
            </form-input>
            <div class="flex flex-col gap-1 mt-4">
              <form-button :show_status="true" :loading="generatingVideo.includes(scenes[selectedSceneIndex].id)" v-if="scenes[selectedSceneIndex].video_src" label="Regenerate Video" color="green" @click="generateVideo"/>
              <form-button :show_status="true" :loading="generatingVideo.includes(scenes[selectedSceneIndex].id)" v-else label="Generate Video" @click="generateVideo" color="green"/>
              <input type="file" class="w-[180px] text-white bg-gray-800 border p-1 rounded-sm text-xs" @input="handleSceneVideoUpload">
            </div>
          </div>
          
          <!-- SCENE IMAGE -->
          <div>
            <!-- IMAGES -->
            <div class="flex gap-2 justify-center items-center">
              <div v-for="name, idx in ['start', 'end']" :key="name" class="flex gap-2 items-center">
                <button class="h-[240px] w-[135px] bg-gray-400 rounded-lg relative" @click="selectedSceneImageIndex = idx"
                  :class="selectedSceneImageIndex == idx && 'border-4 border-blue-500'"
                >
                  <p class="absolute top-4 left-1/2 -translate-x-1/2 text-white fonr-bold z-10">{{ name }}</p>
                  <button v-if="scenes[selectedSceneIndex].images[idx]?.src" class="absolute top-1 right-1 z-10" @click="removeImage(scenes[selectedSceneIndex].images[idx].id)">
                    <font-awesome-icon icon="xmark"/>
                  </button>
                  <img
                    v-if="scenes[selectedSceneIndex].images[idx]?.src"
                    :src="getSrc(scenes[selectedSceneIndex].images[idx].src)"
                    alt="Scene Image"
                    class="w-full h-full object-cover"
                  />
                </button>
                <div v-if="idx != 1">
                  <button @click="console.log('swaping ', idx)">
                    <font-awesome-icon icon="right-left"/>
                  </button>
                </div>
              </div>
            </div>
            <div class="flex gap-2 items-center mt-3 text-xs">
              <form-input label="Image Style" class="w-full mt-4">
                <select v-model="imageGenerationStyle" class="text-white bg-gray-800 border-white rounded-sm w-full border">
                  <option value="" default>Auto style</option>
                  <option value="lifelaps">LifeLaps style</option>
                  <option value="lifelaps_science">LifeLaps style (with_science_shit)</option>
                  <option value="criminal">Criminal style</option>
                </select>
              </form-input>
              <div v-if="imageGenerationStylePower" class="w-full text-xs">
                <label for="stylePower" class="text-gray-300">
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

            <!-- PROMPT TEXT AREA -->
            <form-input label="Image Prompt" class="w-full text-xs mt-5" v-if="scenes[selectedSceneIndex].images[selectedSceneImageIndex]">
              <textarea class="w-full text-white bg-gray-800 border p-1 rounded-sm h-24" v-model="scenes[selectedSceneIndex].images[selectedSceneImageIndex].prompt"></textarea>
              <form-button :show_status="true" :loading="fixingImagePrompt" label="Apply styles" @clicked="fixImagePrompt"/>
              <form-button label="Regenerate prompt" class="mt-2" @clicked="openNewImagePromptForm"/>
            </form-input>

            <!-- REFERENCE IMAGES -->
            <div class="flex gap-6 mt-4 mb-4 text-xs">
              <div class="flex-1">
                <p>
                  Reference Images Added:
                </p>
                <div class="overflow-y-auto max-w-[300px] flex gap-1">
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
                  Available Reference Images:
                </p>
                <div class="overflow-y-auto max-w-[300px] flex gap-1" v-if="availableReferenceImages.length > 0">
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

            <!-- IMAGE FINAL ACTION -->
            <div class="flex flex-col gap-1">
              <form-button v-if="scenes[selectedSceneIndex].image_src" :show_status="true" :loading="generatingImage" label="Regenerate Image" color="green" @clicked="generateImage"/>
              <form-button v-else label="Generate Image" :show_status="true" :loading="generatingImage" @clicked="generateImage" color="green"/>
              <div class="flex justify-center" v-if="false">
                <p>Lowkey</p>
                <input type="checkbox" class="border" v-model="generateImageLowkey">
              </div>
              <input type="file" class="w-full text-white bg-gray-800 border p-1 rounded-sm text-xs" @input="handleSceneImageUpload">
            </div>
          </div>

          <!-- MORE FUNCTIONS -->
          <div class="flex flex-col justify-center gap-6 text-xs">
            <form-input label="Start Time">
              <input type="text" class="w-[100px] text-white bg-gray-800 border p-1 rounded-sm" v-model="scenes[selectedSceneIndex].start_time">
            </form-input>
            <form-input label="Duration">
              <input type="text" class="w-[100px] text-white bg-gray-800 border p-1 rounded-sm" v-model="scenes[selectedSceneIndex].duration">
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
            <audio :src="`http://localhost:8000/${voiceovers[selectedVoiceoverIndex].src}`" controls class="w-full mt-2"></audio>
          </div>
          <form-button v-else label="Generate Voiceover" @clicked="generateVoiceover"/>
          <form-button label="Delete voiceover" @clicked="deleteVoiceover"/>
        </div>

      </div>

      
    </div>

    <!-- Timeline Section -->
    <div class="bg-gray-900 rounded-lg p-4">
      <div class="mb-2 flex justify-end *:w-32 gap-2">
          <form-button label="Add scene" @clicked="addScene"/>
          <form-button label="Add voiceover" @clicked="addVoiceover"/>
      </div>
      <div class="timeline " ref="containerRef"> 
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
            <div class="relative h-24 mt-1 z-0" ref="scenesTrack">
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
                <span class="text-xs text-white p-2 overflow-hidden">{{ scene.video_prompt }}</span>
                <div class="w-full text-center bg-gray-800 z-20 text-white text-xs font-bold cursor-move"
                  @mousedown="startDragging($event, 'scene', scene, index, $refs.scenesTrack)"
                >
                  move
                </div>
              </div>
            </div>
  
            <!-- Voiceovers Track -->
            <div class="relative h-20" ref="voiceoversTrack">
              <div
                v-for="(voiceover, index) in voiceovers"
                :key="voiceover.id"
                class="absolute h-16 mt-1 bg-green-500 rounded cursor-pointer select-none flex flex-col justify-between border border-white"
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
    </div>
    <form-button label="Generate one long voiceover" @clicked="combineVoiceovers"/>
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
import Modal from './ModalContainer.vue'
import getSrc from '../utils/getSrc.js'


const route = 'http://localhost:8000/'
let projectId = null;

const scenes = ref([]);
const voiceovers = ref([]);
const characters = ref([]);

const timelineDuration = 220; // Total duration of the timeline in seconds (adjust as needed)
const pixelsPerSecond = ref(50); // 100px per second
const totalWidth = computed(()=>{
  return timelineDuration * pixelsPerSecond.value;
});

const selectedSceneIndex = ref(null);
const selectedVoiceoverIndex = ref(null);
const generateImageLowkey = ref(true);
const voiceoverTimestamps = ref([])
const selectedSceneImageIndex = ref(null);

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

const orderedScenes = computed(()=>{
  return [...scenes.value].sort((a, b) => a.start_time - b.start_time)
}, {deep: true})

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

  // Sync active video
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

const settingWordForStart = ref(true)
const setWordForImageGeneration = (idx) => {
  if(settingWordForStart.value){
    newImagePromptForm.value.start_word_idx = idx;
  } else {
    if(idx < newImagePromptForm.value.start_word_idx){
      // swap
      newImagePromptForm.value.end_word_idx = newImagePromptForm.value.start_word_idx;
      newImagePromptForm.value.start_word_idx = idx;
      return;
    }
    newImagePromptForm.value.end_word_idx = idx;
  }
  settingWordForStart.value = !settingWordForStart.value;
}

const openNewImagePromptForm = async () => {
  console.log('TEXT CONTEXT')
  let orderedVoiceoversReverse = [...voiceovers.value].sort((a, b) => b.start_time - a.start_time);
  let voiceover;
  let scene = scenes.value[selectedSceneIndex.value];
  
  for(let i = 0; i < orderedVoiceoversReverse.length; i++){
    if(orderedVoiceoversReverse[i].start_time <= scene.start_time){
      voiceover = orderedVoiceoversReverse[i];
      break;
    }
  }

  newImagePromptForm.value.full_voiceover_text = voiceover ? voiceover.text : '';
  newImagePromptForm.value.scene_id = scene.id;
  newImagePromptForm.value.scene_image_id = scene.images[selectedSceneImageIndex.value].id;  
}

const generateNewImagePrompts = async () => {
  try {
    generatingNewImagePrompts.value = true;

    const selectedVoiceoverTextPart = newImagePromptForm.value.full_voiceover_text.split(' ').slice(
      newImagePromptForm.value.start_word_idx,
      newImagePromptForm.value.end_word_idx + 1
    ).join(' ');

    const response = await axios
      .post('http://localhost:8000/generators/generate-scene-image-prompts', { 
        project_id: projectId,
        full_voiceover_text: newImagePromptForm.value.full_voiceover_text,
        selected_voiceover_text_part: selectedVoiceoverTextPart,
        additional_info: newImagePromptForm.value.additional_info
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; // Re-throw the error after logging it
      })
    console.log(response.data.new_scene_descriptions);
    newImagePromptForm.value.options = response.data.new_scene_descriptions.options;
  } catch (error) {
    console.error('Error regenerating scene image prompt:', error);
  } finally {
    generatingNewImagePrompts.value = false;
  }
}

const applyNewImagePrompt = (option) => {
  scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value].prompt = option.image_description;
  scenes.value[selectedSceneIndex.value].video_prompt = option.video_description; // reset image
  newImagePromptForm.value = {
    scene_id: null,
    scene_image_id: null,
    full_voiceover_text: null,
    start_word_idx: null,
    end_word_idx: null,
    options: [],
  }
}



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

const generatingVideo = ref([]);

const generateVideo = async () => {
  const sceneIndex = selectedSceneIndex.value;
  const scene = scenes.value[selectedSceneIndex.value];
  try {
    // Reset the form
    generatingVideo.value.push(scene.id);
    const response = await axios.post(`http://localhost:8000/scenes/generate-scene-video/${scene.id}`, {
      prompt: scene.video_prompt,
      duration: scene.duration,
    });

    console.log("the task started")
    console.log(response.data);

    let task_id = response.data.task_id;

    let task_response 
    // start polling for task status
    while(true || false || true){
      task_response = await axios.get(`http://localhost:8000/tasks/${task_id}`);
      console.log("polling task status")
      console.log(task_response.data);
      
      if(task_response.data.status == 'success'){
        const newSrc = task_response.data.result.video_url;
        scenes.value[sceneIndex].video_src = newSrc + "?v=" + Date.now(); // Assuming the backend returns the video URL in 'video_ur
        break;
      }
      else if(task_response.data.status == 'failed'){
        throw new Error('Video generation task failed');
      }
      // wait for a few seconds before polling again
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  } catch (error) {
    console.error('Error generating scene video:', error.response?.data || error.message);
  } finally {
    generatingVideo.value = generatingVideo.value.filter(id => id !== scene.id);
  }
}


// GENERATING IMAGE
const imageGenerationStyle = ref(null);
const imageGenerationStylePower = ref(5);

const fixingImagePrompt = ref(false);

const fixImagePrompt = async () => {
  try {
    fixingImagePrompt.value = true;
    const response = await axios
      .post('http://localhost:8000/generators/fix-scene-image-prompt', { 
        prompt: scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value].prompt,
        style: imageGenerationStyle.value,
        style_power: imageGenerationStylePower.value
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; // Re-throw the error after logging it
      })
    ;
    scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value].prompt = response.data.fixed_prompt;
  } catch (error) {
    console.error('Error fixing scene image prompt:', error);
  } finally {
    fixingImagePrompt.value = false;
  }
}

const generatingImage = ref(false);

const removeImage = async (sceneImageId) => {
  if(!sceneImageId) return
  await axios.delete(`${route}scenes/remove-image/${sceneImageId}`);
  scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value].src = null;
}

const generateImage = async () => {
  const formData = new FormData();
  generatingImage.value = true;
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
    const file = await urlToFile(img.src, `scene_${img.name}`); 
    formData.append("files", file); 
  }

  const scene = scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value];
  formData.append("lowkey", generateImageLowkey.value);
  formData.append("prompt", scene.prompt);
  formData.append("scene_image_id", scene.id);

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

  generatingImage.value = false;

  console.log(response.data);
  scenes.value[selectedSceneIndex.value].image_src = response.data.image_url;
};

// MANUAL SCENE LOAD
const handleSceneImageUpload = async (event) => {
  const img = event.target.files[0];
  const formData = new FormData();
  formData.append('image', img);
  formData.append('time', ["start", "end"][selectedSceneImageIndex.value]);
  formData.append('scene_image_id', scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value].id ?? '');
  formData.append('scene_image_prompt', scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value].prompt ?? '');
  console.log(formData);
  const response = await axios.put(`${route}scenes/upload-image/${scenes.value[selectedSceneIndex.value].id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  console.log('-----------response--------------');
  console.log(response.data);
  scenes.value[selectedSceneIndex.value].images[selectedSceneImageIndex.value] = response.data.scene_image
}

const handleSceneVideoUpload = async (event) => {
  const video = event.target.files[0];
  const formData = new FormData();
  formData.append('video', video);

  const response = await axios.put(`${route}scenes/upload-video/${scenes.value[selectedSceneIndex.value].id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });

  scenes.value[selectedSceneIndex.value].video_src = response.data.video_url;

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
      if(el.images && el.images.length > 0){
        el.images.forEach(img => {
          if(img.src && !addedSrcs.includes(img.src)){
            result.push({
              name: el.id + '_' + img.time,
              src: img.src
            })
          }
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
  const voiceoverIndex = selectedVoiceoverIndex.value;
  const voiceover = voiceovers.value[selectedVoiceoverIndex.value];
  const voiceoverResponse = await axios.post(`http://localhost:8000/voiceovers/generate/${voiceover.id}`, {
    text: voiceover.text
  });
  voiceovers.value[voiceoverIndex].src = voiceoverResponse.data.src+"?v="+Date.now();
  voiceovers.value[voiceoverIndex].duration = voiceoverResponse.data.duration
  voiceovers.value[voiceoverIndex].timestamps = voiceoverResponse.data.timestamps
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
  selectedSceneImageIndex.value = 0;
  filterSceneImages();
};

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
  selectedVoiceoverIndex.value = voiceovers.value.findIndex(el => el.id == voiceoverId);
  selectedSceneIndex.value = null;
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
/* video {
  transition: opacity 0.1s ease;
} */

</style>