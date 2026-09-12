function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}

function renderList(containerId, countId, items, emptyLabel, renderItem) {
  const container = document.getElementById(containerId);
  const countEl = document.getElementById(countId);
  countEl.textContent = items.length ? `${items.length}` : "";

  if (!items.length) {
    container.innerHTML = `<div class="empty-state">${emptyLabel}</div>`;
    return;
  }
  container.innerHTML = items.map(renderItem).join("");
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { ...AuthStore.authHeader() },
  });
  if (response.status === 401) {
    window.location.href = "login.html";
    return null;
  }
  if (!response.ok) throw new Error(`Erreur ${response.status} sur ${path}`);
  return response.json();
}

async function loadDashboard() {
  try {
    const me = await apiGet("/student/me");
    if (!me) return;

    document.getElementById("greeting").textContent = `Bonjour, ${me.nom_complet}`;
    document.getElementById("identityLine").innerHTML = `
      <span>Filière : <strong>${me.filiere}</strong></span>
      <span>Option : <strong>${me.option}</strong></span>
      <span>Année : <strong>${me.annee_etude}</strong></span>
      <span>Classe : <strong>${me.classe}</strong></span>
    `;

    const [cours, devoirs, examens, notifications] = await Promise.all([
      apiGet("/student/documents?type=cours"),
      apiGet("/student/documents?type=devoir"),
      apiGet("/student/exams"),
      apiGet("/student/notifications"),
    ]);

    renderList("coursList", "coursCount", cours.items, "Aucun cours publié pour le moment.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}</p>
          <p class="entry-meta">${item.matiere} · ${item.enseignant}</p>
        </div>
        <div class="entry-date">${formatDate(item.date_publication)}</div>
      </div>
    `);

    renderList("devoirsList", "devoirsCount", devoirs.items, "Aucun devoir en cours.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}</p>
          <p class="entry-meta">${item.matiere} · ${item.enseignant}</p>
        </div>
        <div class="entry-date">${formatDate(item.date_publication)}</div>
      </div>
    `);

    renderList("examensList", "examensCount", examens.items, "Aucun examen programmé.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}</p>
          <p class="entry-meta">${item.matiere} · Salle ${item.salle}</p>
        </div>
        <div class="entry-date">${formatDate(item.date)} · ${item.heure}</div>
      </div>
    `);

    renderList("notifList", "notifCount", notifications.items, "Aucune notification.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}${item.lu ? "" : ' <span class="badge attente">Nouveau</span>'}</p>
          <p class="entry-meta">${item.message}</p>
        </div>
        <div class="entry-date">${formatDate(item.date)}</div>
      </div>
    `);

    const adminDocs = await apiGet("/student/academic-programs");
    renderList("adminDocsList", "adminDocsCount", adminDocs.items, "Aucun document administratif pour le moment.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}</p>
          <p class="entry-meta">${item.annee_academique || ""}</p>
        </div>
        <div class="entry-date">${formatDate(item.date_publication)}</div>
      </div>
    `);

    document.getElementById("profilInfo").textContent = `${me.email}${me.telephone ? " · " + me.telephone : ""}`;
    document.getElementById("profilTelephone").value = me.telephone || "";
  } catch (err) {
    console.error(err);
  }
}

const toast = document.getElementById("toast");
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  setTimeout(() => toast.classList.remove("visible"), 2800);
}

document.getElementById("profilSaveBtn").addEventListener("click", async () => {
  const formData = new FormData();
  formData.append("telephone", document.getElementById("profilTelephone").value.trim());
  const photo = document.getElementById("profilPhoto").files[0];
  if (photo) formData.append("photo", photo);

  try {
    const response = await fetch(`${API_BASE_URL}/student/me`, {
      method: "PATCH",
      headers: { ...AuthStore.authHeader() },
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur lors de la mise à jour.");
    showToast("Profil mis à jour.");
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("passwordForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const nouveau = document.getElementById("pwdNouveau").value;
  const confirm = document.getElementById("pwdConfirm").value;
  if (nouveau !== confirm) {
    showToast("Les mots de passe ne correspondent pas.", true);
    return;
  }
  try {
    const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...AuthStore.authHeader() },
      body: JSON.stringify({
        mot_de_passe_actuel: document.getElementById("pwdActuel").value,
        nouveau_mot_de_passe: nouveau,
        confirmation: confirm,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur lors du changement de mot de passe.");
    showToast("Mot de passe mis à jour.");
    e.target.reset();
  } catch (err) {
    showToast(err.message, true);
  }
});

loadDashboard();