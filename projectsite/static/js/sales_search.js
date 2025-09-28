document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchInput");
  const categoryFilter = document.getElementById("categoryFilter");
  const dateFilter = document.getElementById("dateFilter");
  const tableBody = document.getElementById("salesTableBody");
  const pagination = document.querySelector(".pagination-container");
  const summaryContainer = document.getElementById("salesSummary");

  let timeout;

  function fetchSales() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      let url = "/sales/?";
      const params = new URLSearchParams();

      if (searchInput.value.trim()) params.append("q", searchInput.value.trim());
      if (categoryFilter.value) params.append("category", categoryFilter.value);
      if (dateFilter.value) params.append("month", dateFilter.value);

      url += params.toString();

      fetch(url)
        .then(response => response.text())
        .then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");

          // Replace table body
          const newRows = doc.querySelector("#salesTableBody");
          if (newRows) tableBody.innerHTML = newRows.innerHTML;

          // Replace pagination
          const newPagination = doc.querySelector(".pagination-container");
          if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;

          // Replace summary
          const newSummary = doc.querySelector("#salesSummary");
          if (newSummary && summaryContainer) summaryContainer.innerHTML = newSummary.innerHTML;
        })
        .catch(err => console.error("Error fetching sales:", err));
    }, 300);
  }

  // Event listeners
  searchInput.addEventListener("input", fetchSales);
  categoryFilter.addEventListener("change", fetchSales);
  dateFilter.addEventListener("change", fetchSales);
});
