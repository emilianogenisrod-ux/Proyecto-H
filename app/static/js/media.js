/* Biblioteca de medios — upload y galería */
function formatBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

async function uploadMediaFile({ file, title = "", kind = "auto" }) {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("title", title);
  fd.append("kind", kind);
  showLoading("Subiendo archivo…");
  try {
    const res = await fetch("/api/media/upload", { method: "POST", body: fd });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
    }
    return res.json();
  } finally {
    hideLoading();
  }
}

async function fetchMediaList({ kind = "", mine = false } = {}) {
  const params = new URLSearchParams();
  if (kind) params.set("kind", kind);
  if (mine) params.set("mine", "true");
  const q = params.toString();
  return api(`/media${q ? `?${q}` : ""}`);
}

async function deleteMediaItem(id) {
  await api(`/media/${id}`, { method: "DELETE" });
}

function renderMediaGallery(container, items, { canDelete = true } = {}) {
  if (!container) return;
  if (!items.length) {
    container.innerHTML = '<p class="empty">No hay archivos todavía. Suba una imagen o video.</p>';
    return;
  }
  container.innerHTML = items
    .map((m) => {
      const preview =
        m.kind === "image"
          ? `<img src="${m.url}" alt="${m.title}" loading="lazy">`
          : `<video src="${m.url}" controls preload="metadata"></video>`;
      return `<article class="media-card" data-id="${m.id}">
        <div class="media-card__preview">${preview}</div>
        <div class="media-card__meta">
          <strong>${m.title}</strong>
          <span>${m.kind === "image" ? "Imagen" : "Video"} · ${formatBytes(m.size_bytes)}</span>
          <span class="media-card__who">${m.uploaded_by || "—"}</span>
        </div>
        <div class="media-card__actions">
          <a class="btn btn-sm btn-ghost" href="${m.url}" target="_blank" rel="noopener">Abrir</a>
          ${canDelete ? `<button type="button" class="btn btn-sm btn-danger" data-delete-media="${m.id}">Eliminar</button>` : ""}
        </div>
      </article>`;
    })
    .join("");

  container.querySelectorAll("[data-delete-media]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("¿Eliminar este archivo?")) return;
      try {
        await deleteMediaItem(btn.dataset.deleteMedia);
        toast("Archivo eliminado");
        const card = btn.closest(".media-card");
        card?.remove();
        if (!container.querySelector(".media-card")) {
          container.innerHTML = '<p class="empty">No hay archivos todavía. Suba una imagen o video.</p>';
        }
      } catch (e) {
        toast(e.message, "error");
      }
    });
  });
}

function bindMediaPanel({ formId = "media-upload-form", galleryId = "media-gallery" } = {}) {
  const form = document.getElementById(formId);
  const gallery = document.getElementById(galleryId);
  const filter = document.getElementById("media-filter-kind");
  const refreshBtn = document.getElementById("media-refresh");

  async function refresh() {
    try {
      const kind = filter?.value || "";
      const items = await fetchMediaList({ kind });
      renderMediaGallery(gallery, items);
    } catch (e) {
      toast(e.message, "error");
    }
  }

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("media-file");
    const file = fileInput?.files?.[0];
    if (!file) return toast("Seleccione un archivo", "error");
    try {
      await uploadMediaFile({
        file,
        title: document.getElementById("media-title")?.value || "",
        kind: document.getElementById("media-kind")?.value || "auto",
      });
      toast("Archivo subido correctamente");
      form.reset();
      await refresh();
    } catch (err) {
      toast(err.message, "error");
    }
  });

  filter?.addEventListener("change", refresh);
  refreshBtn?.addEventListener("click", refresh);

  return refresh;
}
