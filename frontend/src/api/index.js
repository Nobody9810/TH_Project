// import axios from 'axios';

// const API_URL = 'http://127.0.0.1:8000/api';

// const api = axios.create({
//   baseURL: API_URL,
//   headers: {
//     'Content-Type': 'application/json',
//   },
// });

// // Token 拦截器
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('access');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// export const login = async (username, password) => {
//   const res = await axios.post('http://127.0.0.1:8000/api/auth/token/', { username, password });
//   localStorage.setItem('access', res.data.access);
//   localStorage.setItem('refresh', res.data.refresh);
//   return res.data;
// };

// export const logout = () => {
//   localStorage.removeItem('access');
//   localStorage.removeItem('refresh');
// };

// export const getHotels = async () => {
//   const res = await api.get('/materials/');
//   return res.data;
// };

// export const getQuestions = async () => {
//   const res = await api.get('/supportticket/');
//   return res.data;
// };

// export const getUserProfile = async () => {
//   const res = await api.get('/me/');
//   return res.data;
// };



// export default api;
