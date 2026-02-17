<template>


  <div v-if="tasks.length != 0 && closed">
    <!-- ADD TOGGLE BUTTON TO SHOW TASKS - MINIMAL NOT TO OVERTHOW THE MAIN SUBJECTS ON THE SCREEN -->
    <div class="fixed bottom-4 right-8 bg-blue-600 text-white p-2 rounded-full shadow-lg cursor-pointer hover:bg-blue-700 transition-colors" @click="closed = false">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
    </div>
  </div>

  <div v-if="tasks.length !== 0 && !closed" class="text-center">
    <div class="flex flex-col space-y-4 px-4 py-2 max-h-[600px] overflow-y-auto bg-slate-50 rounded-xl border border-slate-200 shadow-inner
      fixed bottom-4 right-8
    ">

      <!-- ADD BUTTON TO HIDE TASKS -->
      <div class="flex justify-end">
        <button class="text-slate-400 hover:text-blue-600 hover:bg-blue-50 p-2 rounded-full transition-colors" @click="closed = true" title="Hide Tasks">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 transform rotate-180" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
      </div>

      <div 
        v-for="task in tasks" 
        :key="task.task_id"
        class="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden flex-shrink-0 transition-all duration-300 hover:shadow-md"
      >
        <div class="p-4 flex items-center justify-between gap-4">
          
          {{ task.type }}

          <div class="flex items-center gap-3">
            <div 
              class="flex items-center justify-center w-8 h-8 rounded-full"
              :class="task.status === 'in_progress' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'"
            >
              <svg 
                v-if="task.status === 'in_progress'" 
                class="w-5 h-5 animate-spin" 
                xmlns="http://www.w3.org/2000/svg" 
                fill="none" 
                viewBox="0 0 24 24"
              >
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
  
              <svg 
                v-else 
                xmlns="http://www.w3.org/2000/svg" 
                class="w-5 h-5" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                stroke-width="2" 
                stroke-linecap="round" 
                stroke-linejoin="round"
              >
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            
            <div class="flex flex-col">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-400">
                Task #{{ task.task_id }}
              </span>
              <span class="font-medium text-slate-700 text-sm">
                {{ task.latest_message || 'Initializing...' }}
              </span>
            </div>
          </div>
  
          <button 
            @click="task.toggleHistory()"
            class="text-slate-400 hover:text-blue-600 hover:bg-blue-50 p-2 rounded-full transition-colors"
            :title="task.isOpen ? 'Hide History' : 'Show History'"
          >
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              class="w-5 h-5 transition-transform duration-200"
              :class="{ 'rotate-180': task.isOpen }"
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round"
            >
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>
  
        <div 
          v-if="task.isOpen" 
          class="bg-slate-50 border-t border-slate-100 p-4 text-sm space-y-2 animate-in slide-in-from-top-2 duration-200"
        >
          <div class="text-xs font-semibold text-slate-400 mb-2 uppercase">History Log</div>
          <ul class="space-y-2 flex flex-col-reverse">
            <li v-if="task.messages_history.length === 0" class="text-slate-400 italic">
              No previous history.
            </li>
            <li 
              v-for="(msg, index) in task.messages_history" 
              :key="index"
              class="text-slate-600 flex gap-2"
            >
              <span class="text-slate-300">•</span>
              <span>{{ msg }}</span>
            </li>
          </ul>
        </div>
  
      </div>
    </div>
  </div>
  
</template>

<script setup>
import { ref, watch, reactive } from 'vue';

const props = defineProps({
    notifications: {
        type: Array,
        required: true
    }
})

const closed = ref(false);
const tasks = ref([]);

class Task {
    constructor(task_id, type) {
        this.task_id = task_id;
        this.latest_message = '';
        this.messages_history = [];
        this.type = type;
        this.status = 'in_progress';
        // Added for UI state
        this.isOpen = false; 
    }

    handleNewMessage(message){
        // Push the previous "latest" to history before updating new "latest"
        if (this.latest_message) {
            this.messages_history.push(this.latest_message);
        }
        
        this.latest_message = message.message;
        
        if(message.type === "finished"){
           this.status = "finished"; 
        }
    }

    // Helper to toggle UI
    toggleHistory() {
        this.isOpen = !this.isOpen;
    }
}

watch(() => props.notifications, _ => {
    // Safety check for empty array
    if (!props.notifications.length) return;

    let latestNotification = props.notifications[props.notifications.length - 1];
    
    if(latestNotification.status === "init"){
        // Wrap in reactive() is technically optional for ref([]) but good for deep nested reactivity consistency
        // But standard class in ref array usually works in Vue 3 Proxy system
        let newTask = new Task(latestNotification.task_id);
        newTask.handleNewMessage(latestNotification);
        tasks.value.push(newTask);
        return;
    } else {
        let task = tasks.value.find(t => t.task_id === latestNotification.task_id);
        if(task){
            task.handleNewMessage(latestNotification);
        } else {
            console.warn("Received message for unknown task_id:", latestNotification.task_id);
        }
    }
}, { deep: true });
</script>