document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("searchInput");
    const itemTypeFilter = document.getElementById("itemTypeFilter");
    const reasonFilter = document.getElementById("reasonFilter");
    const dateFilter = document.getElementById("dateFilter");
    const tableBody = document.getElementById("withdrawalTableBody");
    const pagination = document.querySelector(".pagination-container");

    let timeout;

    function buildUrl(page = 1) {
        const params = new URLSearchParams();

        if (searchInput.value.trim()) params.append("q", searchInput.value.trim());
        if (itemTypeFilter.value) params.append("item_type", itemTypeFilter.value);
        if (reasonFilter.value) params.append("reason", reasonFilter.value);
        if (dateFilter.value) params.append("date", dateFilter.value);

        params.append("page", page); // ✅ keep pagination working
        return `/withdrawals/?${params.toString()}`;
    }

    function fetchWithdrawals(page = 1) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const url = buildUrl(page);

            fetch(url)
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, "text/html");

                    // ✅ Update table body
                    const newRows = doc.querySelector("#withdrawalTableBody");
                    if (newRows) tableBody.innerHTML = newRows.innerHTML;

                    // ✅ Update pagination
                    const newPagination = doc.querySelector(".pagination-container");
                    if (newPagination && pagination) {
                        pagination.innerHTML = newPagination.innerHTML;

                        // ✅ Re-bind pagination links
                        pagination.querySelectorAll("a").forEach(link => {
                            link.addEventListener("click", function (e) {
                                e.preventDefault();
                                const page = new URL(this.href).searchParams.get("page");
                                fetchWithdrawals(page);
                            });
                        });
                    }
                })
                .catch(err => console.error("Error fetching withdrawals:", err));
        }, 300);
    }

    // Event listeners
    searchInput.addEventListener("input", () => fetchWithdrawals(1));
    itemTypeFilter.addEventListener("change", () => fetchWithdrawals(1));
    reasonFilter.addEventListener("change", () => fetchWithdrawals(1));
    dateFilter.addEventListener("change", () => fetchWithdrawals(1));

    // ✅ Initial pagination binding
    if (pagination) {
        pagination.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", function (e) {
                e.preventDefault();
                const page = new URL(this.href).searchParams.get("page");
                fetchWithdrawals(page);
            });
        });
    }
});
