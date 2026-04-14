// src/composables/useWebSockets.js
import { reactive, ref, computed } from 'vue';

// --- GLOBAL STATE ---
let globalSocket = null;
let responsesSocket = null;

export const activeTasks = reactive({});
export const notifications = ref([]);
export const completedTasksQueue = ref([]);

export function useWebSockets() {
  
  // 1. Connection for Background Task Responses
  const connectResponsesWS = () => {
    if (responsesSocket && responsesSocket.readyState !== WebSocket.CLOSED) return; 

    responsesSocket = new WebSocket('ws://localhost:8000/ws/responses');

    responsesSocket.onopen = () => console.log("✅ Responses WebSocket Connected");

    responsesSocket.onmessage = (event) => {
        try {

            console.log("✨ Received message on responses WS:", event.data);

            const payload = JSON.parse(event.data);
            if (payload.task_id) {
                if(payload.status === "completed") {
                    // Optionally, you can remove completed tasks after some time
                    console.log("payload", payload);
                    completedTasksQueue.value.push(payload);
                    activeTasks[payload.task_id] = false;
                } else {
                    activeTasks[payload.task_id] = true;
                }
            }
        } catch(e) {
            console.error("Failed to parse response JSON", e);
        }
    };
    
    responsesSocket.onclose = () => {
       responsesSocket = null;
    };
  };

  // 2. Connection for Global Notifications
  const connectGlobalWS = () => {
    if (globalSocket && globalSocket.readyState !== WebSocket.CLOSED) return; 

    globalSocket = new WebSocket('ws://localhost:8000/ws');

    globalSocket.onopen = () => console.log("✅ Global WebSocket Connected");

    globalSocket.onmessage = (event) => {
      try {
        const jsonData = JSON.parse(event.data);
        console.log("Global Msg:", jsonData);
        notifications.value.push(jsonData);
      } catch (e) {
        console.log("Global Text:", event.data);
      }
    };

    globalSocket.onclose = () => {
       globalSocket = null;
    };
  };

  return {
    connectGlobalWS,
    connectResponsesWS,
  };
}

export function isTaskRunning(taskId) {
    // return activeTasks[taskId] != undefined && activeTasks[taskId] === true;
    return !!activeTasks[taskId];
}