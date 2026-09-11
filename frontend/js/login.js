const form = document.getElementById("loginForm");
const errorBanner = document.getElementById("errorBanner");
const submitBtn = document.getElementById("submitBtn");
const roleButtons = document.querySelectorAll("#roleSwitch button");

let selectedRole = "etudiant";

roleButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    roleButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    selectedRole = btn.dataset.role;
  });
});

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.add("visible");
}

function hideError() {
  errorBanner.classList.remove("visible");
}

function redirectForRole(role) {
  if (role === "etudiant") window.location.href = "student-dashboard.html";
  else if (role === "enseignant") window.location.href = "teacher-dashboard.html";
  else window.location.href = "admin-dashboard.html";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;

  if (!email || !password) {
    showError("Merci de renseigner votre e-mail et votre mot de passe.");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Connexion…";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, mot_de_passe: password }),
    });

    const data = await response.json();

    if (!response.ok) {
      if (response.status === 403 && data.statut) {
        showError(messageForStatus(data.statut));
      } else {
        showError(data.message || "Identifiants incorrects.");
      }
      return;
    }

    AuthStore.setSession(data.access_token, data.user);
    redirectForRole(data.user.role);
  } catch (err) {
    showError("Impossible de joindre le serveur. Réessayez dans un instant.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Se connecter";
  }
});

function messageForStatus(statut) {
  const messages = {
    en_attente_de_validation:
      "Votre compte est en attente de validation par l'administration.",
    refuse: "Votre inscription a été refusée. Contactez l'administration.",
    piece_a_fournir:
      "Une nouvelle pièce justificative est demandée pour valider votre compte.",
  };
  return messages[statut] || "Votre compte n'est pas encore actif.";
}
