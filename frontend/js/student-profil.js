async function loadProfil() {
  try {
    const me = await apiGet("/student/me");
    if (!me) return;
    document.getElementById("profilInfo").textContent = `${me.email}${me.telephone ? " · " + me.telephone : ""}`;
    document.getElementById("profilTelephone").value = me.telephone || "";
  } catch (err) {
    showToast(err.message, true);
  }
}

document.getElementById("profilSaveBtn").addEventListener("click", async () => {
  const formData = new FormData();
  formData.append("telephone", document.getElementById("profilTelephone").value.trim());
  const photo = document.getElementById("profilPhoto").files[0];
  if (photo) formData.append("photo", photo);

  try {
    const response = await fetch(`${API_BASE_URL}/student/me`, {
      method: "PATCH",
      headers: { ...AuthStore.authHeader() },
      body: formData,
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur lors de la mise à jour.");
    showToast("Profil mis à jour.");
  } catch (err) {
    showToast(err.message, true);
  }
});

document.getElementById("passwordForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const nouveau = document.getElementById("pwdNouveau").value;
  const confirmValue = document.getElementById("pwdConfirm").value;
  if (nouveau !== confirmValue) {
    showToast("Les mots de passe ne correspondent pas.", true);
    return;
  }
  try {
    const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...AuthStore.authHeader() },
      body: JSON.stringify({
        mot_de_passe_actuel: document.getElementById("pwdActuel").value,
        nouveau_mot_de_passe: nouveau,
        confirmation: confirmValue,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || "Erreur lors du changement de mot de passe.");
    showToast("Mot de passe mis à jour.");
    e.target.reset();
  } catch (err) {
    showToast(err.message, true);
  }
});

loadProfil();