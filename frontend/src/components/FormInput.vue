<template>
    <div class="div relative">
        <p class="absolute -top-5 pt-1 px-1 left-1/2 -translate-x-1/2 bg-gray-800 text-center whitespace-nowrap">{{ label }}</p>
        <slot></slot>
    </div>
</template>

<script setup>

    defineProps({
        label: String
    })

</script>
