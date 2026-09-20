async function loadCours() {
  try {
    const data = await apiGet("/student/documents?type=cours");
    if (!data) return;
    renderList("coursList", "coursCount", data.items, "Aucun cours publié pour le moment.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}</p>
          <p class="entry-meta">${item.matiere} · ${item.enseignant}</p>
        </div>
        <div class="entry-date">${formatDate(item.date_publication)}</div>
      </div>
    `);
  } catch (err) {
    showToast(err.message, true);
  }
}

loadCours();