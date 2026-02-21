import { createRouter, createWebHistory } from 'vue-router';
import CharactersList from './components/CharactersList.vue';
import CreateProject from './components/CreateProject.vue';
import SelectProject from './pages/ProjectsList.vue';
import ProjectDetails from './components/ProjectDetails.vue';
import CreatePhotoDump from './components/CreatePhotoDump.vue';
import ImagesPackage from './components/ImagesPackage.vue';
import PhotoDumpProjectDetails from './components/PhotoDumpProjectDetails.vue';

const routes = [
  { path: '/', redirect: '/create-project' },
  { path: '/create-project', component: CreateProject },
  { path: '/create-photo-dump', component: CreatePhotoDump },
  { path: '/images-packages/:packageId', component: ImagesPackage },
  { path: '/select-project', component: SelectProject },
  { path: '/photo-dump-projects/:projectId', component: PhotoDumpProjectDetails },
  { path: '/characters-list', component: CharactersList },
  { path: '/projects/:projectId', component: ProjectDetails },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;