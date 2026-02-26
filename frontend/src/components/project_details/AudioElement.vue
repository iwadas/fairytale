<template>
    <div class="w-full overflow-hidden rounded-[10px] bg-medium">
        <div ref="waveformRef" class="w-full h-[40px] -mt-[20px]"></div>
        <p class="whitespace-nowrap p-1 overflow-ellipsis truncate max-w-full">
            {{ voiceover?.text || music?.name }}
        </p>
    </div>
</template>

<script setup>
import WaveSurfer from 'wavesurfer.js'
import { onMounted, onBeforeUnmount, watch, ref } from 'vue';

const props = defineProps({
    voiceover: Object,
    music: Object
})

// Use a ref to target the exact DOM element for this specific component instance
const waveformRef = ref(null);
let wavesurfer = null;

// Helper to get the current formatted URL
const getAudioUrl = () => {
    const src = props.voiceover?.src || props.music?.src;
    return src ? `http://localhost:8000/${src}` : null;
}

const initWaveSurfer = () => {
    const url = getAudioUrl();
    if (!url || !waveformRef.value) return;

    try {
        wavesurfer = WaveSurfer.create({
            container: waveformRef.value, // Pass the DOM node directly, not a string selector
            height: 40,
            width: '100%', 
            waveColor: '#ee4545',
            progressColor: '#ee4545',
            interact: false,
            url: url
        });
    } catch (error) {
        console.error('Error initializing WaveSurfer:', error);
    }
}

onMounted(() => {
    initWaveSurfer();
})

// Watch for source changes
watch(() => props.voiceover?.src || props.music?.src, () => {
    const newUrl = getAudioUrl();
    
    if (newUrl) {
        if (wavesurfer) {
            // If instance exists, just load the new audio file
            console.log('Loading new wave src:', newUrl);
            wavesurfer.load(newUrl);
        } else {
            // Fallback if it wasn't initialized yet
            initWaveSurfer();
        }
    } else if (wavesurfer) {
        // If the src is removed, clear the waveform
        wavesurfer.empty();
    }
})

onBeforeUnmount(() => {
    if (wavesurfer) {
        wavesurfer.destroy();
    }
})
</script>