<template>
  <div class="bg-white p-4 rounded-lg shadow-sm mb-4">
    <div class="flex justify-between items-center">
      <h3 class="text-lg font-medium text-gray-700">Scene {{ scene.id }}</h3>
      <p class="text-sm text-gray-600">Duration: {{ scene.duration }}s</p>
    </div>
    <div class="mt-4">
      <label class="block text-sm font-medium text-gray-600">Image Description</label>
      <textarea
        v-model="scene.description"
        class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
        rows="3"
        placeholder="Describe the scene..."
      ></textarea>
    </div>
    <div class="mt-4" v-if="scene.image || scene.video">
      <img
        v-if="scene.image"
        :src="scene.image"
        alt="Scene Image"
        class="w-32 h-32 object-cover rounded"
      />
      <video
        v-if="scene.video"
        :src="scene.video"
        controls
        class="w-32 h-32 object-cover rounded"
      ></video>
    </div>
    <div class="mt-4">
      <label class="block text-sm font-medium text-gray-600">Generate Image/Video</label>
      <input
        type="file"
        accept="image/*,video/*"
        @change="handleMediaUpload"
        class="mt-1 p-2 border rounded-md w-full"
      />
      <button
        @click="generateMedia"
        class="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
      >
        {{ scene.image || scene.video ? 'Regenerate' : 'Generate' }} Media
      </button>
    </div>
  </div>
</template>

<script setup>

defineProps({
  scene: {
    type: Object,
    required: true,
  },
});

const handleMediaUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    console.log('Media uploaded:', file.name);
  }
};

const generateMedia = () => {
  console.log('Generating media for scene:', scene.value);
};
</script>
