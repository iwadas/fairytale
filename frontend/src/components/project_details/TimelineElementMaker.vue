<template>

    <div class="flex gap-2 items-center mb-2">
      <button class="button-secondary text-xs text-light"
        @click="addScene"
      >
        <font-awesome-icon icon="video"/>
        <font-awesome-icon icon="plus-circle" class="text-primary"/>
      </button>
      <button class="button-secondary text-xs text-light"
        @click="console.log('TO BE IMPLEMENTED')"
      >
        <font-awesome-icon icon="image"/>
        <font-awesome-icon icon="plus-circle" class="text-primary"/>
      </button>
      <button class="button-secondary text-xs text-light"
        @click="addVoiceover"
      >
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

</template>

<script setup>

import axios from 'axios';
import route from '@/utils/route.js';

const emits = defineEmits(['add-timeline-element']);

const props = defineProps({
    currentTime: Number,
    projectId: String,
})

const addMusic = async () => {
    try{
        const response = await axios.post(route(`music/${props.projectId}`), {
            start_time: props.currentTime,
        });
        let newMusic = response.data;
        newMusic["type"] = "music";
        console.log('New music added:', newMusic);
        emits('add-timeline-element', newMusic);
    } catch (error) {
        console.error("Error adding music:", error);
    }
}

const addVoiceover = async () => {
    try{
        const response = await axios.post(route(`voiceovers/${props.projectId}`), {
            start_time: props.currentTime,
        });
        let newVoiceover = response.data;
        newVoiceover["type"] = "voiceover";
        console.log('New voiceover added:', newVoiceover);

        emits('add-timeline-element', newVoiceover);
    } catch (error) {
        console.error("Error adding voiceover:", error);
    }
}


const addScene = async () => {
    try{
        const response = await axios.post(route(`scenes/${props.projectId}`), {
            start_time: props.currentTime,
        });
        let newScene = response.data;
        newScene["type"] = "scene";
        console.log('New scene added:', newScene);
        emits('add-timeline-element', newScene);
    } catch (error) {
        console.error("Error adding scene:", error);
    }
}



</script>