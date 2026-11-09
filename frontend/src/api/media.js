import { API_BASE_URL } from '@/config';

// Absolute backend URL for a backend-relative path (e.g. `static/...`).
// Plain concatenation, no checks (replaces the former utils/route.js and the
// inline `http://localhost:8000/${src}` strings).
export const backendUrl = (path) => `${API_BASE_URL}/${path}`;

// URL for a media `src` coming from the backend or from a local upload preview
// (replaces the former utils/getSrc.js):
// - empty/falsy -> ''
// - `blob:` object URLs are returned unchanged
// - anything else is treated as backend-relative
export const mediaUrl = (src) => {
  if (!src) return '';
  if (src.startsWith('blob:')) return src;
  return backendUrl(src);
};

// Raw fetch of a media file (absolute or blob: URL). Returns the native Response;
// like fetch, it does not reject on HTTP error statuses.
export const fetchMedia = (url) => fetch(url);
