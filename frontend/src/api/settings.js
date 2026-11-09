import http from './http';

export const getSettings = () =>
  http.get('/settings').then((r) => r.data);

// Partial update: send only the keys being changed.
export const updateSettings = (payload) =>
  http.put('/settings', payload).then((r) => r.data);
