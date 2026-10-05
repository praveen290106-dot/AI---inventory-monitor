/**
 * Dashboard Controller - Fetches live KPIs, initializes Chart.js graphs,
 * and handles modal restock actions.
 */

let categoryChartInstance = null;
let statusChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  loadDashboardData();
  setupRestockModalHandler();
});

async function loadDashboardData() {
  try {
    const res = await fetch("/api/dashboard");
    const json = await res.json();

    if (!json.success || !json.data) {
      console.error("Failed to load dashboard data:", json);
      return;
    }

    const data = json.data;

    // 1. Update KPI Cards
    document.getElementById("kpiTotalProducts").innerText = data.total_products.toLocaleString();
    document.getElementById("kpiTotalUnits").innerText = data.total_units.toLocaleString();
    document.getElementById("kpiTotalValue").innerText = "$" + data.total_value.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
    document.getElementById("kpiLowStock").innerText = data.low_stock_count;
    document.getElementById("kpiOutOfStock").innerText = data.out_of_stock_count;

    // 2. Render Charts
    renderCategoryChart(data.category_distribution);
    renderStatusChart(data.normal_stock_count, data.low_stock_count, data.out_of_stock_count);

    // 3. Render Critical Attention Table (Out of stock + Low stock)
    renderAttentionTable(data.out_of_stock_products, data.low_stock_products);

    // 4. Render AI Insights
    renderRecentInsights(data.recent_insights);

    // 5. Render Recent Transactions
    renderTransactionsTable(data.recent_transactions);

  } catch (err) {
    console.error("Network error loading dashboard:", err);
  }
}

function renderCategoryChart(catData) {
  const ctx = document.getElementById("categoryChart").getContext("2d");
  const labels = Object.keys(catData);
  const values = Object.values(catData);

  if (categoryChartInstance) {
    categoryChartInstance.destroy();
  }

  categoryChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Units in Stock",
        data: values,
        backgroundColor: "rgba(168, 85, 247, 0.65)",
        borderColor: "#c084fc",
        borderWidth: 1.5,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          ticks: { color: "#a79fc2" },
          grid: { color: "rgba(39, 32, 61, 0.6)" }
        },
        y: {
          ticks: { color: "#a79fc2" },
          grid: { color: "rgba(39, 32, 61, 0.6)" },
          beginAtZero: true
        }
      }
    }
  });
}

function renderStatusChart(normal, low, out) {
  const ctx = document.getElementById("statusChart").getContext("2d");

  if (statusChartInstance) {
    statusChartInstance.destroy();
  }

  statusChartInstance = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Normal Stock", "Low Stock", "Out of Stock"],
      datasets: [{
        data: [normal, low, out],
        backgroundColor: [
          "#10b981", // Emerald
          "#f59e0b", // Amber
          "#ef4444"  // Rose
        ],
        borderColor: "#0f0d18",
        borderWidth: 3
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: "#cbd5e1", boxWidth: 14 }
        }
      }
    }
  });
}

function renderAttentionTable(outList, lowList) {
  const tbody = document.getElementById("attentionTableBody");
  const combined = [
    ...outList.map(item => ({ ...item, alertType: "OUT_OF_STOCK" })),
    ...lowList.map(item => ({ ...item, alertType: "LOW_STOCK" }))
  ];

  if (combined.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #10b981; padding: 24px;">
      <i class="fa-solid fa-circle-check"></i> All catalog products have healthy inventory levels!
    </td></tr>`;
    return;
  }

  tbody.innerHTML = combined.map(p => `
    <tr>
      <td><strong>${escapeHtml(p.product_name)}</strong></td>
      <td><span style="color: var(--text-dim);">${escapeHtml(p.category)}</span></td>
      <td><strong style="color: ${p.alertType === 'OUT_OF_STOCK' ? '#f87171' : '#fbbf24'};">${p.quantity}</strong></td>
      <td>${p.minimum_stock}</td>
      <td>
        <span class="badge ${p.alertType === 'OUT_OF_STOCK' ? 'badge-out' : 'badge-low'}">
          ${p.alertType === 'OUT_OF_STOCK' ? 'Out of Stock' : 'Low Stock'}
        </span>
      </td>
      <td>
        <button class="btn btn-sm btn-cyan" onclick="openRestockModal(${p.id}, '${escapeHtml(p.product_name).replace(/'/g, "\\'")}', ${p.quantity})">
          <i class="fa-solid fa-plus"></i> Restock
        </button>
      </td>
    </tr>
  `).join("");
}

function renderRecentInsights(insights) {
  const container = document.getElementById("recentInsightsContainer");

  if (!insights || insights.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; color: var(--text-dim); padding: 24px;">
        <i class="fa-solid fa-robot" style="font-size: 2rem; margin-bottom: 8px; display: block;"></i>
        No AI insights recorded yet. Visit the <a href="/ai-assistant">AI Assistant</a> to generate recommendations!
      </div>
    `;
    return;
  }

  container.innerHTML = insights.map(i => {
    let badgeClass = "badge-priority-medium";
    if (i.priority === "HIGH") badgeClass = "badge-priority-high";
    if (i.priority === "LOW") badgeClass = "badge-priority-low";

    const formattedDate = i.created_at ? new Date(i.created_at).toLocaleString() : "";

    return `
      <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span class="badge ${badgeClass}">${i.priority} PRIORITY</span>
          <span style="font-size: 0.75rem; color: var(--text-dim);">${formattedDate}</span>
        </div>
        <div style="font-size: 0.85rem; font-weight: 600; color: #fff; margin-bottom: 4px;">
          <i class="fa-solid fa-cube" style="color: var(--primary);"></i> ${escapeHtml(i.product_name)}
        </div>
        <p style="font-size: 0.85rem; color: var(--text-muted); line-height: 1.4;">${escapeHtml(i.recommendation)}</p>
      </div>
    `;
  }).join("");
}

function renderTransactionsTable(transactions) {
  const tbody = document.getElementById("transactionsTableBody");

  if (!transactions || transactions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 24px;">No transactions recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = transactions.map(t => {
    let typeBadge = "badge-tx-in";
    let sign = "+";
    if (t.transaction_type === "STOCK_OUT") {
      typeBadge = "badge-tx-out";
      sign = "-";
    } else if (t.transaction_type === "ADJUSTMENT") {
      typeBadge = "badge-tx-adj";
      sign = "±";
    }

    const formattedDate = t.created_at ? new Date(t.created_at).toLocaleString() : "";

    return `
      <tr>
        <td><code>#TX-${t.id}</code></td>
        <td style="color: var(--text-dim);">${formattedDate}</td>
        <td><strong>${escapeHtml(t.product_name)}</strong></td>
        <td><span class="badge ${typeBadge}">${t.transaction_type}</span></td>
        <td><strong>${sign}${t.quantity}</strong></td>
        <td style="color: var(--text-muted);">${t.previous_quantity} &rarr; <strong>${t.new_quantity}</strong></td>
        <td style="color: var(--text-muted);">${escapeHtml(t.remarks || "-")}</td>
      </tr>
    `;
  }).join("");
}

/* Modal Helpers */
function openRestockModal(productId, productName, currentStock) {
  document.getElementById("modalProductId").value = productId;
  document.getElementById("modalProductName").value = productName;
  document.getElementById("modalCurrentStock").value = currentStock;
  document.getElementById("modalAddQty").value = 10;
  document.getElementById("modalRemarks").value = "Quick restock from dashboard";
  document.getElementById("restockModal").classList.add("active");
}

function closeRestockModal() {
  document.getElementById("restockModal").classList.remove("active");
}

function setupRestockModalHandler() {
  document.getElementById("quickRestockForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const productId = parseInt(document.getElementById("modalProductId").value);
    const qty = parseInt(document.getElementById("modalAddQty").value);
    const remarks = document.getElementById("modalRemarks").value.trim();

    try {
      const res = await fetch("/api/inventory/stock-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product_id: productId, quantity: qty, remarks: remarks })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        closeRestockModal();
        loadDashboardData(); // Refresh UI
      } else {
        alert(data.error || "Failed to restock product");
      }
    } catch (err) {
      alert("Network error processing stock-in.");
    }
  });
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
