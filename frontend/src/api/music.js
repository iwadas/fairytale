import http from './http';

const multipart = { headers: { 'Content-Type': 'multipart/form-data' } };

export const createMusic = (projectId, payload) =>
  http.post(`/music/${projectId}`, payload).then((r) => r.data);

// payload: { src }
export const updateMusic = (musicId, payload) =>
  http.put(`/music/${musicId}`, payload).then((r) => r.data);

// formData: music_file, music_id
export const uploadMusic = (musicId, formData) =>
  http.put(`/music/upload-music/${musicId}`, formData, multipart).then((r) => r.data);

export const deleteMusic = (musicId) =>
  http.delete(`/music/${musicId}`).then((r) => r.data);

export const duplicateMusic = (musicId, payload) =>
  http.post(`/music/${musicId}/duplicate`, payload).then((r) => r.data);
