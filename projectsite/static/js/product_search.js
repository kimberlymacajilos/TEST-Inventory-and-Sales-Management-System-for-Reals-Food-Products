//prod_list search
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("searchInput");
    const dateInput = document.getElementById("dateInput");
    const searchForm = document.getElementById("searchForm");
    const productsTableBody = document.getElementById("productsTableBody");
    const pagination = document.querySelector(".pagination");

    searchForm.addEventListener("submit", function(e) {
        e.preventDefault();
        fetchProducts(searchInput.value.trim(), dateInput ? dateInput.value : "");
    });

    let timeout;
    searchInput.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            fetchProducts(searchInput.value.trim(), dateInput ? dateInput.value : "");
        }, 300);
    });

    if (dateInput) {
        dateInput.addEventListener("change", function () {
            console.log("Date selected:", dateInput.value);
            fetchProducts(searchInput.value.trim(), dateInput.value);
        });
    }

    function fetchProducts(query = "", date = "") {
        let url = "/products/";
        let params = [];

        if (query) params.push(`q=${encodeURIComponent(query)}`);
        if (date) params.push(`date_created=${encodeURIComponent(date)}`);

        if (params.length > 0) {
            url += `?${params.join("&")}`;
        }

        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");

                const newRows = doc.querySelector("#productsTableBody");
                if (newRows) {
                    productsTableBody.innerHTML = newRows.innerHTML;
                }

                const newPagination = doc.querySelector(".pagination");
                if (newPagination && pagination) {
                    pagination.innerHTML = newPagination.innerHTML;
                }
            })
            .catch(err => console.error("Error fetching products:", err));
    }
});


document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("batchSearchInput");
    const monthInput = document.getElementById("batchDateFilter");
    const batchTableBody = document.getElementById("batchTableBody");
    const pagination = document.querySelector(".pagination-container");

    let timeout;

    // Trigger search on typing
    searchInput.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            fetchBatches(searchInput.value.trim(), monthInput ? monthInput.value : "");
        }, 300);
    });


    if (monthInput) {
        monthInput.addEventListener("change", function () {
            fetchBatches(searchInput.value.trim(), monthInput.value);
        });
    }

    function fetchBatches(query = "", month = "") {
        let url = "/prodbatch/";
        let params = [];

        if (query) params.push(`q=${encodeURIComponent(query)}`);
        if (month) params.push(`month=${encodeURIComponent(month)}`);

        if (params.length > 0) url += `?${params.join("&")}`;

        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");

                // Update table body
                const newRows = doc.querySelector("#batchTableBody");
                if (newRows) batchTableBody.innerHTML = newRows.innerHTML;

                // Update pagination
                const newPagination = doc.querySelector(".pagination-container");
                if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;
            })
            .catch(err => console.error("Error fetching batches:", err));
    }
});


// prodinvent_list search
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("searchInput");
    const searchForm = document.getElementById("searchForm");
    const inventoryTableBody = document.getElementById("inventoryTableBody");
    const pagination = document.querySelector(".pagination");

    // Prevent normal form submission
    searchForm.addEventListener("submit", function(e) {
        e.preventDefault();
        fetchInventory(searchInput.value.trim());
    });

    // Live search with debounce
    let timeout;
    searchInput.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            fetchInventory(searchInput.value.trim());
        }, 300);
    });

    // Fetch inventory data
    function fetchInventory(query = "") {
        let url = "/product-inventory/";
        if (query) {
            url += `?q=${encodeURIComponent(query)}`;
        }

        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");

                // Replace table body
                const newRows = doc.querySelector("#inventoryTableBody");
                if (newRows) {
                    inventoryTableBody.innerHTML = newRows.innerHTML;
                }

                // Replace pagination
                const newPagination = doc.querySelector(".pagination");
                if (newPagination && pagination) {
                    pagination.innerHTML = newPagination.innerHTML;
                }
            })
            .catch(err => console.error("Error fetching inventory:", err));
    }
});

