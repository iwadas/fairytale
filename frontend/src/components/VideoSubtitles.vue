<template>
  <div class="text-md font-bold tracking-wide text-center text-white" v-if="segmentsTimings[activeSegmentIndex]">
    <span
      v-for="(item, index) in segmentsTimings[activeSegmentIndex].words"
      :key="index"
      class="inline-block relative"
      :class="shouldHaveMargin(item.word) ? 'ml-1' : ''"
    >
      <span class="absolute left-0 -top-4 opacity-0 stroke"
        :class="activeWordsIndices[index] && 'appear'"
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
  },
  pauses: String
});

const SYMBOLS = [",", ".", "?", ":", '"']

const shouldHaveMargin = (word) => {
  return !SYMBOLS.includes(word);
}

const splittedPauses = computed(()=>{
  let result = props.pauses.split("|").join(" | ").split("'").join(" ' ")
  SYMBOLS.forEach(el => result = result.replaceAll(el, ` ${el}`))
  return result.split(" ").filter(el => !el.startsWith("["))
})


const currentTime = computed(() => parseFloat(props.time));

const activeSegmentIndex = computed(()=>{
  return segmentsTimings.value.findIndex(el => {
    return currentTime.value >= el.start_time && currentTime.value <= el.end_time
  });
})

const activeWordsIndices = computed(()=>{
  if(activeSegmentIndex.value != -1){
    return segmentsTimings.value[activeSegmentIndex.value].words.map(el => el.time < currentTime.value)
  } else {
    return [];
  }
})

const segmentsTimings = computed(()=>{
  
  let currentSegmentIndex = 0;
  let lastWordTime = 0;
  let newSegmentStartTime = 0;
  let timestampsWordTracker = 0

  const normalize = str => str
    .trim()

  // output
  let segments = [];
  let setTimes = false;

  for(let pausesWordTracker = 0; pausesWordTracker < splittedPauses.value.length; pausesWordTracker++){
    const word = splittedPauses.value[pausesWordTracker];
    console.log('checking word')
    console.log(word);
    // if pause it means we are in new segment
    if(word == '|'){
      // increase segment
      console.log('incrementing segment');
      currentSegmentIndex++;
      setTimes = true;
    } else {
      // searching for this word in timestamps
      console.log('searching for word')
      while((timestampsWordTracker < props.timestamps.length) && (props.timestamps[timestampsWordTracker]?.word && normalize(props.timestamps[timestampsWordTracker].word)) != normalize(word)){
        console.log('skipping to next word, because this doesnt match:')
        console.log(word)
        console.log(props.timestamps[timestampsWordTracker].word)
        timestampsWordTracker++;
      }

      console.log(props.timestamps.length);
      // means the word is not found - break;
      if(timestampsWordTracker >= props.timestamps.length){console.log("wtf"); break}

      console.log('found word at index', timestampsWordTracker)
      
      // this means that this is the first word after "|" -> so we need to set end times for previous segment
      if(setTimes){
        console.log('setting end_time for previous segment');
        newSegmentStartTime = props.timestamps[timestampsWordTracker].time;
        const timeBetweenThoseTimestamps = Math.max(lastWordTime + 0.25, (newSegmentStartTime + lastWordTime) / 2 - 0.1)
        segments[currentSegmentIndex - 1].end_time = timeBetweenThoseTimestamps;
        segments[currentSegmentIndex] = {"start_time": newSegmentStartTime}
        setTimes = false;
      }

      lastWordTime = props.timestamps[timestampsWordTracker].time;
      
      // add word to segment
      console.log("appending word")
      console.log({"word": word, "time": lastWordTime});
      if(!segments[currentSegmentIndex]){segments[currentSegmentIndex] = {}}
      if(!segments[currentSegmentIndex]["words"]){ segments[currentSegmentIndex]["words"] = []}
      segments[currentSegmentIndex]["words"].push({"word": word, "time": lastWordTime})
    }
  }
  if(segments && segments.length){
    segments[0].start_time = props.timestamps[0].time;
    segments[segments.length - 1].end_time = props.timestamps[props.timestamps.length - 1].time + 0.1
  }
  return segments;
})

</script>