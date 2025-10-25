document.addEventListener("DOMContentLoaded", function () {
  const monthFilter = document.getElementById("monthFilter");
  const yearFilter = document.getElementById("yearFilter");
  const resetFilter = document.getElementById("resetFilter");
  const contentContainer = document.getElementById("bestsellerContent");
  const filterInfo = document.getElementById("filterInfo");

  let timeout;

  function fetchBestsellers() {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      let url = "/best-seller-products/?";
      const params = new URLSearchParams();

      if (monthFilter && monthFilter.value) {
        params.append("month", monthFilter.value);
      } 
      else if (yearFilter && yearFilter.value) {
        params.append("year", yearFilter.value);
      }

      url += params.toString();

      fetch(url)
        .then(response => response.text())
        .then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");

          const newContent = doc.querySelector("#bestsellerContent");
          if (newContent && contentContainer) {
            contentContainer.innerHTML = newContent.innerHTML;
          }

          const newFilterInfo = doc.querySelector("#filterInfo");
          if (newFilterInfo && filterInfo) {
            filterInfo.textContent = newFilterInfo.textContent;
          }
        })
        .catch(err => console.error("Error fetching bestsellers:", err));
    }, 300);
  }

  function resetToCurrentMonth() {
    if (monthFilter) monthFilter.value = "";
    if (yearFilter) yearFilter.value = "";
    fetchBestsellers();
  }

  function handleMonthChange() {
    if (monthFilter.value && yearFilter) {
      yearFilter.value = "";
    }
    fetchBestsellers();
  }

  function handleYearChange() {
    if (yearFilter.value && monthFilter) {
      monthFilter.value = "";
    }
    fetchBestsellers();
  }

  if (monthFilter) monthFilter.addEventListener("change", handleMonthChange);
  if (yearFilter) yearFilter.addEventListener("change", handleYearChange);
  if (resetFilter) resetFilter.addEventListener("click", resetToCurrentMonth);
});
