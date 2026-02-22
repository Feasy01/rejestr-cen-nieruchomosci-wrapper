import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/v1',
  timeout: 30000,
});

export default apiClient;
