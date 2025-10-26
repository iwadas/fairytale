import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'; // Import Tailwind CSS
import router from './router';

createApp(App).use(router).mount('#app')
