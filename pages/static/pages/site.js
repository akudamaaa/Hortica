(() => {
  const menuButton = document.querySelector(".menu-toggle");
  const menuPanel = document.querySelector(".menu-panel");
  let menuCloseTimer;

  const setMenuOpen = (open) => {
    if (!menuButton || !menuPanel) return;
    window.clearTimeout(menuCloseTimer);
    if (open) {
      menuPanel.hidden = false;
      window.requestAnimationFrame(() => menuPanel.classList.add("is-open"));
      menuButton.setAttribute("aria-expanded", "true");
      return;
    }
    menuPanel.classList.remove("is-open");
    menuButton.setAttribute("aria-expanded", "false");
    menuCloseTimer = window.setTimeout(() => { menuPanel.hidden = true; }, 180);
  };

  if (menuButton && menuPanel) {
    menuButton.addEventListener("click", () => {
      setMenuOpen(menuButton.getAttribute("aria-expanded") !== "true");
    });
    menuPanel.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => setMenuOpen(false)));
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".header-actions")) setMenuOpen(false);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && menuButton.getAttribute("aria-expanded") === "true") {
        setMenuOpen(false);
        menuButton.focus();
      }
    });
  }

  const brandLink = document.querySelector(".brand");
  const brandLogo = document.querySelector(".brand-logo");
  if (brandLink && brandLogo) {
    const defaultLogo = brandLogo.dataset.logoDefault;
    const hoverLogo = brandLogo.dataset.logoHover;
    const preload = new Image();
    preload.src = hoverLogo;
    const showHoverLogo = () => { brandLogo.src = hoverLogo; };
    const showDefaultLogo = () => { brandLogo.src = defaultLogo; };
    brandLink.addEventListener("pointerenter", showHoverLogo);
    brandLink.addEventListener("pointerleave", showDefaultLogo);
    brandLink.addEventListener("focus", showHoverLogo);
    brandLink.addEventListener("blur", showDefaultLogo);
  }

  const dialog = document.querySelector(".photo-dialog");

  if (dialog && typeof dialog.showModal === "function") {
    const image = dialog.querySelector("figure img");
    const caption = dialog.querySelector("figcaption");
    const counter = dialog.querySelector(".photo-counter");
    const close = dialog.querySelector(".photo-close");
    const previous = dialog.querySelector(".photo-previous");
    const next = dialog.querySelector(".photo-next");
    let activePhotos = [];
    let activeIndex = 0;

    const renderPhoto = () => {
      const link = activePhotos[activeIndex];
      if (!link) return;
      image.src = link.href;
      image.alt = link.dataset.caption || "Фотография из архива яхты «Хортица»";
      caption.textContent = link.dataset.caption || "";
      counter.textContent = activePhotos.length > 1 ? `${activeIndex + 1} / ${activePhotos.length}` : "";
      previous.hidden = activePhotos.length < 2;
      next.hidden = activePhotos.length < 2;
    };

    const openPhoto = (link) => {
      const group = link.dataset.photoGroup;
      activePhotos = group
        ? Array.from(document.querySelectorAll("[data-photo-group]"))
            .filter((item) => item.dataset.photoGroup === group)
        : [link];
      activeIndex = Math.max(0, activePhotos.indexOf(link));
      renderPhoto();
      dialog.showModal();
    };

    document.querySelectorAll("[data-photo]").forEach((link) => {
      link.addEventListener("click", (event) => {
        event.preventDefault();
        openPhoto(link);
      });
    });

    previous.addEventListener("click", () => {
      activeIndex = (activeIndex - 1 + activePhotos.length) % activePhotos.length;
      renderPhoto();
    });
    next.addEventListener("click", () => {
      activeIndex = (activeIndex + 1) % activePhotos.length;
      renderPhoto();
    });
    close.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
    dialog.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft" && activePhotos.length > 1) previous.click();
      if (event.key === "ArrowRight" && activePhotos.length > 1) next.click();
    });
    dialog.addEventListener("close", () => {
      image.removeAttribute("src");
      caption.textContent = "";
      counter.textContent = "";
      activePhotos = [];
    });
  }

  document.querySelectorAll("[data-photo-cycle]").forEach((link) => {
    const photos = link.dataset.photoCycle.split("|").filter(Boolean);
    const image = link.querySelector("img");
    if (photos.length < 2 || !image) return;
    let current = Math.max(0, photos.indexOf(image.getAttribute("src")));

    window.setInterval(() => {
      let nextPhoto = Math.floor(Math.random() * photos.length);
      if (photos.length > 1 && nextPhoto === current) nextPhoto = (nextPhoto + 1) % photos.length;
      current = nextPhoto;
      image.classList.add("is-changing");
      window.setTimeout(() => {
        image.src = photos[current];
        image.classList.remove("is-changing");
      }, 180);
    }, 5000);
  });

  const profileImages = new Map();
  document.querySelectorAll("[data-profile-key]").forEach((link) => {
    const image = link.querySelector("img");
    if (!image) return;
    profileImages.set(link.dataset.profileKey, {
      image,
      base: link.dataset.profileBase,
      variants: link.dataset.profileVariants.split("|"),
    });
  });

  document.querySelectorAll("[data-profile-target]").forEach((target) => {
    const profile = profileImages.get(target.dataset.profileTarget);
    if (!profile || profile.variants.length !== 3) return;

    target.addEventListener("pointermove", (event) => {
      const bounds = target.getBoundingClientRect();
      const relativeY = ((event.clientY - bounds.top) / Math.max(bounds.height, 1)) * 150;
      let state = "base";
      if (relativeY <= 50) state = "upper";
      else if (relativeY > 51 && relativeY <= 100) state = "middle";
      else if (relativeY > 101) state = "lower";
      const index = { upper: 0, middle: 1, lower: 2 }[state];
      profile.image.src = index === undefined ? profile.base : profile.variants[index];
    });
    target.addEventListener("pointerleave", () => {
      profile.image.src = profile.base;
    });
  });
})();
