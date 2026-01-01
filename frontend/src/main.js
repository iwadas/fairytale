import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'; // Import Tailwind CSS
import router from './router';

import { library } from '@fortawesome/fontawesome-svg-core'

/* 2. Import the fontawesome icon component */
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

/* 3. Import specific icons */
import { fas } from '@fortawesome/free-solid-svg-icons'
library.add(fas); // Add the imported icons to the library
    
const app = createApp(App).use(router)
app.component('font-awesome-icon', FontAwesomeIcon)
app.mount('#app')
