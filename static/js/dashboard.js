function drawBarChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.clientWidth * window.devicePixelRatio;
    const height = canvas.height = 220 * window.devicePixelRatio;
    const scale = window.devicePixelRatio;
    ctx.scale(scale, scale);
    ctx.clearRect(0, 0, width, height);

    const chartWidth = canvas.clientWidth - 44;
    const chartHeight = 150;
    const startX = 34;
    const startY = 176;
    const maxValue = Math.max(...data.map((item) => Number(item.value)), 1);
    const barWidth = Math.max(24, chartWidth / Math.max(data.length, 1) - 18);
    const colors = options.colors || ["#176b87", "#63a088", "#d8973c", "#7b506f"];

    ctx.font = "12px system-ui";
    ctx.fillStyle = "#657085";
    if (!data.length) {
        ctx.fillText("No data yet", startX, 95);
        return;
    }

    data.forEach((item, index) => {
        const value = Number(item.value);
        const x = startX + index * (barWidth + 18);
        const barHeight = (value / maxValue) * chartHeight;
        ctx.fillStyle = colors[index % colors.length];
        ctx.fillRect(x, startY - barHeight, barWidth, barHeight);
        ctx.fillStyle = "#172033";
        ctx.fillText(String(value), x, startY - barHeight - 8);
        ctx.fillStyle = "#657085";
        const label = String(item.label).slice(0, 12);
        ctx.fillText(label, x, startY + 18);
    });

    ctx.strokeStyle = "#dce2ea";
    ctx.beginPath();
    ctx.moveTo(startX, startY);
    ctx.lineTo(startX + chartWidth, startY);
    ctx.stroke();
}

function renderDashboard() {
    const metrics = window.dashboardMetrics || {};
    drawBarChart("departmentChart", metrics.department_distribution || []);
    drawBarChart("complexityChart", metrics.complexity_distribution || [], {
        colors: ["#16794c", "#d8973c", "#b42318"],
    });
    drawBarChart("priorityChart", metrics.priority_by_department || [], {
        colors: ["#124f63", "#176b87", "#63a088", "#d8973c"],
    });
}

window.addEventListener("resize", renderDashboard);
renderDashboard();
