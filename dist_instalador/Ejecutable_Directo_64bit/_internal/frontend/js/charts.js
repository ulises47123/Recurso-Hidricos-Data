/**
 * Renderizador ligero y 100% offline de Gráficos HTML5 Canvas para Recursos Hídricos
 */

window.AppCharts = {
  // 1. Gráfico Donut para Distribución por Situación de Revista
  renderDonut: function(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    if (!data || data.length === 0) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Sin datos para mostrar", width / 2, height / 2);
      return;
    }

    const total = data.reduce((acc, item) => acc + item.cantidad, 0);
    const colors = ["#2b6cb0", "#00a8cc", "#f59e0b", "#10b981", "#8b5cf6", "#ec4899"];
    
    const centerX = width / 3;
    const centerY = height / 2;
    const radius = Math.min(centerX, centerY) - 15;
    const innerRadius = radius * 0.58;

    let startAngle = -Math.PI / 2;

    data.forEach((item, index) => {
      const sliceAngle = (item.cantidad / total) * 2 * Math.PI;
      const color = colors[index % colors.length];

      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle);
      ctx.arc(centerX, centerY, innerRadius, startAngle + sliceAngle, startAngle, true);
      ctx.closePath();
      ctx.fillStyle = color;
      ctx.fill();

      startAngle += sliceAngle;
    });

    // Texto Central (Total)
    ctx.fillStyle = "#1e293b";
    ctx.font = "bold 16px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(total.toString(), centerX, centerY - 8);

    ctx.fillStyle = "#64748b";
    ctx.font = "10px sans-serif";
    ctx.fillText("Agentes", centerX, centerY + 10);

    // Leyenda Lateral
    const legendX = (width / 3) * 2 - 20;
    let legendY = 25;

    data.forEach((item, index) => {
      const color = colors[index % colors.length];
      const pct = Math.round((item.cantidad / total) * 100);

      // Cuadrado color
      ctx.fillStyle = color;
      ctx.fillRect(legendX, legendY - 8, 10, 10);

      // Texto
      ctx.fillStyle = "#1e293b";
      ctx.font = "11px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      const labelText = `${item.label}: ${item.cantidad} (${pct}%)`;
      ctx.fillText(labelText, legendX + 16, legendY - 3);

      legendY += 22;
    });
  },

  // 2. Gráfico de Barras Horizontales para Personal por Área
  renderBarChart: function(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    if (!data || data.length === 0) {
      ctx.fillStyle = "#94a3b8";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Sin datos para mostrar", width / 2, height / 2);
      return;
    }

    const maxVal = Math.max(...data.map(d => d.cantidad), 1);
    const topData = data.slice(0, 6); // Mostrar hasta top 6 áreas
    const barHeight = 16;
    const gap = 14;
    const startY = 20;
    const labelWidth = 140;
    const chartWidth = width - labelWidth - 60;

    topData.forEach((item, idx) => {
      const y = startY + idx * (barHeight + gap);
      const barW = (item.cantidad / maxVal) * chartWidth;

      // Label área (recortado)
      ctx.fillStyle = "#475569";
      ctx.font = "11px sans-serif";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      let shortLabel = item.area;
      if (shortLabel.length > 22) shortLabel = shortLabel.substring(0, 20) + "...";
      ctx.fillText(shortLabel, 10, y + barHeight / 2);

      // Barra de fondo
      ctx.fillStyle = "#f1f5f9";
      ctx.beginPath();
      ctx.roundRect(labelWidth, y, chartWidth, barHeight, 4);
      ctx.fill();

      // Barra de progreso
      ctx.fillStyle = "#2b6cb0";
      ctx.beginPath();
      ctx.roundRect(labelWidth, y, Math.max(barW, 6), barHeight, 4);
      ctx.fill();

      // Valor numérico
      ctx.fillStyle = "#1e293b";
      ctx.font = "bold 11px sans-serif";
      ctx.fillText(item.cantidad.toString(), labelWidth + barW + 8, y + barHeight / 2);
    });
  }
};
