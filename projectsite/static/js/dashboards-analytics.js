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

  fetch("/api/revenue-change/")
    .then(res => res.json())
    .then(data => {
      const months = data.months;
      const revenueChanges = data.revenue_changes;

      const now = new Date();
      const currentMonth = now.toISOString().slice(5, 7);
      const currentYear = now.getFullYear().toString();  

      const options = {
        chart: { type: "bar", height: 350 },
        series: [{ name: "Revenue Change", data: [] }],
        xaxis: { categories: [] },
        title: { text: "Revenue Change" },
        dataLabels: { 
          enabled: true, 
          formatter: val => `₱${val.toLocaleString()}`
        },
        plotOptions: {
          bar: {
            colors: {
              ranges: [
                {
                  from: -1000000000, 
                  to: -1,            
                  color: "#FF0000"  
                },
                {
                  from: 0,
                  to: 1000000000,  
                  color: "#008FFB"  
                }
              ]
            }
          }
        }
      };
      const chart = new ApexCharts(document.querySelector("#revenueChangeChart"), options);
      chart.render();

      const yearSelect = document.querySelector("#yearFilter");
      const monthSelect = document.querySelector("#monthFilter");

      function updateChart() {
        const selectedYear = yearSelect.value;
        const selectedMonth = monthSelect.value;

        const filteredMonths = months.filter(m => m.startsWith(selectedYear));
        const filteredRevenues = revenueChanges.filter((_, i) => months[i].startsWith(selectedYear));

        if (selectedMonth === "all") {

          chart.updateOptions({
            series: [{ data: filteredRevenues }],
            xaxis: { categories: filteredMonths },
            title: { text: `Revenue Change - ${selectedYear}` }
          });
        } else {
          const selected = `${selectedYear}-${selectedMonth}`;
          const i = months.indexOf(selected);
          chart.updateOptions({
            series: [{ data: i >= 0 ? [revenueChanges[i]] : [] }],
            xaxis: { categories: i >= 0 ? [months[i]] : [] },
            title: { text: `Revenue Change - ${selected}` }
          });
        }
      }

      yearSelect.addEventListener("change", updateChart);
      monthSelect.addEventListener("change", updateChart);

      if ([...yearSelect.options].some(opt => opt.value === currentYear)) {
        yearSelect.value = currentYear;
      }
      if ([...monthSelect.options].some(opt => opt.value === currentMonth)) {
        monthSelect.value = currentMonth;
      } else {
        monthSelect.value = "all";
      }

      updateChart();
    });

})();

