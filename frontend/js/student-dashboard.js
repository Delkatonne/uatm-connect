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
  } catch (err) {
    console.error(err);
  }
}

loadDashboard();
