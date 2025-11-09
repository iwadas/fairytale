<template>
    <button @click="$emit('clicked')" class="w-full bg-blue-500 text-white text-center py-1 text-xs font-bold">
        {{ label }}
    </button>
</template>

<script setup>

    defineProps({
        label: String
    })

    defineEmits(['clicked'])

</script>