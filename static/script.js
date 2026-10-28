// admin (add JS for admin.html under this)

// base (add JS for base.html under this)

// cart (add JS for cart.html under this)

// checkout (add JS for checkout.html under this)

// game (add JS for game.html under this)

// index (add JS for index.html under this)

document.querySelectorAll("[data-multiselect]").forEach((box) => {
    const toggle = box.querySelector(".multiselect-toggle");
    const dropdown = box.querySelector(".multiselect-dropdown");
    const search = box.querySelector(".multiselect-search");
    const options = box.querySelectorAll(".multiselect-option");
    const label = box.querySelector(".multiselect-label");
    const includeRadio = box.querySelector('input[value="include"]');
    const excludeRadio = box.querySelector('input[value="exclude"]');
    const checkboxes = box.querySelectorAll('input[type="checkbox"]');
  
    const isGenre = Boolean(box.querySelector(".genre-checkbox"));
    const isPlatform = Boolean(box.querySelector(".platform-checkbox"));
  
    const updateLabel = () => {
      const selected = Array.from(checkboxes).filter((item) => item.checked);
      const selectedCount = selected.length;
  
      if (selectedCount === 0) {
        label.textContent = label.dataset.placeholder || "Any";
        return;
      }
  
      const excluding = excludeRadio && excludeRadio.checked;
      const prefix = excluding ? "Excluding" : "Including";
  
      if (selectedCount === 1) {
        label.textContent = `${prefix} ${selected[0].closest(".multiselect-option").querySelector("span").textContent}`;
      } else {
        label.textContent = `${prefix} ${selectedCount} selected`;
      }
    };
  
    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      const isOpen = !dropdown.hidden;
  
      document.querySelectorAll(".multiselect-dropdown").forEach((other) => {
        if (other !== dropdown) {
          other.hidden = true;
        }
      });
  
      dropdown.hidden = isOpen;
      toggle.setAttribute("aria-expanded", String(!isOpen));
  
      if (!isOpen) {
        search.focus();
      }
    });
  
    search.addEventListener("input", () => {
      const query = search.value.trim().toLowerCase();
  
      options.forEach((option) => {
        const text = option.querySelector("span").textContent.toLowerCase();
        option.style.display = text.includes(query) ? "" : "none";
      });
    });
  
    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", updateLabel);
    });
  
    if (includeRadio) {
      includeRadio.addEventListener("change", updateLabel);
    }
  
    if (excludeRadio) {
      excludeRadio.addEventListener("change", updateLabel);
    }
  
    updateLabel();
  });
  
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-multiselect]")) {
      document.querySelectorAll(".multiselect-dropdown").forEach((dropdown) => {
        dropdown.hidden = true;
      });
  
      document.querySelectorAll(".multiselect-toggle").forEach((toggle) => {
        toggle.setAttribute("aria-expanded", "false");
      });
    }
  });
  
  document.getElementById("catalog-filter-form")?.addEventListener("submit", () => {
    const genreMode = document.querySelector('input[name="genre_mode"]:checked')?.value;
    const platformMode = document.querySelector('input[name="platform_mode"]:checked')?.value;
  
    const genreChecks = Array.from(document.querySelectorAll(".genre-checkbox"));
    const platformChecks = Array.from(document.querySelectorAll(".platform-checkbox"));
  
    genreChecks.forEach((checkbox) => {
      checkbox.name = genreMode === "exclude" ? "exclude_genre_ids" : "genre_ids";
    });
  
    platformChecks.forEach((checkbox) => {
      checkbox.name = platformMode === "exclude" ? "exclude_platform_ids" : "platform_ids";
    });
  });
  
// login (add JS for login.html under this)

// orders (add JS for orders.html under this)

// register (add JS for register.html under this)

// wishlist (add JS for wishlist.html under this)
