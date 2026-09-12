// Point d'entrée unique pour configurer l'URL de l'API Flask.
// En développement, adapter au port réel du backend (ex: http://localhost:5000/api).
const API_BASE_URL = "https://uatm-connect.onrender.com/api";

const AuthStore = {
  setSession(token, user) {
    sessionStorage.setItem("uatm_token", token);
    sessionStorage.setItem("uatm_user", JSON.stringify(user));
  },
  clearSession() {
    sessionStorage.removeItem("uatm_token");
    sessionStorage.removeItem("uatm_user");
  },
  get token() {
    return sessionStorage.getItem("uatm_token");
  },
  get user() {
    const raw = sessionStorage.getItem("uatm_user");
    return raw ? JSON.parse(raw) : null;
  },
  authHeader() {
    const token = this.token;
    return token ? { Authorization: `Bearer ${token}` } : {};
  },
};