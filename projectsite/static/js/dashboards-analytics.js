/**
 * Dashboard Analytics
 */

'use strict';

(function () {
  // Detect dark mode
  const isDarkMode = () => document.documentElement.getAttribute('data-theme') === 'dark';
  
  // Get theme colors
  const getThemeColors = () => {
    if (isDarkMode()) {
      return {
        textColor: '#f1f8f4',
        gridColor: 'rgba(119, 178, 84, 0.2)',
        tooltipBg: 'rgba(26, 31, 32, 0.95)',
        tooltipText: '#f1f8f4'
      };
    }
    return {
      textColor: '#2f3e46',
      gridColor: '#e0e0e0',
      tooltipBg: '#ffffff',
      tooltipText: '#2f3e46'
    };
  };

  // Store chart instances globally so we can update them
  let salesExpensesChart = null;
  let bestSellerChart = null;
  let revenueChart = null;

  // Function to update all charts with new theme colors
  const updateChartsTheme = () => {
    const themeColors = getThemeColors();
    const commonOptions = {
      chart: {
        foreColor: themeColors.textColor
      },
      xaxis: {
        labels: {
          style: {
            colors: themeColors.textColor
          }
        }
      },
      yaxis: {
        labels: {
          style: {
            colors: themeColors.textColor
          }
        }
      },
      title: {
        style: {
          color: themeColors.textColor
        }
      },
      grid: {
        borderColor: themeColors.gridColor
      },
      tooltip: {
        theme: isDarkMode() ? 'dark' : 'light'
      },
      legend: {
        labels: {
          colors: themeColors.textColor
        }
      }
    };

    if (salesExpensesChart) {
      salesExpensesChart.updateOptions(commonOptions);
    }
    if (bestSellerChart) {
      bestSellerChart.updateOptions(commonOptions);
    }
    if (revenueChart) {
      revenueChart.updateOptions(commonOptions);
    }
  };

  // Listen for theme changes
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.type === 'attributes' && mutation.attributeName === 'data-theme') {
        updateChartsTheme();
      }
    });
  });

  // Start observing theme changes
  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  });

  fetch("/api/sales-vs-expenses/")
    .then(res => res.json())
    .then(data => {
      const themeColors = getThemeColors();
      const options = { 
        chart: { 
          type: "line", 
          height: 350,
          foreColor: themeColors.textColor
        },
        series: [],
        xaxis: { 
          categories: [],
          labels: {
            style: {
              colors: themeColors.textColor
            }
          }
        },
        yaxis: {
          labels: {
            style: {
              colors: themeColors.textColor
            }
          }
        },
        title: { 
          text: "Sales vs Expenses",
          style: {
            color: themeColors.textColor
          }
        },
        dataLabels: {
          enabled: false 
        },
        markers: {
          size: 5,
          colors: ["#008FFB", "#00E396"], 
          strokeColors: "#fff",
          strokeWidth: 2,
          hover: { size: 7 }
        },
        grid: {
          borderColor: themeColors.gridColor
        },
        tooltip: {
          theme: isDarkMode() ? 'dark' : 'light'
        },
        legend: {
          labels: {
            colors: themeColors.textColor
          }
        }
      };
      salesExpensesChart = new ApexCharts(document.querySelector("#salesExpensesChart"), options);
      salesExpensesChart.render();

      const yearSelect = document.querySelector("#yearFilter");
      const monthSelect = document.querySelector("#monthFilter");

      function updateChart() {
        const selectedYear = yearSelect.value;
        const selectedMonth = monthSelect.value;

        if (selectedMonth === "all") {
          const filteredMonths = data.months.filter(m => m.startsWith(selectedYear));
          const filteredSales = data.sales.filter((_, i) => data.months[i].startsWith(selectedYear));
          const filteredExpenses = data.expenses.filter((_, i) => data.months[i].startsWith(selectedYear));

          salesExpensesChart.updateOptions({
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

          salesExpensesChart.updateOptions({
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
      const themeColors = getThemeColors();
      bestSellerChart = new ApexCharts(document.querySelector("#bestSellerChart"), {
        chart: { 
          type: "pie", 
          height: 300,
          foreColor: themeColors.textColor
        },
        series: data.data,
        labels: data.labels,
        legend: { 
          position: "bottom",
          labels: {
            colors: themeColors.textColor
          }
        },
        tooltip: {
          theme: isDarkMode() ? 'dark' : 'light'
        }
      });
      bestSellerChart.render();
    });

  document.addEventListener("DOMContentLoaded", function () {
  const yearSelect = document.querySelector("#revenueYearFilter");
  const monthSelect = document.querySelector("#revenueMonthFilter");

  const themeColors = getThemeColors();
  const options = {
    chart: {
      type: "bar",
      height: 350,
      toolbar: { show: true },
      zoom: { enabled: true },
      foreColor: themeColors.textColor
    },
    series: [{ name: "Revenue Change", data: [] }],
    xaxis: {
      categories: [],
      tickPlacement: "on",
      labels: {
        style: {
          colors: themeColors.textColor
        }
      }
    },
    yaxis: {
      labels: {
        style: {
          colors: themeColors.textColor
        }
      }
    },
    plotOptions: {
      bar: {
        columnWidth: "40%",
        distributed: false
      }
    },
    dataLabels: {
      enabled: true,
      formatter: val => `₱${val.toLocaleString()}`,
      style: {
        colors: [themeColors.textColor]
      }
    },
    title: { 
      text: "Revenue Change",
      style: {
        color: themeColors.textColor
      }
    },
    tooltip: {
      theme: isDarkMode() ? 'dark' : 'light',
      x: {
        formatter: val => val
      }
    },
    grid: {
      borderColor: themeColors.gridColor
    },
    legend: {
      labels: {
        colors: themeColors.textColor
      }
    }
  };
  revenueChart = new ApexCharts(document.querySelector("#revenueChangeChart"), options);
  revenueChart.render();

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
        revenueChart.updateOptions({
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

