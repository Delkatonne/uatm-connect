const form = document.getElementById("registerForm");
const errorBanner = document.getElementById("errorBanner");
const submitBtn = document.getElementById("submitBtn");
const successPanel = document.getElementById("successPanel");

const filiereSelect = document.getElementById("filiere");
const optionSelect = document.getElementById("option");
const anneeEtudeSelect = document.getElementById("anneeEtude");
const classeSelect = document.getElementById("classe");
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

function resetSelect(select, placeholder) {
  select.innerHTML = `<option value="">${placeholder}</option>`;
  select.disabled = true;
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) throw new Error(`Erreur ${response.status} sur ${path}`);
  return response.json();
}

async function loadPrograms() {
  try {
    const data = await apiGet("/academic/programs");
    filiereSelect.innerHTML =
      '<option value="">Sélectionner…</option>' +
      data.items
        .map((p) => `<option value="${p.id}">${p.nom} — ${p.code}</option>`)
        .join("");
  } catch (err) {
    showError("Impossible de charger la liste des filières.");
  }
}

async function loadStudyYears() {
  try {
    const data = await apiGet("/academic/study-years");
    anneeEtudeSelect.dataset.items = JSON.stringify(data.items);
  } catch (err) {
    // silencieux : rechargé au moment où l'option est choisie
  }
}

filiereSelect.addEventListener("change", async () => {
  resetSelect(optionSelect, "Chargement…");
  resetSelect(anneeEtudeSelect, "Choisir d'abord une option");
  resetSelect(classeSelect, "—");

  if (!filiereSelect.value) {
    resetSelect(optionSelect, "Choisir d'abord une filière");
    return;
  }

  try {
    const data = await apiGet(`/academic/options?program_id=${filiereSelect.value}`);
    optionSelect.innerHTML =
      '<option value="">Sélectionner…</option>' +
      data.items.map((o) => `<option value="${o.id}">${o.nom} — ${o.code}</option>`).join("");
    optionSelect.disabled = false;
  } catch (err) {
    showError("Impossible de charger les options de cette filière.");
  }
});

optionSelect.addEventListener("change", async () => {
  resetSelect(anneeEtudeSelect, "Chargement…");
  resetSelect(classeSelect, "—");

  if (!optionSelect.value) {
    resetSelect(anneeEtudeSelect, "Choisir d'abord une option");
    return;
  }

  try {
    const data = await apiGet("/academic/study-years");
    anneeEtudeSelect.innerHTML =
      '<option value="">Sélectionner…</option>' +
      data.items.map((y) => `<option value="${y.id}">${y.nom}</option>`).join("");
    anneeEtudeSelect.disabled = false;
  } catch (err) {
    showError("Impossible de charger les années d'étude.");
  }
});

anneeEtudeSelect.addEventListener("change", async () => {
  resetSelect(classeSelect, "Chargement…");

  if (!anneeEtudeSelect.value) {
    resetSelect(classeSelect, "—");
    return;
  }

  try {
    const data = await apiGet(
      `/academic/classes?option_id=${optionSelect.value}&study_year_id=${anneeEtudeSelect.value}`
    );
    if (!data.items.length) {
      classeSelect.innerHTML = '<option value="">Aucune classe disponible</option>';
      classeSelect.disabled = true;
      return;
    }
    classeSelect.innerHTML = data.items
      .map((c) => `<option value="${c.id}">${c.nom}</option>`)
      .join("");
    classeSelect.disabled = false;
  } catch (err) {
    showError("Impossible de charger les classes correspondantes.");
  }
});

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
  if (!classeSelect.value) {
    showError("Merci de sélectionner votre classe.");
    return;
  }
  if (!justificatifInput.files[0]) {
    showError("Le justificatif d'inscription est obligatoire.");
    return;
  }

  const payload = new FormData();
  payload.append("nom_complet", document.getElementById("nomComplet").value.trim());
  payload.append("email", document.getElementById("email").value.trim());
  payload.append("telephone", document.getElementById("telephone").value.trim());
  payload.append("mot_de_passe", motDePasse);
  payload.append("confirmation_mot_de_passe", confirmation);
  payload.append("classe_id", classeSelect.value);
  payload.append(
    "annee_inscription",
    document.getElementById("anneeInscription").value
  );
  payload.append("justificatif", justificatifInput.files[0]);

  submitBtn.disabled = true;
  submitBtn.textContent = "Envoi en cours…";

  try {
    const response = await fetch(`${API_BASE_URL}/auth/register/student`, {
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

loadPrograms();
loadStudyYears();