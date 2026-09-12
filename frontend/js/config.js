// Point d'entrée unique pour configurer l'URL de l'API Flask.
// En développement, adapter au port réel du backend (ex: http://localhost:5000/api).
const API_BASE_URL = "https://uatm-connect.onrender.com/api";

// Stockage du token en mémoire pour la session de navigation en cours.
// Pour une vraie mise en production, préférer un cookie httpOnly côté serveur
// plutôt qu'un stockage accessible en JavaScript.
const AuthStore = {
  token: null,
  user: null,
  setSession(token, user) {
    this.token = token;
    this.user = user;
  },
  clearSession() {
    this.token = null;
    this.user = null;
  },
  authHeader() {
    return this.token ? { Authorization: `Bearer ${this.token}` } : {};
  },
};
