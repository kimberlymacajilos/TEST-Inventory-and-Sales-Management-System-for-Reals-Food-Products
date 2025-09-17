/**
 * Dashboard Analytics
 */

'use strict';

(function () {
  fetch("/api/sales-vs-expenses/")
    .then(res => res.json())
    .then(data => {
      new ApexCharts(document.querySelector("#salesExpensesChart"), {
        chart: { type: "line", height: 300 },
        series: [
          { name: "Sales", data: data.sales },
          { name: "Expenses", data: data.expenses }
        ],
        xaxis: { categories: data.months }
      }).render();
    });

  fetch("/api/best-sellers/")
    .then(res => res.json())
    .then(data => {
      new ApexCharts(document.querySelector("#bestSellerChart"), {
        chart: { type: "pie", height: 300 },
        series: data.data,
        labels: data.labels,
        legend: { position: "bottom" }
      }).render();
    });
})();

