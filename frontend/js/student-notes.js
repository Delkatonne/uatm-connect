async function loadNotes() {
  try {
    const data = await apiGet("/student/grades");
    if (!data) return;
    const typeLabels = { interrogation: "Interrogation", session: "Session", rattrapage: "Rattrapage" };
    document.querySelector("#gradesTable tbody").innerHTML = data.items.length
      ? data.items
          .map(
            (g) =>
              `<tr><td>${g.matiere || "—"}</td><td>${typeLabels[g.type] || g.type}</td><td>${g.valeur} / ${g.bareme}</td><td>${g.semestre || "—"}</td></tr>`
          )
          .join("")
      : '<tr><td colspan="4">Aucune note disponible pour le moment.</td></tr>';
  } catch (err) {
    showToast(err.message, true);
  }
}

loadNotes();