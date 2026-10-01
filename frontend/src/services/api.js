import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  timeout: 30000,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Terjadi kesalahan saat menghubungi server.";
    return Promise.reject(new Error(message));
  }
);

export async function detectImage(file) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/detection/image", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function detectFrame(blob) {
  const formData = new FormData();
  formData.append("file", blob, "frame.jpg");
  const { data } = await api.post("/api/detection/frame", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getHistory(page = 1, pageSize = 10) {
  const { data } = await api.get("/api/detection/history", {
    params: { page, page_size: pageSize },
  });
  return data;
}

export async function getDetectionDetail(id) {
  const { data } = await api.get(`/api/detection/${id}`);
  return data;
}

export async function deleteDetection(id) {
  const { data } = await api.delete(`/api/detection/${id}`);
  return data;
}

export async function getDashboardStats() {
  const { data } = await api.get("/api/dashboard/stats");
  return data;
}

export async function getHealth() {
  const { data } = await api.get("/health");
  return data;
}

export default api;
