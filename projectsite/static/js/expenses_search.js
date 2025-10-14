document.addEventListener("DOMContentLoaded", function () {
  const categoryFilter = document.getElementById("categoryFilter");
  const dateFilter = document.getElementById("dateFilter");
  const tableBody = document.getElementById("expensesTableBody");
  const pagination = document.querySelector(".pagination-container");
  const summaryContainer = document.getElementById("expensesSummary");

  let timeout;

  function fetchExpenses() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      let url = "/expenses/?";
      const params = new URLSearchParams();

      if (categoryFilter.value) params.append("category", categoryFilter.value);
      if (dateFilter.value) params.append("month", dateFilter.value);

      url += params.toString();

      fetch(url)
        .then(response => response.text())
        .then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");

          // Replace table body
          const newRows = doc.querySelector("#expensesTableBody");
          if (newRows) tableBody.innerHTML = newRows.innerHTML;

          // Replace pagination
          const newPagination = doc.querySelector(".pagination-container");
          if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;

          // Replace summary
          const newSummary = doc.querySelector("#expensesSummary");
          if (newSummary && summaryContainer) summaryContainer.innerHTML = newSummary.innerHTML;
        })
        .catch(err => console.error("Error fetching expenses:", err));
    }, 300);
  }

  // Event listeners
  categoryFilter.addEventListener("change", fetchExpenses);
  dateFilter.addEventListener("change", fetchExpenses);
});
