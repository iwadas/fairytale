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
        <div class="relative min-w-[270px] bg-gray-900 rounded-lg overflow-hidden">
          <video
            ref="videoEl"
            controls
            width="270"
            height="480"
            @timeupdate="onTimeUpdate"
          ></video>

          <!-- Hidden audio for voiceovers -->
          <audio ref="audioEl" @timeupdate="onAudioTimeUpdate"></audio>

          <div class="flex flex-col gap-2 text-white">
            <form-button @clicked="togglePlay" :label="isPlaying ? 'Pause' : 'Play'"/>
            <form-button @clicked="reset" label="Reset"/>
            <span ckass="text-center">Time: {{ currentTime.toFixed(2) }}s</span>
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
        </div>
      </div>

      <!-- 2. Voiceover selected (scene ignored) -->
      
    </div>

    <!-- Timeline Section -->
    <div class="timeline bg-gray-900 rounded-lg p-4" ref="containerRef"> 
      <div class="overflow-x-auto relative">
        <div class="relative" :style="{ width: `${totalWidth}px`, minWidth: '100%' }">
          <!-- Timeline Background with Time Markers -->
          <div class="absolute top-0 left-0 w-full h-full bg-gray-800 rounded">
            <!-- Time Markers -->
            <div class="flex text-xs text-gray-400 mt-2">
              <span v-for="tick in timeTicks" :key="tick" class="absolute" :style="{ left: `${tick * pixelsPerSecond}px` }">
                {{ formatTime(tick) }}
              </span>
            </div>
          </div>

          <!-- Scenes Track -->
          <div class="relative h-40" ref="scenesTrack">
            <div
              v-for="(scene, index) in scenes"
              :key="scene.id"
              class="absolute h-full mt-8 bg-blue-500 rounded cursor-move select-none border"
              :style="{
                left: `${scene.start_time * pixelsPerSecond}px`,
                width: `${scene.duration * pixelsPerSecond}px`,
              }"
              @mousedown="startDragging($event, 'scene', scene, index, $refs.scenesTrack)"
              @click="selectScene(scene.id)"
            >
              <span class="text-xs text-white">{{ scene.image_prompt }}</span>
            </div>
          </div>

          <!-- Voiceovers Track -->
          <div class="relative h-20 mt-4" ref="voiceoversTrack">
            <div
              v-for="(voiceover, index) in voiceovers"
              :key="voiceover.id"
              class="absolute h-full mt-6 p-2 bg-green-500 rounded cursor-move select-none"
              :style="{
                left: `${voiceover.start_time * pixelsPerSecond}px`,
                width: `${voiceover.duration * pixelsPerSecond}px`,
              }"
              @mousedown="startDragging($event, 'voiceover', voiceover, index, $refs.voiceoversTrack)"
              @click="selectVoiceover(voiceover.id)"
            >
              <span class="text-xs text-white truncate" :style="`max-width: ${voiceover.duration * pixelsPerSecond}px`">{{ voiceover.text }} </span>
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
import ReferenceImage from './ReferenceImage.vue'
import getSrc from '../utils/getSrc.js'


const route = 'http://localhost:8000/'
let projectId = null;

const scenes = ref([]);
const voiceovers = ref([]);
const characters = ref([]);

const timelineDuration = 200; // Total duration of the timeline in seconds (adjust as needed)
const pixelsPerSecond = ref(50); // 100px per second
const totalWidth = computed(()=>{
  return timelineDuration * pixelsPerSecond.value;
});


const selectedSceneIndex = ref(null);
const selectedVoiceoverIndex = ref(null);
const generateImageLowkey = ref(true);


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


// TODO
// TODO
// TODO
// PREVIEW LOGIC
// Preview refs & state
const videoEl = ref(null)
const audioEl = ref(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const rafId = ref(null)

// Loading states (optional for UI feedback)
const videoLoading = ref(false)
const audioLoading = ref(false)

// Performance tracking
let playbackStartTime = 0
let playbackStartTimestamp = 0

// Throttling: prevent source change spam
const LAST_CHANGE_THRESHOLD = 0.05 // 50ms
let lastVideoChange = -1000
let lastAudioChange = -1000

// ================ ACTIVE ITEMS ================
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

// ================ SAFE SOURCE SETTERS ================
const setVideoSource = async (src, offset = 0) => {
  const now = currentTime.value
  if (now - lastVideoChange < LAST_CHANGE_THRESHOLD) {
    videoEl.value.currentTime = offset
    return
  }

  const fullSrc = (route + src).replaceAll("\\", "/")

  // Same source? Just seek
  if (videoEl.value.src === fullSrc && !videoLoading.value) {
    videoEl.value.currentTime = offset
    return
  }

  lastVideoChange = now
  videoLoading.value = true

  // Pause first to avoid playback during load
  videoEl.value.pause()

  try {
    videoEl.value.src = fullSrc
    videoEl.value.currentTime = offset
    await videoEl.value.load()

    // Wait for canplaybefore playing
    if (isPlaying.value) {
      await videoEl.value.play().catch(() => {}) // ignore user gesture errors
    }
  } catch (err) {
    if (err.name !== 'AbortError') {
      console.error('Video load error:', err)
    }
  } finally {
    videoLoading.value = false
  }
}

const setAudioSource = async (src, offset = 0) => {
  const now = currentTime.value
  if (now - lastAudioChange < LAST_CHANGE_THRESHOLD) {
    audioEl.value.currentTime = offset
    return
  }

  const fullSrc = (route + src).replaceAll("\\", "/")

  if (audioEl.value.src === fullSrc && !audioLoading.value) {
    audioEl.value.currentTime = offset
    return
  }

  lastAudioChange = now
  audioLoading.value = true

  audioEl.value.pause()
  try {
    audioEl.value.src = fullSrc
    audioEl.value.currentTime = offset
    await audioEl.value.load()

    if (isPlaying.value) {
      await audioEl.value.play().catch(() => {})
    }
  } catch (err) {
    if (err.name !== 'AbortError') console.error('Audio load error:', err)
  } finally {
    audioLoading.value = false
  }
}

// Clear sources when no media
const clearVideo = () => {
  videoEl.value.pause()
  videoEl.value.removeAttribute('src')
  videoEl.value.load()
}

const clearAudio = () => {
  audioEl.value.pause()
  audioEl.value.removeAttribute('src')
  audioEl.value.load()
}

// ================ UPDATE SOURCES ================
const updateSourcesAtTime = async (time) => {
  const scene = activeScene.value
  const vo = activeVoiceover.value

  // Video
  if (scene) {
    await setVideoSource(scene.video_src, time - scene.start_time)
  } else if (videoEl.value.src) {
    clearVideo()
  }

  // Audio
  if (vo) {
    await setAudioSource(vo.src, time - vo.start_time)
  } else if (audioEl.value.src) {
    clearAudio()
  }
}

let previousActiveScene = null
let previousActiveVoiceover = null
// ================ PLAYBACK LOOP (RAF) ================
const tick = () => {
  if (!isPlaying.value) return

  const now = performance.now()
  const elapsed = (now - playbackStartTimestamp) / 1000
  currentTime.value = playbackStartTime + elapsed

  const time = currentTime.value
  const scene = activeScene.value
  const vo = activeVoiceover.value

  let shouldUpdate = false

  // 1. Always check if voiceover changed (most important!)
  const prevVo = previousActiveVoiceover // we'll track this below
  if (vo !== prevVo) {
    shouldUpdate = true
  }

  // 2. Scene change detection
  const prevScene = previousActiveScene
  if (scene !== prevScene) {
    shouldUpdate = true
  }

  // 3. Near boundary fallback (for safety)
  if (scene) {
    const localTime = time - scene.start_time
    const nearEnd = scene.duration - localTime < 0.15
    const nearStart = localTime < 0.1
    if (nearEnd || nearStart) shouldUpdate = true
  }

  // 4. Drift correction
  if (scene && Math.abs(videoEl.value.currentTime - (time - scene.start_time)) > 0.15) {
    shouldUpdate = true
  }

  if (shouldUpdate) {
    updateSourcesAtTime(time)
  }

  // Store for next frame
  previousActiveScene = scene
  previousActiveVoiceover = vo

  rafId.value = requestAnimationFrame(tick)
}
// ================ CONTROLS ================
const play = async () => {
  if (isPlaying.value) return

  playbackStartTime = currentTime.value
  playbackStartTimestamp = performance.now()

  isPlaying.value = true

  // Start both if possible
  const videoPlay = videoEl.value.src ? videoEl.value.play() : null
  const audioPlay = audioEl.value.src ? audioEl.value.play() : null

  await Promise.allSettled([videoPlay, audioPlay].filter(Boolean))
  rafId.value = requestAnimationFrame(tick)
}

const pause = () => {
  if (!isPlaying.value) return

  isPlaying.value = false
  videoEl.value.pause()
  audioEl.value.pause()

  if (rafId.value) {
    cancelAnimationFrame(rafId.value)
    rafId.value = null
  }
}

const togglePlay = () => {
  isPlaying.value ? pause() : play()
}

const seekTo = async (time) => {
  currentTime.value = Math.max(0, time)
  pause()
  await updateSourcesAtTime(currentTime.value)

  // Sync playback start point
  playbackStartTime = currentTime.value
  playbackStartTimestamp = performance.now()
}

const reset = () => {
  seekTo(0)
}

// ================ EVENT LISTENERS ================
// Attach events
// ================ LIFECYCLE ================
onBeforeUnmount(() => {
  pause()
  if (rafId.value) cancelAnimationFrame(rafId.value)
})

onMounted(()=>{
  setTimeout(()=>{
    updateSourcesAtTime(0)
  }, 1000)
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
const timeTicks = Array.from({ length: Math.ceil(timelineDuration / 10) + 1 }, (_, i) => i * 10);

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
  updateSourcesAtTime(0)

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

</style>