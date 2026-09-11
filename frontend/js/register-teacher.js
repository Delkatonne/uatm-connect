const form = document.getElementById("registerForm");
const errorBanner = document.getElementById("errorBanner");
const submitBtn = document.getElementById("submitBtn");
const successPanel = document.getElementById("successPanel");

const departementSelect = document.getElementById("departement");
const justificatifInput = document.getElementById("justificatif");
const fileNameEl = document.getElementById("fileName");

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.add("visible");
  errorBanner.scrollIntoView({ behavior: "smooth", block: "center" });
}

function hideError() {
  errorBanner.classList.remove("visible");
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw new Error(`Erreur ${response.status} sur ${path}`);
  return response.json();
}

async function loadDepartements() {
  try {
    const data = await apiGet("/academic/programs");
    departementSelect.innerHTML =
      '<option value="">Sélectionner…</option>' +
      data.items
        .map((p) => `<option value="${p.id}">${p.nom} — ${p.code}</option>`)
        .join("");
  } catch (err) {
    showError("Impossible de charger la liste des filières/départements.");
  }
}

justificatifInput.addEventListener("change", () => {
  fileNameEl.textContent = justificatifInput.files[0]
    ? `Fichier sélectionné : ${justificatifInput.files[0].name}`
    : "";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const motDePasse = document.getElementById("motDePasse").value;
  const confirmation = document.getElementById("confirmation").value;

  if (motDePasse !== confirmation) {
    showError("Les mots de passe ne correspondent pas.");
    return;
  }
  if (!departementSelect.value) {
    showError("Merci de sélectionner votre filière/département.");
    return;
  }
  if (!justificatifInput.files[0]) {
    showError("Le justificatif est obligatoire.");
    return;
  }

  const payload = new FormData();
  payload.append("nom_complet", document.getElementById("nomComplet").value.trim());
  payload.append("email", document.getElementById("email").value.trim());
  payload.append("telephone", document.getElementById("telephone").value.trim());
  payload.append("mot_de_passe", motDePasse);
  payload.append("confirmation_mot_de_passe", confirmation);
  payload.append("departement_id", departementSelect.value);
  payload.append("fonction", document.getElementById("fonction").value.trim());
  payload.append("matieres_declarees", document.getElementById("matieres").value.trim());
  payload.append("justificatif", justificatifInput.files[0]);

  submitBtn.disabled = true;
  submitBtn.textContent = "Envoi en cours…";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/register/teacher`, {
      method: "POST",
      body: payload,
    });
    const data = await response.json();

    if (!response.ok) {
      showError(data.message || "Une erreur est survenue lors de l'inscription.");
      return;
    }

    form.style.display = "none";
    successPanel.classList.add("visible");
  } catch (err) {
    showError("Impossible de joindre le serveur. Réessayez dans un instant.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Envoyer ma demande d'inscription";
  }
});

loadDepartements();