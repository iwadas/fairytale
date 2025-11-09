<template>
    <div class="p-2 border rounded w-[100px]">
        <p class="text-xs truncate">{{ name }}</p>
        <div class="size-[82px] bg-gray-200">
            <img v-if="src" class="w-full h-full object-contain" :src="getSrc(src)" alt="">
        </div>
        <form-button v-if="added" label="Remove" @clicked="removeReferenceImage"/>
        <form-button v-else label="Add" @clicked="addReferenceImage"/>
    </div>
</template>


<script setup>

    import FormButton from './FormButton.vue';
    import getSrc from '../utils/getSrc.js'

    const props = defineProps({
        name: String,
        src: String,
        added: Boolean,
    })

    const emit = defineEmits(['remove', 'add'])

    const removeReferenceImage = () => {
        emit('remove', props.src)
    }

    const addReferenceImage = () => {
        emit('add', {name: props.name, src: props.src});
    }


</script>