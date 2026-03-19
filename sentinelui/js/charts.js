/**
 * SentinelTwin AI — Chart Manager
 * Manages all Chart.js real-time charts across the dashboard.
 */
class ChartManager {
  constructor() {
    this.charts = {};
    this.maxDataPoints = 30;
  }

  _defaultOpts(color, label, yMax) {
    return {
      type: 'line',
      data: {
        labels: Array(this.maxDataPoints).fill(''),
        datasets: [{
          label, data: Array(this.maxDataPoints).fill(null),
          borderColor: color, backgroundColor: color + '18',
          borderWidth: 2, pointRadius: 0, tension: 0.4, fill: true,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
        scales: {
          x: { display: false },
          y: {
            min: 0, max: yMax || undefined,
            grid: { color: 'rgba(0,0,0,0.04)' },
            ticks: { font: { size: 10 }, color: '#718096', maxTicksLimit: 4 }
          }
        }
      }
    };
  }

  initProductionChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    const cfg = this._defaultOpts('#1976D2', 'Throughput %', 100);
    cfg.data.datasets.push({
      label: 'Target', data: Array(this.maxDataPoints).fill(90),
      borderColor: '#E0E0E0', borderWidth: 1, borderDash: [4,4],
      pointRadius: 0, tension: 0, fill: false,
    });
    this.charts[canvasId] = new Chart(ctx, cfg);
  }

  initMachineHealthChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    const colors = ['#1976D2','#43A047','#F57F17','#E53935','#7B1FA2'];
    const machineIds = ['M1','M2','M3','M4','M5'];
    const datasets = machineIds.map((id, i) => ({
      label: id, data: Array(this.maxDataPoints).fill(null),
      borderColor: colors[i], borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false,
    }));
    this.charts[canvasId] = new Chart(ctx, {
      type: 'line',
      data: { labels: Array(this.maxDataPoints).fill(''), datasets },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } } },
        scales: {
          x: { display: false },
          y: { min: 0, max: 100, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 10 }, color: '#718096' } }
        }
      }
    });
  }

  initSensorChart(canvasId, sensorName, color, yMax) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    this.charts[canvasId] = new Chart(ctx, this._defaultOpts(color, sensorName, yMax));
  }

  initBarChart(canvasId, labels, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    this.charts[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          data: labels.map(() => 80 + Math.random() * 15),
          backgroundColor: colors || ['#1976D2','#43A047','#F57F17','#E53935','#7B1FA2'],
          borderRadius: 4, borderSkipped: false,
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 } } },
          y: { min: 0, max: 100, grid: { color: 'rgba(0,0,0,0.04)' }, ticks: { font: { size: 10 } } }
        }
      }
    });
  }

  initRadarChart(canvasId) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;
    this.charts[canvasId] = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: ['Utilization', 'Throughput', 'Downtime', 'Energy', 'Health'],
        datasets: [{
          label: 'Factory KPIs',
          data: [88, 92, 95, 87, 90],
          borderColor: '#1976D2', backgroundColor: 'rgba(25,118,210,0.15)',
          borderWidth: 2, pointRadius: 3, pointBackgroundColor: '#1976D2',
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, animation: false,
        plugins: { legend: { display: false } },
        scales: { r: { min: 0, max: 100, ticks: { font: { size: 9 }, stepSize: 25 } } }
      }
    });
  }

  pushData(canvasId, value, datasetIndex = 0) {
    const chart = this.charts[canvasId];
    if (!chart) return;
    const ds = chart.data.datasets[datasetIndex];
    ds.data.push(value);
    if (ds.data.length > this.maxDataPoints) ds.data.shift();
    chart.data.labels.push('');
    if (chart.data.labels.length > this.maxDataPoints) chart.data.labels.shift();
    chart.update('none');
  }

  updateBarData(canvasId, values) {
    const chart = this.charts[canvasId];
    if (!chart) return;
    chart.data.datasets[0].data = values;
    const colors = values.map(v => v >= 85 ? '#43A047' : v >= 65 ? '#F57F17' : '#E53935');
    chart.data.datasets[0].backgroundColor = colors;
    chart.update('none');
  }

  updateRadar(canvasId, values) {
    const chart = this.charts[canvasId];
    if (!chart) return;
    chart.data.datasets[0].data = values;
    chart.update('none');
  }

  destroy() {
    Object.values(this.charts).forEach(c => c.destroy());
    this.charts = {};
  }
}
