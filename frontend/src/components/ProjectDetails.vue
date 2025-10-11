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
        <textarea v-model="sceneVideoPrompt.prompt" placeholder="Describe the scene..." class="h-[400px]"></textarea>
        <button @click="generateSceneVideo" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">Generate Video</button>
        <button @click="cancelSceneVideo" class="bg-gray-300 text-white px-4 py-2 rounded-md hover:bg-blue-700">Cancel</button>
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
              v-for="scene in project.scenes" :key="scene.id" :style="`height: ${scene.duration * 100}px`" 
              class="border rounded-md flex justify-between relative gap-4"
            >
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
                      :src="`http://localhost:8000/${scene.image_src}?v=${Date.now()}`" 
                      alt="Scene Image" class="w-full h-full object-cover rounded-md border zoomable-img" 
                      :data-zoom-src="`http://localhost:8000/${scene.image_src}?v=${Date.now()}`"
                      data-zoomable
                      
                    />
                  </div>
                </div>
  
                <div v-if="scene.video_src" class="max-h-[50%]">
                  <button @click="openSceneVideoForm(scene.id)" class="bg-blue-600 z-10 text-sm font-bold text-white py-2 w-full text-center">Regenerate video</button>
                  <div class="w-[200px] h-auto min-w-[200px] rounded-lg">
                    <video controls :src="`http://localhost:8000/${scene.video_src}?v=${Date.now()}`" alt="Scene Video" class="w-full h-full object-cover rounded-md border" />
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

          <div class="w-[600px] rounded-lg flex flex-col relative" ref="timelineRef">
            <div 
              v-for="voiceover in project.voiceovers" 
              :key="voiceover.id" 
              class="border absolute w-full left-0 voiceover-container" 
              :style="`height: ${voiceover.duration * 100}px; top: ${voiceover.start_time * 100}px;`"
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
  background-color: lightblue; /* Adjust for better visibility */
  border: 1px solid blue;
  cursor: grab;
  user-select: none; /* Prevent text selection during drag */
}

.voiceover-container.dragging {
  cursor: grabbing;
  opacity: 0.8;
}
</style>

<script setup>

  import { ref, onMounted, computed, reactive, onUnmounted } from 'vue';
  import ModalContainer from './ModalContainer.vue';
  import axios from 'axios'
  import mediumZoom from 'medium-zoom'

  const project = ref({});

  const projectDuration = computed(()=>{
    if (!project.value.scenes) return 0;
    return project.value.scenes.reduce((total, scene) => total + scene.duration, 0);
  })


  // DRAGGABLE VOICEOVERS
  const voiceoverRefs = ref([]);

  function useVerticalDraggable(elementRef, { onDragStart, onDrag, onDragEnd }) {
    let isDragging = false;
    let startY = 0;
    let initialTop = 0;

    const handlePointerDown = (event) => {
      if (event.button !== 0) return; // Only left click
      isDragging = true;
      startY = event.clientY;
      initialTop = parseFloat(getComputedStyle(elementRef.value).top) || 0;
      document.addEventListener('pointermove', handlePointerMove);
      document.addEventListener('pointerup', handlePointerUp);
      onDragStart?.(event);
    };

    const handlePointerMove = (event) => {
      if (!isDragging) return;
      const deltaY = event.clientY - startY;
      const newTop = initialTop + deltaY;
      elementRef.value.style.top = `${newTop}px`; // Smooth drag
      onDrag?.(deltaY, event);
    };

    const handlePointerUp = (event) => {
      if (!isDragging) return;
      isDragging = false;
      document.removeEventListener('pointermove', handlePointerMove);
      document.removeEventListener('pointerup', handlePointerUp);
      const deltaY = event.clientY - startY;
      onDragEnd?.(deltaY, event);
    };

    // Attach event listener
    if (elementRef.value) {
      elementRef.value.addEventListener('pointerdown', handlePointerDown);
    }

    return { isDragging };
  }

  // Function to make voiceovers draggable
  function makeVoiceoversDraggable() {
    voiceoverRefs.value.forEach((el, index) => {
      if (!el) return;
      useVerticalDraggable(ref(el), {
        onDragStart: () => {
          el.classList.add('dragging');
        },
        onDrag: () => {
          // Optional: Live feedback during drag
        },
        onDragEnd: (deltaY) => {
          el.classList.remove('dragging');
          const timeScale = 100; // Pixels per second (100px = 1s, matching template)
          const timeDelta = deltaY / timeScale; // Convert pixels to seconds
          const newStartTime = project.value.voiceovers[index].start_time + timeDelta;

          // Update start_time with constraint
          project.value.voiceovers[index].start_time = Math.max(0, newStartTime); // Prevent negative start_time
          // Optional: Add additional constraints, e.g., prevent overlaps or cap at project duration
        }
      });
    });
  }

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
    prompt: '',
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
    sceneImagePrompt.prompt = scene.image_prompt + '\nImportant: The final image/scene should reflect the realm of the characters. If the characters are cartoonish, the environment should also be in a cartoonish style. The goal is for the scene and characters to feel like they naturally belong together, in the same artistic world.';
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


  const fixImagePrompt = async () => {
    try {
      console.log(sceneImagePrompt.prompt);
      console.log('Sending request with body:', { prompt: sceneImagePrompt.prompt });
      const response = await axios.post('http://localhost:8000/generators/fix-scene-image-prompt', { 
        prompt: sceneImagePrompt.prompt,
      });
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


  let zoom = null
  onMounted(async () => {
    const projectId = window.location.pathname.split('/').pop();
    const response = await fetch(`http://localhost:8000/projects/${projectId}`);
    project.value = await response.json();
    makeVoiceoversDraggable();

    setTimeout(() => {
      if (zoom) {
        zoom.detach()
      }
      zoom = mediumZoom('[data-zoomable]')
      zoom.on('open', () => {
        console.log('Image expanded')
      })
    }, 1000)

    console.log(project.value);
  }); 

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