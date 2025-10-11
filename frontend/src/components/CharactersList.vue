<template>
  <div>
    <h2 class="text-2xl font-semibold text-gray-800 mb-4">Characters</h2>
    <div class="grid grid-cols-1 gap-4">
      <!-- Character Creation Form -->
      <div class="bg-white p-6 rounded-lg shadow-sm">
        <h3 class="text-lg font-medium text-gray-700 mb-4">Create Character</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-600">Character Name</label>
            <input
              v-model="characterName"
              type="text"
              class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
              placeholder="Enter character name..."
            />
          </div>
          <div>
            <div class="flex justify-between">
              <label class="block text-sm font-medium text-gray-600">Character Description</label>
              <button class="px-2 py-1 text-sm bg-blue-700 text-white hover:underline font-bold rounded-lg" @click="fixCharacterDescription">AI</button>
            </div>
            <textarea
              v-model="characterPrompt"
              class="w-full mt-1 p-2 border rounded-md focus:ring-2 focus:ring-blue-500"
              rows="4"
              placeholder="Describe the character..."
            ></textarea>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600">Upload Reference Image 1 (Required)</label>
            <div class="flex justify-between items-center">
              <input
                type="file"
                accept="image/*"
                @change="handleImage1Upload"
                class="mt-1 p-2 border rounded-md w-full"
              />
              <div class="size-32" v-if="image1Preview">
                <img :src="image1Preview" alt="Image 1 Preview" class="object-cover rounded" />
              </div>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600">Upload Reference Image 2 (Optional)</label>
            <div class="flex justify-between items-center">
              <input
                type="file"
                accept="image/*"
                @change="handleImage2Upload"
                class="mt-1 p-2 border rounded-md w-full"
              />
              <div class="size-32" v-if="image2Preview">
                <img :src="image2Preview" alt="Image 2 Preview" class="object-cover rounded" />
              </div>
            </div>
          </div>
          <button
            @click="generateImage"
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Generate Image
          </button>
        </div>
      </div>

      <!-- Character List -->
      <div>
        <h3 class="text-lg font-medium text-gray-700 mb-4">Existing Characters</h3>
        <div class="grid grid-cols-3 gap-4">
          <div
            v-for="character in characters"
            :key="character.id"
            class="bg-white p-4 rounded-lg shadow-sm flex items-center justify-center space-x-4"
          >
            <img
              v-if="character.src"
              :src="`http://localhost:8000/${character.src}`"
              alt="Character"
              class="size-32 object-cover rounded"
            />
            <div class="flex flex-col">
              <p class="text-gray-800 font-medium">{{ character.name }}</p>
              <button
                @click="updateCharacter(character)"
                class="mt-2 hover:underlineb bg-blue-600 text-white rounded-lg font-bold px-2 py-1 text-sm"
              >
                {{ character.src ? 'Update image' : 'Fill image' }}
              </button>
              <button
                @click="useCharacterAsReference(character)"
                class="mt-2 hover:underlineb bg-blue-600 text-white rounded-lg font-bold px-2 py-1 text-sm"
              >
                Use as reference
              </button>
              <button
                @click="deleteCharacter(character.id)"
                class="mt-2 hover:underlineb bg-red-600 text-white rounded-lg font-bold px-2 py-1 text-sm"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import axios from 'axios';

const characterPrompt = ref('');
const characterName = ref('');
const characterId = ref(null);
const image1 = ref(null);
const image2 = ref(null);
const characters = ref([]);
const image1Preview = computed(() => image1.value ? URL.createObjectURL(image1.value) : null);
const image2Preview = computed(() => image2.value ? URL.createObjectURL(image2.value) : null);


const handleImage1Upload = (event) => {
  image1.value = event.target.files[0];
  if (image1.value) {
    console.log('Image 1 uploaded:', image1.value.name);
  }
};


const handleImage2Upload = (event) => {
  image2.value = event.target.files[0];
  if (image2.value) {
    console.log('Image 2 uploaded:', image2.value.name);
  }
};

const fixCharacterDescription = async () => {
  if (!characterPrompt.value) {
    alert('Please enter a character description first.');
    return;
  }
  try {
    console.log(characterPrompt.value);
    console.log('Sending request with body:', { prompt: characterPrompt.value });
    const response = await axios.post('http://localhost:8000/fix-character-prompt', { 
      prompt: characterPrompt.value,
    });
    characterPrompt.value = response.data.fixed_prompt;
    console.log('Character prompt fixed:', characterPrompt.value);
  } catch (error) {
    console.error('Error fixing character prompt:', error);
  }
};


const fetchCharacters = () => {
  axios.get('http://localhost:8000/characters')
    .then(response => {
      console.log('Fetched characters:', response.data);
      characters.value = response.data;
    })
    .catch(error => {
      console.error('Error fetching characters:', error);
    });
};

const generateImage = async () => {
  if (!characterPrompt.value || !image1.value) {
    alert('Description and at least one reference image are required.');
    return;
  }
  const formData = new FormData();
  formData.append('name', characterName.value);
  formData.append('prompt', characterPrompt.value);
  formData.append('image1', image1.value);
  if (image2.value) {
    formData.append('image2', image2.value);
  }
  try {

    let response;
    if(characterId.value) {
      formData.append('id', characterId.value);
      response = await axios.put(`http://localhost:8000/characters/${characterId.value}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    } else {
      response = await axios.post('http://localhost:8000/characters', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
    }

    console.log('Character created:', response.data);
    // Clear form
    characterPrompt.value = '';
    image1.value = null;
    image2.value = null;
    // Refetch characters
    fetchCharacters();
  } catch (error) {
    console.error('Error creating character:', error);
  }
};


const updateCharacter = (character) => {
  characterPrompt.value = character.prompt;
  characterName.value = character.name;
  characterId.value = character.id;
}

const useCharacterAsReference = async (character) => {
  console.log('Selected character:', character.name);
  try {
    // Fetch the image from the src URL and convert to File
    const response = await axios.get(
      `http://localhost:8000/images/characters/${character.id}`,
      {
        responseType: "blob", // important for images
      }
    );  
    console.log(response);
    const blob = response.data;
    image2.value = new File(
      [blob],
      character.src.split("/").pop(),
      { type: blob.type }
    );
    console.log('Image 1 set from selected character:', image2.value.name);
  } catch (error) {
    console.error('Error fetching character image:', error);
  }
};

const deleteCharacter = async (characterId) => {
  try {
    await axios.delete(`http://localhost:8000/characters/${characterId}`);
    console.log('Character deleted:', characterId);
    // Refetch characters
    fetchCharacters();
  } catch (error) {
    console.error('Error deleting character:', error);
  }
};

onMounted(() => {
  fetchCharacters();
});
</script>