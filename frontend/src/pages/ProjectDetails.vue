<template>
  <div class="container mx-auto">

    <!-- REGENERATING PROMPT -->
    <div class="preview mb-4 h-[600px]">
      <div
        class="flex gap-10 h-full"
      >
        <!-- PREVIEW -->
        <div class="flex flex-col justify-between w-[400px]">
          <project-preview
            v-model:currentTime="currentTime"
            v-model:isPlaying="isPlaying"
            :timelineElements="timelineElements"
          />
  
          <timeline-element-maker
            @add-timeline-element="addTimelineElement"
            :currentTime="currentTime"
            :projectId="projectId"
          />
        </div>

        <!-- EDIT TIMELINE ELEMENT -->
        <scene-editor
          v-if="selectedTimelineElement && selectedTimelineElement.type === 'scene'"
          v-model:scene="timelineElements[selectedTimelineElementIndex]"
          v-model:scene_tasks="sceneTasks"
          :project-id="projectId"
          :voiceovers="voiceovers"
        />
        <voiceover-editor
          v-else-if="selectedTimelineElement && selectedTimelineElement.type === 'voiceover'"
          v-model:voiceover="timelineElements[selectedTimelineElementIndex]"
          v-model:voiceover_tasks="voiceoverTasks"
        />
        <music-editor
          v-else-if="selectedTimelineElement && selectedTimelineElement.type === 'music'"
          v-model:music="timelineElements[selectedTimelineElementIndex]"
        />

      </div>

      
    </div>

    <div
      v-if="timelineElements"
    >
      <timeline 
        v-model:timeline_elements="timelineElements"
        v-model:is_playing="isPlaying"
        v-model:current_time="currentTime"
        v-model:selected_timeline_element_index="selectedTimelineElementIndex"
      />
    </div>
    

  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios'
import VoiceoverEditor from '@/components/project_details/VoiceoverEditor.vue'
import MusicEditor from '@/components/project_details/MusicEditor.vue'
import Timeline from '@/components/project_details/Timeline.vue'
import SceneEditor from '@/components/project_details/SceneEditor.vue'
import ProjectPreview from '@/components/project_details/Preview.vue'
import TimelineElementMaker from '@/components/project_details/TimelineElementMaker.vue'

const route = 'http://localhost:8000/'
let projectId = null;

const currentTime = ref(0)
const isPlaying = ref(false)

const scenes = ref([]);
const voiceovers = ref([]);
const backgroundMusic = ref([]);
const characters = ref([]);
const timelineElements = ref([]);


const selectedTimelineElementIndex = ref(null);

const addTimelineElement = (newElement) => {
  console.log('Adding new timeline element:', newElement);
  timelineElements.value.push(newElement);
  // selectedTimelineElementIndex.value = timelineElements.value.length - 1;
}

const selectedTimelineElement = computed(()=>{
  if(typeof(selectedTimelineElementIndex.value) != 'number') return null;
  return timelineElements.value[selectedTimelineElementIndex.value];
})


const sceneTasks = ref({
  fixing_image_prompt: {},
  generating_video: {},
  generating_image: {},
  generating_prompt: {},
});


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

// Select scene for preview
const selectScene = (sceneId) => {
  deselectAll();
  console.log('deselecting')
  selectedSceneIndex.value = scenes.value.findIndex(el => el.id == sceneId);
  console.log('selected scene index: ' + selectedSceneIndex.value)
  filterSceneImages();
  console.log('filtered images');
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
    vo.type = "voiceover";
    parsedElements.push(vo)

    // Advance the fallback timer for the next audio clip
  })


  backgroundMusic.value.forEach((music, index) => {
    music.cut_start = music.cut_start || 0;
    music.cut_end = music.cut_end || 0;
    music.layer = music.layer || 4;
    music.type = "music";

    parsedElements.push(music)
  })

  return parsedElements
}


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

  timelineElements.value = parseProjectData()

  selectedTimelineElementIndex.value = 0;

  console.log('project');
  console.log(project);

});

</script>
