// Single source of truth for backend locations.
// Override at build/serve time via frontend/.env.local (vue-cli `VUE_APP_*` convention).

const stripTrailingSlash = (url) => url.replace(/\/+$/, '');

export const API_BASE_URL = stripTrailingSlash(
  process.env.VUE_APP_API_URL || 'http://localhost:8000'
);

// Defaults to the API URL with http(s) -> ws(s).
export const WS_BASE_URL = stripTrailingSlash(
  process.env.VUE_APP_WS_URL || API_BASE_URL.replace(/^http/, 'ws')
);
