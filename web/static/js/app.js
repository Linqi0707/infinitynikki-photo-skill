/* ===== InfinityNikki Photo Skill - Web UI App ===== */

const API_BASE = "";
let tagDimensions = [];
let activeFilters = {};
let currentPage = 1;
let totalPages = 1;
let currentPageSize = 60;
let searchQuery = "";
let searchMode = false;
let currentPhotoData = null; // stores the currently open photo's full detail
let editMode = false;

// Tag label maps (English value -> Chinese label)
const TAG_LABELS = {
    photo_type: { portrait: "人像", scenery: "景象" },
    framing: { close_up: "大头照", half_body: "半身照", full_body: "全身照" },
    view: { front: "正面", back: "背面", side: "侧面" },
    scene: {
        architecture: "建筑",
        nature: "自然风景",
        animal: "动物",
        insect: "昆虫",
        other: "其他",
    },
    game_time: { day: "白天", dusk: "黄昏", night: "夜晚", unknown: "未知" },
    color_tone: { warm: "暖色", cool: "冷色" },
    background: { white: "白色", black: "黑色", normal: "普通环境" },
    orientation: { landscape: "横屏", portrait: "竖屏", square: "方形" },
};

const DIMENSION_LABELS = {
    photo_type: "照片类型",
    framing: "构图",
    view: "视角",
    scene: "场景",
    game_time: "游戏时间",
    color_tone: "色调",
    background: "背景",
    orientation: "横竖屏",
};

// Editable semantic fields configuration
const EDIT_FIELDS = [
    { key: "photo_type", label: "类型", options: TAG_LABELS.photo_type, allowNull: false },
    { key: "portrait_framing", label: "构图", options: TAG_LABELS.framing, allowNull: true },
    { key: "portrait_view", label: "视角", options: TAG_LABELS.view, allowNull: true },
    { key: "scene_category", label: "场景", options: TAG_LABELS.scene, allowNull: true },
    { key: "game_time", label: "游戏时间", options: TAG_LABELS.game_time, allowNull: false },
    { key: "color_tone", label: "色调", options: TAG_LABELS.color_tone, allowNull: false },
    { key: "background", label: "背景", options: TAG_LABELS.background, allowNull: false },
];

// ===== Init =====
async function init() {
    await loadTags();
    await loadStats();
    renderFilters();
    await loadPhotos();
}

// ===== Load tag dimensions =====
async function loadTags() {
    try {
        const res = await fetch(`${API_BASE}/api/tags`);
        const data = await res.json();
        tagDimensions = data.dimensions || [];
    } catch (e) {
        console.error("Failed to load tags:", e);
    }
}

// ===== Load stats =====
async function loadStats() {
    try {
        const res = await fetch(`${API_BASE}/api/stats`);
        const data = await res.json();
        document.getElementById("statTotal").textContent = data.total_photos || 0;
        document.getElementById("statOutfits").textContent =
            data.total_outfits || 0;
    } catch (e) {
        console.error("Failed to load stats:", e);
    }
}

// ===== Render filter sidebar =====
function renderFilters() {
    const container = document.getElementById("filterContainer");
    container.innerHTML = "";

    tagDimensions.forEach((dim) => {
        const section = document.createElement("div");
        section.className = "filter-section";

        const title = document.createElement("div");
        title.className = "filter-section-title";
        title.textContent = dim.label;
        section.appendChild(title);

        const chipsDiv = document.createElement("div");
        chipsDiv.className = "filter-chips";

        dim.choices.forEach((choice) => {
            const chip = document.createElement("span");
            chip.className = "chip";
            chip.dataset.key = dim.key;
            chip.dataset.value = choice;
            const label =
                dim.labels && dim.labels[choice] ? dim.labels[choice] : choice;
            chip.textContent = label;
            chip.onclick = () => toggleFilter(dim.key, choice);
            chipsDiv.appendChild(chip);
        });

        section.appendChild(chipsDiv);
        container.appendChild(section);
    });
}

// ===== Toggle a filter =====
function toggleFilter(key, value) {
    if (activeFilters[key] === value) {
        delete activeFilters[key];
    } else {
        activeFilters[key] = value;
    }
    // Update chip UI
    document.querySelectorAll(`.chip[data-key="${key}"]`).forEach((chip) => {
        if (
            chip.dataset.value === value &&
            activeFilters[key] === value
        ) {
            chip.classList.add("active");
        } else {
            chip.classList.remove("active");
        }
    });
    currentPage = 1;
    searchMode = false;
    searchQuery = "";
    document.getElementById("searchInput").value = "";
    loadPhotos();
}

// ===== Reset all filters =====
function resetFilters() {
    activeFilters = {};
    currentPage = 1;
    searchMode = false;
    searchQuery = "";
    document.getElementById("searchInput").value = "";
    document
        .querySelectorAll(".chip.active")
        .forEach((c) => c.classList.remove("active"));
    loadPhotos();
}

// ===== Handle search input =====
let searchTimer = null;
function handleSearch(event) {
    const value = event.target.value.trim();
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        if (value) {
            searchMode = true;
            searchQuery = value;
        } else {
            searchMode = false;
            searchQuery = "";
        }
        currentPage = 1;
        loadPhotos();
    }, 300);
}

// ===== Build query string =====
function buildQueryString() {
    const params = new URLSearchParams();
    params.set("page", currentPage);
    params.set("page_size", currentPageSize);

    if (searchMode && searchQuery) {
        params.set("q", searchQuery);
    } else {
        for (const [key, value] of Object.entries(activeFilters)) {
            params.set(key, value);
        }
    }
    return params.toString();
}

// ===== Load photos =====
async function loadPhotos() {
    const wall = document.getElementById("photoWall");
    showSkeletons(wall);

    const endpoint = searchMode ? "/api/search" : "/api/photos";

    try {
        const res = await fetch(`${API_BASE}${endpoint}?${buildQueryString()}`);
        const data = await res.json();

        totalPages = data.total_pages || 1;
        renderActiveFilters();
        renderResultInfo(data);
        renderPhotos(data.photos || []);
        renderPagination();
    } catch (e) {
        console.error("Failed to load photos:", e);
        wall.innerHTML =
            '<div class="empty-state"><div class="icon">⚠️</div><p>加载失败，请检查服务器是否运行</p></div>';
    }
}

// ===== Show loading skeletons =====
function showSkeletons(container) {
    let html = "";
    for (let i = 0; i < 12; i++) {
        html += `<div class="skeleton-card"><div class="skeleton-img"></div></div>`;
    }
    container.innerHTML = html;
}

// ===== Render photo cards =====
function renderPhotos(photos) {
    const wall = document.getElementById("photoWall");

    if (!photos.length) {
        wall.innerHTML =
            '<div class="empty-state"><div class="icon">📷</div><p>没有找到符合条件的照片</p></div>';
        return;
    }

    wall.innerHTML = photos
        .map((photo) => {
            // Build tag badges for overlay
            const tags = [];
            if (photo.photo_type)
                tags.push(TAG_LABELS.photo_type[photo.photo_type]);
            if (photo.portrait_framing)
                tags.push(TAG_LABELS.framing[photo.portrait_framing]);
            if (photo.game_time)
                tags.push(TAG_LABELS.game_time[photo.game_time]);
            if (photo.color_tone)
                tags.push(TAG_LABELS.color_tone[photo.color_tone]);
            if (photo.background)
                tags.push(TAG_LABELS.background[photo.background]);

            const tagHtml = tags
                .slice(0, 4)
                .map((t) => `<span class="photo-card-tag">${t}</span>`)
                .join("");

            return `
                <div class="photo-card" onclick="openDetail('${photo.photo_id}')">
                    <img
                        class="photo-card-img"
                        src="${API_BASE}/api/photo_file/${photo.photo_id}"
                        alt="${escapeHtml(photo.filename)}"
                        loading="lazy"
                    >
                    <div class="photo-card-overlay">
                        <div class="filename">${escapeHtml(photo.filename)}</div>
                        <div class="photo-card-tags">${tagHtml}</div>
                    </div>
                </div>
            `;
        })
        .join("");
}

// ===== Render result info =====
function renderResultInfo(data) {
    const info = document.getElementById("resultInfo");
    if (data.total !== undefined) {
        info.textContent = `共 ${data.total} 张`;
    }
}

// ===== Render active filters bar =====
function renderActiveFilters() {
    const container = document.getElementById("activeFilters");

    if (searchMode) {
        container.innerHTML = `
            <span class="active-filter-chip" onclick="clearSearch()">
                🔍 "${escapeHtml(searchQuery)}"
                <span class="remove">✕</span>
            </span>
        `;
        return;
    }

    const chips = Object.entries(activeFilters).map(([key, value]) => {
        const dimLabel = DIMENSION_LABELS[key] || key;
        const valLabel =
            TAG_LABELS[key] && TAG_LABELS[key][value]
                ? TAG_LABELS[key][value]
                : value;
        return `
            <span class="active-filter-chip" onclick="toggleFilter('${key}', '${value}')">
                ${dimLabel}: ${valLabel}
                <span class="remove">✕</span>
            </span>
        `;
    });

    container.innerHTML = chips.join("");
}

function clearSearch() {
    searchMode = false;
    searchQuery = "";
    document.getElementById("searchInput").value = "";
    currentPage = 1;
    loadPhotos();
}

// ===== Pagination =====
function renderPagination() {
    const pagination = document.getElementById("pagination");
    const firstBtn = document.getElementById("firstBtn");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const lastBtn = document.getElementById("lastBtn");
    const pageInfo = document.getElementById("pageInfo");
    const pageNumbers = document.getElementById("pageNumbers");
    const jumpInput = document.getElementById("jumpInput");

    if (totalPages <= 1) {
        pagination.style.display = "none";
        return;
    }

    pagination.style.display = "flex";
    firstBtn.disabled = currentPage <= 1;
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= totalPages;
    lastBtn.disabled = currentPage >= totalPages;
    pageInfo.textContent = `第 ${currentPage} / ${totalPages} 页`;
    jumpInput.max = totalPages;

    // Build page number window (5 pages around current)
    const windowSize = 5;
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + windowSize - 1);
    // Adjust startPage if we're near the end
    if (endPage - startPage < windowSize - 1) {
        startPage = Math.max(1, endPage - windowSize + 1);
    }

    let numbersHtml = "";
    // Left ellipsis
    if (startPage > 1) {
        numbersHtml += `<span class="page-num" onclick="goToPage(1)">1</span>`;
        if (startPage > 2) {
            numbersHtml += `<span class="page-ellipsis">…</span>`;
        }
    }
    // Page numbers in window
    for (let p = startPage; p <= endPage; p++) {
        const activeClass = p === currentPage ? " active" : "";
        numbersHtml += `<span class="page-num${activeClass}" onclick="goToPage(${p})">${p}</span>`;
    }
    // Right ellipsis
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            numbersHtml += `<span class="page-ellipsis">…</span>`;
        }
        numbersHtml += `<span class="page-num" onclick="goToPage(${totalPages})">${totalPages}</span>`;
    }
    pageNumbers.innerHTML = numbersHtml;
}

function goToPage(page) {
    page = parseInt(page);
    if (isNaN(page) || page < 1 || page > totalPages || page === currentPage)
        return;
    currentPage = page;
    loadPhotos();
    document.querySelector(".main-content").scrollTop = 0;
    window.scrollTo(0, 0);
}

function changePage(delta) {
    goToPage(currentPage + delta);
}

function handlePageJump(event) {
    if (event.key !== "Enter") return;
    const val = parseInt(event.target.value);
    if (!isNaN(val)) {
        goToPage(val);
        event.target.value = "";
    }
}

function handleJumpBtn() {
    const input = document.getElementById("jumpInput");
    const val = parseInt(input.value);
    if (!isNaN(val)) {
        goToPage(val);
        input.value = "";
    }
}

// ===== Photo Detail Modal =====
async function openDetail(photoId) {
    const modal = document.getElementById("detailModal");
    const modalImage = document.getElementById("modalImage");
    const modalInfo = document.getElementById("modalInfo");
    const modalTitle = document.getElementById("modalTitle");

    // Reset edit mode
    editMode = false;
    currentPhotoData = null;

    // Show modal immediately with loading state
    modalImage.src = `${API_BASE}/api/photo_file/${photoId}`;
    modalInfo.innerHTML =
        '<div style="text-align:center;color:var(--text-tertiary);padding:40px;">加载中…</div>';
    modalTitle.textContent = "照片详情";
    modal.classList.add("show");

    try {
        const res = await fetch(`${API_BASE}/api/photo/${photoId}`);
        const data = await res.json();

        if (data.error) {
            modalInfo.innerHTML = `<p style="color:red;">${data.error}</p>`;
            return;
        }

        currentPhotoData = data;
        modalTitle.textContent = data.filename || "照片详情";
        modalInfo.innerHTML = renderDetailInfo(data);
    } catch (e) {
        console.error("Failed to load detail:", e);
        modalInfo.innerHTML =
            '<p style="color:red;">加载详情失败</p>';
    }
}

function renderDetailInfo(data) {
    // Semantic tags
    const tags = [];
    if (data.photo_type)
        tags.push({
            label: "类型",
            value: TAG_LABELS.photo_type[data.photo_type],
        });
    if (data.portrait_framing)
        tags.push({
            label: "构图",
            value: TAG_LABELS.framing[data.portrait_framing],
        });
    if (data.portrait_view)
        tags.push({
            label: "视角",
            value: TAG_LABELS.view[data.portrait_view],
        });
    if (data.scene_category)
        tags.push({
            label: "场景",
            value: TAG_LABELS.scene[data.scene_category],
        });
    if (data.game_time)
        tags.push({
            label: "游戏时间",
            value: TAG_LABELS.game_time[data.game_time],
        });
    if (data.color_tone)
        tags.push({
            label: "色调",
            value: TAG_LABELS.color_tone[data.color_tone],
        });
    if (data.background)
        tags.push({
            label: "背景",
            value: TAG_LABELS.background[data.background],
        });
    if (data.orientation)
        tags.push({
            label: "横竖屏",
            value: TAG_LABELS.orientation[data.orientation],
        });

    const tagBadges = tags
        .map(
            (t) =>
                `<span class="tag-badge">${t.label}: ${t.value}</span>`
        )
        .join("");

    // Outfits
    let outfitsHtml = "";
    if (data.outfits && data.outfits.length > 0) {
        outfitsHtml = data.outfits
            .map(
                (o) => `
            <div style="margin-bottom:12px;">
                <div class="code-block">${escapeHtml(o.outfit_code)}</div>
                ${
                    o.outfit_description
                        ? `<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">${escapeHtml(o.outfit_description)}</div>`
                        : ""
                }
            </div>
        `
            )
            .join("");
    } else {
        outfitsHtml = '<div class="no-data">尚未录入搭配码</div>';
    }

    // Camera params
    let cameraHtml = "";
    if (data.camera_params && data.camera_params.length > 0) {
        cameraHtml = data.camera_params
            .map(
                (c) => `
            <div style="margin-bottom:12px;">
                <div class="code-block">${escapeHtml(c.camera_code)}</div>
                ${
                    c.description
                        ? `<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">${escapeHtml(c.description)}</div>`
                        : ""
                }
            </div>
        `
            )
            .join("");
    } else {
        cameraHtml = '<div class="no-data">尚未录入摄影参数</div>';
    }

    return `
        <div class="info-group">
            <div class="info-group-header">
                <div class="info-group-title">语义标签</div>
                <button class="edit-btn" onclick="enterEditMode()">✎ 编辑</button>
            </div>
            <div class="tag-badges">${tagBadges}</div>
        </div>

        <div class="info-group">
            <div class="info-group-title">基本信息</div>
            <div class="info-row">
                <span class="label">文件名</span>
                <span class="value" style="font-size:11px;">${escapeHtml(data.filename || "")}</span>
            </div>
            <div class="info-row">
                <span class="label">拍摄时间</span>
                <span class="value">${escapeHtml(data.shoot_time || "")}</span>
            </div>
            <div class="info-row">
                <span class="label">尺寸</span>
                <span class="value">${data.width || "?"} × ${data.height || "?"}</span>
            </div>
            <div class="info-row">
                <span class="label">photo_id</span>
                <span class="value" style="font-size:11px;">${escapeHtml(data.photo_id || "")}</span>
            </div>
        </div>

        <div class="info-group">
            <div class="info-group-title">搭配码 (Outfit Code)</div>
            ${outfitsHtml}
        </div>

        <div class="info-group">
            <div class="info-group-title">摄影参数 (Camera Code)</div>
            ${cameraHtml}
        </div>
    `;
}

// ===== Enter Edit Mode =====
function enterEditMode() {
    if (!currentPhotoData) return;
    editMode = true;
    const modalInfo = document.getElementById("modalInfo");
    modalInfo.innerHTML = renderEditableInfo(currentPhotoData);
}

// ===== Render Editable Info Form =====
function renderEditableInfo(data) {
    // Build semantic dropdowns
    const semanticRows = EDIT_FIELDS.map((field) => {
        const currentVal = data[field.key] || "";
        let optionsHtml = "";
        if (field.allowNull) {
            optionsHtml += `<option value="" ${currentVal === "" ? "selected" : ""}>— 无 —</option>`;
        }
        for (const [val, label] of Object.entries(field.options)) {
            const selected = currentVal === val ? "selected" : "";
            optionsHtml += `<option value="${val}" ${selected}>${label}</option>`;
        }
        return `
            <div class="edit-field-row">
                <span class="field-label">${field.label}</span>
                <select class="edit-select" id="edit_${field.key}">${optionsHtml}</select>
            </div>
        `;
    }).join("");

    // Orientation (read-only)
    const orientationLabel = data.orientation
        ? TAG_LABELS.orientation[data.orientation]
        : "";
    const orientationRow = `
        <div class="edit-field-row">
            <span class="field-label">横竖屏</span>
            <span class="readonly-badge">${orientationLabel} (只读)</span>
        </div>
    `;

    // Outfit fields
    const outfitCode = (data.outfits && data.outfits[0]) ? (data.outfits[0].outfit_code || "") : "";
    const outfitDesc = (data.outfits && data.outfits[0]) ? (data.outfits[0].outfit_description || "") : "";

    // Camera fields
    const cameraCode = (data.camera_params && data.camera_params[0]) ? (data.camera_params[0].camera_code || "") : "";
    const cameraDesc = (data.camera_params && data.camera_params[0]) ? (data.camera_params[0].description || "") : "";

    return `
        <div class="info-group">
            <div class="info-group-header">
                <div class="info-group-title">语义标签 (编辑中)</div>
            </div>
            ${semanticRows}
            ${orientationRow}
        </div>

        <div class="info-group">
            <div class="info-group-title">搭配码 (Outfit Code)</div>
            <input type="text" class="edit-input" id="edit_outfit_code"
                value="${escapeHtml(outfitCode)}" placeholder="搭配码">
            <textarea class="edit-textarea" id="edit_outfit_desc"
                placeholder="搭配说明">${escapeHtml(outfitDesc)}</textarea>
        </div>

        <div class="info-group">
            <div class="info-group-title">摄影参数 (Camera Code)</div>
            <input type="text" class="edit-input" id="edit_camera_code"
                value="${escapeHtml(cameraCode)}" placeholder="摄影参数码">
            <textarea class="edit-textarea" id="edit_camera_desc"
                placeholder="摄影参数说明">${escapeHtml(cameraDesc)}</textarea>
        </div>

        <div id="editStatus" class="edit-status"></div>

        <div class="edit-actions">
            <button class="btn-cancel" onclick="cancelEdit()">取消</button>
            <button class="btn-save" onclick="saveEdit()">保存</button>
        </div>
    `;
}

// ===== Save Edit =====
async function saveEdit() {
    if (!currentPhotoData) return;
    const photoId = currentPhotoData.photo_id;
    const statusEl = document.getElementById("editStatus");
    statusEl.className = "edit-status";
    statusEl.textContent = "正在保存…";

    // Collect semantics
    const semantics = {};
    for (const field of EDIT_FIELDS) {
        const el = document.getElementById(`edit_${field.key}`);
        let val = el ? el.value : "";
        // Convert empty to null for allow-null fields
        if (val === "" && field.allowNull) {
            val = null;
        }
        semantics[field.key] = val;
    }

    // Collect outfit
    const outfitCode = document.getElementById("edit_outfit_code").value;
    const outfitDesc = document.getElementById("edit_outfit_desc").value;
    const outfit = { code: outfitCode, description: outfitDesc };

    // Collect camera
    const cameraCode = document.getElementById("edit_camera_code").value;
    const cameraDesc = document.getElementById("edit_camera_desc").value;
    const camera = { code: cameraCode, description: cameraDesc };

    const payload = { semantics, outfit, camera };

    try {
        const res = await fetch(`${API_BASE}/api/photo/${photoId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (!res.ok) {
            statusEl.className = "edit-status error";
            statusEl.textContent = `保存失败: ${data.error || res.statusText}`;
            if (data.field) {
                statusEl.textContent += ` (字段: ${data.field})`;
            }
            return;
        }

        // Success: update currentPhotoData and re-render view mode
        currentPhotoData = data;
        editMode = false;
        document.getElementById("modalInfo").innerHTML = renderDetailInfo(data);
        const newStatus = document.createElement("div");
        newStatus.className = "edit-status success";
        newStatus.textContent = "✓ 已保存";
        document.getElementById("modalInfo").prepend(newStatus);
        // Auto-remove success message after 2 seconds
        setTimeout(() => {
            const s = document.querySelector(".edit-status.success");
            if (s) s.remove();
        }, 2000);

        // Also refresh the photo wall silently so the updated tags show
        // only if we're on the current page
        loadPhotos();
    } catch (e) {
        console.error("Save failed:", e);
        statusEl.className = "edit-status error";
        statusEl.textContent = "保存失败: 网络错误";
    }
}

// ===== Cancel Edit =====
function cancelEdit() {
    if (!currentPhotoData) return;
    editMode = false;
    document.getElementById("modalInfo").innerHTML =
        renderDetailInfo(currentPhotoData);
}

// ===== Close modal =====
function closeModal(event) {
    if (event && event.target !== document.getElementById("detailModal")) return;
    document.getElementById("detailModal").classList.remove("show");
    document.getElementById("modalImage").src = "";
    editMode = false;
    currentPhotoData = null;
}

// ===== Utility =====
function escapeHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// ===== Keyboard: ESC to close modal =====
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
});

// ===== Start =====
init();
