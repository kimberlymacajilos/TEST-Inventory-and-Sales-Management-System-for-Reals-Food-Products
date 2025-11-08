document.addEventListener("DOMContentLoaded", function () {
  // Check for success message after page reload
  const expenseSuccess = sessionStorage.getItem('expenseSuccess');
  if (expenseSuccess) {
    showToast(expenseSuccess, 'success');
    sessionStorage.removeItem('expenseSuccess');
  }
  
  const categoryFilter = document.getElementById("categoryFilter");
  const dateFilter = document.getElementById("dateFilter");
  const tableBody = document.getElementById("expensesTableBody");
  const pagination = document.querySelector(".pagination-container");
  const summaryContainer = document.getElementById("expensesSummary");
  const currentMonthDisplay = document.getElementById("currentMonthDisplay");

  let timeout;

  function updateFilterInfo() {
    const now = new Date();
    const monthNames = ["January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"];
    
    if (dateFilter.value) {
      const [year, month] = dateFilter.value.split('-');
      const monthName = monthNames[parseInt(month) - 1];
      currentMonthDisplay.textContent = `${monthName} ${year}`;
    } else {
      const currentMonth = monthNames[now.getMonth()];
      const currentYear = now.getFullYear();
      currentMonthDisplay.textContent = `${currentMonth} ${currentYear}`;
    }
  }

  updateFilterInfo();

  function fetchExpenses(resetPage = true) {
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

      const url = "/expenses/?" + params.toString();

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
          
          // Update URL without page reload
          window.history.pushState({}, '', url);
        })
        .catch(err => console.error("Error fetching expenses:", err));
    }, 300);
  }

  // Event listeners
  categoryFilter.addEventListener("change", () => fetchExpenses(true));
  dateFilter.addEventListener("change", () => {
    updateFilterInfo();
    fetchExpenses(true);
  });
  
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
          const newRows = doc.querySelector("#expensesTableBody");
          if (newRows) tableBody.innerHTML = newRows.innerHTML;

          // Replace pagination
          const newPagination = doc.querySelector(".pagination-container");
          if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;

          // Replace summary
          const newSummary = doc.querySelector("#expensesSummary");
          if (newSummary && summaryContainer) summaryContainer.innerHTML = newSummary.innerHTML;
          
          // Update URL without page reload
          window.history.pushState({}, '', url);
          
          // Scroll to top of table
          document.querySelector(".card").scrollIntoView({ behavior: "smooth" });
        })
        .catch(err => console.error("Error fetching expenses:", err));
    }
  });
});
