async function loadAdminDocs() {
  try {
    const data = await apiGet("/student/academic-programs");
    if (!data) return;
    renderList("adminDocsList", "adminDocsCount", data.items, "Aucun document administratif pour le moment.", (item) => `
      <div class="entry-row">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}</p>
          <p class="entry-meta">${item.annee_academique || ""}</p>
        </div>
        <div class="entry-date">${formatDate(item.date_publication)}</div>
      </div>
    `);
  } catch (err) {
    showToast(err.message, true);
  }
}

loadAdminDocs();