async function loadNotifications() {
  try {
    const data = await apiGet("/student/notifications");
    if (!data) return;
    renderList("notifList", "notifCount", data.items, "Aucune notification.", (item) => `
      <div class="entry-row notif-row" data-notif-id="${item.id}" data-lu="${item.lu}" style="cursor:pointer;">
        <div class="entry-marker"></div>
        <div class="entry-body">
          <p class="entry-title">${item.titre}${item.lu ? "" : ' <span class="badge attente">Nouveau</span>'}</p>
          <p class="entry-meta">${item.message}</p>
        </div>
        <div class="entry-date">${formatDate(item.date)}</div>
      </div>
    `);

    document.querySelectorAll(".notif-row").forEach((row) => {
      if (row.dataset.lu === "true") return;
      row.addEventListener("click", async () => {
        try {
          const response = await fetch(`${API_BASE_URL}/student/notifications/${row.dataset.notifId}/read`, {
            method: "PATCH",
            headers: { ...AuthStore.authHeader() },
          });
          if (response.ok) {
            row.querySelector(".badge")?.remove();
            row.dataset.lu = "true";
          }
        } catch (err) {
          console.error(err);
        }
      });
    });
  } catch (err) {
    showToast(err.message, true);
  }
}

loadNotifications();