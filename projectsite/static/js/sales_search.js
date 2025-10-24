document.addEventListener("DOMContentLoaded", function () {
  const categoryFilter = document.getElementById("categoryFilter");
  const dateFilter = document.getElementById("dateFilter");
  const tableBody = document.getElementById("salesTableBody");
  const pagination = document.querySelector(".pagination-container");
  const summaryContainer = document.getElementById("salesSummary");

  let timeout;

  function fetchSales(resetPage = true) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      const params = new URLSearchParams(window.location.search);
      
      // Update or remove category filter
      if (categoryFilter.value) {
        params.set("category", categoryFilter.value);
      } else {
        params.delete("category");
      }
      
      // Update or remove month filter
      if (dateFilter.value) {
        params.set("month", dateFilter.value);
      } else {
        params.delete("month");
      }
      
      // Reset to page 1 when filters change
      if (resetPage) {
        params.delete("page");
      }

      const url = "/sales/?" + params.toString();

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
          
          // Update URL without page reload
          window.history.pushState({}, '', url);
        })
        .catch(err => console.error("Error fetching sales:", err));
    }, 300);
  }

  // Event listeners
  categoryFilter.addEventListener("change", () => fetchSales(true));
  dateFilter.addEventListener("change", () => fetchSales(true));
  
  // Handle pagination clicks
  document.addEventListener("click", function(e) {
    if (e.target.closest(".pagination a")) {
      e.preventDefault();
      const link = e.target.closest("a");
      const url = link.getAttribute("href");
      
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
          
          // Update URL without page reload
          window.history.pushState({}, '', url);
          
          // Scroll to top of table
          document.querySelector(".card").scrollIntoView({ behavior: "smooth" });
        })
        .catch(err => console.error("Error fetching sales:", err));
    }
  });
});
