import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const demoMode = (import.meta.env.VITE_DEMO_MODE ?? "false") === "true";

const client = axios.create({
  baseURL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" }
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("bis_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem("bis_refresh_token");
        const res = await axios.post(`${baseURL}/api/auth/refresh`, { refresh_token: refreshToken });
        const { access_token, refresh_token } = res.data;
        localStorage.setItem("bis_access_token", access_token);
        localStorage.setItem("bis_refresh_token", refresh_token);
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return client(originalRequest);
      } catch (e) {
        localStorage.removeItem("bis_access_token");
        localStorage.removeItem("bis_refresh_token");
        localStorage.removeItem("bis_user");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  auth: {
    register: async (name, email, password) => {
      if (demoMode) return demo.auth.register();
      const res = await client.post("/api/auth/register", { name, email, password });
      return res.data;
    },
    login: async (email, password) => {
      if (demoMode) return demo.auth.login();
      const res = await client.post("/api/auth/login", { email, password });
      return res.data;
    },
    refresh: async (refreshToken) => {
      if (demoMode) return demo.auth.refresh();
      const res = await client.post("/api/auth/refresh", { refresh_token: refreshToken });
      return res.data;
    },
    logout: async (refreshToken) => {
      if (demoMode) return demo.auth.logout();
      await client.post("/api/auth/logout", { refresh_token: refreshToken });
    },
    me: async () => {
      if (demoMode) return demo.auth.me();
      const res = await client.get("/api/auth/me");
      return res.data;
    }
  },
  dashboard: async () => demoMode ? demo.dashboard : (await client.get("/api/dashboard")).data,
  standards: async (params) => demoMode ? demo.standards : (await client.get("/api/standards", { params })).data,
  standardCategories: async () => demoMode ? demo.categories : (await client.get("/api/standards/categories")).data,
  standardDetail: async (id) => demoMode ? demo.standards.find(s => s.id === id) : (await client.get(`/api/standards/${id}`)).data,
  chat: async (message) => demoMode ? ({ answer: "Demo mode is active. Your question was: " + message }) : (await client.post("/api/chat", { message })).data,
  analyze: async (formData) => demoMode ? ({ status: "demo" }) : (await client.post("/api/product/analyze", formData, { headers: { "Content-Type": "multipart/form-data" } })).data,
  compliance: {
    check: async (payload) => demoMode ? ({ status: "demo" }) : (await client.post("/api/compliance/check", payload)).data,
    overview: async () => demoMode ? ({ status: "demo" }) : (await client.get("/api/compliance/overview")).data,
    checks: async () => demoMode ? ({ status: "demo" }) : (await client.get("/api/compliance/checks")).data,
    checkDetail: async (id) => demoMode ? ({ status: "demo" }) : (await client.get(`/api/compliance/checks/${id}`)).data,
  },
  compare: async (payload) => demoMode ? ({ status: "demo" }) : (await client.post("/api/compare", payload)).data,
  laboratories: async (params) => demoMode ? demo.labs : (await client.get("/api/laboratories", { params })).data,
  qco: async (params) => demoMode ? [] : (await client.get("/api/qco", { params })).data,
  hallmarking: async (params) => demoMode ? [] : (await client.get("/api/hallmarking", { params })).data,
  consumer: async (params) => demoMode ? [] : (await client.get("/api/consumer", { params })).data,
  certification: async (params) => demoMode ? demo.certification : (await client.get("/api/certification/roadmap", { params })).data,
  history: async () => demoMode ? demo.history : (await client.get("/api/history")).data,
  health: async () => demoMode ? { status: "ok", db: "sqlite" } : (await client.get("/api/health")).data,
};

export const demo = {
  dashboard: { standards: "1,248", searches: "86", reports: "24", checks: "17" },
  standards: [
    { id: "1", is_number: "IS 14543", title: "Packaged Drinking Water", category: "Food & Beverage", status: "Active", description: "Requirements and related product context for packaged drinking water." },
    { id: "2", is_number: "IS 302", title: "Safety of Household and Similar Electrical Appliances", category: "Electrical", status: "Active", description: "General safety requirements for household and similar electrical appliances." },
    { id: "3", is_number: "IS 16000", title: "Indoor Air Quality", category: "Environment", status: "Active", description: "Methods and guidance associated with indoor air quality assessment." }
  ],
  categories: ["Food & Beverage", "Electrical", "Environment", "Construction", "Automotive", "Safety Equipment", "Lighting", "Cement", "Electrical Cables"],
  activity: [
    { title: "Searched for packaged drinking water", meta: "Standards Explorer", time: "12 min ago" },
    { title: "Compared two standards", meta: "Compare workspace", time: "1 hr ago" },
    { title: "Generated compliance checklist", meta: "Compliance Assistant", time: "Yesterday" }
  ],
  chat: [
    { role: "assistant", text: "Hi! I'm BISense AI. Ask me about Indian Standards, BIS certification, testing, hallmarking, packaged commodities or related services." }
  ],
  labs: [],
  certification: { is_number: "IS 302-2-1", title: "Safety of Electric Water Heaters", scheme: "ISI Mark", scheme_type: "Compulsory Certification", steps: [], documents_required: [] },
  history: [],
  auth: {
    register: () => ({ access_token: "demo_access", refresh_token: "demo_refresh", token_type: "bearer", expires_in: 86400, user: { id: "demo", email: "demo@bisense.ai", name: "Demo User", role: "user" } }),
    login: () => ({ access_token: "demo_access", refresh_token: "demo_refresh", token_type: "bearer", expires_in: 86400, user: { id: "demo", email: "demo@bisense.ai", name: "Demo User", role: "user" } }),
    refresh: () => ({ access_token: "demo_access", refresh_token: "demo_refresh", token_type: "bearer", expires_in: 86400 }),
    logout: () => ({}),
    me: () => ({ id: "demo", email: "demo@bisense.ai", name: "Demo User", role: "user" })
  }
};