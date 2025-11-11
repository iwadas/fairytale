<template>
  <div class="text-md font-bold tracking-wide text-center text-white">
    <span
      v-for="(item, index) in timestamps"
      :key="index"
      class="inline-block relative"
      :class="shouldHaveMargin(item.word) ? 'ml-1' : ''"
    >
      <span class="absolute left-0 -top-4 opacity-0 stroke"
        :class="isVisible(index) && 'appear'"
      >
      {{ item.word }}
      </span>
      <span class="opacity-0 stroke stroke">
        {{ item.word }}
      </span>
    </span>
  </div>
</template>

<style scoped>

@keyframes appear {
  100% {
    top: 0;
    opacity: 1
  }
}

.appear{
  animation: appear 0.1s ease-in-out forwards;
}

.stroke {
  color: white;
  font-weight: bold;
  text-shadow:
    /* Outer black stroke layers for smoothness */
    -1px -1px 0 #000,
    1px -1px 0 #000,
    -1px 1px 0 #000,
    1px 1px 0 #000,
    /* Inner white "fill" to blend seamlessly */
    -0.5px -0.5px 0 white,
    0.5px -0.5px 0 white,
    -0.5px 0.5px 0 white,
    0.5px 0.5px 0 white,
    0 0 0 white; /* Solid white center */
  line-height: 1.1; /* Tight spacing like TikTok's 13 equivalent */
}

</style>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  timestamps: {
    type: Array,
    required: true
  },
  time: {
    type: [Number, String],
    required: true,
    validator: (v) => !isNaN(parseFloat(v))
  }
});

const shouldHaveMargin = (word) => {
  return ![",", ".", "?", ":"].includes(word);
}

const currentTime = computed(() => parseFloat(props.time));

const visibleIndices = computed(() => {
  const visible = new Set();
  const now = currentTime.value;

  props.timestamps.forEach((item, index) => {
    if (now >= item.time) {
      visible.add(index);
    }
  });

  return visible;
});

const isVisible = (index) => visibleIndices.value.has(index);

</script>