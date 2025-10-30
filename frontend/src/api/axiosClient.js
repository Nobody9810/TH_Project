import axios from 'axios';

const axiosClient = axios.create({
  baseURL: '/api',  // 通过 vite proxy 转发到 Django
  headers: {
    'Content-Type': 'application/json',
  },
});

axiosClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default axiosClient;
