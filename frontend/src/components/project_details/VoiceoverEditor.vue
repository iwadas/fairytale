<template>
  <div
    class="text-light flex flex-col gap-6 h-fit p-4 text-xs w-full container-background rounded-lg" 
  >
    <div class="flex gap-4 justify-center">

      <form-input 
        v-model="voiceover.start_time" 
        label="Start Time"
        type="text"
        placeholder="Enter start time..."
        class="w-full"
      />

      <form-input 
        v-model="voiceover.duration" 
        label="Duration"
        type="text"
        placeholder="Enter duration..."
        class="w-full"
      />
      
    </div>
    <form-input 
      v-model="voiceover.text" 
      label="Text"
      type="textarea"
      placeholder="Enter text..."
      class="w-full"
    />

    <!-- <form-input 
      v-model="voiceover.text_with_pauses" 
      label="Text With Pauses"
      type="textarea"
      placeholder="Enter text with pauses..."
      class="w-full"
    /> -->

    <div class="flex flex-col gap-2">
      <label class="text-sm font-bold" for="">Text with pauses</label>
      {{ voiceover.text_with_pauses }}
      <div class="flex gap-1 flex-wrap">
        <div v-for="(item, index) in voiceover.text_with_pauses" :key="index" class="flex items-center gap-1">
          <button 
            v-if="item.word == '[PAUSE]'" 
            @click="removePause(index)"
            class="size-3 grid place-items-center group"
          >
            <div 
              class="bg-primary group-hover:bg-primary-dark w-1 h-full rounded-sm"
            ></div>
          </button>
          <div v-else class="flex gap-1 items-center">
            <button @click="toggleSpecialWord(index)">
              <p class="p-1" 
                :class="{
                  'text-primary': item.is_special,
                }"
              >
                {{ item.word }}
              </p>
            </button>
            <button 
              v-if="(index + 1 != voiceover.text_with_pauses.length) && (voiceover.text_with_pauses[index + 1]?.word != '[PAUSE]')"
              @click="addPause(index + 1)"
              class="size-3 grid place-items-center group"
            >
              <div 
                class="bg-light opacity-50 group-hover:opacity-100 rounded-full size-1 transition-opacity transition-300"
              >
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>

    
    <div v-if="voiceover.src" class="w-full">
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


  // TEXT WITH PAUSES HANDLERS
  const addPause = (index) => {
    voiceover.value.text_with_pauses.splice(index, 0, { word: '[PAUSE]' });
  }
  const removePause = (index) => {
    voiceover.value.text_with_pauses.splice(index, 1);
  }

  const toggleSpecialWord = (index) => {
    // make sure that the key is_special exists
    if (!('is_special' in voiceover.value.text_with_pauses[index]) || voiceover.value.text_with_pauses[index].is_special == false) {
      voiceover.value.text_with_pauses[index].is_special = true;
    } else {
      voiceover.value.text_with_pauses[index].is_special = false;
    }
  }

  const generateVoiceover = async () => {
    voiceoverTasks.value.generating_voiceover[voiceover.value.id] = true;
    try {
      const voiceoverResponse = await axios.post(`http://localhost:8000/voiceovers/generate/${voiceover.value.id}`, {
        text: voiceover.value.text
      });
      voiceover.value.src = voiceoverResponse.data.src+"?v="+Date.now();
      voiceover.value.duration = voiceoverResponse.data.duration
      voiceover.value.timestamps = JSON.parse(voiceoverResponse.data.timestamps)
      voiceover.value.text_with_pauses = JSON.parse(voiceoverResponse.data.text_with_pauses)
    } catch (error) {
      console.error("Error generating voiceover:", error);
    } finally {
      voiceoverTasks.value.generating_voiceover[voiceover.value.id] = false;
    }
  }
</script>