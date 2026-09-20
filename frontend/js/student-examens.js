async function loadExamens() {
  try {
    const data = await apiGet("/student/exams");
    if (!data) return;
    renderList("examensList", "examensCount", data.items, "Aucun examen programmé.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}</p>
          <p class="entry-meta">${item.matiere} · Salle ${item.salle}</p>
        </div>
        <div class="entry-date">${formatDate(item.date)} · ${item.heure}</div>
      </div>
    `);
  } catch (err) {
    showToast(err.message, true);
  }
}

loadExamens();