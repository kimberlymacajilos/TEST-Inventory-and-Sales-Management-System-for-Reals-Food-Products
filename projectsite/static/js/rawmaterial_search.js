//raw material search
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("rawMaterialSearchInput");
    const searchForm = document.getElementById("rawMaterialSearchForm");
    const tableBody = document.getElementById("rawMaterialTableBody");
    const pagination = document.querySelector(".pagination-container");

    searchForm.addEventListener("submit", function(e) {
        e.preventDefault();
        fetchMaterials(searchInput.value.trim());
    });

    let timeout;
    searchInput.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            fetchMaterials(searchInput.value.trim());
        }, 300);
    });

    function fetchMaterials(query = "") {
        let url = "/rawmaterials/";
        if (query) {
            url += `?q=${encodeURIComponent(query)}`;
        }

        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");

                const newRows = doc.querySelector("#rawMaterialTableBody");
                if (newRows) tableBody.innerHTML = newRows.innerHTML;

                const newPagination = doc.querySelector(".pagination-container");
                if (newPagination && pagination) pagination.innerHTML = newPagination.innerHTML;
            })
            .catch(err => console.error("Error fetching materials:", err));
    }
});


// raw material batches search
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("batchSearchInput");
    const searchForm = document.getElementById("batchSearchForm");
    const tableBody = document.getElementById("batchTableBody");
    const pagination = document.querySelector(".pagination-container");

    
    searchForm.addEventListener("submit", function(e) {
        e.preventDefault();
        fetchBatches(searchInput.value.trim());
    });

   
    let timeout;
    searchInput.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            fetchBatches(searchInput.value.trim());
        }, 300);
    });

    function fetchBatches(query = "") {
        let url = "/rawmatbatch/"; 
        if (query) {
            url += `?q=${encodeURIComponent(query)}`;
        }

        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");

                
                const newRows = doc.querySelector("#batchTableBody");
                if (newRows) {
                    tableBody.innerHTML = newRows.innerHTML;
                }

                
                const newPagination = doc.querySelector(".pagination-container");
                if (newPagination && pagination) {
                    pagination.innerHTML = newPagination.innerHTML;
                }
            })
            .catch(err => console.error("Error fetching batches:", err));
    }
});


// raw material inventory search
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("inventorySearchInput");
    const searchForm = document.getElementById("inventorySearchForm");
    const tableBody = document.getElementById("inventoryTableBody");
    const pagination = document.querySelector(".pagination-container");

    // Prevent form from submitting normally
    searchForm.addEventListener("submit", function(e) {
        e.preventDefault();
        fetchInventory(searchInput.value.trim());
    });

    // Debounce typing
    let timeout;
    searchInput.addEventListener("input", function() {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            fetchInventory(searchInput.value.trim());
        }, 300);
    });

    function fetchInventory(query = "") {
        // Use the correct URL from Django
        let url = "/rawmaterial-inventory/";
        if (query) {
            url += `?q=${encodeURIComponent(query)}`;
        }

        fetch(url)
            .then(response => response.text())
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, "text/html");

                // Update table body
                const newRows = doc.querySelector("#inventoryTableBody");
                if (newRows) {
                    tableBody.innerHTML = newRows.innerHTML;
                }

                // Update pagination
                const newPagination = doc.querySelector(".pagination-container");
                if (newPagination && pagination) {
                    pagination.innerHTML = newPagination.innerHTML;
                }
            })
            .catch(err => console.error("Error fetching inventory:", err));
    }
});

