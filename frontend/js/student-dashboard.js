async function loadAccueil() {
  try {
    const me = await apiGet("/student/me");
    if (!me) return;

    document.getElementById("greeting").textContent = `Bonjour, ${me.nom_complet}`;
    document.getElementById("identityLine").innerHTML = `
      <span>Centre : <strong>${me.centre || "—"}</strong></span>
      <span>Filière : <strong>${me.filiere}</strong></span>
      <span>Option : <strong>${me.option}</strong></span>
      <span>Année : <strong>${me.annee_etude}</strong></span>
      <span>Classe : <strong>${me.classe}</strong></span>
    `;

    const [cours, devoirs, examens, notifications] = await Promise.all([
      apiGet("/student/documents?type=cours"),
      apiGet("/student/documents?type=devoir"),
      apiGet("/student/exams"),
      apiGet("/student/notifications"),
    ]);

    const stats = [
      { label: "Cours récents", count: cours.items.length, href: "student-cours.html" },
      { label: "Devoirs", count: devoirs.items.length, href: "student-devoirs.html" },
      { label: "Examens", count: examens.items.length, href: "student-examens.html" },
      { label: "Notifications", count: notifications.items.filter((n) => !n.lu).length, href: "student-notifications.html" },
    ];

    document.getElementById("accueilStats").innerHTML = stats
      .map(
        (s) => `
      <a href="${s.href}" style="text-decoration:none; color:inherit;">
        <div class="stat-card">
          <div class="value">${s.count}</div>
          <div class="label">${s.label}</div>
        </div>
      </a>`
      )
      .join("");
  } catch (err) {
    console.error(err);
  }
}

loadAccueil();