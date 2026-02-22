<template>
    <button @click="$emit('clicked')" :class="button_style == 'primary' ? 'button-primary' : 'button-secondary'" class="flex gap-2 items-center justify-center" :style="(!rounded_t) && 'border-top-left-radius: 0; border-top-right-radius: 0'">
        <span v-if="show_status" class="text-[11px]">
            <font-awesome-icon v-if="loading" icon="spinner" class="animate-spin"/>
            <font-awesome-icon v-else icon="wand-sparkles"/>
        </span>
        {{ label }}
    </button>
</template>

<script setup>

    defineProps({
        label: String,
        color: {
            type: String,
            default: 'blue'
        },
        button_style: {
            type: String,
            default: 'secondary'
        },
        rounded_t: {
            type: Boolean,
            default: true
        },
        show_status: Boolean,
        loading: Boolean,
       
    })
    

    defineEmits(['clicked'])

</script>