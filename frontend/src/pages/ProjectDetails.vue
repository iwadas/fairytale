<template>
  <div class="container mx-auto">

    <!-- REGENERATING PROMPT -->
    <div class="preview h-[600px] mb-4">
      <div
        class="flex gap-10 h-full"
      >
        <!-- PREVIEW -->
        <div class="flex flex-col justify-between w-[400px]">
          <project-actions
            :timelineElements="timelineElements"
            :projectId="projectId"
          />
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

        <div class="flex-1 *:container-background">

          <scene-editor
            v-if="selectedTimelineElement && selectedTimelineElement.type === 'scene'"
            v-model:scene="timelineElements[selectedTimelineElementIndex]"
            v-model:scene_tasks="sceneTasks"
            :project-id="projectId"
            :voiceovers="voiceovers"
          />
          <voiceover-editor
            class="max-h-[600px] overflow-y-auto"
            v-else-if="selectedTimelineElement && selectedTimelineElement.type === 'voiceover'"
            v-model:voiceover="timelineElements[selectedTimelineElementIndex]"
            v-model:voiceover_tasks="voiceoverTasks"
          />
          <music-editor
            class="max-h-[600px] overflow-y-auto"
            v-else-if="selectedTimelineElement && selectedTimelineElement.type === 'music'"
            v-model:music="timelineElements[selectedTimelineElementIndex]"
          />
        </div>
        <!-- EDIT TIMELINE ELEMENT -->

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
import ProjectActions from '@/components/project_details/ProjectActions.vue'
import Modal from '@/components/ModalContainer.vue'

const route = 'http://localhost:8000/'
let projectId = null;

const currentTime = ref(0)
const isPlaying = ref(false)

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

// SAVE
const saveProjectChanges = async () => {
  // images are saved automatically
  try{
    axios.put(`${route}projects/${projectId}`, {
      timeline_elements: timelineElements.value
    })
    console.log("Project changes saved successfully.");
  } catch (error) {
    console.error('Error saving project changes:', error);
  }
}

// REQUESTS
const voiceoverTasks = ref({
  generating_voiceover: {},
});

const parseProjectData = (scenes, voiceovers, backgroundMusic) => {
  const parsedElements = []

  // 1. Parse Scenes (Main Visual Track -> Layer 1)
  scenes.forEach(scene => {
    scene.cut_start = scene.cut_start || 0;
    scene.cut_end = scene.cut_end || 0;
    scene.layer = scene.layer || 2;
    scene.type = "scene";
    parsedElements.push(scene);
  })

  voiceovers.forEach(vo => {
    vo.cut_start = vo.cut_start || 0;
    vo.cut_end = vo.cut_end || 0;
    vo.layer = vo.layer || 3;
    vo.type = "voiceover";
    parsedElements.push(vo)
  })

  backgroundMusic.forEach(music => {
    music.cut_start = music.cut_start || 0;
    music.cut_end = music.cut_end || 0;
    music.layer = music.layer || 4;
    music.type = "music";

    parsedElements.push(music)
  })

  return parsedElements
}


const voiceovers = computed(()=>{
  return timelineElements.value.filter(el => el.type === 'voiceover');
})

onMounted(async () => {
  projectId = window.location.pathname.split('/').pop();
  const response = await fetch(`http://localhost:8000/projects/${projectId}`);
  const project = await response.json();

  timelineElements.value = parseProjectData(project.scenes, project.voiceovers, project.background_music)

  selectedTimelineElementIndex.value = timelineElements.value.length > 0 ? 0 : null;

  console.log('project');
  console.log(project);

});

</script>
