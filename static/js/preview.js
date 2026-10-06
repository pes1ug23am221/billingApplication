/**
 * preview.js — Fast phone uploads with client-side image compression.
 * Resizes 4K phone photos down to 1080p-1440p in milliseconds before upload,
 * shrinking 10MB phone uploads down to ~250KB for instant checkout.
 */

const input       = document.getElementById('images');
const container   = document.getElementById('preview-container');
const form        = document.getElementById('new-bill-form');
const banner      = document.getElementById('processing-banner');
const bannerText  = banner ? banner.querySelector('p') : null;
const submitBtn   = document.getElementById('submit-btn');

// ── Show thumbnail previews ──────────────────────────────
if (input && container) {
  input.addEventListener('change', function () {
    container.innerHTML = '';
    const files = Array.from(this.files);

    files.forEach(function (file, index) {
      if (!file.type.startsWith('image/')) return;
      const thumbWrap = document.createElement('div');
      thumbWrap.style.position = 'relative';

      const img = document.createElement('img');
      img.className = 'preview-thumb';
      img.alt = file.name;
      img.src = URL.createObjectURL(file);
      img.onload = function () { URL.revokeObjectURL(img.src); };

      const badge = document.createElement('span');
      badge.style.position = 'absolute';
      badge.style.bottom = '4px';
      badge.style.right = '4px';
      badge.style.background = 'rgba(0,0,0,0.6)';
      badge.style.color = '#fff';
      badge.style.fontSize = '10px';
      badge.style.padding = '1px 4px';
      badge.style.borderRadius = '3px';
      badge.textContent = '#' + (index + 1);

      thumbWrap.appendChild(img);
      thumbWrap.appendChild(badge);
      container.appendChild(thumbWrap);
    });
  });
}

// ── Fast Client-Side Image Compressor ────────────────────
function compressImage(file, maxDimension = 1600, quality = 0.82) {
  return new Promise((resolve) => {
    // If not an image, return original
    if (!file.type.startsWith('image/')) {
      return resolve(file);
    }

    const reader = new FileReader();
    reader.onload = function (e) {
      const img = new Image();
      img.onload = function () {
        let width = img.width;
        let height = img.height;

        // Calculate aspect-preserving dimensions
        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          } else {
            width = Math.round((width * maxDimension) / height);
            maxDimension = maxDimension;
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          function (blob) {
            if (!blob) {
              return resolve(file);
            }
            // Preserve filename with .jpg extension
            const compressedFile = new File([blob], file.name.replace(/\.[^.]+$/, '') + '.jpg', {
              type: 'image/jpeg',
              lastModified: Date.now(),
            });
            resolve(compressedFile);
          },
          'image/jpeg',
          quality
        );
      };
      img.onerror = function () {
        resolve(file);
      };
      img.src = e.target.result;
    };
    reader.onerror = function () {
      resolve(file);
    };
    reader.readAsDataURL(file);
  });
}

// ── Intercept form submit: Compress -> Fast Upload ──────
if (form && input && banner && submitBtn) {
  form.addEventListener('submit', async function (e) {
    if (!input.files || input.files.length === 0) return;

    e.preventDefault();
    submitBtn.disabled = true;
    banner.style.display = 'flex';

    try {
      const files = Array.from(input.files);
      const formData = new FormData();

      // Add CSRF token
      const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]');
      if (csrfToken) formData.append('csrfmiddlewaretoken', csrfToken.value);

      // Add store name
      const storeName = form.querySelector('[name=store_name]');
      if (storeName) formData.append('store_name', storeName.value);

      // Compress each photo
      for (let i = 0; i < files.length; i++) {
        if (bannerText) {
          bannerText.textContent = `⚡ Optimizing photo ${i + 1} of ${files.length} for fast upload…`;
        }
        const compressed = await compressImage(files[i]);
        formData.append('images', compressed);
      }

      if (bannerText) {
        bannerText.textContent = `🔍 Analyzing groceries… this takes ~2 seconds.`;
      }

      // Send via fetch
      const response = await fetch(form.action || window.location.href, {
        method: 'POST',
        body: formData,
      });

      if (response.redirected) {
        window.location.href = response.url;
      } else if (response.ok) {
        const text = await response.text();
        document.open();
        document.write(text);
        document.close();
      } else {
        alert('Upload failed. Please check your connection and try again.');
        banner.style.display = 'none';
        submitBtn.disabled = false;
      }
    } catch (err) {
      console.error('Fast upload error:', err);
      // Fallback: regular submit
      form.submit();
    }
  });
}
