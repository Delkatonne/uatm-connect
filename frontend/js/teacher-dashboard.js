const toast = document.getElementById("toast");
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  setTimeout(() => toast.classList.remove("visible"), 2800);
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: { ...AuthStore.authHeader() } });
  if (response.status === 401) {
    window.location.href = "login.html";
    return null;
  }
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).message || `Erreur ${response.status}`);
  return response.json();
}

async function apiPostJson(path, body) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...AuthStore.authHeader() },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || `Erreur ${response.status}`);
  return data;
}

async function apiPostForm(path, formData) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { ...AuthStore.authHeader() },
    body: formData,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || `Erreur ${response.status}`);
  return data;
}

function fillSelect(select, items, valueKey, labelFn) {
  select.innerHTML =
    '<option value="">Sélectionner…</option>' +
    items.map((item) => `<option value="${item[valueKey]}">${labelFn(item)}</option>`).join("");
}

function formatDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}

// ---------- Navigation ----------

document.querySelectorAll(".tab-link").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".tab-link").forEach((l) => l.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    link.classList.add("active");
    document.getElementById(`tab-${link.dataset.tab}`).classList.add("active");
  });
});

// ---------- Accueil ----------

async function loadHome() {
  const me = await apiGet("/teacher/me");
  if (!me) return;

  document.getElementById("greeting").textContent = `Bonjour, ${me.nom_complet}`;
  document.getElementById("identityLine").innerHTML = `
    <span>Filière : <strong>${me.departement || "—"}</strong></span>
    <span>Fonction : <strong>${me.fonction || "—"}</strong></span>
  `;

  const [classes, subjects] = await Promise.all([
    apiGet("/teacher/classes"),
    apiGet("/teacher/subjects"),
  ]);

  document.getElementById("classesCount").textContent = classes.items.length || "";
  document.getElementById("classesList").innerHTML = classes.items.length
    ? classes.items
        .map(
          (c) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${c.nom}</p>
          <p class="entry-meta">${c.filiere} — ${c.option} — ${c.annee_etude}</p>
        </div>
      </div>`
        )
        .join("")
    : '<div class="empty-state">Aucune classe affectée pour le moment.</div>';

  document.getElementById("subjectsCount").textContent = subjects.items.length || "";
  document.getElementById("subjectsList").innerHTML = subjects.items.length
    ? subjects.items
        .map(
          (s) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${s.nom}</p>
          <p class="entry-meta">${s.filiere} — ${s.annee_etude}</p>
        </div>
      </div>`
        )
        .join("")
    : '<div class="empty-state">Aucune matière affectée pour le moment.</div>';

  return { classes: classes.items, subjects: subjects.items };
}

// ---------- Publication ----------

function populateClassSubjectSelects(classes, subjects) {
  fillSelect(document.getElementById("docClasse"), classes, "id", (c) => c.nom);
  fillSelect(document.getElementById("docSubject"), subjects, "id", (s) => s.nom);
  fillSelect(document.getElementById("examClasse"), classes, "id", (c) => c.nom);
  fillSelect(document.getElementById("examSubject"), subjects, "id", (s) => s.nom);
  fillSelect(document.getElementById("gradeClasse"), classes, "id", (c) => c.nom);
  fillSelect(document.getElementById("gradeSubject"), subjects, "id", (s) => s.nom);
}

document.getElementById("docFichier").addEventListener("change", (e) => {
  document.getElementById("docFileName").textContent = e.target.files[0]
    ? `Fichier sélectionné : ${e.target.files[0].name}`
    : "";
});

document.getElementById("publishForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData();
  formData.append("classe_id", document.getElementById("docClasse").value);
  formData.append("subject_id", document.getElementById("docSubject").value);
  formData.append("type", document.getElementById("docType").value);
  formData.append("titre", document.getElementById("docTitre").value.trim());
  formData.append("description", document.getElementById("docDescription").value.trim());
  formData.append("fichier", document.getElementById("docFichier").files[0]);

  try {
    await apiPostForm("/teacher/documents", formData);
    showToast("Document publié — la classe a été notifiée.");
    e.target.reset();
    document.getElementById("docFileName").textContent = "";
    loadPublications();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("examForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await apiPostJson("/teacher/exams", {
      classe_id: document.getElementById("examClasse").value,
      subject_id: document.getElementById("examSubject").value,
      titre: document.getElementById("examTitre").value.trim(),
      date: document.getElementById("examDate").value,
      heure: document.getElementById("examHeure").value,
      salle: document.getElementById("examSalle").value.trim(),
    });
    showToast("Examen publié — la classe a été notifiée.");
    e.target.reset();
    loadExams();
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- Mes publications ----------

async function loadPublications() {
  const data = await apiGet("/teacher/documents");
  document.getElementById("publicationsList").innerHTML = data.items.length
    ? data.items
        .map(
          (d) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${d.titre} <span class="badge attente">${d.type}</span></p>
          <p class="entry-meta">${d.matiere || ""}</p>
        </div>
        <div class="entry-date">${formatDate(d.date_publication)}</div>
      </div>`
        )
        .join("")
    : '<div class="empty-state">Aucune publication pour le moment.</div>';
}

// ---------- Examens ----------

async function loadExams() {
  const data = await apiGet("/teacher/exams");
  document.getElementById("examensList").innerHTML = data.items.length
    ? data.items
        .map(
          (ex) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${ex.titre}</p>
          <p class="entry-meta">${ex.matiere || ""} · Salle ${ex.salle || "—"}</p>
        </div>
        <div class="entry-date">${formatDate(ex.date)} · ${ex.heure}</div>
      </div>`
        )
        .join("")
    : '<div class="empty-state">Aucun examen programmé.</div>';
}

// ---------- Emploi du temps ----------

const JOURS_ORDRE = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];

async function loadScheduleSemesters() {
  // Semestres visibles indirectement via les affectations de l'enseignant
  const assignments = await apiGet("/teacher/assignments");
  const semesters = {};
  assignments.items.forEach((a) => {
    if (a.semester_id) semesters[a.semester_id] = a.semestre + " — " + a.annee_academique;
  });
  const select = document.getElementById("scheduleSemester");
  select.innerHTML = Object.entries(semesters)
    .map(([id, label]) => `<option value="${id}">${label}</option>`)
    .join("");

  const gradeSemesterSelect = document.getElementById("gradeSemester");
  if (gradeSemesterSelect) {
    gradeSemesterSelect.innerHTML =
      '<option value="">Sans semestre</option>' +
      Object.entries(semesters)
        .map(([id, label]) => `<option value="${id}">${label}</option>`)
        .join("");
  }

  if (select.value) loadSchedule(select.value);
  select.addEventListener("change", () => loadSchedule(select.value));
  if (select.options.length) loadSchedule(select.options[0].value);
}

async function loadSchedule(semesterId) {
  if (!semesterId) return;
  const data = await apiGet(`/teacher/schedule?semester_id=${semesterId}`);
  const sorted = data.items.sort(
    (a, b) => JOURS_ORDRE.indexOf(a.jour_semaine) - JOURS_ORDRE.indexOf(b.jour_semaine)
  );
  document.querySelector("#scheduleTable tbody").innerHTML = sorted.length
    ? sorted
        .map(
          (s) =>
            `<tr><td>${s.jour_semaine}</td><td>${s.heure_debut}–${s.heure_fin}</td><td>${s.matiere || "—"}</td><td>${s.classe || "—"}</td><td>${s.salle || "—"}</td></tr>`
        )
        .join("")
    : '<tr><td colspan="5">Aucun créneau pour ce semestre.</td></tr>';
}

// ---------- Notes ----------

document.getElementById("gradeSetupForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const classeId = document.getElementById("gradeClasse").value;

  try {
    const data = await apiGet(`/teacher/classes/${classeId}/students`);
    const table = document.getElementById("gradeEntryTable");
    const tbody = table.querySelector("tbody");

    if (!data.items.length) {
      tbody.innerHTML = '<tr><td colspan="2">Aucun étudiant dans cette classe.</td></tr>';
    } else {
      tbody.innerHTML = data.items
        .map(
          (s) => `
        <tr data-student-id="${s.student_id}">
          <td>${s.nom_complet}</td>
          <td><input type="number" min="0" max="20" step="0.25" class="grade-input" style="width:80px; padding:6px 8px; border:1px solid var(--slate-light); border-radius:3px;" /></td>
        </tr>`
        )
        .join("");
    }

    table.style.display = "table";
    document.getElementById("saveGradesBtn").style.display = "inline-block";
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("saveGradesBtn").addEventListener("click", async () => {
  const rows = document.querySelectorAll("#gradeEntryTable tbody tr[data-student-id]");
  const entries = [];
  rows.forEach((row) => {
    const input = row.querySelector(".grade-input");
    if (input && input.value !== "") {
      entries.push({ student_id: row.dataset.studentId, valeur: parseFloat(input.value) });
    }
  });

  if (!entries.length) {
    showToast("Renseignez au moins une note.", true);
    return;
  }

  try {
    await apiPostJson("/teacher/grades", {
      classe_id: document.getElementById("gradeClasse").value,
      subject_id: document.getElementById("gradeSubject").value,
      type: document.getElementById("gradeType").value,
      semester_id: document.getElementById("gradeSemester").value || null,
      entries,
    });
    showToast("Notes enregistrées — les étudiants ont été notifiés.");
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- Notifications ----------

async function loadNotifications() {
  const data = await apiGet("/teacher/notifications");
  document.getElementById("notifList").innerHTML = data.items.length
    ? data.items
        .map(
          (n) => `
      <div class="entry-row notif-row" data-notif-id="${n.id}" data-lu="${n.lu}" style="cursor:pointer;">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${n.titre}${n.lu ? "" : ' <span class="badge attente">Nouveau</span>'}</p>
          <p class="entry-meta">${n.message}</p>
        </div>
        <div class="entry-date">${formatDate(n.date)}</div>
      </div>`
        )
        .join("")
    : '<div class="empty-state">Aucune notification.</div>';

  document.querySelectorAll(".notif-row").forEach((row) => {
    if (row.dataset.lu === "true") return;
    row.addEventListener("click", async () => {
      try {
        await apiPostJsonPatch(`/teacher/notifications/${row.dataset.notifId}/read`);
        row.querySelector(".badge")?.remove();
        row.dataset.lu = "true";
      } catch (err) {
        console.error(err);
      }
    });
  });
}

async function apiPostJsonPatch(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PATCH",
    headers: { ...AuthStore.authHeader() },
  });
  if (!response.ok) throw new Error(`Erreur ${response.status}`);
  return response.json();
}

// ---------- Documents administratifs ----------

async function loadAdminDocs() {
  const data = await apiGet("/teacher/academic-programs");
  document.getElementById("adminDocsList").innerHTML = data.items.length
    ? data.items
        .map(
          (d) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${d.titre}</p>
          <p class="entry-meta">${d.annee_academique || ""}</p>
        </div>
        <div class="entry-date">${formatDate(d.date_publication)}</div>
      </div>`
        )
        .join("")
    : '<div class="empty-state">Aucun document administratif pour le moment.</div>';
}

// ---------- Mon profil ----------

async function loadProfilSection(me) {
  document.getElementById("profilInfo").textContent = `${me.email}${me.telephone ? " · " + me.telephone : ""}`;
  document.getElementById("profilTelephone").value = me.telephone || "";
}

document.getElementById("profilSaveBtn").addEventListener("click", async () => {
  const formData = new FormData();
  formData.append("telephone", document.getElementById("profilTelephone").value.trim());
  const photo = document.getElementById("profilPhoto").files[0];
  if (photo) formData.append("photo", photo);

  try {
    const response = await fetch(`${API_BASE_URL}/teacher/me`, {
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
  const confirmValue = document.getElementById("pwdConfirm").value;
  if (nouveau !== confirmValue) {
    showToast("Les mots de passe ne correspondent pas.", true);
    return;
  }
  try {
    await apiPostJson("/auth/change-password", {
      mot_de_passe_actuel: document.getElementById("pwdActuel").value,
      nouveau_mot_de_passe: nouveau,
      confirmation: confirmValue,
    });
    showToast("Mot de passe mis à jour.");
    e.target.reset();
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- Initialisation ----------

async function init() {
  try {
    const home = await loadHome();
    if (home) populateClassSubjectSelects(home.classes, home.subjects);
    await loadPublications();
    await loadExams();
    await loadScheduleSemesters();
    await loadNotifications();
    await loadAdminDocs();

    const me = await apiGet("/teacher/me");
    await loadProfilSection(me);
  } catch (err) {
    showToast(err.message, true);
  }
}

init();