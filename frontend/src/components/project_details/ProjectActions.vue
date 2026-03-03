<template>

  <div class="flex gap-3 text-xs">
      <form-button
        @click="saveChanges"
        button_style="primary"
        label="Save Changes" 
      />
      <form-button
        @click="console.log('Downloading video...')"
        button_style="secondary"
        label="Download" 
      />
  </div>

</template>

<script setup>

import axios from 'axios';
import FormButton from '@/components/FormButton.vue'

const props = defineProps({
  timelineElements: {
    type: Array,
    required: true
  },
  projectId: String
})


const saveChanges = async () => {
  try{
    axios.put(`http://localhost:8000/projects/${props.projectId}`, {
      timeline_elements: props.timelineElements
    })
    console.log("Project changes saved successfully.");
  } catch (error) {
    console.error('Error saving project changes:', error);
  }
}

</script>