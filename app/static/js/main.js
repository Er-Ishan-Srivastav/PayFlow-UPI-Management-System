document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((el) => {
    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 250ms ease";
    }, 4200);
  });
});
