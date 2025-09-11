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
})();
