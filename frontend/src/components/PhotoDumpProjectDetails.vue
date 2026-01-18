<template>
  <div>
    <h2 class="text-2xl font-semibold text-gray-800 mb-4">EDIT Photo Dump</h2>
    <div 
      v-if="project"  
      class="bg-white p-6 rounded-lg shadow-sm"
    >
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-600">Title</label>
          <input
            v-model="project.name"
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
            v-model="project.voiceovers[0].text"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter story..."
            rows="4"></textarea>
        </div>

        <audio :src="`http://localhost:8000/${project.voiceovers[0]?.src || ''}`" controls class="w-full mt-2"></audio>

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
                  <span v-if="!project.images_packages_ids.includes(imgPackage.id)">
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
          @click="updateProject"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Save Changes
        </button>
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

const projectId = window.location.pathname.split('/').pop();

const project = ref(null);

onMounted(async () => {
  let responseProject = await axios.get(`http://localhost:8000/projects/${projectId}`);
  console.log('--project details------');
  console.log(responseProject.data);
  let projectFull = responseProject.data;
  projectFull.images_packages_ids = projectFull.images_packages.map(pkg => pkg.id);
  project.value = projectFull;
  let responsePackages = await axios.get('http://localhost:8000/images-packages');
  imagesPackages.value = responsePackages.data;
});

const togglePackageSelection = (packageId) => {
  const index = project.value.images_packages_ids.indexOf(packageId);
  if (index > -1) {
    project.value.images_packages_ids.splice(index, 1);
  } else {
    project.value.images_packages_ids.push(packageId);
  }
}

const addPackage = async () => {
  const response = await axios.post(`http://localhost:8000/images-packages`);
  router.push(`/images-packages/${response.data}`);
}

const updateProject = async () => {
  await axios.put(`http://localhost:8000/projects/photo-dump/${projectId}`, {
    name: project.value.name,
    images_packages_ids: project.value.images_packages_ids,
  });
}

const generateVideo = async () => {
  await axios.post(`http://localhost:8000/projects/download-pd/${projectId}`);
}

</script>