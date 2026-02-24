<template>

    <div class="w-full overflow-hidden rounded-[10px] bg-medium">
        <div id="waveform" class="w-full h-[40px] -mt-[20px]"></div>
        <p class="whitespace-nowrap p-1 overflow-ellipsis truncate max-w-full">{{ voiceover.text }}</p>
    </div>

</template>


<script setup>

    import WaveSurfer from 'wavesurfer.js'
    import { onMounted, onBeforeUnmount } from 'vue';

    const props = defineProps({
        voiceover: Object
    })

    const options = {
        height: 40,
        width: '100%', 
        container: '#waveform',
        waveColor: '#ee4545',
        progressColor: '#ee4545',
        interact: false,
        url: `http://localhost:8000/${props.voiceover.src}`,
    }

    let wavesurfer;

    onMounted(() => {
        try {
            if(props.voiceover.src){
                wavesurfer = WaveSurfer.create(options)
            }
        } catch (error) {
            console.error('Error initializing WaveSurfer:', error);
        }
    })

    onBeforeUnmount(() => {
        if (wavesurfer) {
            wavesurfer.destroy();
        }
    })

</script>