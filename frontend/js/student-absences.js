async function loadAbsences() {
  try {
    const data = await apiGet("/student/absences");
    if (!data) return;
    document.querySelector("#absencesTableStudent tbody").innerHTML = data.items.length
      ? data.items
          .map(
            (a) =>
              `<tr><td>${a.date}</td><td>${a.matiere || "—"}</td><td>${a.justifiee ? "Justifiée" : "Non justifiée"}</td></tr>`
          )
          .join("")
      : '<tr><td colspan="3">Aucune absence enregistrée.</td></tr>';
  } catch (err) {
    showToast(err.message, true);
  }
}

loadAbsences();