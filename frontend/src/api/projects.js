import http from './http';

export const listProjects = () =>
  http.get('/projects').then((r) => r.data);

export const getProject = (projectId) =>
  http.get(`/projects/${projectId}`).then((r) => r.data);

export const generateScript = (payload) =>
  http.post('/projects/generate-script', payload).then((r) => r.data);

export const createProject = (payload) =>
  http.post('/projects/create-project', payload).then((r) => r.data);

// payload: { timeline_elements }
export const updateProject = (projectId, payload) =>
  http.put(`/projects/${projectId}`, payload).then((r) => r.data);

export const deleteProject = (projectId) =>
  http.delete(`/projects/${projectId}`).then((r) => r.data);

// FIXME(api): the backend renders the video synchronously and returns JSON
// ({ message: "success" }), not the video file. ProjectActions saves it as a .mp4.
export const downloadProject = (projectId) =>
  http.post(`/projects/download/${projectId}`).then((r) => r.data);

export const copyProject = (projectId) =>
  http.post(`/projects/copy/${projectId}`).then((r) => r.data);

// FIXME(api): the backend handler is a stub (returns immediately).
export const addTranslations = (projectId) =>
  http.post(`/projects/add-translations/${projectId}`).then((r) => r.data);
