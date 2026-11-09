<template>

    <div class="flex gap-2 items-center">
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

import { createMusic } from '@/api/music';
import { createVoiceover } from '@/api/voiceovers';
import { createScene } from '@/api/scenes';

const emits = defineEmits(['add-timeline-element']);

const props = defineProps({
    currentTime: Number,
    projectId: String,
})

const addMusic = async () => {
    try{
        const data = await createMusic(props.projectId, {
            start_time: props.currentTime,
        });
        let newMusic = data;
        newMusic["type"] = "music";
        console.log('New music added:', newMusic);
        emits('add-timeline-element', newMusic);
    } catch (error) {
        console.error("Error adding music:", error);
    }
}

const addVoiceover = async () => {
    try{
        const data = await createVoiceover(props.projectId, {
            start_time: props.currentTime,
        });
        let newVoiceover = data;
        newVoiceover["type"] = "voiceover";
        console.log('New voiceover added:', newVoiceover);

        emits('add-timeline-element', newVoiceover);
    } catch (error) {
        console.error("Error adding voiceover:", error);
    }
}


const addScene = async () => {
    try{
        const data = await createScene(props.projectId, {
            start_time: props.currentTime,
        });
        let newScene = data;
        newScene["type"] = "scene";
        console.log('New scene added:', newScene);
        emits('add-timeline-element', newScene);
    } catch (error) {
        console.error("Error adding scene:", error);
    }
}



</script>