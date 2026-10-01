import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

let isRefreshing = false;

let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: Error | null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(null);
    }
  });
  failedQueue = [];
};

// Таймаут для refresh, чтобы isRefreshing не завис
const REFRESH_TIMEOUT = 10000; // 10 секунд

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    const url = originalRequest.url || '';
    if (
      url.includes('/auth/login') ||
      url.includes('/auth/refresh') ||
      url.includes('/auth/register')
    ) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then(() => apiClient(originalRequest))
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      await axios.post(`${API_BASE_URL}/auth/refresh`, null, {
        withCredentials: true,
        timeout: REFRESH_TIMEOUT,
      });

      processQueue(null);
      isRefreshing = false;

      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError as Error);
      isRefreshing = false;

      const path = window.location.pathname;
      const isAuthPage =
        path.includes('/login') ||
        path.includes('/register') ||
        path.includes('/join');

      if (!isAuthPage) {
        // SPA-переход через кастомное событие
        window.dispatchEvent(new CustomEvent('auth:expired'));
      }

      return Promise.reject(refreshError);
    }
  }
);

export default apiClient;