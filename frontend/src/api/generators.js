import http from './http';

// FIXME(api): the backend handler is a stub (returns immediately) and declares an
// untyped `request` param, so this likely returns 422; `fixed_prompt` is never returned.
// payload: { prompt }
export const fixCharacterPrompt = (payload) =>
  http.post('/generators/fix-character-prompt', payload).then((r) => r.data);
