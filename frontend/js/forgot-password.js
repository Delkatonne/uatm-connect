const form = document.getElementById("forgotForm");
const errorBanner = document.getElementById("errorBanner");
const submitBtn = document.getElementById("submitBtn");
const successPanel = document.getElementById("successPanel");

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.add("visible");
}

function hideError() {
  errorBanner.classList.remove("visible");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const email = document.getElementById("email").value.trim();
  if (!email) {
    showError("Merci de renseigner votre e-mail.");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Envoi en cours…";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    const data = await response.json();

    if (!response.ok) {
      showError(data.message || "Une erreur est survenue.");
      return;
    }

    form.style.display = "none";
    successPanel.classList.add("visible");
  } catch (err) {
    showError("Impossible de joindre le serveur. Réessayez dans un instant.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Envoyer le lien";
  }
});