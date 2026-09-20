function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
}

function renderList(containerId, countId, items, emptyLabel, renderItem) {
  const container = document.getElementById(containerId);
  const countEl = countId ? document.getElementById(countId) : null;
  if (countEl) countEl.textContent = items.length ? `${items.length}` : "";

  if (!items.length) {
    container.innerHTML = `<div class="empty-state">${emptyLabel}</div>`;
    return;
  }
  container.innerHTML = items.map(renderItem).join("");
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { ...AuthStore.authHeader() },
  });
  if (response.status === 401) {
    window.location.href = "login.html";
    return null;
  }
  if (!response.ok) throw new Error(`Erreur ${response.status} sur ${path}`);
  return response.json();
}

const toastEl = document.getElementById("toast");
function showToast(message, isError = false) {
  if (!toastEl) return;
  toastEl.textContent = message;
  toastEl.classList.toggle("error", isError);
  toastEl.classList.add("visible");
  setTimeout(() => toastEl.classList.remove("visible"), 2800);
}