<template>
  <div class="bg-white p-4 rounded-lg shadow-sm mb-4">
    <div class="flex justify-between items-center">
      <h2 class="text-xl font-bold text-gray-700">
        {{ project.name }}
      </h2>
    </div>

    <!-- GENERATING SCENE IMAGE -->
    <modal-container v-if="sceneImagePrompt.scene_id">
      <div class="flex flex-col gap-4">
        <h3>Generate image for scene</h3>
        <button @click="fixImagePrompt" class="bg-blue-500 text-white p-2 font-bold text-sm">AI</button>
        <textarea v-model="sceneImagePrompt.prompt" placeholder="Describe the scene..." class="h-[400px]"></textarea>

        <p>Additional Image</p>
        <input type="file" @change="addedImageToImagePrompt" class="w-full h-full object-cover rounded-md" />
        <div v-if="scenePromptImageUrl" class="mt-2 size-[100px]">
          <img :src="scenePromptImageUrl" alt="Selected Image" class="w-full h-full object-cover rounded-md" />
        </div>

        <button @click="generateSceneImage" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Generate Image</button>
        <button @click="cancelSceneImage" class="bg-gray-300 text-white px-4 py-2 rounded-md hover:bg-blue-700">Cancel</button>        
      </div>
    </modal-container>

    <modal-container v-if="sceneVideoPrompt.scene_id">
      <div class="flex flex-col gap-4">
        <h3>Generate video for scene</h3>
        <button @click="fixVideoPrompt" class="bg-blue-500 text-white p-2 font-bold text-sm">AI</button>
        <textarea v-model="sceneVideoPrompt.prompt" placeholder="Describe the scene..." class="h-[400px]"></textarea>
        <button @click="generateSceneVideo" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Generate Video</button>
        <button @click="cancelSceneVideo" class="bg-gray-300 text-white px-4 py-2 rounded-md hover:bg-blue-700">Cancel</button>
      </div>
    </modal-container>

    <modal-container v-if="typingSceneForm.scene_id">
      <div class="flex flex-col gap-4">
        <h3>Generate video for scene</h3>
        <textarea v-model="typingSceneForm.text" placeholder="Describe the scene..." class="h-[400px]"></textarea>
        <button @click="generateTypingScene" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Generate Typing Scene</button>
        <button @click="typingSceneForm.scene_id = null" class="bg-gray-300 text-white px-4 py-2 rounded-md hover:bg-blue-700">Cancel</button>
      </div>
    </modal-container>

    <div v-if="project.name" class="flex flex-col gap-6 mt-4">
      <div>
        <h3 class="font-bold text-lg">Characters</h3>
        <ul class="flex flex-wrap gap-5">
          <li v-for="character in project.characters" :key="character.id">
            <p class="font-medium">{{ character.name }}</p>
            <div v-if="character.src" class="size-[100px]">
              <img :src="`http://localhost:8000/${character.src}`" alt="Character Image" class="w-full h-full object-cover rounded-md" />
            </div>
            <p v-else class="text-sm text-gray-600">{{ character.description }}</p>
          </li>
        </ul>
      </div>
      <div>
        <h3 class="font-bold text-lg">Scenes</h3>
        <div class="flex gap-4">
          <div class="w-10 rounded-lg bg-green-500">
            <div v-for="x in Math.ceil(projectDuration / 5)" :key="x" class="h-[500px] w-10 border-b border-gray-300 text-xs text-gray-500 relative">
              <span class="absolute bottom-0 text-white w-10 font-bold left-0 text-center">{{ x*5 }}s</span>
            </div>
          </div>
          <ul class="flex-1">
            <li 
              v-for="scene in project.scenes.sort((a, b) => a.scene_number - b.scene_number)" :key="scene.id" :style="`height: ${scene.duration * 100}px`" 
              class="border rounded-md flex justify-between relative gap-4"
            >
              <div class="absolute bottom-0 right-0">
                <button class="bg-gray-500 text-white p-2 rounded-md text-center" @click="showTypingSceneForm(scene.id)">
                  Generate typing scene
                </button>
                <button class="bg-red-500 text-white p-2 rounded-md size-6 flex items-center justify-center" @click="deleteScene(scene.id)">
                  X
                </button>
              </div> 

              <div class="absolute -top-3 left-1/2 -translate-x-1/2 flex flex-col items-center bg-blue-100  z-50">
                <button @click="toggleNewSceneForm(scene.scene_number)" class="h-6 px-2 bg-green-500 text-white rounded-full  absolute z-10">
                  <p class="whitespace-nowrap font-bold">
                    + add scene
                  </p>
                </button>
                <div v-if="newSceneForm.scene_number == scene.scene_number" class="mt-6 p-4 bg-white border rounded-md shadow-lg">
                  <div class="flex gap-5 justify-between">
                    <label for="image_prompt">Image prompt</label>
                    <input v-model="newSceneForm.image_prompt" type="text" id="image_prompt">
                  </div>
                  <div class="flex gap-5 justify-between">
                    <label for="video_prompt">Video prompt</label>
                    <input v-model="newSceneForm.video_prompt" type="text" id="video_prompt">
                  </div>
                  <div class="flex gap-5 justify-between">
                    <label for="duration">Duration</label>
                    <input v-model="newSceneForm.duration" type="number" id="duration">
                  </div>
                  <div class="flex justify-center gap-2">
                    <button @click="addNewScene(scene.scene_number)" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 mt-2">Add Scene</button>
                    <button @click="newSceneForm.scene_number = null" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 mt-2">Cancel</button>
                  </div>

                </div>
              </div>

              <div v-if="scene.image_src || scene.video_src" class="flex gap-1">
                <div v-if="scene.image_src" class="max-h-[50%]">
                  <button @click="openSceneVideoForm(scene.id)" class="bg-blue-600 z-10 text-sm font-bold text-white py-2 w-full text-center" v-if="!scene.video_src">Generate video</button>
                  <div class="relative">
                    <button @click="showAvailableEffects(scene.id)" class="border-blue-600 border-2 z-10 text-sm font-bold py-2 w-full text-center">Add effect</button>
                    <div class="absolute top-0 left-0 z-20 bg-white p-2 border rounded-md w-full" v-if="showEffects[scene.id]">
                      <p>Choose effect</p>
                      <div class="flex flex-col gap-2 *:bg-gray-100 *:rounded-md *:p-2 mt-4">
                        <button @click="generateSceneWithEffect(scene.id, 'zoom_in')" class="hover:bg-gray-200">Zoom</button>
                        <button @click="generateSceneWithEffect(scene.id, 'pan')" class="hover:bg-gray-200">Pan</button>
                        <button @click="generateSceneWithEffect(scene.id, 'fade')" class="hover:bg-gray-200">Fade</button>
                      </div>
                      <button @click="cancelAvailableEffect(scene.id)" class="bg-gray-300 text-white px-4 py-2 rounded-md hover:bg-blue-700 mt-4 w-full">Cancel</button>
                    </div>
                  </div>
                  <button @click="openSceneImageForm(scene.id)" class="border-blue-600 border-2 z-10 text-sm font-bold py-2 w-full text-center">Regenerate image</button>
                  <div class="w-[200px] h-auto min-w-[200px] rounded-lg overflow-hidden">
                    <img 
                      :src="`http://localhost:8000/${scene.image_src}?v=${version}`" 
                      alt="Scene Image" class="w-full h-full object-cover rounded-md border zoomable-img" 
                      :data-zoom-src="`http://localhost:8000/${scene.image_src}?v=${version}`"
                      data-zoomable
                      
                    />
                  </div>
                </div>
  
                <div v-if="scene.video_src" class="max-h-[50%]">
                  <button @click="openSceneVideoForm(scene.id)" class="bg-blue-600 z-10 text-sm font-bold text-white py-2 w-full text-center">Regenerate video</button>
                  <div class="w-[200px] h-auto min-w-[200px] rounded-lg">
                    <video controls :src="`http://localhost:8000/${scene.video_src}?v=${version}`" alt="Scene Video" class="w-full h-full object-cover rounded-md border" />
                  </div>
                </div>
              </div>
              
              <div v-else class="w-[200px] h-[100px] min-w-[200px] bg-gray-200 rounded-lg flex flex-col justify-center items-center gap-3">
                <button @click="openSceneImageForm(scene.id)" class="bg-blue-600 rounded-lg text-sm font-bold text-white py-2 w-full">Generate image</button>
                <input type="file" alt="Scene Image" @change="setSceneImage(scene.id, $event)" class="w-full h-full object-cover rounded-md" />
              </div>
              <div class="flex flex-col gap-4">
                <p class="text-sm text-gray-600">{{ scene.image_prompt }}</p>
                <p class="text-sm text-gray-600">{{ scene.video_prompt }}</p>
                <ul class="flex gap-2">
                  <div v-for="character in scene.characters" :key="character.id" class="mt-2 p-2 rounded-md bg-gray-200">
                    <p class="text-sm text-gray-800">{{ character.name }}</p>
                  </div>
                </ul>
                <button @click="showCharactersToAdd = scene.id" v-if="showCharactersToAdd != scene.id" class="bg-blue-600 text-white rounded-md px-2 py-1">Add characters</button>
                <ul v-if="showCharactersToAdd === scene.id" class="flex gap-2">
                  <div v-for="character in project.characters.filter(c => !scene.characters.some(sc => sc.id === c.id))" :key="character.id" class="mt-2 p-2 rounded-md bg-gray-200">
                    <p class="text-sm text-gray-800">{{ character.name }}</p>
                    <button @click="addCharacterToScene(scene.id, character.id)" class="bg-blue-600 text-white rounded-md px-2 py-1">Add</button>
                  </div>
                </ul>
              </div>
            </li>
          </ul>

          <div class="w-[400px] rounded-lg flex flex-col relative" ref="timelineRef">
            <div
              v-for="voiceover in project.voiceovers"
              :key="voiceover.id"
              class="border absolute w-full left-0 voiceover-container"
              :style="`height: ${Math.max(voiceover.duration * 100, 100)}px; top: ${voiceover.start_time * 100}px;`"
              ref="voiceoverRefs"
            >
              <p>{{ voiceover.text }}</p>
              <button @click="generateVoiceover(voiceover.id)" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Generate</button>
              <audio v-if="voiceover.src" :src="`http://localhost:8000/${voiceover.src}`" controls class="w-full mt-2"></audio>
            </div>
          </div>
        </div>
      </div>
      <div>
        <!-- DOWNLOAD BUTTON -->
        <button class="bg-blue-500 rounded-md p-2" @click="downloadVideo">
          Download Video
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.voiceover-container {
  position: absolute;
  width: 100%;
  background-color: lightblue;
  border: 1px solid blue;
  cursor: grab;
  user-select: none;
  transition: top 0.1s ease-out; /* Smooth movement */
}

.voiceover-container.dragging {
  cursor: grabbing;
  opacity: 0.8;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Visual feedback */
}
</style>

<script setup>

  import { ref, onMounted, computed, reactive, onUnmounted, nextTick } from 'vue';
  import ModalContainer from './ModalContainer.vue';
  import axios from 'axios'
  import mediumZoom from 'medium-zoom'

  const project = ref({});
  const timelineRef = ref(null);
  const voiceoverRefs = ref([]);

  // Triggering images to update
  const version = ref(0);
  let zoom = null;

  const projectDuration = computed(()=>{
    if (!project.value.scenes) return 0;
    return project.value.scenes.reduce((total, scene) => total + scene.duration, 0);
  })

  // TYPING SCENE
  const typingSceneForm = reactive({
    scene_id: null,
    text: '',
  })

  const showTypingSceneForm = (sceneId) => {
    typingSceneForm.scene_id = sceneId;
    const scene = project.value.scenes.find(s => s.id === sceneId);
    typingSceneForm.text = scene ? scene.video_prompt : '';
  }

  const generateTypingScene = async () => {
    await axios.post(`http://localhost:8000/scenes/generate-typing-scene/${typingSceneForm.scene_id}`, {
        text: typingSceneForm.text
      })
      .then(res => {
        console.log('Typing scene generated:', res.data);
        const scene = project.value.scenes.find(s => s.id === typingSceneForm.scene_id);
        if (scene) {
          scene.video_src = res.data.video_url;
        }
        typingSceneForm.scene_id = null; // Close the form
      })
    ;
  }

  // DELETE SCENE
  const deleteScene = async (sceneId) => {
    await axios.delete(`http://localhost:8000/scenes/${sceneId}`);
    project.value.scenes = project.value.scenes.filter(scene => scene.id !== sceneId);
  }

  // NEW SCENE FORM
  const newSceneForm = reactive({
    scene_number: null,
    image_prompt: '',
    video_prompt: '',
    duration: 5,
  })

  const addNewScene = async () => {
    // add + 1 to all scenes with scene_number >= newSceneForm.scene_number
    project.value.scenes.forEach(scene => {
      if (scene.scene_number >= newSceneForm.scene_number) {
        scene.scene_number += 1;
      }
    });

    const newSceneResponse = await axios.post(`http://localhost:8000/projects/add-scene/${project.value.id}`, {
      project_id: project.value.id,
      scene_number: newSceneForm.scene_number,
      image_prompt: newSceneForm.image_prompt,
      video_prompt: newSceneForm.video_prompt,
      duration: newSceneForm.duration,
    });
    console.log(newSceneResponse.data);
    project.value.scenes.push(newSceneResponse.data.scene);
  }

  const toggleNewSceneForm = (scene_number) => {
    // Add new scene with form values to be the index of the project - imporatant - do not overwrite existing scenes - just add one to the given index
    if (newSceneForm.scene_number === scene_number) {
      // If the form is already open for this scene, close it
      newSceneForm.scene_number = null;
      return;
    } else {
      newSceneForm.scene_number = scene_number;
      newSceneForm.image_prompt = '';
      newSceneForm.video_prompt = '';
      newSceneForm.duration = 5;
    }
  }

  // DRAGGABLE VOICEOVERS
  function useVerticalDraggable(elementRef, voiceover, options = {}) {
  const { onDragStart, onDrag, onDragEnd } = options;
  let isDragging = false;
  let startY = 0;
  let initialTop = 0;

  const handlePointerDown = (event) => {
    if (event.button !== 0) return; // Only left click
    console.log(`Pointer down on voiceover ${voiceover.id}`); // Debug log
    event.preventDefault(); // Prevent text selection
    isDragging = true;
    startY = event.clientY;
    initialTop = parseFloat(getComputedStyle(elementRef).top) || 0;
    elementRef.classList.add('dragging');
    document.addEventListener('pointermove', handlePointerMove);
    document.addEventListener('pointerup', handlePointerUp);
    onDragStart?.(event, voiceover);
  };

  const handlePointerMove = (event) => {
    if (!isDragging) return;
    const deltaY = event.clientY - startY;
    let newTop = initialTop + deltaY;

    // Snap to grid (0.1s increments, assuming 100px = 1s)
    const timeScale = 100; // Pixels per second
    const snapInterval = 10; // Snap to 0.1s (10px)
    newTop = Math.round(newTop / snapInterval) * snapInterval;

    // Constrain within timeline bounds
    const maxTop = (projectDuration.value - voiceover.duration) * timeScale;
    newTop = Math.max(0, Math.min(newTop, maxTop));

    elementRef.style.top = `${newTop}px`;
    onDrag?.(newTop, event, voiceover);
  };

  const handlePointerUp = (event) => {
    if (!isDragging) return;
    console.log(`Pointer up on voiceover ${voiceover.id}`); // Debug log
    isDragging = false;
    elementRef.classList.remove('dragging');
    document.removeEventListener('pointermove', handlePointerMove);
    document.removeEventListener('pointerup', handlePointerUp);

    const timeScale = 100; // Pixels per second
    const newTop = parseFloat(elementRef.style.top) || 0;
    const newStartTime = newTop / timeScale;

    // Update voiceover start_time
    voiceover.start_time = Math.max(0, newStartTime);
    onDragEnd?.(newTop, event, voiceover);
  };

  // Attach event listener
  console.log(`Attaching pointerdown listener to voiceover ${voiceover.id}`); // Debug log
  elementRef.addEventListener('pointerdown', handlePointerDown);

  // Return cleanup function
  return () => {
    console.log(`Cleaning up pointerdown listener for voiceover ${voiceover.id}`); // Debug log
    elementRef.removeEventListener('pointerdown', handlePointerDown);
    document.removeEventListener('pointermove', handlePointerMove);
    document.removeEventListener('pointerup', handlePointerUp);
  };
}

// Function to make voiceovers draggable
function makeVoiceoversDraggable() {
  console.log('makeVoiceoversDraggable called'); // Debug log
  console.log('voiceoverRefs:', voiceoverRefs.value); // Debug log
  const cleanupFunctions = [];
  voiceoverRefs.value.forEach((el, index) => {
    if (!el) {
      console.warn(`No element found for voiceover at index ${index}`); // Debug log
      return;
    }
    const voiceover = project.value.voiceovers[index];
    if (!voiceover) {
      console.warn(`No voiceover data found for index ${index}`); // Debug log
      return;
    }
    console.log(`Making voiceover ${voiceover.id} draggable`); // Debug log
    const cleanup = useVerticalDraggable(el, voiceover, {
      onDragStart: (event, voiceover) => {
        console.log(`Dragging started for voiceover ${voiceover.id}`);
      },
      onDrag: (newTop, event, voiceover) => {
        const timeScale = 100;
        const currentTime = newTop / timeScale;
        console.log(`Dragging voiceover ${voiceover.id} to ${currentTime.toFixed(2)}s`);
      },
      onDragEnd: (newTop, event, voiceover) => {
        console.log(`Dropped voiceover ${voiceover.id} at ${voiceover.start_time.toFixed(2)}s`);
        // Persist the new start_time to the backend
        axios
          .post(
            `http://localhost:8000/voiceovers/${voiceover.id}`,
            { start_time: voiceover.start_time },
            { headers: { 'Content-Type': 'application/json' } }
          )
          .then(() => console.log('Voiceover position updated'))
          .catch((error) => console.error('Error updating voiceover:', error));
      },
    });
    cleanupFunctions.push(cleanup);
  });

  // Cleanup on unmount
  onUnmounted(() => {
    console.log('Cleaning up voiceover draggable listeners'); // Debug log
    cleanupFunctions.forEach((cleanup) => cleanup());
  });
}

onMounted(async () => {
  const projectId = window.location.pathname.split('/').pop();
  const response = await fetch(`http://localhost:8000/projects/${projectId}`);
  project.value = await response.json();
  console.log('Project loaded:', project.value); // Debug log

  // Wait for the next tick to ensure DOM is updated with voiceover elements
  await nextTick();
  console.log('voiceoverRefs after nextTick:', voiceoverRefs.value); // Debug log
  makeVoiceoversDraggable();

  setTimeout(() => {
    if (zoom) {
      zoom.detach();
    }
    zoom = mediumZoom('[data-zoomable]');
    zoom.on('open', () => {
      console.log('Image expanded');
    });
  }, 1000);
});



  // DOWNLOAD VIDEO
  const downloadVideo = async () => {
    const projectId = project.value.id;
    try {
      const response = await axios.post(`http://localhost:8000/projects/download/${projectId}`, {
        responseType: 'blob', // Important for downloading files
      });
      // Create a URL for the blob
      const url = window.URL.createObjectURL(new Blob([response.data]));
      // Create a link element
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `project_${projectId}_video.mp4`); // Set the file name
      // Append to the document and trigger the download
      document.body.appendChild(link);
      link.click();
      // Clean up
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading video:', error);
    }
  }

  // SCENE EFFECTS
  const showEffects = ref({});
  const showAvailableEffects = (sceneId) => {
    showEffects.value[sceneId] = true;
  }
  const cancelAvailableEffect = (sceneId) => {
    showEffects.value[sceneId] = false;
  }

  // ADJUSTING SCENE CHARACTERS
  const showCharactersToAdd = ref(null);

  const addCharacterToScene = (sceneId, characterId) => {
    const scene = project.value.scenes.find(s => s.id === sceneId);
    const character = project.value.characters.find(c => c.id === characterId);
    if (scene && character && !scene.characters.some(c => c.id === characterId)) {
      scene.characters.push(character);
    }
    axios.post(`http://localhost:8000/scenes/add-character-to-scene`, {
      scene_id: sceneId,
      character_id: characterId,
    });
    
  }

  // VOICEOVER GENERATION
  const generateVoiceover = async (voiceoverId) => {
    const voiceover = project.value.voiceovers.find(v => v.id === voiceoverId);
    if (!voiceover) return;
    try {
      const response = await axios.post(`http://localhost:8000/voiceovers/generate-voiceover/${voiceoverId}`);
      const data = response.data;
      console.log('Voiceover generation response:', data);
      // Update the project data with the new voiceover src
      voiceover.src = data.voiceover_src; // Assuming the backend returns the voiceover URL in 'voiceover_url'
      voiceover.duration = data.duration; // Update duration if provided
    } catch (error) {
      console.error('Error generating voiceover:', error.response?.data || error.message);
    }
  }

  // SCENE IMAGE DEFINITION
  const setSceneImage = async (sceneId, event) => {
    const file = event.target.files[0];
    if (!file) return;
    const scene = project.value.scenes.find(s => s.id === sceneId);
    if (scene) {
      scene.src = URL.createObjectURL(file);
      const formData = new FormData();
      formData.append('image', file);
      await axios.post(`http://localhost:8000/scenes/upload-scene-image/${sceneId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      console.log('Uploaded image for scene:', sceneId);
    }
  }

  // SCENE IMAGE EFFECTS

  const generateSceneWithEffect = async (sceneId, effect) => {
    console.log('Generating scene with effect:', sceneId, effect);
    try {
      const response = await axios.post(`http://localhost:8000/scenes/add-effect-to-image/${sceneId}`, {
        effect: effect,
      });
      const data = response.data;
      console.log('Scene effect generation response:', data);
      // Update the project data with the new image
      const scene = project.value.scenes.find(s => s.id === sceneId);
      if (scene) {
        scene.image_src = data.image_url; // Assuming the backend returns the image URL in 'image_url'
      }
    } catch (error) {
      console.error('Error generating scene with effect:', error.response?.data || error.message);
    }
  }

  // SCENE IMAGE GENERATION
  const sceneImagePrompt = reactive({
    prompt: '',
    scene_id: null,
    character_ids: [],
    image: null,
  })

  const sceneVideoPrompt = reactive({
    video_prompt: '',
    scene_id: null,
  })

  const addedImageToImagePrompt = (event) => {
    const file = event.target.files[0];
    if (file) {
      sceneImagePrompt.image = file;
    }
  }
  const cancelSceneImage = () => {
    sceneImagePrompt.scene_id = null;
    sceneImagePrompt.prompt = '';
    sceneImagePrompt.character_ids = [];
    sceneImagePrompt.image = null;
  }
  const openSceneImageForm = (sceneId) => {
    const scene = project.value.scenes.find(s => s.id === sceneId);
    if (!scene) return;
    sceneImagePrompt.scene_id = sceneId;
    sceneImagePrompt.prompt = scene.image_prompt;
    sceneImagePrompt.character_ids = scene.characters.map(c => c.id);
    console.log('Opening image form for scene:', sceneId);
  }

  const scenePromptImageUrl = computed(() => {
    if (sceneImagePrompt.image) {
      return URL.createObjectURL(sceneImagePrompt.image);
    }
    return null;
  });

  // GENERATING VIDEO FOR SCENE
  const openSceneVideoForm = (sceneId) => {
    const scene = project.value.scenes.find(s => s.id === sceneId);
    if (!scene) return;
    sceneVideoPrompt.scene_id = sceneId;
    sceneVideoPrompt.prompt = scene.video_prompt;
    console.log('Opening video form for scene:', sceneId);
  }

  const generateSceneVideo = async () => {
    console.log('Generating video for scene:', sceneVideoPrompt);
    try {
      // Reset the form

      const response = await axios.post(`http://localhost:8000/scenes/generate-scene-video/${sceneVideoPrompt.scene_id}`, {
        prompt: sceneVideoPrompt.prompt,
      });
      cancelSceneVideo();

      const data = response.data;
      console.log('Video generation response:', data);
      // Update the project data with the new video (if applicable)
      const scene = project.value.scenes.find(s => s.id === sceneVideoPrompt.scene_id);
      if (scene) {
        scene.video_src = data.video_url; // Assuming the backend returns the video URL in 'video_url'
      }

      alert('Video generation started. It may take a few minutes to complete. Please refresh the page after some time to see the updated video.');

    } catch (error) {
      console.error('Error generating scene video:', error.response?.data || error.message);
    }
  }

  const cancelSceneVideo = () => {
    sceneVideoPrompt.scene_id = null;
    sceneVideoPrompt.prompt = '';
  }


  const fixVideoPrompt = async () => {
    try {
      console.log(sceneVideoPrompt.prompt);
      console.log('Sending request with body:', { prompt: sceneVideoPrompt.prompt });
      // const scene = project.value.scenes.find(s => s.id === sceneVideoPrompt.scene_id);
      
      const response = await axios
        .post('http://localhost:8000/generators/fix-scene-video-prompt', { 

          prompt: sceneVideoPrompt.prompt,
        })
        .catch((error) => {
          console.error('Error response from server:', error.response ? error.response.data : error.message);
          throw error; // Re-throw the error after logging it
        })
      ;
      sceneVideoPrompt.prompt = response.data.fixed_prompt;
      console.log('Scene video prompt fixed:', sceneVideoPrompt.prompt);
    } catch (error) {
      console.error('Error fixing scene video prompt:', error);
    }
  }

  const fixImagePrompt = async () => {
    try {
      console.log(sceneImagePrompt.prompt);
      console.log('Sending request with body:', { prompt: sceneImagePrompt.prompt });
      const response = await axios
        .post('http://localhost:8000/generators/fix-scene-image-prompt', { 
          prompt: sceneImagePrompt.prompt,
        })
        .catch((error) => {
          console.error('Error response from server:', error.response ? error.response.data : error.message);
          throw error; // Re-throw the error after logging it
        })
      ;
      sceneImagePrompt.prompt = response.data.fixed_prompt;
      console.log('Scene image prompt fixed:', sceneImagePrompt.prompt);
    } catch (error) {
      console.error('Error fixing scene image prompt:', error);
    }
  }


  const generateSceneImage = async () => {
    console.log('Generating image for scene:', sceneImagePrompt);
    try {

      const formData = new FormData();
      formData.append('name', sceneImagePrompt.name);
      formData.append('prompt', sceneImagePrompt.prompt);
      if (sceneImagePrompt.image){
        formData.append('image', sceneImagePrompt.image);
      }
      if (sceneImagePrompt.character_ids && sceneImagePrompt.character_ids.length > 0) {
          // Append each character_id individually
          sceneImagePrompt.character_ids.forEach(id => {
              formData.append('character_ids', id);
          });
      }

      const response = await axios.post(`http://localhost:8000/scenes/generate-scene-image/${sceneImagePrompt.scene_id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const data = response.data;
      console.log('Image generation response:', data);
      // Update the project data with the new image
      const scene = project.value.scenes.find(s => s.id === sceneImagePrompt.scene_id);
      if (scene) {
        scene.image_src = data.image_url; // Assuming the backend returns the image URL in 'image_url'
        scene.image_prompt = sceneImagePrompt.prompt;
      }
      // Reset the form
      cancelSceneImage();
    } catch (error) {
      console.error('Error generating scene image:', error.response?.data || error.message);
    }
  }



  onUnmounted(() => {
    // Clean up to avoid memory leaks
    if (zoom) {
      zoom.detach()
    }
  })

</script>

<style scoped>
.zoomable-img {
  max-width: 100%;
  height: auto;
  cursor: zoom-in;
}
</style>