<template>
  <div
    class="text-light flex flex-col gap-6 container-background w-fit p-4 text-xs" 
  >
    <div class="flex gap-4 justify-center">

      <form-input 
        v-model="voiceover.start_time" 
        label="Start Time"
        type="text"
        placeholder="Enter start time..."
        class="w-[200px]"
      />

      <form-input 
        v-model="voiceover.duration" 
        label="Duration"
        type="text"
        placeholder="Enter duration..."
        class="w-[200px]"
      />
      
    </div>
    <form-input 
      v-model="voiceover.text" 
      label="Text"
      type="textarea"
      placeholder="Enter text..."
      class="w-[416px]"
    />

    <form-input 
      v-model="voiceover.text_with_pauses" 
      label="Text With Pauses"
      type="textarea"
      placeholder="Enter text with pauses..."
      class="w-[416px]"
    />
    
    <div v-if="voiceover.src" class="w-[416px]">
      <audio :src="getSrc(voiceover.src)" controls class="w-full mt-2"></audio>
    </div>

    <form-button 
      :label="voiceover.src ? 'Regenerate Voiceover' : 'Generate Voiceover'" 
      :show_status="true" 
      :loading="voiceoverTasks.generating_voiceover[voiceover.id]" 
      button_style="primary" 
      @click="generateVoiceover"
    />
  </div>
</template>

<script setup>

  import FormInput from '@/components/FormInput.vue';
  import FormButton from '@/components/FormButton.vue';
  import getSrc from '@/utils/getSrc';
  import axios from 'axios';

  const voiceover = defineModel('voiceover', { required: true, type: Object });
  const voiceoverTasks = defineModel('voiceover_tasks', { required: true, type: Object });

  const generateVoiceover = async () => {
    voiceoverTasks.value.generating_voiceover[voiceover.value.id] = true;
    try {
      const voiceoverResponse = await axios.post(`http://localhost:8000/voiceovers/generate/${voiceover.value.id}`, {
        text: voiceover.value.text
      });
      voiceover.value.src = voiceoverResponse.data.src+"?v="+Date.now();
      voiceover.value.duration = voiceoverResponse.data.duration
      voiceover.value.timestamps = voiceoverResponse.data.timestamps

    } catch (error) {
      console.error("Error generating voiceover:", error);
    } finally {
      voiceoverTasks.value.generating_voiceover[voiceover.value.id] = false;
    }
  }
</script>