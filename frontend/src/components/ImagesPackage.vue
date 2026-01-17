<template>
  <div>
    
    <modal v-if="showNewImageForm">
      <div class="flex flex-col gap-2">
        <button @click="showNewImageForm = false" class="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700">
          Close
        </button>
        <p>
          Enter story for new image generation:
        </p>
        <textarea v-model="newImageForm.story" class="w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 mb-2"></textarea>
        <button @click="generateImageOptions" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          Generate Options
        </button>
        <div v-if="newImageOptions.length > 0" class="mt-4">
          <p class="font-semibold mb-2">Select an option:</p>
          <div class="space-y-2 max-h-60 overflow-y-auto">
            <div
              v-for="(option, index) in newImageOptions"
              :key="index"
              class="p-2 border rounded-md hover:bg-gray-100 cursor-pointer"
              @click="selectImageOption(option)"
            >
              {{ option }}
            </div>
          </div>
        </div>
      </div>
    </modal>

    <h2 class="text-2xl font-semibold text-gray-800 mb-4">Images Package</h2>
    <div class="bg-white p-6 rounded-lg shadow-sm">
      <div class="space-y-4" v-if="imagesPackage">
        <div>
          <label class="block text-sm font-medium text-gray-600">Package Name</label>
          <input
            v-model="imagesPackage.name"
            type="text"
            class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
            placeholder="Enter topic..."
          />
        </div>
        <button
          @click="savePackage"
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Change
        </button>
        <div class="flex gap-2 items-center mt-3 text-xs">
          <div label="Image Style" class="w-full mt-4">
            <select v-model="imageGenerationStyle" class="text-white bg-gray-800 border-white rounded-sm w-full border">
              <option value="" default>Auto style</option>
              <option value="darkwave_engraving">Darkwave Engraving</option>
              <option value="byzantine_orthodox">Byzantine Orthodox</option>
              <option value="biblical_epic">Biblical</option>
              <option value="lifelaps">LifeLaps style</option>
              <option value="lifelaps_science">LifeLaps style (with_science_shit)</option>
              <option value="criminal">Criminal style</option>
            </select>
          </div>
          <div v-if="imageGenerationStylePower" class="w-full text-xs">
            <label for="stylePower" class="text-gray-300">
              Style Intensity: <span class="font-semibold text-white">{{ imageGenerationStylePower }}</span>/10
            </label>
            <input
              id="stylePower"
              v-model="imageGenerationStylePower"
              type="range"
              min="1"
              max="10"
              step="1"
              class="w-full accent-indigo-500 cursor-pointer"
            />
          </div>
        </div>
        <div>
          <p>
            Images
          </p>
          <div class="flex flex-wrap justify-center gap-5">
            <div>
              <button @click="showNewImageForm = true">
                Add new image
              </button>
            </div>
            
            <div v-for="n in imagesPackage.images.length" :key="n"
              class="w-[180px] h-[600px]"
            >
              <img 
                v-if="imagesPackage.images[n-1].src" 
                :src="getSrc(imagesPackage.images[n - 1].src)" 
                alt=""
                class="w-[180px] h-[320px] object-cover rounded-md mb-2"
              />
              
              <input type="file" @change="handleFileInput($event, n - 1)" />
              
              <textarea v-model="imagesPackage.images[n - 1].prompt" class="w-full h-32 text-xs p-2 border rounded-md focus:ring-2 focus:ring-blue-500 mb-2">
              </textarea>
            
              <div class="flex justify-end">
                <button class="bg-blue-200"
                 @click="applyStylesToImage(n - 1)"
                >
                  Apply styles
                </button>
                <button class="bg-green-400" @click="regenerateImage(n - 1)">
                  Regenerate
                </button>
                <button class="bg-red-400" @click="deleteImage(n - 1)">
                  Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import getSrc from '../utils/getSrc.js'
import axios from 'axios';
import Modal from './ModalContainer.vue';

const imagesPackage = ref();
const imageGenerationStyle = ref(null);
const imageGenerationStylePower = ref(5);

let packageId = null;

onMounted(async () => {
  packageId = window.location.pathname.split('/').pop();
  let response = await axios.get(`http://localhost:8000/images-packages/${packageId}`);
  imagesPackage.value = response.data;
});


const handleFileInput = async (event, selectedImageIndex) => {
  const img = event.target.files[0];
  const formData = new FormData();
  formData.append('file', img);
  formData.append('prompt', imagesPackage.value.images[selectedImageIndex].prompt ?? '');
  console.log(formData);
  const response = await axios.put(`http://localhost:8000/images-packages/upload-image/${imagesPackage.value.images[selectedImageIndex].id}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  console.log('-----------response--------------');
  console.log(response.data);
  imagesPackage.value.images[selectedImageIndex] = response.data;
}

const savePackage = async () => {
  await axios.put(`http://localhost:8000/images-packages/${packageId}`, {
    name: imagesPackage.value.name,
  });
}

const newImageForm = reactive({
  story: 'Enter story',
});

const showNewImageForm = ref(false);

const newImageOptions = ref([]);

const generateImageOptions = async () => {
  let response = await axios.post('http://localhost:8000/generators/generate-photo-dump-images', newImageForm);
  newImageOptions.value = response.data.images_prompts.options;
}

const selectImageOption = async (option) => {
  console.log(option);
  let newImage = await axios.post(`http://localhost:8000/images-packages/${packageId}/images`, {
    prompt: option,
  });
  imagesPackage.value.images.push(newImage.data);
}

const deleteImage = (index) => {
  let imageId = imagesPackage.value.images[index].id;
  imagesPackage.value.images.splice(index, 1);
  axios.delete(`http://localhost:8000/images-packages/images/${imageId}`);
}

const applyStylesToImage = async (index) => {
  let image = imagesPackage.value.images[index];
  try{
    const response = await axios
      .post('http://localhost:8000/generators/fix-scene-image-prompt', { 
        prompt: image.prompt,
        style: imageGenerationStyle.value,
        style_power: imageGenerationStylePower.value
      })
      .catch((error) => {
        console.error('Error response from server:', error.response ? error.response.data : error.message);
        throw error; 
      });
    imagesPackage.value.images[index].prompt = response.data.fixed_prompt;
  } catch (error) {
    console.error('Error applying styles to image prompt:', error);
    return;
  }
}

</script>