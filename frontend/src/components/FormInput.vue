<template>
  <div class="-mb-1">
    <label v-if="label" class="block text-sm font-medium text-light mb-1">
      {{ label }} <span class="text-[var(--light-gray)] font-normal" v-if="optional">(Optional)</span>
    </label>
        
    <textarea
      v-if="type === 'textarea'"
      v-model="model"
      class="w-full p-3 bg-transparent border border-[var(--light-gray)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all min-h-[120px] resize-y"
      :class="roundedClass"
      :placeholder="placeholder"
    />

    <select
      v-else-if="type === 'select'"
      v-model="model"
      class="w-full p-3 bg-transparent border border-[var(--light-gray)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all cursor-pointer"
      :class="roundedClass"
    >
      <option value="" disabled v-if="placeholder" class="bg-dark text-light">
        {{ placeholder }}
      </option>
      <option 
        v-for="(option, index) in options" 
        :key="index" 
        :value="option.value !== undefined ? option.value : option"
        class="bg-dark text-light"
      >
        {{ option.label !== undefined ? option.label : option }}
      </option>
    </select>

    <input
      v-else
      :type="type"
      v-model="model"
      :class="roundedClass"
      class="w-full p-3 bg-transparent border border-[var(--light-gray)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent text-white transition-all"
      :placeholder="placeholder"
    />

  </div>
</template>

<script setup>
import { computed } from 'vue';

// This handles the two-way data binding perfectly
const model = defineModel()

const props = defineProps({
  label: String,
  optional: Boolean,
  type: {
    type: String,
    default: 'text' // Defaults to standard text input if no type is provided
  },
  placeholder: {
    type: String,
    default: 'Enter value...'
  },
  rounded_b: {
    type: Boolean,
    default: true
  },
  // New options prop for the select dropdown
  options: {
    type: Array,
    default: () => [] 
  }
})

const roundedClass = computed(() => {
  return props.rounded_b ? 'rounded-[10px]' : 'rounded-t-[10px] rounded-b-0';
})  
</script>