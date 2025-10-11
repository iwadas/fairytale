import { createRouter, createWebHistory } from 'vue-router';
import CharactersList from './components/CharactersList.vue';
import CreateProject from './components/CreateProject.vue';
import SelectProject from './components/SelectProject.vue';
import ProjectDetails from './components/ProjectDetails.vue';

const routes = [
  { path: '/', redirect: '/create-project' },
  { path: '/create-project', component: CreateProject },
  { path: '/select-project', component: SelectProject },
  { path: '/characters-list', component: CharactersList },
  { path: '/projects/:projectId', component: ProjectDetails },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;