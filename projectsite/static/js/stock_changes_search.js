document.addEventListener("DOMContentLoaded", function () {
  // Check for success message after page reload
  const stockChangeSuccess = sessionStorage.getItem('stockChangeSuccess');
  if (stockChangeSuccess) {
    showToast(stockChangeSuccess, 'success');
    sessionStorage.removeItem('stockChangeSuccess');
  }
  
  const itemSearch = document.getElementById("itemSearch");
  const categoryFilter = document.getElementById("categoryFilter");
  const dateFilter = document.getElementById("dateFilter");
  const clearFiltersBtn = document.getElementById("clearFilters");
  const tableBody = document.getElementById("stockChangesTableBody");
  const pagination = document.querySelector(".pagination-container");
  const table = document.getElementById("stockChangesTable");

  let timeout;

  // Function to show "No results" message
  function showNoResultsIfEmpty() {
    let rows = tableBody.querySelectorAll('tr');
    let existing = document.getElementById('noStockChangesRow');

    // Exclude no-results row itself
    let actualRows = Array.from(rows).filter(r => r.id !== 'noStockChangesRow');

    if (actualRows.length === 0) {
      if (!existing) {
        const cols = table.querySelectorAll('thead th').length;
        const tr = document.createElement('tr');
        tr.id = 'noStockChangesRow';
        tr.innerHTML = `<td colspan="${cols}" class="text-center text-muted">No stock changes found</td>`;
        tableBody.appendChild(tr);
      }
    } else {
      if (existing) existing.remove();
    }
  }

  // Function to fetch stock changes with search and filters
  function fetchStockChanges(resetPage = true) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      const params = new URLSearchParams(window.location.search);
      
      // Update or remove item search
      if (itemSearch.value.trim()) {
        params.set("item", itemSearch.value.trim());
      } else {
        params.delete("item");
      }
      
      // Update or remove category filter
      if (categoryFilter.value) {
        params.set("category", categoryFilter.value);
      } else {
        params.delete("category");
      }
      
      // Update or remove date filter
      if (dateFilter.value) {
        params.set("date", dateFilter.value);
      } else {
        params.delete("date");
      }
      
      // Reset to page 1 when filters change
      if (resetPage) {
        params.delete("page");
      }

      const url = "/stock-changes/?" + params.toString();

      fetch(url)
        .then(response => response.text())
        .then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");

          // Replace table body
          const newRows = doc.querySelector("#stockChangesTableBody");
          if (newRows) tableBody.innerHTML = newRows.innerHTML;

          // Replace pagination
          const newPagination = doc.querySelector(".pagination-container");
          if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;

          // Replace modals
          const newModals = doc.querySelector('#stockChangeModalsContainer');
          const currentModals = document.querySelector('#stockChangeModalsContainer');
          if (newModals && currentModals) currentModals.innerHTML = newModals.innerHTML;
          
          // Clean up any lingering modal backdrops
          $('.modal-backdrop').remove();
          $('body').removeClass('modal-open');
          $('body').css('padding-right', '');
          
          // Show "No results" if empty
          showNoResultsIfEmpty();
          
          // Update URL without page reload
          window.history.pushState({}, '', url);
        })
        .catch(err => console.error("Error fetching stock changes:", err));
    }, 300);
  }

  // Event listeners for search and filters
  itemSearch.addEventListener("input", () => fetchStockChanges(true));
  categoryFilter.addEventListener("change", () => fetchStockChanges(true));
  dateFilter.addEventListener("change", () => fetchStockChanges(true));
  
  // Clear filters button
  clearFiltersBtn.addEventListener("click", () => {
    // Clear all inputs
    itemSearch.value = '';
    categoryFilter.value = '';
    dateFilter.value = '';
    
    // Redirect to base URL without any parameters
    window.location.href = '/stock-changes/';
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
          const newRows = doc.querySelector("#stockChangesTableBody");
          if (newRows) tableBody.innerHTML = newRows.innerHTML;

          // Replace pagination
          const newPagination = doc.querySelector(".pagination-container");
          if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;

          // Replace modals
          const newModals = doc.querySelector('#stockChangeModalsContainer');
          const currentModals = document.querySelector('#stockChangeModalsContainer');
          if (newModals && currentModals) currentModals.innerHTML = newModals.innerHTML;
          
          // Clean up any lingering modal backdrops
          $('.modal-backdrop').remove();
          $('body').removeClass('modal-open');
          $('body').css('padding-right', '');
          
          // Show "No results" if empty
          showNoResultsIfEmpty();
          
          // Update URL without page reload
          window.history.pushState({}, '', url);
          
          // Scroll to top of table
          document.querySelector(".card").scrollIntoView({ behavior: "smooth" });
        })
        .catch(err => console.error("Error fetching stock changes:", err));
    }
  });

  // Initialize - show no results if empty on page load
  showNoResultsIfEmpty();
  
  // Restore filter values from URL on page load
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.get('item')) {
    itemSearch.value = urlParams.get('item');
  }
  if (urlParams.get('category')) {
    categoryFilter.value = urlParams.get('category');
  }
  if (urlParams.get('date')) {
    dateFilter.value = urlParams.get('date');
  }
});
