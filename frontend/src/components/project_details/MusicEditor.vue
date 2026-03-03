<template>
  <div
    class="text-light flex flex-col gap-6 w-full p-4 text-xs" 
  >
    <div class="flex gap-4 justify-center">

      <form-input 
        v-model="music.start_time" 
        label="Start Time"
        type="text"
        placeholder="Enter start time..."
        class="w-full"
      />

      <form-input 
        v-model="music.duration" 
        label="Duration"
        type="text"
        placeholder="Enter duration..."
        class="w-full"
      />
      
    </div>
    <div class="relative flex flex-col text-xs">
        <div class="relative group">
        <input 
            type="file" 
            class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
            @input="handleMusicUpload"
        >
        <div class="w-full p-3 bg-transparent border border-[var(--light-gray)] rounded-[10px] group-hover:bg-white/5 transition-all flex items-center justify-between text-gray-400">
            <span>Choose a file...</span>
            <span class="bg-[var(--medium)] px-3 py-1 -my-4 rounded-md text-xs text-gray-200 border border-[var(--light-gray)]">Browse</span>
        </div>
        </div>
    </div>

    <div class="flex w-full items-center gap-2">
      <div class="flex-1 h-[1px] bg-light-gray"></div>
      <span>OR</span>
      <div class="flex-1 h-[1px] bg-light-gray"></div>
    </div>

    <form-input 
      v-model="music.src" 
      label="Select from library"
      type="select"
      :options="DEFAULT_MUSIC_OPTIONS"
    />


    <div v-if="music.src" class="w-full">
      <audio :src="getSrc(music.src)" controls class="w-full mt-2"></audio>
    </div>
  </div>
</template>

<script setup>

  import FormInput from '@/components/FormInput.vue';
  import getSrc from '@/utils/getSrc';
  import axios from 'axios';
  import { watch } from 'vue';

  const music = defineModel('music', { required: true, type: Object });
  const route = 'http://localhost:8000/'

  const DEFAULT_MUSIC_OPTIONS = [
    { label: '13 Angels', value: 'static/default/sounds/13_angels.mp3' },
    { label: 'In This Shirt', value: 'static/default/sounds/in_this_shirt.mp3'},
    { label: 'Interstellar', value: 'static/default/sounds/interstellar.mp3'},
    { label: 'Untitled 13', value: 'static/default/sounds/untitled13.mp3'},
    { label: 'Want To Love', value: 'static/default/sounds/want_to_love.mp3'},
  ]

  watch(()=>music.value.src, (newSrc) => {
    
    if(newSrc && DEFAULT_MUSIC_OPTIONS.some(option => option.value === newSrc)) {
      // SEND REQUEST TO BACKEND TO UPDATE MUSIC SRC

      try{
        axios.put(`${route}music/${music.value.id}`, { src: newSrc })
          .then(response => {
            console.log('Music src updated successfully');
            music.value.src = response.data.src;
            music.value.duration = response.data.duration;
            music.value.name = response.data.name;
          })
          .catch(error => {
            console.error('Error updating music src:', error);
          });
      } catch (error) {
        console.error('Error updating music src:', error);
      }
    }
  })

  const handleMusicUpload = async (event) => {
    const music_file = event.target.files[0];
    if(!music_file) return;

    try{
      const formData = new FormData();
      formData.append('music_file', music_file);
      formData.append('music_id', music.value.id ?? '');
      
      const response = await axios.put(`${route}music/upload-music/${music.value.id}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      console.log('-----------response--------------');
      console.log(response.data);
      music.value.src = response.data.src;
      music.value.name = response.data.name;
      music.value.duration = response.data.duration;
    
    } catch (error) {
      console.error('Error uploading music:', error);
    }
  }

</script>