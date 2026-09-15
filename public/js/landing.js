document.addEventListener('DOMContentLoaded', () => {
  loadAmenities();
  setupContactForm();
});

// Qulayliklarni API dan yuklash
async function loadAmenities() {
  const container = document.getElementById('qulayliklar-list');
  try {
    const res = await fetch('/api/amenities');
    if (!res.ok) throw new Error('API xatolik');
    const data = await res.json();

    if (data && data.length > 0) {
      container.innerHTML = data.map(item => `
        <div class="qulaylik-card">
          <h4 class="qulaylik-card-title">${escapeHtml(item.title)}</h4>
          <p class="qulaylik-card-desc">${escapeHtml(item.description)}</p>
        </div>
      `).join('');
    }
  } catch (err) {
    console.error('Qulayliklarni yuklashda xatolik:', err);
  }
}

// Xabar yuborish formasini sozlash
function setupContactForm() {
  const form = document.getElementById('public-contact-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('contact-name').value.trim();
    const phone = document.getElementById('contact-phone').value.trim();
    const message = document.getElementById('contact-message').value.trim();
    const btn = document.getElementById('submit-btn');

    if (!name || !phone || !message) {
      showToast('Iltimos, barcha maydonlarni to\'ldiring!', 'error');
      return;
    }

    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Yuborilmoqda...';

    try {
      const res = await fetch('/api/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone, message })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Xabar yuborishda xatolik');

      showToast('✅ Xabaringiz qabul qilindi! Admin tez orada siz bilan bog\'lanadi.');
      form.reset();
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '<i class="bi bi-send-fill"></i> Xabarni Yuborish';
    }
  });
}

function showToast(text, type = 'success') {
  const toast = document.getElementById('landing-toast');
  const toastText = document.getElementById('toast-text');
  toastText.innerText = text;
  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
