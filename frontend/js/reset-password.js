const form = document.getElementById("resetForm");
const errorBanner = document.getElementById("errorBanner");
const submitBtn = document.getElementById("submitBtn");
const successPanel = document.getElementById("successPanel");

const params = new URLSearchParams(window.location.search);
const token = params.get("token");

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.add("visible");
}

function hideError() {
  errorBanner.classList.remove("visible");
}

if (!token) {
  showError("Ce lien est invalide. Refaites une demande de réinitialisation depuis la page de connexion.");
  submitBtn.disabled = true;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const nouveauMotDePasse = document.getElementById("nouveauMotDePasse").value;
  const confirmation = document.getElementById("confirmation").value;

  if (nouveauMotDePasse !== confirmation) {
    showError("Les mots de passe ne correspondent pas.");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Mise à jour…";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, nouveau_mot_de_passe: nouveauMotDePasse, confirmation }),
    });
    const data = await response.json();

    if (!response.ok) {
      showError(data.message || "Une erreur est survenue.");
      submitBtn.disabled = false;
      submitBtn.textContent = "Mettre à jour le mot de passe";
      return;
    }

    form.style.display = "none";
    successPanel.classList.add("visible");
  } catch (err) {
    showError("Impossible de joindre le serveur. Réessayez dans un instant.");
    submitBtn.disabled = false;
    submitBtn.textContent = "Mettre à jour le mot de passe";
  }
});