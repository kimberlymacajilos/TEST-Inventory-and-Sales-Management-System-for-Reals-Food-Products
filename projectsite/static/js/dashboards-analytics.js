/**
 * Dashboard Analytics
 */

'use strict';

(function () {
  fetch("/api/sales-vs-expenses/")
    .then(res => res.json())
    .then(data => {
      const options = { 
        chart: { type: "line", height: 350 },
        series: [],
        xaxis: { categories: [] },
        title: { text: "Sales vs Expenses" },
        dataLabels: {
          enabled: false 
        },
        markers: {
          size: 5,
          colors: ["#008FFB", "#00E396"], 
          strokeColors: "#fff",
          strokeWidth: 2,
          hover: { size: 7 }
        }
      };
      const chart = new ApexCharts(document.querySelector("#salesExpensesChart"), options);
      chart.render();

      const yearSelect = document.querySelector("#yearFilter");
      const monthSelect = document.querySelector("#monthFilter");

      function updateChart() {
        const selectedYear = yearSelect.value;
        const selectedMonth = monthSelect.value;

        if (selectedMonth === "all") {
          const filteredMonths = data.months.filter(m => m.startsWith(selectedYear));
          const filteredSales = data.sales.filter((_, i) => data.months[i].startsWith(selectedYear));
          const filteredExpenses = data.expenses.filter((_, i) => data.months[i].startsWith(selectedYear));

          chart.updateOptions({
            series: [
              { name: "Sales", data: filteredSales },
              { name: "Expenses", data: filteredExpenses }
            ],
            xaxis: { categories: filteredMonths },
            title: { text: `Monthly Sales vs Expenses - ${selectedYear}` },
            chart: { type: "line" } 
          });
        } else {
          const selected = `${selectedYear}-${selectedMonth}`;
          const filteredDates = data.daily_dates.filter(d => d.startsWith(selected));
          const filteredSales = data.sales_daily.filter((_, i) => data.daily_dates[i].startsWith(selected));
          const filteredExpenses = data.expenses_daily.filter((_, i) => data.daily_dates[i].startsWith(selected));

          const dayLabels = filteredDates.map(d => {
            const day = new Date(d).getDate();
            return `${day}`;
          });

          chart.updateOptions({
            series: [
              { name: "Sales", data: filteredSales },
              { name: "Expenses", data: filteredExpenses }
            ],
            xaxis: { categories: dayLabels },
            title: { text: `Daily Sales vs Expenses - ${selected}` },
            chart: { type: "line" }
          });
        }
      }

      yearSelect.addEventListener("change", updateChart);
      monthSelect.addEventListener("change", updateChart);

      const now = new Date();
      const currentYear = now.getFullYear().toString();
      const currentMonth = String(now.getMonth() + 1).padStart(2, "0");

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

  document.addEventListener("DOMContentLoaded", function () {
  const yearSelect = document.querySelector("#revenueYearFilter");
  const monthSelect = document.querySelector("#revenueMonthFilter");

  const options = {
    chart: {
      type: "bar",
      height: 350,
      toolbar: { show: true },
      zoom: { enabled: true }
    },
    series: [{ name: "Revenue Change", data: [] }],
    xaxis: {
      categories: [],
      tickPlacement: "on"
    },
    plotOptions: {
      bar: {
        columnWidth: "40%",
        distributed: false
      }
    },
    dataLabels: {
      enabled: true,
      formatter: val => `₱${val.toLocaleString()}`
    },
    title: { text: "Revenue Change" },
    tooltip: {
      x: {
        formatter: val => val
      }
    }
  };
  const chart = new ApexCharts(document.querySelector("#revenueChangeChart"), options);
  chart.render();

  function updateChart() {
    const selectedYear = yearSelect.value;
    const selectedMonth = monthSelect.value;

    fetch(`/api/revenue-change/?year=${selectedYear}&month=${selectedMonth}`)
      .then(res => res.json())
      .then(data => {
        const labels = data.labels;
        const revenues = data.revenues;

        const formattedLabels = selectedMonth !== "all"
          ? labels.map(d => `${parseInt(d.split("-")[2], 10)}`)
          : labels.map(d => d); 
        chart.updateOptions({
          series: [{ name: "Sales", data: revenues }],
          xaxis: { categories: formattedLabels },
          title: {
            text: selectedMonth === "all"
              ? `Monthly Sales - ${selectedYear}`
              : `Daily Sales - ${selectedYear}-${selectedMonth}`
          }
        });
      });
  }

  yearSelect.addEventListener("change", updateChart);
  monthSelect.addEventListener("change", updateChart);

  const now = new Date();
  const currentMonth = now.toISOString().slice(5, 7);
  const currentYear = now.getFullYear().toString();

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

