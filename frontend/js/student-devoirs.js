async function loadDevoirs() {
  try {
    const data = await apiGet("/student/documents?type=devoir");
    if (!data) return;
    renderList("devoirsList", "devoirsCount", data.items, "Aucun devoir en cours.", (item) => `
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

loadDevoirs();