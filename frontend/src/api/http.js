import axios from 'axios';
import { API_BASE_URL } from '@/config';

// The one axios instance used by every module in src/api/.
const http = axios.create({
  baseURL: API_BASE_URL,
});

export default http;
