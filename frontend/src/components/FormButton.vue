<template>
    <button @click="$emit('clicked')" :class="`w-full ${colorClass} text-white text-center py-1 text-xs font-bold`">
        {{ label }}
        <span v-if="show_status">
            <font-awesome-icon v-if="loading" icon="spinner" class="animate-spin"/>
            <font-awesome-icon v-else icon="star"/>
        </span>
    </button>
</template>

<script setup>

    import { computed } from 'vue';

    const props = defineProps({
        label: String,
        color: {
            type: String,
            default: 'blue'
        },
        show_status: Boolean,
        loading: Boolean
    })
    
    

    const colorClass = computed(() => {
        switch (props.color) {
            case 'green':
                return 'bg-green-500';
            case 'red':
                return 'bg-red-500';
            case 'blue':
            default:
                return 'bg-blue-500';
        }
    })



    defineEmits(['clicked'])

</script>