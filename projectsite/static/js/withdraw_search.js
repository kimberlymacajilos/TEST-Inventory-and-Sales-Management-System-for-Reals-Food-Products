document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchInput");
  const dateFilter = document.getElementById("dateFilter");
  const tableBody = document.getElementById("withdrawalTableBody");
  const paginationContainer = document.querySelector(".pagination-container");

  let timeout;

  function fetchWithdrawals(page = 1) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      const params = new URLSearchParams();

      if (searchInput.value.trim()) params.append("q", searchInput.value.trim());
      if (dateFilter.value) params.append("date", dateFilter.value);
      params.append("page", page);

      const url = `/withdrawals/?${params.toString()}`;

      fetch(url)
        .then(response => response.text())
        .then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");

          const newRows = doc.querySelector("#withdrawalTableBody");
          if (newRows) tableBody.innerHTML = newRows.innerHTML;

          const newPagination = doc.querySelector(".pagination-container");
          if (newPagination && paginationContainer) {
            paginationContainer.innerHTML = newPagination.innerHTML;

            paginationContainer.querySelectorAll("q").forEach(link => {
              link.addEventListener("click", function (e) {
                e.preventDefault();
                const page = new URL(this.href).searchParams.get("page") || 1;
                fetchWithdrawals(page);
              });
            });
          }
        })
        .catch(err => console.error("Error fetching withdrawals:", err));
    }, 300);
  }

  if (searchInput) searchInput.addEventListener("input", () => fetchWithdrawals(1));
  if (dateFilter) dateFilter.addEventListener("change", () => fetchWithdrawals(1));
});
