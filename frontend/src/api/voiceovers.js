import http from './http';

export const createVoiceover = (projectId, payload) =>
  http.post(`/voiceovers/${projectId}`, payload).then((r) => r.data);

export const deleteVoiceover = (voiceoverId) =>
  http.delete(`/voiceovers/${voiceoverId}`).then((r) => r.data);

export const duplicateVoiceover = (voiceoverId, payload) =>
  http.post(`/voiceovers/${voiceoverId}/duplicate`, payload).then((r) => r.data);

// FIXME(api): VoiceoverEditor JSON.parses `text_with_pauses` from this response,
// but the backend response does not include it.
// payload: { text }
export const generateVoiceover = (voiceoverId, payload) =>
  http.post(`/voiceovers/generate/${voiceoverId}`, payload).then((r) => r.data);

export const combineVoiceovers = (projectId) =>
  http.post(`/voiceovers/combine/${projectId}`).then((r) => r.data);
