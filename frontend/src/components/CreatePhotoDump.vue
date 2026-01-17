<template>
  <div>
    <h2 class="text-2xl font-semibold text-gray-800 mb-4">Create Photo Dump</h2>
    <div class="bg-white p-6 rounded-lg shadow-sm">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-600">Title</label>
          <input
            v-model="projectPrompt.title"
            type="text"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter topic..."
          />
        </div>
        <div class="flex gap-2 items-center">
          <label class="block text-sm font-medium text-gray-600">
            Story
          </label>
          <textarea
            v-model="projectPrompt.story"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter story..."
            rows="4"></textarea>
        </div>
        <div>
          Choose Images Package
          <div class="flex flex-col gap-2">
            <div>
              <button @click="addPackage" class="px-4 py-2 bg-blue-600 text-white">
                Add new image
              </button>
            </div>
            <div v-for="imgPackage in imagesPackages" :key="imgPackage.id">
              <p>
                {{ imgPackage.name }}
              </p>
              <div class="flex overflow-x-auto">
                <div v-for="image in imgPackage.images" :key="`img-${image.id}`">
                  <img v-if="image.src" :src="getSrc(image.src)" class="min-w-9 w-9 h-16 object-cover rounded-md" />
                </div>
              </div>
              <div class="flex justify-end">
                <button class="bg-blue-200"
                  @click="togglePackageSelection(imgPackage.id)"
                >
                  <span v-if="!projectPrompt.images_package_id.includes(imgPackage.id)">
                    Select Package
                  </span>
                  <span v-else>
                    Selected <font-awesome-icon icon="check" />
                  </span>
                </button>
                <router-link :to="`/images-packages/${imgPackage.id}`" 
                  class="bg-green-400">
                  Edit Package
                </router-link>
              </div>
            </div>
          </div>
        </div>
        <button
          @click="generateVideo"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Generate Video
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import getSrc from '../utils/getSrc.js'

const router = useRouter();

const imagesPackages = ref([]);

const projectPrompt = reactive({
  title: '',
  story: '',
  images_package_id: [],
})

onMounted(async () => {
  let response = await axios.get('http://localhost:8000/images-packages');
  imagesPackages.value = response.data;
});

const togglePackageSelection = (packageId) => {
  const index = projectPrompt.images_package_id.indexOf(packageId);
  if (index > -1) {
    projectPrompt.images_package_id.splice(index, 1);
  } else {
    projectPrompt.images_package_id.push(packageId);
  }
}

const addPackage = async () => {
  const response = await axios.post(`http://localhost:8000/images-packages`);
  router.push(`/images-packages/${response.data}`);
}

const generateVideo = async () => {
  await axios.post('http://localhost:8000/projects/download-photo-dump', {
    title: projectPrompt.title,
    story: projectPrompt.story,
    images_package_ids: projectPrompt.images_package_id,
  });
  router.push('/videos');
}

</script>