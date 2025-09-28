document.addEventListener("DOMContentLoaded", function() {
    const adminFilter = document.getElementById("adminFilter");
    const logFilter = document.getElementById("logFilter");
    const dateFilter = document.getElementById("dateFilter");
    const tableBody = document.getElementById("historyTableBody");
    const paginationContainer = document.querySelector(".pagination-container");

    let timeout;

    function fetchHistoryLogs(url = null) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            // Build URL with current filters if no URL is provided
            if (!url) {
                const params = new URLSearchParams();
                if (adminFilter.value) params.append("admin", adminFilter.value);
                if (logFilter.value) params.append("log", logFilter.value);
                if (dateFilter.value) params.append("date", dateFilter.value);
                url = `/historylog/?${params.toString()}`;
            }

            fetch(url)
                .then(res => res.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, "text/html");

                    // Update table body
                    const newRows = doc.querySelector("#historyTableBody");
                    if (newRows) tableBody.innerHTML = newRows.innerHTML;

                    // Update pagination
                    const newPagination = doc.querySelector(".pagination-container");
                    if (newPagination && paginationContainer) {
                        paginationContainer.innerHTML = newPagination.innerHTML;

                        // Reattach click listeners to pagination links
                        paginationContainer.querySelectorAll("a").forEach(link => {
                            link.addEventListener("click", function(e) {
                                e.preventDefault();

                                // Preserve current filters when clicking a page
                                const pageUrl = new URL(this.href);
                                const params = new URLSearchParams();
                                if (adminFilter.value) params.append("admin", adminFilter.value);
                                if (logFilter.value) params.append("log", logFilter.value);
                                if (dateFilter.value) params.append("date", dateFilter.value);

                                const pageNum = pageUrl.searchParams.get("page") || 1;
                                params.append("page", pageNum);

                                fetchHistoryLogs(`/historylog/?${params.toString()}`);
                            });
                        });
                    }
                })
                .catch(err => console.error("Error fetching history logs:", err));
        }, 300);
    }

    // Event listeners: automatically fetch logs when filters change
    adminFilter.addEventListener("change", () => fetchHistoryLogs());
    logFilter.addEventListener("change", () => fetchHistoryLogs());
    dateFilter.addEventListener("change", () => fetchHistoryLogs());

    // Initial pagination links
    if (paginationContainer) {
        paginationContainer.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", function(e) {
                e.preventDefault();

                const pageUrl = new URL(this.href);
                const params = new URLSearchParams();
                if (adminFilter.value) params.append("admin", adminFilter.value);
                if (logFilter.value) params.append("log", logFilter.value);
                if (dateFilter.value) params.append("date", dateFilter.value);

                const pageNum = pageUrl.searchParams.get("page") || 1;
                params.append("page", pageNum);

                fetchHistoryLogs(`/historylog/?${params.toString()}`);
            });
        });
    }
});
