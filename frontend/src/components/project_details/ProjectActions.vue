<template>

  <div class="flex gap-3 text-xs">
      <form-button
        @click="saveChanges"
        button_style="primary"
        label="Save Changes" 
      />
      <form-button
        @click="downloadProject"
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

const downloadProject = async () => {
  await saveChanges();
  try{
    const response = await axios.post(`http://localhost:8000/projects/download/${props.projectId}`);
    // Create a URL for the blob and trigger a download
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `project_${props.projectId}.mp4`);
    document.body.appendChild(link);
    link.click();
  } catch (error) {
    console.error('Error downloading project:', error);
  }
}


</script>