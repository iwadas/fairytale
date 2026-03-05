<template>
  <section class="container-background container mx-auto rounded-[10px] text-light p-6 ">
    <div class="flex items-center justify-between">
      <h2 class="text-lg">
        <font-awesome-icon icon="book-bookmark" class="mr-2"></font-awesome-icon>
        Script Generation Template
      </h2>
      <button @click="showScriptGenerationTemplate = !showScriptGenerationTemplate">
        <font-awesome-icon :icon="showScriptGenerationTemplate ? 'caret-up' : 'caret-down'" class="text-light-gray"/>
      </button>
    </div>
    <div class="flex flex-col gap-4 text-xs mt-6" v-show="showScriptGenerationTemplate">
      <div
        v-for="(value, name) in templates"
        :key="name"
        class="border border-[var(--light-gray)] rounded-[10px] p-4 flex flex-col gap-4"
        :class="[
          selectedTemplate === name ? 'border-[var(--primary)]' : 'border-[var(--light-gray)]'
        ]"
      >   
        <h2 class="">
          {{ name }}
        </h2>
        <form-input 
          label="System Prompt"
          type="textarea"
          v-model="value.role"
        />
        <form-input 
          label="Main Prompt"
          type="textarea"
          v-model="value.main_prompt"
        />
        <form-input 
          label="Revision Prompt"
          type="textarea"
          v-model="value.revision_prompt"
        />
        <div class="flex justify-center gap-4">
          <form-button
            label="Select"
            button_style="primary"
            @clicked="selecteTemplate(name)"
            class="w-1/4 mr-auto"
          />
          <form-button
            label="Save Changes"
            button_style="primary"
            @clicked="saveScriptTemplate(name)"
            class="w-1/4"
          />
          <form-button
            label="Delete"
            button_style="secondary"
            @clicked="deleteScriptTemplate(name)"
            class="w-1/4"
          />
        </div>
      </div>

      <form-button
        label="Add Template"
        button_style="primary"
        v-if="!showNewScriptTemplateForm"
        @clicked="showNewScriptTemplateForm = true"
        class="w-1/4 mx-auto"
      />

      <div 
        v-if="showNewScriptTemplateForm"
        class="flex flex-col gap-4 border border-[var(--light-gray)] rounded-[10px] p-4"
      >
        <h3 class="mb-2 text-lg">New Template</h3>
        <form-input
          label="New Template Name"
          type="text"
          v-model="newScriptTemplate.name"
        />
        <form-input 
          label="System Prompt"
          type="textarea"
          v-model="newScriptTemplate.role"
        />
        <form-input 
          label="Main Prompt"
          type="textarea"
          v-model="newScriptTemplate.main_prompt"
        />
        <form-input 
          label="Revision Prompt"
          type="textarea"
          v-model="newScriptTemplate.revision_prompt"
        />
        <div class="flex justify-center gap-4">
          <form-button
            label="Add Template"
            button_style="primary"
            @clicked="addScriptTemplate"
            class="w-1/4"
          />
          <form-button
            label="Cancel"
            button_style="secondary"
            @clicked="showNewScriptTemplateForm = false"
            class="w-1/4"
          />
        </div>
      </div>
    </div>
</section>
</template>


<script setup>

  import FormInput from '@/components/FormInput.vue';
  import FormButton from '@/components/FormButton.vue';
  import axios from 'axios';
  import { reactive, ref } from 'vue';

  const props = defineProps({
    selectedScriptGenerationTemplate: String,
    scriptGenerationTemplates: Object
  })

  
  const showScriptGenerationTemplate = ref(false);
  const showNewScriptTemplateForm = ref(false);

  const selectedTemplate = ref(props.selectedScriptGenerationTemplate);
  const templates = ref(props.scriptGenerationTemplates);

  const newScriptTemplate = reactive({
      name: '',
      role: '',
      main_prompt: '',
      revision_prompt: '',
  })

  const addScriptTemplate = async () => {
    // VALIDATION
    if (!newScriptTemplate.name || !newScriptTemplate.role || !newScriptTemplate.main_prompt || !newScriptTemplate.revision_prompt) {
      alert("Please provide all fields for the new template.");
      return;
    }
    try {
      // UNIUE NAME CHECK
      if(templates.value && templates.value[newScriptTemplate.name]){
          alert(`A template with the name "${newScriptTemplate.name}" already exists. Please choose a different name.`);
          return;
      }

      // SEND TO BACKEND
      const payload = {
        selected_script_generation_template: newScriptTemplate.name,
        script_generation_templates: {
          [newScriptTemplate.name]: {
            role: newScriptTemplate.role,
            main_prompt: newScriptTemplate.main_prompt,
            revision_prompt: newScriptTemplate.revision_prompt
          }
        }
      }

      console.log(`Adding new script generation template ${newScriptTemplate.name}:`, payload);
      await axios.put(`http://localhost:8000/settings`, payload);
      selectedTemplate.value = newScriptTemplate.name;
      if(!templates.value){
        templates.value = {};
      }
      templates.value[newScriptTemplate.name] = {
        role: newScriptTemplate.role,
        main_prompt: newScriptTemplate.main_prompt,
        revision_prompt: newScriptTemplate.revision_prompt
      };

      // CLEAR
      newScriptTemplate.name = '';
      newScriptTemplate.role = '';
      newScriptTemplate.main_prompt = '';
      newScriptTemplate.revision_prompt = ''; 
      showNewScriptTemplateForm.value = false;
        
    } catch (error) {
      console.error(`Error adding new script generation template "${newScriptTemplate.name}":`, error);
      // alert(`Failed to add new script generation template "${newScriptTemplate.name}". Please try again.`);
    }
  }

  const deleteScriptTemplate = async (template_name) => {
    if (selectedTemplate.value == template_name){
      selectedTemplate.value = null;
    } 
    try {
      const payload = {
        script_generation_templates: {
          [template_name]: null
        }
      }
      await axios.put(`http://localhost:8000/settings`, payload);
      delete templates.value[template_name];
    } catch (error) {
      console.error(`Error deleting script generation template "${template_name}":`, error);
    }
  }

  const saveScriptTemplate = async (template_name) => {
    try {
      const payload = {
        selected_script_generation_template: template_name,
        script_generation_templates: {
          [template_name]: templates.value[template_name]
        }
      }
      selectedTemplate.value = template_name;
      console.log(`Saving script generation template ${template_name}:`, payload);
      await axios.put(`http://localhost:8000/settings`, payload);
      alert(`Script generation template "${template_name}" saved successfully!`);
    } catch (error) {
      console.error(`Error saving script generation template "${template_name}":`, error);
      // alert(`Failed to save script generation template "${template_name}". Please try again.`);
    }
  }

</script>