async function loadProgramme() {
  try {
    const data = await apiGet("/student/programme");
    if (!data) return;
    document.getElementById("programmeList").innerHTML = data.items.length
      ? data.items
          .map(
            (ue) => `
        <div class="entry-row">
          <div class="entry-marker"></div>
          <div class="entry-body">
            <p class="entry-title">${ue.ue}${ue.code ? " (" + ue.code + ")" : ""}</p>
            <p class="entry-meta">${ue.matieres.join(" · ")}</p>
          </div>
        </div>`
          )
          .join("")
      : '<div class="empty-state">Le programme de votre classe n\'a pas encore été renseigné.</div>';
  } catch (err) {
    showToast(err.message, true);
  }
}

loadProgramme();