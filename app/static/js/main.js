document.addEventListener('DOMContentLoaded', () => {
  const body = document.body;
  const sidebar = document.getElementById('sidebar');
  const openBtn = document.querySelector('[data-sidebar-open]');
  const closeEls = document.querySelectorAll('[data-sidebar-close]');

  const setSidebar = (open) => {
    body.classList.toggle('sidebar-open', open);
  };

  openBtn?.addEventListener('click', () => setSidebar(true));
  closeEls.forEach((el) => el.addEventListener('click', () => setSidebar(false)));

  document.querySelectorAll('[data-dismiss-flash]').forEach((btn) => {
    btn.addEventListener('click', () => btn.closest('.flash')?.remove());
  });

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const submit = form.querySelector('button[type="submit"], input[type="submit"]');
      if (!submit || submit.dataset.loadingApplied === 'true') return;
      const label = submit.dataset.loading;
      if (label) {
        submit.dataset.loadingApplied = 'true';
        submit.disabled = true;
        if (submit.tagName === 'BUTTON') submit.innerHTML = `<span class="loading-spinner"></span>${label}`;
        else submit.value = label;
      }
    });
  });

  document.querySelectorAll('input, select, textarea').forEach((field) => {
    field.addEventListener('focus', () => field.closest('.field-block')?.classList.add('focused'));
    field.addEventListener('blur', () => field.closest('.field-block')?.classList.remove('focused'));
  });

  // Profile modal
  const profileModal = document.getElementById('profileModal');
  const openProfile = () => {
    if (!profileModal) return;
    profileModal.classList.add('open');
    profileModal.setAttribute('aria-hidden', 'false');
  };
  const closeProfile = () => {
    if (!profileModal) return;
    profileModal.classList.remove('open');
    profileModal.setAttribute('aria-hidden', 'true');
  };
  document.querySelectorAll('.profile-trigger').forEach((el) => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      openProfile();
    });
  });
  document.getElementById('closeProfile')?.addEventListener('click', closeProfile);
  profileModal?.addEventListener('click', (e) => {
    if (e.target === profileModal) closeProfile();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeProfile();
  });

  window.setTimeout(() => {
    document.querySelectorAll('.flash').forEach((flash) => flash.classList.add('visible'));
  }, 30);
});
