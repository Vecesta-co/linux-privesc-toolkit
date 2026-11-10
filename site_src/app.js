/**
 * Application logic for Linux Privilege Escalation Automation Toolkit website
 * Zero external dependencies. Vanilla JS.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Mobile Nav Toggle
  const toggleBtn = document.querySelector(".mobile-toggle");
  const navLinks = document.querySelector(".nav-links");
  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });
  }

  // Copy code blocks
  document.querySelectorAll(".copy-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-target");
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        navigator.clipboard.writeText(targetEl.innerText.trim()).then(() => {
          const original = btn.innerText;
          btn.innerText = "Copied!";
          setTimeout(() => (btn.innerText = original), 2000);
        });
      }
    });
  });

  // Report Viewer Logic (if on viewer.html)
  if (document.getElementById("report-viewer-app")) {
    initReportViewer();
  }
});

function initReportViewer() {
  const fileSelect = document.getElementById("sample-select");
  const fileInput = document.getElementById("file-upload");
  const searchInput = document.getElementById("search-input");
  const sevFilter = document.getElementById("sev-filter");
  const catFilter = document.getElementById("cat-filter");

  let currentData = null;

  function loadJson(url) {
    showLoading();
    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error("HTTP " + res.status + " while loading " + url);
        return res.json();
      })
      .then((data) => {
        currentData = data;
        renderReport(data);
      })
      .catch((err) => {
        showError("Could not load report: " + err.message);
      });
  }

  if (fileSelect) {
    fileSelect.addEventListener("change", (e) => {
      if (e.target.value) {
        loadJson(e.target.value);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const data = JSON.parse(event.target.result);
          if (!data || typeof data !== "object") throw new Error("Invalid JSON structure");
          currentData = data;
          renderReport(data);
          if (fileSelect) fileSelect.value = "";
        } catch (err) {
          showError("Malformed JSON file: " + err.message);
        }
      };
      reader.readAsText(file);
    });
  }

  function applyFilters() {
    if (!currentData) return;
    const query = searchInput ? searchInput.value.toLowerCase().trim() : "";
    const sev = sevFilter ? sevFilter.value : "ALL";
    const cat = catFilter ? catFilter.value : "ALL";

    const findings = currentData.findings || [];
    const filtered = findings.filter((f) => {
      if (sev !== "ALL" && (f.severity || "").toUpperCase() !== sev.toUpperCase()) return false;
      if (cat !== "ALL" && (f.category || "").toLowerCase() !== cat.toLowerCase()) return false;
      if (query) {
        const str = `${f.id || ""} ${f.title || ""} ${f.exploitation || ""} ${JSON.stringify(f.evidence || {})}`.toLowerCase();
        if (!str.includes(query)) return false;
      }
      return true;
    });

    renderFindingsList(filtered);
  }

  if (searchInput) searchInput.addEventListener("input", applyFilters);
  if (sevFilter) sevFilter.addEventListener("change", applyFilters);
  if (catFilter) catFilter.addEventListener("change", applyFilters);

  // Check URL params for report selection
  const params = new URLSearchParams(window.location.search);
  const paramReport = params.get("report");
  if (paramReport) {
    loadJson("sample-reports/" + paramReport);
  } else if (fileSelect && fileSelect.value) {
    loadJson(fileSelect.value);
  }
}

function showLoading() {
  const container = document.getElementById("viewer-content");
  if (container) {
    container.innerHTML = '<div style="text-align:center;padding:60px 0;color:var(--text-muted);font-size:1.1rem;">Loading report data...</div>';
  }
}

function showError(msg) {
  const container = document.getElementById("viewer-content");
  if (container) {
    container.innerHTML = `
      <div class="alert-box" style="margin:40px 0;">
        <h4>Report Load Error</h4>
        <p>${escapeHtml(msg)}</p>
      </div>`;
  }
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function renderReport(data) {
  const meta = data.meta || {};
  const summary = data.summary || {};
  const bySev = summary.by_severity || {};

  // Populate Categories Filter Dropdown
  const catFilter = document.getElementById("cat-filter");
  if (catFilter) {
    const cats = new Set((data.findings || []).map((f) => f.category).filter(Boolean));
    catFilter.innerHTML = '<option value="ALL">All Categories</option>' +
      Array.from(cats).sort().map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
  }

  const container = document.getElementById("viewer-content");
  if (!container) return;

  const simBanner = meta.simulated_kernel
    ? `<div class="alert-box"><h4>SIMULATED KERNEL VERSION</h4><p>Demonstration value; not the host running kernel.</p></div>`
    : "";

  const wslNotice = meta.wsl
    ? `<div class="info-box"><h4>WSL Environment Detected</h4><p>Windows drive mounts under /mnt/* were excluded from scan traversal.</p></div>`
    : "";

  container.innerHTML = `
    ${simBanner}
    ${wslNotice}
    <div class="card" style="margin-bottom:24px;border-top:4px solid var(--accent-green);">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px;">
        <div>
          <h2>${escapeHtml(meta.label || "Security Audit Scan")}</h2>
          <p style="color:var(--text-muted);margin-bottom:8px;">
            Host: <strong>${escapeHtml(meta.hostname || "unknown")}</strong> · 
            User: <strong>${escapeHtml(meta.user || "unknown")} (${escapeHtml(meta.privilege || "unknown")})</strong> · 
            Date: <strong>${escapeHtml(data.created_at || "unknown")}</strong>
          </p>
          <p style="color:var(--text-muted);margin-bottom:0;">
            OS: <strong>${escapeHtml(meta.os || "Linux")}</strong> · 
            Kernel: <code>${escapeHtml(meta.kernel || "unknown")}</code>
          </p>
        </div>
        <div style="text-align:right;">
          <div style="font-size:0.85rem;color:var(--text-muted);text-transform:uppercase;font-weight:700;">Overall Risk</div>
          <div style="font-size:1.6rem;font-weight:800;color:${getSevColor(summary.overall_risk)};">${escapeHtml(summary.overall_risk || "UNKNOWN")}</div>
          <div style="color:var(--text-muted);font-size:0.9rem;">${summary.total || 0} Total Findings</div>
        </div>
      </div>
    </div>

    <!-- Severity KPI Cards -->
    <div class="grid-4" style="margin-bottom:28px;">
      <div class="stat-card" style="border-left:4px solid var(--sev-critical);">
        <div class="stat-val" style="color:var(--sev-critical);">${bySev.Critical || 0}</div>
        <div class="stat-label">Critical</div>
      </div>
      <div class="stat-card" style="border-left:4px solid var(--sev-high);">
        <div class="stat-val" style="color:var(--sev-high);">${bySev.High || 0}</div>
        <div class="stat-label">High</div>
      </div>
      <div class="stat-card" style="border-left:4px solid var(--sev-medium);">
        <div class="stat-val" style="color:var(--sev-medium);">${bySev.Medium || 0}</div>
        <div class="stat-label">Medium</div>
      </div>
      <div class="stat-card" style="border-left:4px solid var(--sev-info);">
        <div class="stat-val" style="color:var(--sev-info);">${(bySev.Low || 0) + (bySev.Info || 0)}</div>
        <div class="stat-label">Low / Info</div>
      </div>
    </div>

    <!-- Findings Accordion Section -->
    <div style="margin-bottom:36px;">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h3>Findings Analysis</h3>
        <span id="findings-count-badge" class="badge badge-safety">Showing ${(data.findings || []).length} items</span>
      </div>
      <div id="findings-accordion"></div>
    </div>

    <!-- Coverage Checklist -->
    <div style="margin-bottom:36px;">
      <h3>Collector Coverage</h3>
      <div class="table-responsive">
        <table>
          <thead>
            <tr><th>Check Name</th><th>Execution Status</th><th>Reason / Details</th></tr>
          </thead>
          <tbody>
            ${renderCoverageRows(data.coverage || {})}
          </tbody>
        </table>
      </div>
    </div>

    <!-- Command Transcript -->
    <div>
      <h3>Allowlisted Command Executions</h3>
      <div class="table-responsive">
        <table>
          <thead>
            <tr><th>Command Line</th><th>Exit Code</th><th>Elapsed (s)</th><th>Runner Status</th></tr>
          </thead>
          <tbody>
            ${renderCommandRows(data.commands || [])}
          </tbody>
        </table>
      </div>
    </div>
  `;

  renderFindingsList(data.findings || []);
}

function getSevColor(sev) {
  switch ((sev || "").toLowerCase()) {
    case "critical": return "var(--sev-critical)";
    case "high": return "var(--sev-high)";
    case "medium": return "var(--sev-medium)";
    case "low": return "var(--sev-low)";
    default: return "var(--sev-info)";
  }
}

function renderFindingsList(findings) {
  const container = document.getElementById("findings-accordion");
  const countBadge = document.getElementById("findings-count-badge");
  if (countBadge) {
    countBadge.innerText = `Showing ${findings.length} items`;
  }
  if (!container) return;

  if (findings.length === 0) {
    container.innerHTML = '<div class="card" style="text-align:center;color:var(--text-muted);padding:30px;">No findings match the current filter criteria.</div>';
    return;
  }

  container.innerHTML = findings.map((f, idx) => {
    const chipClass = "chip-" + (f.severity || "info").toLowerCase();
    const refs = (f.references || []).map((r) => `<a href="${escapeHtml(r)}" target="_blank" rel="noopener noreferrer">${escapeHtml(r)}</a>`).join(" · ");
    return `
      <div class="finding-item">
        <div class="finding-header" data-idx="${idx}">
          <div class="finding-title-group">
            <span class="chip ${chipClass}">${escapeHtml(f.severity || "Info")}</span>
            <strong>${escapeHtml(f.id || "FINDING")}</strong>
            <span>${escapeHtml(f.title || "Untitled")}</span>
          </div>
          <span style="color:var(--text-muted);font-size:0.85rem;">[+] Expand</span>
        </div>
        <div class="finding-body" id="finding-body-${idx}">
          <div class="finding-field">
            <div class="finding-field-label">Evidence Details</div>
            <pre style="background:rgba(0,0,0,0.3);padding:10px;border-radius:4px;overflow-x:auto;"><code>${escapeHtml(JSON.stringify(f.evidence || {}, null, 2))}</code></pre>
          </div>
          <div class="finding-field">
            <div class="finding-field-label">Exploitation Possibility</div>
            <p style="color:#c9d1d9;">${escapeHtml(f.exploitation || "No explanation provided.")}</p>
          </div>
          <div class="finding-field">
            <div class="finding-field-label">Defensive Mitigation</div>
            <p style="color:#7EE787;"><code>${escapeHtml(f.mitigation || "Inspect file and restrict permissions.")}</code></p>
          </div>
          ${refs ? `
          <div class="finding-field">
            <div class="finding-field-label">Security References</div>
            <p>${refs}</p>
          </div>` : ""}
        </div>
      </div>
    `;
  }).join("");

  // Attach accordion click events
  container.querySelectorAll(".finding-header").forEach((hdr) => {
    hdr.addEventListener("click", () => {
      const idx = hdr.getAttribute("data-idx");
      const body = document.getElementById("finding-body-" + idx);
      const span = hdr.querySelector("span:last-child");
      if (body) {
        body.classList.toggle("open");
        if (body.classList.contains("open")) {
          span.innerText = "[-] Collapse";
        } else {
          span.innerText = "[+] Expand";
        }
      }
    });
  });
}

function renderCoverageRows(coverage) {
  const keys = Object.keys(coverage);
  if (keys.length === 0) {
    return '<tr><td colspan="3" style="text-align:center;color:var(--text-muted);">No coverage data recorded</td></tr>';
  }
  return keys.map((k) => {
    const item = coverage[k];
    const isRan = item.status === "ran";
    const statusChip = isRan
      ? '<span class="chip" style="background:#3FB950;color:#0E1116;">RAN</span>'
      : '<span class="chip" style="background:#D29922;color:#0E1116;">SKIPPED</span>';
    return `<tr>
      <td><strong>${escapeHtml(k)}</strong></td>
      <td>${statusChip}</td>
      <td style="color:var(--text-muted);">${escapeHtml(item.reason || "Executed within allowlist")}</td>
    </tr>`;
  }).join("");
}

function renderCommandRows(commands) {
  if (!commands || commands.length === 0) {
    return '<tr><td colspan="4" style="text-align:center;color:var(--text-muted);">No external commands recorded</td></tr>';
  }
  return commands.map((c) => {
    const isSuccess = c.returncode === 0;
    const codeBadge = isSuccess
      ? '<span style="color:#3FB950;font-weight:700;">0</span>'
      : `<span style="color:#F85149;font-weight:700;">${c.returncode}</span>`;
    return `<tr>
      <td><code>${escapeHtml(c.display || "")}</code></td>
      <td>${codeBadge}</td>
      <td style="font-family:var(--font-mono);">${c.elapsed_seconds || 0}s</td>
      <td style="color:var(--text-muted);">${escapeHtml(c.skipped_reason || "ran")}</td>
    </tr>`;
  }).join("");
}

