(function () {
  var updated = new Date(document.lastModified);

  if (Number.isNaN(updated.getTime())) {
    return;
  }

  var formatted = new Intl.DateTimeFormat("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(updated);

  document.querySelectorAll("[data-last-updated]").forEach(function (element) {
    element.textContent = formatted;
  });
})();
