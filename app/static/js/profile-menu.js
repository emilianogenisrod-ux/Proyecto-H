/* Avatar circular + menú de perfil */
(function () {
  function initProfileMenu() {
    const root = document.getElementById("profile-menu");
    const btn = document.getElementById("profile-avatar-btn");
    const menu = document.getElementById("profile-dropdown");
    if (!root || !btn || !menu) return;

    const settingsDialog = document.getElementById("profile-settings-dialog");
    const accountDialog = document.getElementById("profile-account-dialog");
    const settingsForm = document.getElementById("profile-settings-form");

    function closeMenu() {
      menu.hidden = true;
      btn.setAttribute("aria-expanded", "false");
      root.classList.remove("is-open");
    }

    function openMenu() {
      menu.hidden = false;
      btn.setAttribute("aria-expanded", "true");
      root.classList.add("is-open");
    }

    function toggleMenu() {
      if (menu.hidden) openMenu();
      else closeMenu();
    }

    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      toggleMenu();
    });

    document.addEventListener("click", (e) => {
      if (!root.contains(e.target)) closeMenu();
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeMenu();
    });

    menu.addEventListener("click", (e) => {
      const actionEl = e.target.closest("[data-profile-action]");
      if (!actionEl) return;
      const action = actionEl.dataset.profileAction;
      closeMenu();
      if (action === "settings" && settingsDialog?.showModal) settingsDialog.showModal();
      if (action === "account" && accountDialog?.showModal) accountDialog.showModal();
    });

    if (settingsForm) {
      settingsForm.addEventListener("close", () => {
        if (settingsForm.returnValue !== "save") return;
        const data = new FormData(settingsForm);
        const prefs = {
          locale: data.get("locale"),
          notify_email: data.get("notify_email") === "on",
        };
        try {
          localStorage.setItem("proyecto-h-profile-prefs", JSON.stringify(prefs));
        } catch (_) {
          /* ignore */
        }
        if (typeof toast === "function") toast("Preferencias guardadas");
        else alert("Preferencias guardadas");
      });
    }

    // Restaurar preferencias visuales mínimas
    try {
      const raw = localStorage.getItem("proyecto-h-profile-prefs");
      if (raw && settingsForm) {
        const prefs = JSON.parse(raw);
        const locale = settingsForm.querySelector('[name="locale"]');
        const notify = settingsForm.querySelector('[name="notify_email"]');
        if (locale && prefs.locale) locale.value = prefs.locale;
        if (notify) notify.checked = !!prefs.notify_email;
      }
      const avatarUrl = localStorage.getItem("proyecto-h-avatar-url");
      if (avatarUrl) applyAvatar(avatarUrl);
    } catch (_) {
      /* ignore */
    }

    function applyAvatar(url) {
      document.querySelectorAll(".profile-avatar__initials, #profile-avatar-preview").forEach((el) => {
        if (el.id === "profile-avatar-preview" || el.classList.contains("profile-avatar__initials")) {
          const parent = el.id === "profile-avatar-preview" ? el : el.parentElement;
          if (!parent) return;
          parent.style.backgroundImage = `url(${url})`;
          parent.style.backgroundSize = "cover";
          parent.style.backgroundPosition = "center";
          if (el.classList.contains("profile-avatar__initials")) el.style.opacity = "0";
          if (el.id === "profile-avatar-preview") el.textContent = "";
        }
      });
      const btn = document.getElementById("profile-avatar-btn");
      if (btn) {
        btn.style.backgroundImage = `url(${url})`;
        btn.style.backgroundSize = "cover";
        btn.style.backgroundPosition = "center";
        const initials = btn.querySelector(".profile-avatar__initials");
        if (initials) initials.style.opacity = "0";
      }
    }

    document.getElementById("profile-avatar-upload")?.addEventListener("click", async () => {
      const input = document.getElementById("profile-avatar-file");
      const file = input?.files?.[0];
      if (!file) {
        if (typeof toast === "function") toast("Seleccione una imagen", "error");
        return;
      }
      const fd = new FormData();
      fd.append("file", file);
      fd.append("title", "Avatar de perfil");
      fd.append("kind", "avatar");
      try {
        if (typeof showLoading === "function") showLoading("Subiendo avatar…");
        const res = await fetch("/api/media/upload", { method: "POST", body: fd });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "No se pudo subir");
        localStorage.setItem("proyecto-h-avatar-url", data.url);
        applyAvatar(data.url);
        if (typeof toast === "function") toast("Imagen de perfil actualizada");
      } catch (err) {
        if (typeof toast === "function") toast(err.message, "error");
        else alert(err.message);
      } finally {
        if (typeof hideLoading === "function") hideLoading();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initProfileMenu);
  } else {
    initProfileMenu();
  }
})();
