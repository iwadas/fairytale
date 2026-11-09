import http from './http';

// FIXME(api): the backend characters router is not mounted (backend/main.py has
// `# app.include_router(characters_router)`), so every call below currently 404s.

const multipart = { headers: { 'Content-Type': 'multipart/form-data' } };

export const listCharacters = () =>
  http.get('/characters').then((r) => r.data);

// formData: name, prompt, image1, image2?
export const createCharacter = (formData) =>
  http.post('/characters', formData, multipart).then((r) => r.data);

// formData: name, prompt, image1, image2?, id
export const updateCharacter = (characterId, formData) =>
  http.put(`/characters/${characterId}`, formData, multipart).then((r) => r.data);

export const deleteCharacter = (characterId) =>
  http.delete(`/characters/${characterId}`).then((r) => r.data);

// FIXME(api): wrong path. The backend route is GET /characters/images/{character_id}
// (routers/characters.py); the frontend calls /images/characters/{id}. Kept as-is.
// Returns the full axios response (response.data is a Blob).
export const getCharacterImage = (characterId) =>
  http.get(`/images/characters/${characterId}`, { responseType: 'blob' });
