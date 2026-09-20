const JOURS_ORDRE = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi"];

async function loadStudentSchedule(semesterId) {
  if (!semesterId) return;
  try {
    const scheduleData = await apiGet(`/student/schedule?semester_id=${semesterId}`);
    if (!scheduleData) return;
    const sorted = scheduleData.items.sort(
      (a, b) => JOURS_ORDRE.indexOf(a.jour_semaine) - JOURS_ORDRE.indexOf(b.jour_semaine)
    );
    document.querySelector("#scheduleTableStudent tbody").innerHTML = sorted.length
      ? sorted
          .map(
            (s) =>
              `<tr><td>${s.jour_semaine}</td><td>${s.heure_debut}–${s.heure_fin}</td><td>${s.matiere || "—"}</td><td>${s.enseignant || "—"}</td><td>${s.salle || "—"}</td></tr>`
          )
          .join("")
      : '<tr><td colspan="5">Aucun créneau pour ce semestre.</td></tr>';
  } catch (err) {
    showToast(err.message, true);
  }
}

async function initEmploi() {
  try {
    const semesters = await apiGet("/student/semesters");
    if (!semesters) return;
    const select = document.getElementById("scheduleSemesterStudent");
    select.innerHTML = semesters.items
      .map((s) => `<option value="${s.id}">${s.nom} — ${s.annee_academique}</option>`)
      .join("");
    select.addEventListener("change", () => loadStudentSchedule(select.value));
    if (select.options.length) loadStudentSchedule(select.options[0].value);
  } catch (err) {
    showToast(err.message, true);
  }
}

initEmploi();