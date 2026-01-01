<template>
    <div class="border rounded min-w-[45px] w-[45px] h-[80px]">
        <div class="w-full h-full  bg-gray-200 cursor-pointer" @click="toggleAdded">
            <img v-if="src" class="w-full h-full object-contain" :src="getSrc(src)" alt="">
        </div>
    </div>
</template>


<script setup>
    import getSrc from '../utils/getSrc.js'

    const props = defineProps({
        name: String,
        src: String,
        added: Boolean,
    })

    const emit = defineEmits(['remove', 'add'])

    const toggleAdded = () => {
        if(props.added) {
            removeReferenceImage();
        } else {
            addReferenceImage();
        }
    }

    const removeReferenceImage = () => {
        emit('remove', props.src)
    }

    const addReferenceImage = () => {
        emit('add', {name: props.name, src: props.src});
    }


</script>