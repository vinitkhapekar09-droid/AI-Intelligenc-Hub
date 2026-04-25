import axios from "axios";

const defaultApiBase = "/api";
const configuredBaseUrl = import.meta.env.VITE_API_BASE || defaultApiBase;

const api = axios.create({
  baseURL: configuredBaseUrl.replace(/\/$/, ""),
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.clear();
      window.location = "/auth";
    }
    return Promise.reject(error);
  }
);

export default api;
