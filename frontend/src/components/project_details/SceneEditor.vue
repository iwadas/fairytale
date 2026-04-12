<template>

  <div>
    <modal v-if="newImagePromptForm.scene_id && newImagePromptForm.full_voiceover_text">
      <div class="flex flex-col gap-4 text-xs text-light">
        
        <div class="flex justify-between">
          <h2 class="text-2xl">
            <font-awesome-icon icon="rotate-right" class="text-base text-primary"/>
            Regenerate prompt
          </h2>
          <form-button label="Cancel" class="w-fit" button_type="secondary" @clicked="newImagePromptForm.scene_id = null"/>
        </div>
        
        <div>
          <p class="text-sm">
            Select the part of the scene description that you want to regenerate.
          </p>
          <p>
            <span class="mr-2">
              Set: 
            </span>
            <span v-if="settingWordForStart" class="text-primary font-bold">
              Start
              <font-awesome-icon icon="caret-right"/>
            </span>
            <span v-else class="text-primary font-bold">
              End
              <font-awesome-icon icon="caret-left"/>
            </span>
          </p>
          <div class="flex gap-1 flex-wrap mt-3">
            <p v-for="(word, idx) in newImagePromptForm.full_voiceover_text.split(' ')" :key="`${idx}-word`" class="relative cursor-pointer rounded-sm button-secondary overflow-hidden flex items-center" @click="setWordForImageGeneration(idx)">
              <span class="p-0.5">
                {{ word }}
              </span>
              <font-awesome-icon icon="caret-right" v-if="idx == newImagePromptForm.start_word_idx" class="absolute left-0 h-full -translate-x-1/2 text-primary text-lg"/>
              <font-awesome-icon icon="caret-left" v-if="idx == newImagePromptForm.end_word_idx" class="absolute right-0 h-full translate-x-1/2 text-primary text-lg"/>
            </p>
          </div>
        </div>
  
        <form-input 
          label="Additional Information" 
          :optional="true"
          class="w-full"
          type="textarea"
          placeholder="E.g. specific details you want in the image, or details you want to avoid..."
          v-model="newImagePromptForm.additional_info"
        />
  
        <form-button 
          label="Generate new prompts" 
          :loading="sceneTasks.generating_prompt[scene.id + selectedSceneImageIndex]" 
          :show_status="true" @clicked="generateNewImagePrompts"
          type="primary"  
        />
        
        <div v-if="newImagePromptForm.options.length">
          <h3 class="text-xl mb-2">New Scene Description Options:</h3>
          <div class="flex flex-col gap-2 max-h-[400px] overflow-y-auto">
            <div 
              v-for="(option, idx) in newImagePromptForm.options" 
              :key="`option-${idx}`" 
              class="p-2 border rounded-[10px] hover:bg-[var(--medium)] cursor-pointer"
              @click="applyNewImagePrompt(option)"
            >
              <p>
                <font-awesome-icon icon="image"/>
                {{ option.image_prompt }}
              </p>
              <br>
              <p>
                <font-awesome-icon icon="circle-play"/>
                {{ option.video_prompt }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </modal>
    
    <modal v-if="newVideoPromptForm.scene_id">
      <div class="flex flex-col gap-4 text-xs text-light">
        
        <div class="flex justify-between">
          <h2 class="text-2xl">
            <font-awesome-icon icon="rotate-right" class="text-base text-primary"/>
            Regenerate video prompt
          </h2>
          <form-button label="Cancel" class="w-fit" button_type="secondary" @clicked="newVideoPromptForm.scene_id = null"/>
        </div>
        
        <div>
          <form-input
            label="Camera Movement"
            :optional="true"
            class="w-full"
            type="select"
           :options="[
            { value: '', label: 'No specific camera movement' },
            { value: 'static', label: 'Static / Lock off (no movement)' },
            { value: 'pan left', label: 'Pan left' },
            { value: 'pan right', label: 'Pan right' },
            { value: 'nodal pan left', label: 'Nodal pan left' },
            { value: 'nodal pan right', label: 'Nodal pan right' },
            { value: 'tilt up', label: 'Tilt up' },
            { value: 'tilt down', label: 'Tilt down' },
            { value: 'pan and tilt', label: 'Pan and tilt (diagonal/combined)' },
            { value: 'dolly in', label: 'Dolly in / Track forward' },
            { value: 'dolly out', label: 'Dolly out / Track backward' },
            { value: 'lateral track left', label: 'Lateral track / Crab left' },
            { value: 'lateral track right', label: 'Lateral track / Crab right' },
            { value: 'crane up', label: 'Crane / Pedestal up' },
            { value: 'crane down', label: 'Crane / Pedestal down' },
            { value: 'handheld', label: 'Handheld' },
            { value: 'stabilized', label: 'Stabilized (Gimbal/Steadicam)' },
            { value: 'aerial', label: 'Aerial / Drone' }
          ]"
            v-model="newVideoPromptForm.camera_movement"
          />
          
        </div>
        <form-input 
          label="Additional Information" 
          :optional="true"
          class="w-full"
          type="textarea"
          placeholder="E.g. specific details you want in the image, or details you want to avoid..."
          v-model="newVideoPromptForm.additional_info"
        />
        <form-button 
          label="Generate new prompts" 
          :loading="sceneTasks.generating_prompt[scene.id]" 
          :show_status="true" @clicked="generateNewVideoPrompt"
          type="primary"  
        />
      </div>
    </modal>
  
    <div 
      class="text-gray-300 p-4 pb-4 mb-4 flex gap-6 max-h-[580px] overflow-y-auto container-background rounded-lg" 
    >
      <!-- SCENE VIDEO -->
      <div>
          <!-- MORE FUNCTIONS -->
        <div class="flex items-center gap-6 text-xs mb-5 max-w-[250px]">
          <form-input 
            v-model="scene.start_time" 
            label="Start Time"
            type="text"
            placeholder="Enter start time..."
            class="w-full"
          />
          <form-input 
            v-model="scene.duration" 
            label="Duration"
            type="text"
            placeholder="Enter duration..."
            class="w-full"
          />
        </div>
  
        <div class="h-[250px] w-[250px] rounded-t-lg mx-auto relative bg-dark">
          <video 
            v-if="scene.video_src" 
            :src="route(`${scene.video_src}`)"
            alt="Scene Video"
            class="w-full h-full object-cover rounded-md" 
            controls 
          />
        </div>
  
        <div class="relative flex flex-col text-xs">
          <div class="relative group">
            <input 
              type="file" 
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
              @input="handleSceneVideoUpload"
            >
            <div class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-b-[10px] group-hover:bg-white/5 transition-all flex items-center justify-between text-gray-400">
              <span>Choose a file...</span>
              <span class="bg-[var(--medium)] px-3 py-1 -my-4 rounded-md text-xs text-gray-200 border border-[var(--light-gray)]">Browse</span>
            </div>
          </div>
        </div>
        <!-- <input type="file" class="w-[180px] text-white bg-gray-800 border p-1 rounded-sm text-xs" @input="handleSceneVideoUpload"> -->
  
        <!-- <form-input label="Video Prompt" class="w-[180px] mt-6 text-xs">
          <textarea class="w-[180px] text-white bg-gray-800 border p-1 rounded-sm h-24" v-model="scene.video_prompt"></textarea>
          <form-button label="Fix Prompt" :show_status="true" :loading="fixingVideoPrompt" @clicked="fixVideoPrompt"/>
        </form-input> -->
        <div class="flex flex-col mt-4 text-xs gap-4">
          <form-input 
            v-model="scene.video_prompt" 
            label="Video Prompt" 
            type="textarea" 
            placeholder="Enter video prompt..."
            :rounded_b="false"
          />
          <!-- :loading="generatingVideo.includes(scene.id)"  -->
  
          <div class="flex gap-4 *:flex-1">
            <form-button 
              :label="scene.video_src ? 'Regenerate' : 'Generate'" 
              :show_status="true"
              :loading="sceneTasks.generating_video[scene.id]"
              button_style="primary" 
              @click="generateVideo"
            />
            <form-button 
              label="Regenerate" 
              :show_status="true"
              :loading="sceneTasks.generating_prompt[scene.id]"
              button_style="Secondary" 
              @click="openNewVideoPromptForm"
            />
          </div>
        </div>
      </div>
      
      <!-- SCENE IMAGE -->
      <div class="flex flex-col gap-4 text-xs flex-1">
        <!-- IMAGES -->
        <div class="flex gap-2 justify-center items-center">
          <div v-for="name, idx in ['start', 'end']" :key="name" class="flex gap-2 items-center">
            <button class="h-[135px] w-[135px] bg-dark rounded-lg relative border overflow-hidden" @click="selectedSceneImageIndex = idx"
              :class="selectedSceneImageIndex == idx ? 'border-[var(--primary)]' : 'border-transparent'"
            >
              <!-- <p class="absolute top-4 left-1/2 -translate-x-1/2 text-white fonr-bold z-10">{{ name }}</p> -->
              <button v-if="scene.images[idx]?.src" class="absolute top-1 right-1 z-10" @click="removeImage(scene.images[idx].id)">
                <font-awesome-icon icon="xmark"/>
              </button>
              <img
                v-if="scene.images[idx]?.src"
                :src="getSrc(scene.images[idx].src)"
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
        
        <div class="relative flex flex-col text-xs">
          <div class="relative group">
            <input 
              type="file" 
              class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
              @input="handleSceneImageUpload"
            >
            <div class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-[10px] group-hover:bg-white/5 transition-all flex items-center justify-between text-gray-400">
              <span>Choose a file...</span>
              <span class="bg-[var(--medium)] px-3 py-1 -my-4 rounded-md text-xs text-gray-200 border border-[var(--light-gray)]">Browse</span>
            </div>
          </div>
        </div>
  
        <div class="flex gap-2 items-center mt-3 text-xs">
  
          <form-input 
            v-model="imageGenerationStyle" 
            label="Image Style" 
            type="select"
            :options="[
              { value: '', label: 'Auto style' },
              { value: 'lifelaps', label: 'LifeLaps style' },
              { value: 'lifelaps_science', label: 'LifeLaps style (with science)' },
              { value: 'criminal', label: 'Criminal style' },
            ]" 
            placeholder="Select image style..."
            class="w-full"
          />
  
          <div v-if="imageGenerationStylePower" class="w-full h-[66px] flex flex-col">
            <label for="stylePower" class="text-sm font-medium text-light mb-1">
              Style Intensity: <span class="font-semibold text-light">{{ imageGenerationStylePower }}</span>/10
            </label>
            <input
              id="stylePower"
              v-model="imageGenerationStylePower"
              type="range"
              min="1"
              max="10"
              step="1"
              class="w-full accent-[var(--primary)] cursor-pointer my-auto"
            />
          </div>
        </div>
  
        <div class="flex justify-center">
          <form-button 
            label="Apply Styles To Prompt" 
            :show_status="true" 
            :loading="sceneTasks.fixing_image_prompt[scene.id + selectedSceneImageIndex]" 
            button_style="secondary" 
            @click="fixImagePrompt"
            class="w-fit"
          />
        </div>
  
        <!-- PROMPT TEXT AREA -->
        <form-input 
          v-model="scene.images[selectedSceneImageIndex].style" 
          label="Style"
          type="text"
          placeholder="Enter your style..."
          class="w-full"
        />
        
        <form-input 
          v-model="scene.images[selectedSceneImageIndex].idea" 
          label="Idea"
          type="textarea"
          placeholder="Enter your idea..."
          class="w-full"
        />

        <form-input 
          v-model="scene.images[selectedSceneImageIndex].prompt" 
          label="Image Prompt"
          type="textarea"
          placeholder="Enter image prompt..."
          class="w-full"
        />
  
        <!-- TODO -->
        <!-- <div>
          <div class="flex justify-between">
            <label for="_" class="text-sm font-medium text-light mb-1">
              Reference Images
              <span class="text-[var(--light-gray)]" v-if="addedReferenceImages.length > 0">
                ({{ addedReferenceImages.length }} added)
              </span> 
            </label>
            <button @click="showReferenceImages = !showReferenceImages">
              <font-awesome-icon v-if="showReferenceImages == false" icon="chevron-down" class="text-light-hover"/>
              <font-awesome-icon v-else icon="chevron-up" class="text-light-hover"/>
            </button>
          </div>
  
          <div class="flex gap-6 mt-4 mb-4 text-xs" v-if="showReferenceImages">
            <div class="flex-1">
              <p>
                Added:
              </p>
              <div class="overflow-y-auto max-w-[200px] flex gap-1">
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
                Available:
              </p>
              <div class="overflow-y-auto max-w-[200px] flex gap-1" v-if="availableReferenceImages.length > 0">
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
        </div> -->
  
        <!-- IMAGE FINAL ACTION -->
        <!-- :loading="generatingImage[selectedSceneIndex]"  -->
        <div class="flex justify-center gap-4">
          <form-button 
            :label="scene.images[selectedSceneImageIndex]?.src ? 'Regenerate Image' : 'Generate Image'" 
            :show_status="true" 
            :loading="sceneTasks.generating_image[scene.id + selectedSceneImageIndex]" 
            button_style="primary" 
            class="flex-1"
            @click="generateImage"
          />
          <form-button 
            label="Regenerate Prompt" 
            button_style="secondary" 
            class="flex-1"
            @click="openNewImagePromptForm"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import axios from 'axios';
import getSrc from '@/utils/getSrc';
import FormInput from '@/components/FormInput.vue';
import FormButton from '@/components/FormButton.vue';
import Modal from '@/components/ModalContainer.vue';
import route from '@/utils/route.js';

// defineModel automatically sets up the prop AND the emit for us!
// It acts exactly like a ref that is synced with the parent.
const scene = defineModel('scene', { required: true, type: Object });
const sceneTasks = defineModel('scene_tasks', { required: true, type: Object });


// Standard props for things the child shouldn't change
const props = defineProps({
  projectId: String,
  voiceovers: Array,
});

const selectedSceneImageIndex = ref(0);

// UPLOADS
const handleSceneImageUpload = async (event) => {
  const img = event.target.files[0];
  if(!img) return;
  const formData = new FormData();
  formData.append('image', img);
  formData.append('time', ["start", "end"][selectedSceneImageIndex.value]);
  formData.append('scene_image_id', scene.value.images[selectedSceneImageIndex.value].id ?? '');
  formData.append('scene_image_prompt', scene.value.images[selectedSceneImageIndex.value].prompt ?? '');
  console.log(formData);
  try {
    const response = await axios.put(route(`scenes/upload-image/${scene.value.id}`), formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    console.log(response.data);
    scene.value.images[selectedSceneImageIndex.value] = response.data.scene_image
  } catch (error) {
    console.error('Error uploading scene image:', error);
  }
}

const handleSceneVideoUpload = async (event) => {
  const video = event.target.files[0];
  const formData = new FormData();
  formData.append('video', video);
  try{
    const response = await axios.put(route(`scenes/upload-video/${scene.value.id}`), formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    scene.value.video_src = response.data.video_src;
    scene.value.duration = response.data.duration;
  } catch (error) {
    console.error('Error uploading scene video:', error);
  }
}


// GENERATE
const generateImage = async () => {
  const formData = new FormData();
  sceneTasks.value.generating_image[scene.value.id + selectedSceneImageIndex.value] = true;
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

  formData.append("lowkey", generateImageLowkey.value);
  formData.append("prompt", scene.value.prompt);
  formData.append("scene_image_id", scene.value.images[selectedSceneImageIndex.value].id);

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
    route(`scenes/generate-image/${scene.value.id}`),
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
    }
  );

  sceneTasks.value.generating_image[scene.value.id + selectedSceneImageIndex.value] = false;

  console.log(response.data);
  scene.value.images[selectedSceneImageIndex.value].image_src = response.data.image_url;
};


const generateVideo = async () => {
  if(sceneTasks.value.generating_video[scene.value.id]) return; // Prevent multiple clicks

  try {
    // conntect to the websocket
    let scene_generation_socket = new WebSocket(`ws://localhost:8000/ws/scene/generate-video/${scene.value.id}`);
    scene_generation_socket.onopen = () => {
      console.log("✅ WebSocket Connected");
    };
    scene_generation_socket.onmessage = (event) => {
      try {
        const jsonData = JSON.parse(event.data);
        console.log(jsonData);
        if(jsonData.video_src){
          scene.value.video_src = jsonData.video_src;
          scene_generation_socket.close();
        }
      } catch (e) {
        console.error("Error parsing WebSocket message:", e);
      }
    };

    sceneTasks.value.generating_video[scene.value.id] = true;
    await axios.post(route(`scenes/generate-video/${scene.value.id}`), {
      prompt: scene.value.video_prompt,
      duration: scene.value.duration,
    });
    
    // We mutate the model directly! Vue automatically emits this up to the parent.

  } catch (error) {
    console.error('Error generating scene video:', error);
  } finally {
    sceneTasks.value.generating_video[scene.value.id] = false;
  }
}

const imageGenerationStyle = ref('');
const imageGenerationStylePower = ref(5);
const fixImagePrompt = async () => {
  try {
    sceneTasks.value.fixing_image_prompt[scene.value.id + selectedSceneImageIndex.value] = true;
    const response = await axios
      .post(route(`scenes/fix-image-prompt`), { 
        scene_prompt: scene.value.images[selectedSceneImageIndex.value].prompt,
        style: imageGenerationStyle.value,
        style_power: imageGenerationStylePower.value
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; // Re-throw the error after logging it
      })
    ;
    console.log(response.data);
    scene.value.images[selectedSceneImageIndex.value].prompt = response.data.fixed_prompt;
  } catch (error) {
    console.error('Error fixing scene image prompt:', error);
  } finally {
    sceneTasks.value.fixing_image_prompt[scene.value.id + selectedSceneImageIndex.value] = false;
  }
}


// NEW VIDEO PROMPT
const newVideoPromptForm = ref({
  scene_id: null,
  camera_movement: null,
  additional_info: null,
});

const openNewVideoPromptForm = async () => {
  newVideoPromptForm.value.scene_id = scene.value.id;
  newVideoPromptForm.value.camera_movement = '';
  newVideoPromptForm.value.additional_info = '';
}

const generateNewVideoPrompt = async () => {
  try {
    sceneTasks.value.generating_prompt[scene.value.id] = true;
    const response = await axios
      .post(route(`scenes/fix-video-prompt/${scene.value.id}`), { 
        new_camera_movement: newVideoPromptForm.value.camera_movement,
        additional_info: newVideoPromptForm.value.additional_info
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; // Re-throw the error after logging it
      })
    console.log(response.data.new_video_prompts);
    scene.value.video_prompt = response.data.video_prompt;
  } catch (error) {
    console.error('Error regenerating scene video prompt:', error);
  } finally {
    newVideoPromptForm.value.scene_id = null;
    sceneTasks.value.generating_prompt[scene.value.id] = false;
  }
}


// NEW IMAGE PROMPT
const newImagePromptForm = ref({
  scene_id: null,
  scene_image_id: null,
  full_voiceover_text: null,
  start_word_idx: null,
  end_word_idx: null,
  options: [],
});

const openNewImagePromptForm = async () => {
  console.log('TEXT CONTEXT')
  let orderedVoiceoversReverse = [...props.voiceovers].sort((a, b) => b.start_time - a.start_time);
  let voiceover;
  
  for(let i = 0; i < orderedVoiceoversReverse.length; i++){
    if(orderedVoiceoversReverse[i].start_time <= scene.value.start_time){
      voiceover = orderedVoiceoversReverse[i];
      break;
    }
  }

  newImagePromptForm.value.full_voiceover_text = voiceover ? voiceover.text : '';
  newImagePromptForm.value.scene_id = scene.value.id;
  newImagePromptForm.value.scene_image_id = scene.value.images[selectedSceneImageIndex.value].id;  
}

const generateNewImagePrompts = async () => {
  try {
    sceneTasks.value.generating_prompt[scene.value.id + selectedSceneImageIndex.value] = true;
    const selectedVoiceoverTextPart = newImagePromptForm.value.full_voiceover_text.split(' ').slice(
      newImagePromptForm.value.start_word_idx,
      newImagePromptForm.value.end_word_idx + 1
    ).join(' ');

    const response = await axios
      .post(route(`scenes/generate-image-prompts`), { 
        project_id: props.projectId,
        full_voiceover_text: newImagePromptForm.value.full_voiceover_text,
        selected_voiceover_text_part: selectedVoiceoverTextPart,
        additional_info: newImagePromptForm.value.additional_info
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; // Re-throw the error after logging it
      })
    console.log(response.data.new_scene_descriptions);
    newImagePromptForm.value.options = response.data.new_scene_descriptions;
  } catch (error) {
    console.error('Error regenerating scene image prompt:', error);
  } finally {
    sceneTasks.value.generating_prompt[scene.value.id + selectedSceneImageIndex.value] = false;
  }
}

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


const applyNewImagePrompt = (option) => {
  scene.value.images[selectedSceneImageIndex.value].prompt = option.image_prompt;
  scene.value.video_prompt = option.video_prompt; // reset image
  newImagePromptForm.value = {
    scene_id: null,
    scene_image_id: null,
    full_voiceover_text: null,
    start_word_idx: null,
    end_word_idx: null,
    options: [],
  }
}



// REFERENCE IMAGES
// TODO
const addedReferenceImages = ref([]);
const showReferenceImages = ref(false);


const prepareImages = () => {
  const timeSlots = [null, null]; // start, mid, end
  scene.value.images.forEach(img => {
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
  for(let i = 0; i < 2; i++) {
    if(!timeSlots[i]) {
      timeSlots[i] = {
        id: null,
        scene_id: scene.value.id,
        src: null,
        time: i == 0 ? 'start' : 'end',
        prompt: 'Change camera angle / add action description',
      };
    }
  }
  scene.value.images = timeSlots;
}

onMounted(()=>{
  prepareImages();
})

watch(() => scene.value.id, () => {
  prepareImages();
})



</script>