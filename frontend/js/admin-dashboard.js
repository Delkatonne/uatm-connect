// ---------- Utilitaires ----------

const toast = document.getElementById("toast");
function showToast(message, isError = false) {
  toast.textContent = message;
  toast.classList.toggle("error", isError);
  toast.classList.add("visible");
  setTimeout(() => toast.classList.remove("visible"), 2800);
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...AuthStore.authHeader(),
      ...(options.headers || {}),
    },
  });
  if (response.status === 401) {
    window.location.href = "login.html";
    return null;
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.message || `Erreur ${response.status}`);
  return data;
}

const get = (path) => api(path);
const post = (path, body) => api(path, { method: "POST", body: JSON.stringify(body) });
const patch = (path, body) => api(path, { method: "PATCH", body: JSON.stringify(body) });

function fillSelect(select, items, valueKey, labelFn, placeholder) {
  select.innerHTML =
    (placeholder ? `<option value="">${placeholder}</option>` : "") +
    items.map((item) => `<option value="${item[valueKey]}">${labelFn(item)}</option>`).join("");
}

// ---------- Navigation par onglets ----------

document.querySelectorAll(".tab-link").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".tab-link").forEach((l) => l.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    link.classList.add("active");
    document.getElementById(`tab-${link.dataset.tab}`).classList.add("active");
  });
});

// ---------- Vue d'ensemble ----------

async function loadStats() {
  try {
    const s = await get("/admin/stats");
    const labels = {
      etudiants: "Étudiants",
      enseignants: "Enseignants",
      comptes_en_attente: "Comptes en attente",
      comptes_valides: "Comptes validés",
      comptes_refuses: "Comptes refusés",
      filieres: "Filières",
      options: "Options",
      classes: "Classes",
      matieres: "Matières",
    };
    document.getElementById("statGrid").innerHTML = Object.entries(labels)
      .map(
        ([key, label]) => `
        <div class="stat-card">
          <div class="value">${s[key] ?? 0}</div>
          <div class="label">${label}</div>
        </div>`
      )
      .join("");
  } catch (err) {
    showToast(err.message, true);
  }
}

// ---------- Comptes en attente ----------

let currentRoleFilter = "";

async function loadAccounts() {
  try {
    const query = currentRoleFilter ? `?role=${currentRoleFilter}` : "";
    const data = await get(`/admin/accounts${query}`);
    const pending = data.items.filter((u) => u.statut !== "valide" && u.statut !== "refuse");

    if (!pending.length) {
      document.getElementById("accountsList").innerHTML =
        '<div class="empty-state">Aucun compte en attente.</div>';
      return;
    }

    document.getElementById("accountsList").innerHTML = pending
      .map((u) => {
        const details =
          u.role === "etudiant" && u.details
            ? `Classe demandée : ${u.details.classe ? u.details.classe.nom : "—"} · Année d'inscription : ${u.details.annee_inscription}`
            : u.role === "enseignant" && u.details
            ? `Filière : ${u.details.departement || "—"} · Matières déclarées : ${u.details.matieres_declarees || "—"}`
            : "";
        const docLinks = (u.justificatifs || [])
          .map(
            (d) =>
              `<a class="doc-link" href="${API_BASE_URL}/admin/documents/${d.fichier}" target="_blank">Voir le justificatif</a>`
          )
          .join(" · ");

        return `
        <div class="account-card" data-user-id="${u.id}">
          <div class="top-row">
            <div>
              <div class="name">${u.nom_complet} <span class="badge attente">${u.role}</span></div>
              <div class="meta">${u.email}${u.telephone ? " · " + u.telephone : ""}</div>
              <div class="meta">${details}</div>
              <div class="meta">${docLinks}</div>
            </div>
          </div>
          <div class="account-actions">
            <button class="btn-small validate" data-action="validate">Valider</button>
            <button class="btn-small request-doc" data-action="request-document">Demander une pièce</button>
            <button class="btn-small refuse" data-action="refuse">Refuser</button>
          </div>
        </div>`;
      })
      .join("");

    document.querySelectorAll(".account-actions button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const card = btn.closest(".account-card");
        const userId = card.dataset.userId;
        const action = btn.dataset.action;
        try {
          await post(`/admin/accounts/${userId}/${action}`, {});
          showToast("Compte mis à jour.");
          loadAccounts();
          loadStats();
        } catch (err) {
          showToast(err.message, true);
        }
      });
    });
  } catch (err) {
    showToast(err.message, true);
  }
}

document.getElementById("accountRoleFilter").addEventListener("click", (e) => {
  if (e.target.tagName !== "BUTTON") return;
  document.querySelectorAll("#accountRoleFilter button").forEach((b) => b.classList.remove("active"));
  e.target.classList.add("active");
  currentRoleFilter = e.target.dataset.role;
  loadAccounts();
});

// ---------- Filières, options, années, classes ----------

async function loadPrograms() {
  const data = await get("/admin/programs");
  document.querySelector("#programsTable tbody").innerHTML = data.items
    .map((p) => `<tr><td>${p.nom}</td><td>${p.code}</td></tr>`)
    .join("");
  fillSelect(document.getElementById("optionProgram"), data.items, "id", (p) => `${p.nom} — ${p.code}`, "Sélectionner…");
  fillSelect(document.getElementById("ueProgram"), data.items, "id", (p) => `${p.nom} — ${p.code}`, "Sélectionner…");
  return data.items;
}

async function loadOptionsAdmin() {
  const data = await get("/admin/options");
  document.querySelector("#optionsTable tbody").innerHTML = data.items
    .map((o) => `<tr><td>${o.program_id}</td><td>${o.nom}</td><td>${o.code}</td></tr>`)
    .join("");
  fillSelect(document.getElementById("classOption"), data.items, "id", (o) => `${o.nom} — ${o.code}`, "Sélectionner…");
  return data.items;
}

async function loadStudyYearsAdmin() {
  const data = await get("/admin/study-years");
  document.querySelector("#studyYearsTable tbody").innerHTML = data.items
    .map((y) => `<tr><td>${y.nom}</td><td>${y.niveau}</td></tr>`)
    .join("");
  fillSelect(document.getElementById("classStudyYear"), data.items, "id", (y) => y.nom, "Sélectionner…");
  fillSelect(document.getElementById("ueStudyYear"), data.items, "id", (y) => y.nom, "Sélectionner…");
  return data.items;
}

async function loadClassesAdmin() {
  const data = await get("/admin/classes");
  document.querySelector("#classesTable tbody").innerHTML = data.items
    .map((c) => `<tr><td>${c.nom}</td><td>${c.filiere || "—"}</td><td>${c.option || "—"}</td><td>${c.annee_etude || "—"}</td></tr>`)
    .join("");
  fillSelect(document.getElementById("assignClass"), data.items, "id", (c) => c.nom, "Sélectionner…");
  return data.items;
}

document.getElementById("programForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/programs", {
      nom: document.getElementById("programNom").value.trim(),
      code: document.getElementById("programCode").value.trim(),
    });
    e.target.reset();
    showToast("Filière ajoutée.");
    loadPrograms();
    loadStats();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("optionForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/options", {
      program_id: document.getElementById("optionProgram").value,
      nom: document.getElementById("optionNom").value.trim(),
      code: document.getElementById("optionCode").value.trim(),
    });
    e.target.reset();
    showToast("Option ajoutée.");
    loadOptionsAdmin();
    loadStats();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("studyYearForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/study-years", {
      nom: document.getElementById("studyYearNom").value.trim(),
      niveau: parseInt(document.getElementById("studyYearNiveau").value, 10),
    });
    e.target.reset();
    showToast("Année d'étude ajoutée.");
    loadStudyYearsAdmin();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("classForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/classes", {
      option_id: document.getElementById("classOption").value,
      study_year_id: document.getElementById("classStudyYear").value,
      nom: document.getElementById("classNom").value.trim(),
    });
    e.target.reset();
    showToast("Classe ajoutée.");
    loadClassesAdmin();
    loadStats();
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- UE & matières ----------

async function loadUes() {
  const data = await get("/admin/teaching-units");
  document.querySelector("#uesTable tbody").innerHTML = data.items
    .map((u) => `<tr><td>${u.nom}</td><td>${u.filiere || "—"}</td><td>${u.annee_etude || "—"}</td></tr>`)
    .join("");
  fillSelect(document.getElementById("subjectUe"), data.items, "id", (u) => `${u.nom} (${u.filiere} — ${u.annee_etude})`, "Sélectionner…");
  return data.items;
}

async function loadSubjectsAdmin() {
  const data = await get("/admin/subjects");
  document.querySelector("#subjectsTable tbody").innerHTML = data.items
    .map((s) => `<tr><td>${s.nom}</td><td>${s.ue || "—"}</td><td>${s.filiere || "—"}</td><td>${s.annee_etude || "—"}</td></tr>`)
    .join("");
  fillSelect(document.getElementById("assignSubject"), data.items, "id", (s) => `${s.nom} (${s.filiere} — ${s.annee_etude})`, "Sélectionner…");
  return data.items;
}

document.getElementById("ueForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/teaching-units", {
      program_id: document.getElementById("ueProgram").value,
      study_year_id: document.getElementById("ueStudyYear").value,
      nom: document.getElementById("ueNom").value.trim(),
    });
    e.target.reset();
    showToast("UE ajoutée.");
    loadUes();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("subjectForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/subjects", {
      ue_id: document.getElementById("subjectUe").value,
      nom: document.getElementById("subjectNom").value.trim(),
    });
    e.target.reset();
    showToast("Matière ajoutée.");
    loadSubjectsAdmin();
    loadStats();
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- Semestres & affectations ----------

let semestersCache = [];

async function loadSemesters() {
  const data = await get("/admin/semesters");
  semestersCache = data.items;
  fillSelect(document.getElementById("assignSemester"), data.items, "id", (s) => `${s.nom} — ${s.annee_academique}`, "Sélectionner…");
  fillSelect(document.getElementById("publishSemester"), data.items, "id", (s) => `${s.nom} — ${s.annee_academique}`, "Sélectionner…");
  fillSelect(document.getElementById("scheduleFileSemester"), data.items, "id", (s) => `${s.nom} — ${s.annee_academique}`, "Sélectionner…");
  return data.items;
}

async function loadTeachersAdmin() {
  const data = await get("/admin/teachers");
  fillSelect(document.getElementById("assignTeacher"), data.items, "id", (t) => t.nom_complet, "Sélectionner…");
  fillSelect(document.getElementById("publishTeacher"), data.items, "id", (t) => t.nom_complet, "Sélectionner…");
  fillSelect(document.getElementById("scheduleFileTeacher"), data.items, "user_id", (t) => t.nom_complet, "Sélectionner…");
  return data.items;
}

async function loadAssignments() {
  const data = await get("/admin/teacher-assignments");
  document.querySelector("#assignmentsTable tbody").innerHTML = data.items
    .map(
      (a) =>
        `<tr><td>${a.enseignant || "—"}</td><td>${a.matiere || "—"}</td><td>${a.classe || "—"}</td><td>${a.semestre || "—"}</td></tr>`
    )
    .join("");
  fillSelect(
    document.getElementById("slotAssignment"),
    data.items,
    "id",
    (a) => `${a.enseignant} — ${a.matiere} — ${a.classe}`,
    "Sélectionner…"
  );
  return data.items;
}

document.getElementById("semesterForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/semesters", {
      nom: document.getElementById("semesterNom").value.trim(),
      annee_academique: document.getElementById("semesterAnnee").value.trim(),
      date_debut: document.getElementById("semesterDebut").value,
      date_fin: document.getElementById("semesterFin").value,
    });
    e.target.reset();
    showToast("Semestre créé.");
    loadSemesters();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("assignmentForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/teacher-assignments", {
      teacher_id: document.getElementById("assignTeacher").value,
      classe_id: document.getElementById("assignClass").value,
      subject_id: document.getElementById("assignSubject").value,
      semester_id: document.getElementById("assignSemester").value,
    });
    showToast("Affectation créée.");
    loadAssignments();
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- Emploi du temps ----------

async function loadSlots() {
  const data = await get("/admin/schedule-slots");
  document.querySelector("#slotsTable tbody").innerHTML = data.items
    .map(
      (s) =>
        `<tr><td>${s.classe || "—"}</td><td>${s.matiere || "—"} / ${s.classe || "—"}</td><td>${s.jour_semaine}</td><td>${s.heure_debut}–${s.heure_fin}</td><td>${s.salle || "—"}</td></tr>`
    )
    .join("");
}

document.getElementById("slotForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/schedule-slots", {
      assignment_id: document.getElementById("slotAssignment").value,
      jour_semaine: document.getElementById("slotJour").value,
      heure_debut: document.getElementById("slotDebut").value,
      heure_fin: document.getElementById("slotFin").value,
      salle: document.getElementById("slotSalle").value.trim(),
    });
    showToast("Créneau ajouté.");
    loadSlots();
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("publishForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await post("/admin/schedule/publish", {
      teacher_id: document.getElementById("publishTeacher").value,
      semester_id: document.getElementById("publishSemester").value,
    });
    showToast("Enseignant notifié.");
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("scheduleFileInput").addEventListener("change", (e) => {
  document.getElementById("scheduleFileName").textContent = e.target.files[0]
    ? `Fichier sélectionné : ${e.target.files[0].name}`
    : "";
});

document.getElementById("scheduleFileForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const semesterId = document.getElementById("scheduleFileSemester").value;
  const semester = semestersCache.find((s) => s.id === semesterId);

  const formData = new FormData();
  formData.append(
    "titre",
    semester ? `Emploi du temps — ${semester.nom} (${semester.annee_academique})` : "Emploi du temps"
  );
  formData.append("annee_academique", semester ? semester.annee_academique : "");
  formData.append("destinataire_type", "utilisateur");
  formData.append("destinataire_id", document.getElementById("scheduleFileTeacher").value);
  formData.append("fichier", document.getElementById("scheduleFileInput").files[0]);

  try {
    const response = await fetch(`${API_BASE_URL}/admin/academic-programs`, {
      method: "POST",
      headers: { ...AuthStore.authHeader() },
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur lors de l'envoi.");
    showToast("Emploi du temps envoyé à l'enseignant.");
    e.target.reset();
    document.getElementById("scheduleFileName").textContent = "";
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- Programmes & documents administratifs ----------

document.getElementById("progDestinataireType").addEventListener("change", (e) => {
  document.getElementById("progClasseWrapper").style.display =
    e.target.value === "classe" ? "block" : "none";
});

document.getElementById("progFichier").addEventListener("change", (e) => {
  document.getElementById("progFileName").textContent = e.target.files[0]
    ? `Fichier sélectionné : ${e.target.files[0].name}`
    : "";
});

async function loadProgramsList() {
  const data = await get("/admin/academic-programs");
  const labels = {
    classe: "Classe",
    role_etudiant: "Tous les étudiants",
    role_enseignant: "Tous les enseignants",
    tous: "Tout le monde",
    utilisateur: "Utilisateur précis",
  };
  document.querySelector("#programsTable2 tbody").innerHTML = data.items
    .map(
      (p) =>
        `<tr><td>${p.titre}</td><td>${labels[p.destinataire_type] || p.destinataire_type}</td><td>${p.annee_academique || "—"}</td><td>${new Date(p.date_publication).toLocaleDateString("fr-FR")}</td></tr>`
    )
    .join("");
}

document.getElementById("programForm2").addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData();
  formData.append("titre", document.getElementById("progTitre").value.trim());
  formData.append("annee_academique", document.getElementById("progAnnee").value.trim());
  formData.append("destinataire_type", document.getElementById("progDestinataireType").value);
  if (document.getElementById("progDestinataireType").value === "classe") {
    formData.append("destinataire_id", document.getElementById("progClasse").value);
  }
  formData.append("fichier", document.getElementById("progFichier").files[0]);

  try {
    const response = await fetch(`${API_BASE_URL}/admin/academic-programs`, {
      method: "POST",
      headers: { ...AuthStore.authHeader() },
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur lors de l'envoi.");
    showToast("Document envoyé et notifications déclenchées.");
    e.target.reset();
    document.getElementById("progFileName").textContent = "";
    loadProgramsList();
  } catch (err) {
    showToast(err.message, true);
  }
});

// ---------- Initialisation ----------

async function init() {
  await loadStats();
  await loadAccounts();
  await loadPrograms();
  await loadOptionsAdmin();
  await loadStudyYearsAdmin();
  const classes = await loadClassesAdmin();
  await loadUes();
  await loadSubjectsAdmin();
  await loadSemesters();
  await loadTeachersAdmin();
  await loadAssignments();
  await loadSlots();
  await loadProgramsList();

  fillSelect(document.getElementById("progClasse"), classes, "id", (c) => c.nom, "Sélectionner…");
}

init();