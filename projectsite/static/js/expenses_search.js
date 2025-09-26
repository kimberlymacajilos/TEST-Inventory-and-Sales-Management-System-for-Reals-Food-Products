document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("searchInput");
    const categoryFilter = document.getElementById("categoryFilter");
    const dateFilter = document.getElementById("dateFilter");
    const tableBody = document.getElementById("expensesTableBody");
    const pagination = document.querySelector(".pagination-container");
    const summaryContainer = document.getElementById("expensesSummary");

    // Debounce typing
    let timeout;

    function fetchExpenses() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            let url = "/expenses/?";
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

                    const newRows = doc.querySelector("#expensesTableBody");
                    if (newRows) tableBody.innerHTML = newRows.innerHTML;

                    const newPagination = doc.querySelector(".pagination-container");
                    if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;

              
                    const newSummary = doc.querySelector("#expensesSummary");
                    if (newSummary && summaryContainer) summaryContainer.innerHTML = newSummary.innerHTML;
                })
                .catch(err => console.error("Error fetching expenses:", err));
        }, 300);
    }

    
    searchInput.addEventListener("input", fetchExpenses);
    categoryFilter.addEventListener("change", fetchExpenses);
    dateFilter.addEventListener("change", fetchExpenses);
});
