import http from './http';

const multipart = { headers: { 'Content-Type': 'multipart/form-data' } };

export const createScene = (projectId, payload) =>
  http.post(`/scenes/${projectId}`, payload).then((r) => r.data);

export const deleteScene = (sceneId) =>
  http.delete(`/scenes/${sceneId}`).then((r) => r.data);

export const duplicateScene = (sceneId, payload) =>
  http.post(`/scenes/${sceneId}/duplicate`, payload).then((r) => r.data);

// formData: image, time, scene_image_id, scene_image_prompt
export const uploadSceneImage = (sceneId, formData) =>
  http.put(`/scenes/upload-image/${sceneId}`, formData, multipart).then((r) => r.data);

// formData: video
export const uploadSceneVideo = (sceneId, formData) =>
  http.put(`/scenes/upload-video/${sceneId}`, formData, multipart).then((r) => r.data);

// FIXME(api): the backend handler is a stub (`pass`, returns null).
// formData: files[], lowkey, prompt, scene_image_id
export const generateSceneImage = (sceneId, formData) =>
  http.post(`/scenes/generate-image/${sceneId}`, formData, multipart).then((r) => r.data);

// payload: { prompt, duration }. The result arrives over /ws/responses.
export const generateSceneVideo = (sceneId, payload) =>
  http.post(`/scenes/generate-video/${sceneId}`, payload).then((r) => r.data);

// payload: { scene_prompt, style, style_power }
export const fixImagePrompt = (payload) =>
  http.post('/scenes/fix-image-prompt', payload).then((r) => r.data);

// payload: { new_camera_movement, additional_info }
export const fixVideoPrompt = (sceneId, payload) =>
  http.post(`/scenes/fix-video-prompt/${sceneId}`, payload).then((r) => r.data);

// payload: { project_id, full_voiceover_text, selected_voiceover_text_part, additional_info }
export const generateImagePrompts = (payload) =>
  http.post('/scenes/generate-image-prompts', payload).then((r) => r.data);
