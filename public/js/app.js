// ==========================================================================
// STANDALONE ADMIN PANEL API ROUTER & CONFIGURATION
// ==========================================================================
const API_BASE_URL = (
  (typeof window !== 'undefined' && window.API_BASE_URL) ||
  (typeof localStorage !== 'undefined' && localStorage.getItem('API_BASE_URL')) ||
  ((typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) ? 'http://127.0.0.1:3000' : 'https://api.kichikalloma.uz')
).replace(/\/+$/, '');

window.API_BASE_URL = API_BASE_URL;

window.getApiBaseUrl = function () {
  return API_BASE_URL;
};

window.toFullMediaUrl = function (url, fallback = '') {
  if (!url || typeof url !== 'string') return fallback || '';
  url = url.trim();
  if (!url) return fallback || '';
  if (url.startsWith('data:')) return url;

  // Agar localhost yoki 127.0.0.1 bilan kelgan bo'lsa, API_BASE_URL ga almashtiramiz
  const localMatch = url.match(/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?(\/.*)$/i);
  if (localMatch) {
    return API_BASE_URL + localMatch[3];
  }

  // To'liq internet manzili bo'lsa (https://api.kichikalloma.uz/... va boshqa)
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }

  // Nisbiy yo'l bo'lsa (/images/uploads/..., images/uploads/..., /media/... va h.k.)
  if (url.startsWith('/')) {
    return API_BASE_URL + url;
  }
  return API_BASE_URL + '/' + url;
};

window.normalizeImageUrl = function (url, fallback = '') {
  return window.toFullMediaUrl(url, fallback);
};

// Global fetch interceptor: forwards relative /api/ and /mobile/ calls to API_BASE_URL
(function () {
  const _origFetch = window.fetch;
  window.fetch = function (input, init) {
    if (typeof input === 'string') {
      if (input.startsWith('/api/') || input.startsWith('/mobile/')) {
        input = API_BASE_URL + input;
      }
    } else if (input && typeof input.url === 'string') {
      if (input.url.startsWith('/api/') || input.url.startsWith('/mobile/')) {
        try {
          input = new Request(API_BASE_URL + input.url, input);
        } catch (e) {}
      }
    }
    return _origFetch.call(this, input, init);
  };
})();

// Global state
let currentTab = 'dashboard';
let planetsList = [];
let amenitiesList = [];
let teamsList = [];
let galleryList = [];
let messagesList = [];
let libraryList = [];
let libraryCategoriesList = [];
let currentModalVideoUrl = '';
let currentModalVideoTitle = '';
let currentModalBookId = null;
let currentOpenCatId = null;
let currentOpenCatName = '';
let currentCatDetailData = null;
let faqsList = [
  {
    id: 1,
    name: "Kichik Alloma platformasi nima va u kimlar uchun mo'ljallangan?",
    description: "Kichik Alloma — 3 yoshdan 11 yoshgacha bo'lgan bolalarning aqliy, mantiqiy, nutqiy va ijodiy salohiyatini rivojlantiruvchi interaktiv ta'lim platformasidir. Platforma bolalarga sayyoralar bo'ylab qiziqarli o'yinlar, ertaklar, so'z boyligi va sun'iy intellekt orqali ta'lim beradi.",
    status: "active",
    order_num: 1
  },
  {
    id: 2,
    name: "Alloma AI yordamchisi qanday ishlaydi va uning ovozli muloqot xususiyati bormi?",
    description: "Alloma AI — Google Gemini ilg'or sun'iy intellekt texnologiyasi asosida yaratilgan pedagogik yordamchidir. Bola unga mikrofon orqali ovozli savollar berishi, darslar haqida so'rashi, ertaklar eshitishi yoki yangi bilimlarni xavfsiz va tushunarli tilda o'rganishi mumkin.",
    status: "active",
    order_num: 2
  },
  {
    id: 3,
    name: "Uran sayyorasida ingliz tilini qanday o'rganish mumkin (So'zlar, talaffuz va testlar)?",
    description: "Uran sayyorasi bolalarning chet tilini o'rganishi uchun mo'ljallangan bo'lib, 10 ta asosiy mavzu (Mevalar, Hayvonlar, Ranglar, Maktab, Oila va h.k.), har bir so'zning sof audio talaffuzi, rasmlar, transkripsiya va 4 ta variantli interaktiv test savollarini o'z ichiga oladi.",
    status: "active",
    order_num: 3
  },
  {
    id: 4,
    name: "Ota-onalar farzandining ta'lim jarayonini qanday nazorat qiladi (Ota-onalar burchagi)?",
    description: "Maxsus himoyalangan 'Ota-onalar burchagi' orqali bolaning qaysi sayyoralarni o'rganganligi, kunlik sarflagan vaqti, test natijalari, so'z boyligi o'sishi va muvaffaqiyat hisobotlarini real vaqtda kuzatib borish mumkin.",
    status: "active",
    order_num: 4
  },
  {
    id: 5,
    name: "Mobil ilovadan internet bo'lmaganda ham foydalanish mumkinmi (Offline rejim)?",
    description: "Ha! Yuklab olingan barcha sayyora darslari, audio ertaklar va ingliz tili so'zlari offline rejimda, internetsiz ham to'liq va uzluksiz ishlaydi. Sayr yoki safarda internet talab etilmaydi.",
    status: "active",
    order_num: 5
  }
];
let uranCategoriesList = [];
let uranWordsList = [];
let currentUranView = 'words';
let messageFilter = 'all';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupKeyboardShortcuts();
  loadAllData();
});

// Setup sidebar tab navigation
function setupNavigation() {
  const navButtons = document.querySelectorAll('.sidebar-nav .nav-btn[data-tab]');
  navButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      switchTab(tab);
    });
  });
}

function switchTab(tabId) {
  currentTab = tabId;

  // Update nav buttons
  document.querySelectorAll('.sidebar-nav .nav-btn').forEach(b => {
    if (b.getAttribute('data-tab') === tabId) {
      b.classList.add('active');
    } else {
      b.classList.remove('active');
    }
  });

  // Update tabs content
  document.querySelectorAll('.tab-content').forEach(section => {
    section.classList.remove('active');
  });

  const activeSection = document.getElementById(`tab-${tabId}`);
  if (activeSection) {
    activeSection.classList.add('active');
  }

  // Update page header
  const titleMap = {
    'dashboard': { title: 'Dashboard', subtitle: 'Umumiy tizim holati va so\'nggi ma\'lumotlar' },
    'planets': { title: 'Sayyoralar Boshqaruvi (Rasmli 8 ta Sayyora)', subtitle: 'Rasmli ta\'limiy sayyoralarni boshqarish' },
    'amenities': { title: 'Qulayliklar Boshqaruvi', subtitle: 'Mavjud barcha qulayliklarni boshqarish' },
    'teams': { title: 'Bizning Jamoa (Teams)', subtitle: 'Jamoa a\'zolari: Ismi, familiyasi, yo\'nalishi va rasmlarini boshqarish' },
    'gallery': { title: 'Galereya (Gallery)', subtitle: 'Platforma fotosuratlari va rasmlarini boshqarish' },
    'messages': { title: 'Kelgan Xabarlar', subtitle: 'Mijozlar tomonidan yuborilgan so\'rov va murojaatlar' },
    'faqs': { title: 'Ko\'p So\'raladigan Savollar (FAQ)', subtitle: `Mobil ilova va vebsayt uchun tez-tez beriladigan savol-javoblarni boshqarish` },
    'uran': { title: 'Uran / Nutq va Til Sayyorasi (So\'zlar va Testlar)', subtitle: 'Mobil ilova uchun inglizcha-o\'zbekcha lug\'at kategoriyalari, so\'zlar va 4 ta variantli testlar' },
    'library': { title: 'Kutubxona & Video Darslar (Library)', subtitle: 'Kutubxona kitoblari, ertaklar, audio va video darslarni to\'liq boshqarish va yuklab olish' },
    'ai': { title: 'Alloma AI Ta\'lim Yordamchisi', subtitle: 'Google Gemini 3.6 Flash asosidagi ta\'limiy va pedagogik AI' }
  };

  if (titleMap[tabId]) {
    document.getElementById('page-title').innerText = titleMap[tabId].title;
    document.getElementById('page-subtitle').innerText = titleMap[tabId].subtitle;
  }

  // Auto refresh specific tabs
  if (tabId === 'faqs') {
    fetchFaqs();
  } else if (tabId === 'uran') {
    fetchUranCategories();
  } else if (tabId === 'library') {
    fetchLibraryCategories();
    fetchLibraryBooks();
  }

  // Close mobile sidebar if open
  closeSidebar();
}

// Sidebar open/close for tablets & laptops
function toggleSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar && overlay) {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  }
}

function closeSidebar() {
  const sidebar = document.getElementById('app-sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar && overlay) {
    sidebar.classList.remove('open');
    overlay.classList.remove('active');
  }
}

// Global keyboard shortcuts (Esc to close modals)
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closePlanetModal();
      closeAmenityModal();
      closeTeamModal();
      closeGalleryModal();
      closeFaqModal();
      closeLibraryModal();
      closeLibraryVideoModal();
      closeSidebar();
    }
  });
}

// Handle clicking outside modal to close
function handleOverlayClick(event, modalId) {
  if (event.target && event.target.id === modalId) {
    if (modalId === 'planet-modal') closePlanetModal();
    if (modalId === 'amenity-modal') closeAmenityModal();
    if (modalId === 'team-modal') closeTeamModal();
    if (modalId === 'gallery-modal') closeGalleryModal();
    if (modalId === 'faq-modal') closeFaqModal();
    if (modalId === 'uran-word-modal') closeUranWordModal();
    if (modalId === 'uran-words-modal') closeUranModal();
    if (modalId === 'library-modal') closeLibraryModal();
    if (modalId === 'library-video-modal') closeLibraryVideoModal();
  }
}

// ==========================================================================
// DATA FETCHING & SYNC (/api/website/*)
// ==========================================================================

async function loadAllData() {
  await Promise.all([
    fetchStats(),
    fetchPlanets(),
    fetchAmenities(),
    fetchTeams(),
    fetchGallery(),
    fetchMessages(),
    fetchFaqs(),
    fetchUranCategories(),
    fetchUranWords(),
    fetchLibraryCategories(),
    fetchLibraryBooks()
  ]);
  syncAllCounts();
  renderDashboard();
}

// Har doim hamma joydagi sonlar va badgelarni real vaqtda yangilovchi funksiya
function syncAllCounts() {
  // Sayyoralar
  const planetsBadge = document.getElementById('planets-count-badge');
  const planetsStat = document.getElementById('stat-total-planets');
  if (planetsBadge) planetsBadge.innerText = planetsList.length;
  if (planetsStat) planetsStat.innerText = planetsList.length;

  // Qulayliklar
  const amenitiesBadge = document.getElementById('amenities-count-badge');
  const amenitiesStat = document.getElementById('stat-total-amenities');
  if (amenitiesBadge) amenitiesBadge.innerText = amenitiesList.length;
  if (amenitiesStat) amenitiesStat.innerText = amenitiesList.length;

  // Jamoa
  const teamsBadge = document.getElementById('teams-count-badge');
  const teamsStat = document.getElementById('stat-total-teams');
  if (teamsBadge) teamsBadge.innerText = teamsList.length;
  if (teamsStat) teamsStat.innerText = teamsList.length;

  // Galereya
  const galleryBadge = document.getElementById('gallery-count-badge');
  const galleryStat = document.getElementById('stat-total-gallery');
  if (galleryBadge) galleryBadge.innerText = galleryList.length;
  if (galleryStat) galleryStat.innerText = galleryList.length;

  // FAQ Savollar
  const faqsBadge = document.getElementById('faqs-count-badge');
  const faqsStat = document.getElementById('stat-total-faqs');
  if (faqsBadge) faqsBadge.innerText = faqsList.length;
  if (faqsStat) faqsStat.innerText = faqsList.length;

  // Uran / Ingliz Tili
  const uranBadge = document.getElementById('uran-count-badge') || document.getElementById('uran-words-count-badge');
  if (uranBadge) uranBadge.innerText = uranWordsList.length;

  const statUranWords = document.getElementById('stat-uran-words-total');
  if (statUranWords) statUranWords.innerText = `${uranWordsList.length} ta`;

  const statUranCats = document.getElementById('stat-uran-cats-total');
  if (statUranCats) statUranCats.innerText = `${uranCategoriesList.length} ta`;

  const statUranTests = document.getElementById('stat-uran-tests-total');
  if (statUranTests) statUranTests.innerText = `${uranWordsList.length} ta`;

  // Kutubxona & Video
  const libraryBadge = document.getElementById('library-count-badge');
  const libraryStat = document.getElementById('stat-total-library');
  if (libraryBadge) libraryBadge.innerText = libraryList.length;
  if (libraryStat) libraryStat.innerText = libraryList.length;

  // Xabarlar
  const messagesStat = document.getElementById('stat-total-messages');
  if (messagesStat) messagesStat.innerText = messagesList.length;

  const unreadCount = messagesList.filter(m => m.is_read === 0).length;
  const unreadBadge = document.getElementById('unread-count-badge');
  if (unreadBadge) {
    unreadBadge.innerText = unreadCount;
    unreadBadge.style.display = unreadCount > 0 ? 'inline-block' : 'none';
  }
}

// Fetch stats
async function fetchStats() {
  try {
    const res = await fetch('/api/website/stats');
    if (!res.ok) throw new Error('Statistika olishda xatolik');
    const data = await res.json();

    if (document.getElementById('stat-total-visitors')) document.getElementById('stat-total-visitors').innerText = (data.totalVisitors || 0).toLocaleString();
    if (document.getElementById('stat-total-planets')) document.getElementById('stat-total-planets').innerText = data.totalPlanets || 0;
    if (document.getElementById('stat-total-amenities')) document.getElementById('stat-total-amenities').innerText = data.totalAmenities || 0;
    if (document.getElementById('stat-total-teams')) document.getElementById('stat-total-teams').innerText = data.totalTeams || 0;
    if (document.getElementById('stat-total-gallery')) document.getElementById('stat-total-gallery').innerText = data.totalGallery || 0;
    if (document.getElementById('stat-total-messages')) document.getElementById('stat-total-messages').innerText = data.totalMessages || 0;
    if (document.getElementById('stat-total-faqs')) document.getElementById('stat-total-faqs').innerText = data.totalFaqs || 0;

    // Badges
    if (document.getElementById('planets-count-badge')) document.getElementById('planets-count-badge').innerText = data.totalPlanets || 0;
    if (document.getElementById('amenities-count-badge')) document.getElementById('amenities-count-badge').innerText = data.totalAmenities || 0;
    if (document.getElementById('teams-count-badge')) document.getElementById('teams-count-badge').innerText = data.totalTeams || 0;
    if (document.getElementById('gallery-count-badge')) document.getElementById('gallery-count-badge').innerText = data.totalGallery || 0;
    if (document.getElementById('faqs-count-badge')) document.getElementById('faqs-count-badge').innerText = data.totalFaqs || 0;
    
    const unreadBadge = document.getElementById('unread-count-badge');
    if (unreadBadge) {
      unreadBadge.innerText = data.unreadMessages || 0;
      unreadBadge.style.display = (data.unreadMessages > 0) ? 'inline-block' : 'none';
    }
  } catch (err) {
    console.error('Stats error:', err);
  }
}

// ==========================================================================
// 1. SAYYORALAR (PLANETS) LOGIC (/api/website/planets)
// ==========================================================================

function normalizeImageUrl(url, fallback = '') {
  return window.toFullMediaUrl(url, fallback);
}

function getPlanetFallback(title) {
  const t = (title || '').toLowerCase();
  if (t.includes('mars') || t.includes('jismoniy')) return 'images/planets/mars.svg';
  if (t.includes('saturn') || t.includes('mantiq')) return 'images/planets/saturn.svg';
  if (t.includes('merkur') || t.includes('mercury') || t.includes('kasb')) return 'images/planets/purple.svg';
  if (t.includes('yupiter') || t.includes('jupiter') || t.includes('taym')) return 'images/planets/coral.svg';
  if (t.includes('uran') || t.includes('axloqiy') || t.includes('ingliz')) return 'images/planets/cyan-rings.svg';
  if (t.includes('vener') || t.includes('venus') || t.includes('do\'kon') || t.includes('dokon')) return 'images/planets/teal-moon.svg';
  if (t.includes('neptun') || t.includes('neptune') || t.includes('emotsion')) return 'images/planets/deep-blue.svg';
  return 'images/planets/earth.svg';
}

async function fetchPlanets() {
  try {
    const res = await fetch('/api/website/planets');
    if (!res.ok) throw new Error('Sayyoralarni olishda xatolik');
    planetsList = await res.json();
    renderPlanets();
  } catch (err) {
    console.error('Planets error:', err);
    document.getElementById('planets-grid').innerHTML = `<div class="empty-state">Sayyoralarni yuklab bo'lmadi.</div>`;
  }
}


// Helper to map planet name or id to 3D shape key
function getPlanet3DShapeKey(planet) {
  if (!planet) return 'logo';
  const name = ((planet.title || planet.name || '') + '').toLowerCase();
  if (name.includes('merkur') || name.includes('mercury')) return 'mercury';
  if (name.includes('vener') || name.includes('venus')) return 'venus';
  if (name.includes('yer') || name.includes('earth') || name.includes('zamin')) return 'earth';
  if (name.includes('mars')) return 'mars';
  if (name.includes('yupiter') || name.includes('jupiter')) return 'jupiter';
  if (name.includes('saturn')) return 'saturn';
  if (name.includes('uran')) return 'uran';
  if (name.includes('neptun') || name.includes('neptune')) return 'neptune';
  
  const idMap = { 1: 'earth', 2: 'mars', 3: 'jupiter', 4: 'saturn', 5: 'uran', 6: 'neptune', 7: 'venus', 8: 'mercury' };
  return idMap[planet.id] || 'saturn';
}

function open3DPlanetExperience(planetId) {
  const planet = planetsList.find(p => p.id === planetId) || { id: planetId, title: 'Sayyora' };
  const shapeKey = getPlanet3DShapeKey(planet);
  if (window.openCosmicUniverse) {
    window.openCosmicUniverse(shapeKey);
  }
}
window.open3DPlanetExperience = open3DPlanetExperience;

function renderPlanets() {
  syncAllCounts();
  const container = document.getElementById('planets-grid');
  const searchTerm = (document.getElementById('planet-search')?.value || '').toLowerCase();

  const filtered = planetsList.filter(p => 
    (p.title || p.name || '').toLowerCase().includes(searchTerm) || 
    (p.description && p.description.toLowerCase().includes(searchTerm))
  );

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="bi bi-globe-americas" style="font-size: 36px; color: var(--yellow-primary);"></i>
        <p style="margin-top: 8px;">Hech qanday sayyora topilmadi.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => {
    const planetTitle = item.title || item.name || 'Sayyora';
    const fallbackSvg = getPlanetFallback(planetTitle + ' ' + (item.description || ''));
    const cleanImg = normalizeImageUrl(item.image, fallbackSvg);

    const shapeKey = getPlanet3DShapeKey(item);
    return `
    <div class="planet-card" onclick="open3DPlanetExperience(${item.id})" style="cursor: pointer; position: relative;">
      <div class="planet-image-container">
        <img src="${escapeHtml(cleanImg)}" 
             alt="${escapeHtml(planetTitle)}" 
             class="planet-img" 
             loading="lazy"
             onerror="this.onerror=null; this.src='${fallbackSvg}';">
        <div style="position: absolute; top: 12px; right: 12px; background: rgba(0,0,0,0.65); backdrop-filter: blur(8px); border: 1px solid rgba(250,204,21,0.4); color: #facc15; font-size: 11px; font-weight: 800; padding: 4px 10px; border-radius: 20px; display: inline-flex; align-items: center; gap: 4px;">
          <i class="bi bi-stars"></i> 3D Particle
        </div>
      </div>

      <div class="planet-content">
        <div class="planet-header-row">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span style="width: 16px; height: 16px; border-radius: 50%; background: ${item.gradient || 'linear-gradient(150deg, #ff5e00, #ff8c00)'}; display: inline-block; border: 1px solid rgba(255,255,255,0.3); box-shadow: 0 0 6px rgba(0,0,0,0.5);" title="Card foni gradienti"></span>
            <h4 class="planet-card-title">${escapeHtml(planetTitle)}</h4>
            ${item.video ? `<span style="background: rgba(250,204,21,0.18); color: #facc15; border: 1px solid rgba(250,204,21,0.4); font-size: 10px; font-weight: 800; padding: 2px 7px; border-radius: 6px; display: inline-flex; align-items: center; gap: 3px;" title="Video dars mavjud"><i class="bi bi-play-circle-fill"></i> Video</span>` : ''}
          </div>
          <span class="badge-status ${item.status === 'active' ? 'active' : 'inactive'}">
            ${item.status === 'active' ? '● Faol' : '● Nofaol'}
          </span>
        </div>

        <p class="planet-card-desc">${escapeHtml(item.description || '')}</p>

        <div class="planet-footer" onclick="event.stopPropagation()">
          <button class="btn btn-sm btn-yellow" onclick="open3DPlanetExperience(${item.id})" style="font-size: 12px; font-weight: 800; padding: 5px 12px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px;">
            <i class="bi bi-stars"></i> 3D Ko'rish
          </button>
          <div class="amenity-actions">
            <button class="action-btn-sm" title="Tahrirlash" onclick="openPlanetModal(${item.id})">
              <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="action-btn-sm delete-btn" title="O'chirish" onclick="handleDeletePlanet(${item.id})">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  }).join('');
}

// Gradient yordamchi funksiyalari
function parsePlanetGradient(gradStr) {
  let color1 = '#ff5e00';
  let color2 = '#ff8c00';
  let angle = '150deg';
  if (!gradStr) return { color1, color2, angle, full: `linear-gradient(${angle}, ${color1} 0%, ${color2} 100%)` };

  const angleMatch = gradStr.match(/linear-gradient\(\s*([^,]+)/);
  if (angleMatch && angleMatch[1]) {
    const rawAngle = angleMatch[1].trim();
    if (rawAngle.includes('deg') || rawAngle.includes('to ') || /^\d+$/.test(rawAngle)) {
      angle = rawAngle.endsWith('deg') || rawAngle.startsWith('to ') ? rawAngle : rawAngle + 'deg';
    }
  }

  const hexMatches = gradStr.match(/#[a-fA-F0-9]{6}|#[a-fA-F0-9]{3}/g);
  if (hexMatches && hexMatches.length >= 2) {
    color1 = hexMatches[0];
    color2 = hexMatches[1];
  }
  return { color1, color2, angle, full: gradStr };
}

window.handleAngleSelectChange = function(val) {
  if (!val) return;
  const angleInput = document.getElementById('planet-grad-angle');
  if (angleInput) {
    angleInput.value = val;
    handleGradientChange();
  }
};

window.handleGradientChange = function() {
  const c1 = (document.getElementById('planet-grad-color1') && document.getElementById('planet-grad-color1').value) || '#ff5e00';
  const c2 = (document.getElementById('planet-grad-color2') && document.getElementById('planet-grad-color2').value) || '#ff8c00';
  let ang = (document.getElementById('planet-grad-angle') && document.getElementById('planet-grad-angle').value) || '150deg';
  
  // Format pure numbers into degrees (e.g. 120 -> 120deg)
  ang = ang.trim();
  if (/^\d+$/.test(ang)) {
    ang = ang + 'deg';
  }
  if (!ang) ang = '150deg';

  const grad = `linear-gradient(${ang}, ${c1} 0%, ${c2} 100%)`;
  if (document.getElementById('planet-gradient-val')) document.getElementById('planet-gradient-val').value = grad;
  const prev = document.getElementById('planet-gradient-preview');
  if (prev) prev.style.background = grad;

  // Sync select if it matches
  const select = document.getElementById('planet-grad-angle-select');
  if (select) {
    const exists = Array.from(select.options).some(o => o.value === ang);
    select.value = exists ? ang : '';
  }
};

window.setPlanetGradient = function(c1, c2, ang = '150deg') {
  if (document.getElementById('planet-grad-color1')) document.getElementById('planet-grad-color1').value = c1;
  if (document.getElementById('planet-grad-color2')) document.getElementById('planet-grad-color2').value = c2;
  if (document.getElementById('planet-grad-angle')) document.getElementById('planet-grad-angle').value = ang;
  const select = document.getElementById('planet-grad-angle-select');
  if (select) {
    const exists = Array.from(select.options).some(o => o.value === ang);
    select.value = exists ? ang : '';
  }
  handleGradientChange();
};

// Open Planet Modal
function openPlanetModal(id = null) {
  const modal = document.getElementById('planet-modal');
  const modalTitle = document.getElementById('planet-modal-title');
  const form = document.getElementById('planet-form');

  form.reset();
  document.getElementById('custom-url-group').style.display = 'none';

  if (id) {
    const item = planetsList.find(p => p.id === id);
    if (item) {
      document.getElementById('planet-id').value = item.id;
      document.getElementById('planet-title').value = item.title;
      document.getElementById('planet-desc').value = item.description || '';
      document.getElementById('planet-status').value = item.status || 'active';
      
      const currentImage = item.image || '/images/planets/earth.svg';
      document.getElementById('planet-image-val').value = currentImage;

      const presetSelect = document.getElementById('planet-preset-select');
      const hasOption = Array.from(presetSelect.options).some(o => o.value === currentImage);
      if (hasOption) {
        presetSelect.value = currentImage;
      } else {
        presetSelect.value = 'custom';
        document.getElementById('custom-url-group').style.display = 'block';
        document.getElementById('planet-custom-url').value = currentImage;
      }

      updatePlanetImageDisplay(currentImage);

      // Gradientni o'rnatish
      const gradInfo = parsePlanetGradient(item.gradient);
      if (document.getElementById('planet-grad-color1')) document.getElementById('planet-grad-color1').value = gradInfo.color1;
      if (document.getElementById('planet-grad-color2')) document.getElementById('planet-grad-color2').value = gradInfo.color2;
      if (document.getElementById('planet-grad-angle')) document.getElementById('planet-grad-angle').value = gradInfo.angle;
      const angleSelect = document.getElementById('planet-grad-angle-select');
      if (angleSelect) {
        const exists = Array.from(angleSelect.options).some(o => o.value === gradInfo.angle);
        angleSelect.value = exists ? gradInfo.angle : '';
      }
      if (document.getElementById('planet-gradient-val')) document.getElementById('planet-gradient-val').value = item.gradient || gradInfo.full;
      const prev = document.getElementById('planet-gradient-preview');
      if (prev) prev.style.background = item.gradient || gradInfo.full;

      // Videoni o'rnatish
      const currentVideo = item.video || '';
      if (document.getElementById('planet-video-url')) document.getElementById('planet-video-url').value = currentVideo;
      updatePlanetVideoPreview(currentVideo);

      modalTitle.innerHTML = '<i class="bi bi-pencil-square text-yellow"></i> <span>Sayyorani Tahrirlash</span>';
    }
  } else {
    document.getElementById('planet-id').value = '';
    document.getElementById('planet-preset-select').value = '/images/planets/earth.svg';
    document.getElementById('planet-image-val').value = '/images/planets/earth.svg';
    updatePlanetImageDisplay('/images/planets/earth.svg');
    setPlanetGradient('#ff5e00', '#ff8c00', '150deg');
    if (document.getElementById('planet-video-url')) document.getElementById('planet-video-url').value = '';
    updatePlanetVideoPreview('');
    modalTitle.innerHTML = '<i class="bi bi-plus-circle text-yellow"></i> <span>Yangi Sayyora Qo\'shish</span>';
  }

  modal.classList.add('show');
}

function closePlanetModal() {
  const player = document.getElementById('planet-video-preview-player');
  if (player) {
    try { player.pause(); } catch(e) {}
    player.src = '';
  }
  const modal = document.getElementById('planet-modal');
  if (modal) modal.classList.remove('show');
}

// Video boshqaruvi funksiyalari
function updatePlanetVideoPreview(url) {
  const wrap = document.getElementById('planet-video-preview-wrap');
  const player = document.getElementById('planet-video-preview-player');
  if (!wrap || !player) return;

  if (url && url.trim()) {
    player.src = normalizeImageUrl(url.trim());
    wrap.style.display = 'block';
  } else {
    try { player.pause(); } catch(e) {}
    player.src = '';
    wrap.style.display = 'none';
  }
}

window.handlePlanetVideoUrlChange = function(url) {
  updatePlanetVideoPreview(url);
};

window.clearPlanetVideo = function() {
  if (document.getElementById('planet-video-url')) document.getElementById('planet-video-url').value = '';
  if (document.getElementById('planet-video-file-upload')) document.getElementById('planet-video-file-upload').value = '';
  updatePlanetVideoPreview('');
};

window.handlePlanetVideoFileUpload = async function(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  showToast("Video yuklanmoqda, iltimos kuting...", "info");

  try {
    const res = await fetch('/api/website/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      let errMsg = "Video yuklashda xatolik yuz berdi";
      if (res.status === 413) {
        errMsg = "Video hajmi juda katta (413 Request Entity Too Large)! Serverda Nginx 'client_max_body_size 100M;' sozlanmagan.";
      } else {
        try {
          const err = await res.json();
          errMsg = err.detail || errMsg;
        } catch (e) {
          errMsg = `Server xatoligi: ${res.status} ${res.statusText}`;
        }
      }
      throw new Error(errMsg);
    }

    const data = await res.json();
    const videoUrl = data.url || (data.filename ? '/images/uploads/' + data.filename : '');
    if (document.getElementById('planet-video-url')) {
      document.getElementById('planet-video-url').value = videoUrl;
    }
    updatePlanetVideoPreview(videoUrl);
    showToast("Video muvaffaqiyatli yuklandi!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
};

function handlePlanetPresetChange(val) {
  const customGroup = document.getElementById('custom-url-group');
  if (val === 'custom') {
    customGroup.style.display = 'block';
    const customUrl = document.getElementById('planet-custom-url').value.trim() || '/images/planets/earth.svg';
    updatePlanetImageDisplay(customUrl);
  } else {
    customGroup.style.display = 'none';
    updatePlanetImageDisplay(val);
  }
}

function handleCustomUrlChange(url) {
  if (url.trim()) {
    updatePlanetImageDisplay(url.trim());
  }
}

function updatePlanetImageDisplay(imgSrc, label = null) {
  document.getElementById('planet-image-val').value = imgSrc;
  const previewImg = document.getElementById('planet-preview-img');
  const previewName = document.getElementById('planet-preview-name');
  
  if (previewImg) {
    previewImg.src = normalizeImageUrl(imgSrc, 'images/planets/earth.svg');
    previewImg.onerror = function() { this.onerror = null; this.src = 'images/planets/earth.svg'; };
  }
  if (previewName) {
    previewName.innerText = label || ((imgSrc && (imgSrc.includes('/uploads/') || imgSrc.startsWith('http'))) ? 'Tanlangan/Yuklangan rasm' : imgSrc);
  }
}

// Save Planet (/api/website/planets)
async function handleSavePlanet(event) {
  event.preventDefault();
  const id = document.getElementById('planet-id').value;
  const title = document.getElementById('planet-title').value.trim();
  const description = document.getElementById('planet-desc').value.trim();
  const image = document.getElementById('planet-image-val').value || '/images/planets/earth.svg';
  const status = document.getElementById('planet-status').value;
  const gradient = (document.getElementById('planet-gradient-val') && document.getElementById('planet-gradient-val').value) || null;
  const video = (document.getElementById('planet-video-url') && document.getElementById('planet-video-url').value.trim()) || null;

  if (!title) {
    showToast("Iltimos, sayyora nomini kiriting!", "error");
    return;
  }

  const payload = { title, description, image, status, gradient, video };

  try {
    let res;
    if (id) {
      res = await fetch(`/api/website/planets/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/website/planets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Xatolik yuz berdi");
    }

    showToast(id ? "Sayyora muvaffaqiyatli yangilandi!" : "Yangi sayyora rasmi bilan qo'shildi!");
    closePlanetModal();
    await fetchPlanets();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Delete Planet (/api/website/planets/{id})
async function handleDeletePlanet(id) {
  if (!confirm("Haqiqatan ham bu sayyorani o'chirmoqchimisiz?")) return;

  try {
    const res = await fetch(`/api/website/planets/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("O'chirishda xatolik yuz berdi");

    showToast("Sayyora muvaffaqiyatli o'chirildi!");
    await fetchPlanets();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ==========================================================================
// 2. QULAYLIKLAR (AMENITIES) LOGIC (/api/website/amenities)
// ==========================================================================

async function fetchAmenities() {
  try {
    const res = await fetch('/api/website/amenities');
    if (!res.ok) throw new Error('Qulayliklarni olishda xatolik');
    amenitiesList = await res.json();
    renderAmenities();
  } catch (err) {
    console.error('Amenities error:', err);
    document.getElementById('amenities-grid').innerHTML = `<div class="empty-state">Qulayliklarni yuklab bo'lmadi.</div>`;
  }
}

function renderAmenities() {
  syncAllCounts();
  const container = document.getElementById('amenities-grid');
  const searchTerm = (document.getElementById('amenity-search')?.value || '').toLowerCase();

  const filtered = amenitiesList.filter(a => 
    a.title.toLowerCase().includes(searchTerm) || 
    (a.description && a.description.toLowerCase().includes(searchTerm))
  );

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="bi bi-inbox" style="font-size: 32px; color: var(--yellow-primary);"></i>
        <p style="margin-top: 8px;">Hech qanday qulaylik topilmadi.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => `
    <div class="amenity-card">
      <div class="amenity-top">
        <h4 class="amenity-title" style="margin-bottom: 0;">${escapeHtml(item.title)}</h4>
        <span class="badge-status ${item.status === 'active' ? 'active' : 'inactive'}">
          ${item.status === 'active' ? '● Faol' : '● Nofaol'}
        </span>
      </div>

      <p class="amenity-desc">${escapeHtml(item.description || 'Tavsif kiritilmagan.')}</p>

      <div class="amenity-footer">
        <span class="amenity-date"><i class="bi bi-calendar3"></i> ${formatDate(item.created_at)}</span>
        <div class="amenity-actions">
          <button class="action-btn-sm" title="Tahrirlash" onclick="openAmenityModal(${item.id})">
            <i class="bi bi-pencil-fill"></i>
          </button>
          <button class="action-btn-sm delete-btn" title="O'chirish" onclick="handleDeleteAmenity(${item.id})">
            <i class="bi bi-trash-fill"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

// Modal open/close for amenities
function openAmenityModal(id = null) {
  const modal = document.getElementById('amenity-modal');
  const modalTitle = document.getElementById('modal-title');
  const form = document.getElementById('amenity-form');

  form.reset();

  if (id) {
    const item = amenitiesList.find(a => a.id === id);
    if (item) {
      document.getElementById('amenity-id').value = item.id;
      document.getElementById('amenity-title').value = item.title;
      document.getElementById('amenity-desc').value = item.description || '';
      document.getElementById('amenity-status').value = item.status || 'active';
      modalTitle.innerHTML = '<i class="bi bi-pencil-square text-yellow"></i> <span>Qulaylikni Tahrirlash</span>';
    }
  } else {
    document.getElementById('amenity-id').value = '';
    modalTitle.innerHTML = '<i class="bi bi-plus-circle text-yellow"></i> <span>Yangi Qulaylik Qo\'shish</span>';
  }

  modal.classList.add('show');
}

function closeAmenityModal() {
  const modal = document.getElementById('amenity-modal');
  if (modal) modal.classList.remove('show');
}

// Save Amenity (/api/website/amenities)
async function handleSaveAmenity(event) {
  event.preventDefault();
  const id = document.getElementById('amenity-id').value;
  const title = document.getElementById('amenity-title').value.trim();
  const description = document.getElementById('amenity-desc').value.trim();
  const status = document.getElementById('amenity-status').value;

  if (!title) {
    showToast("Iltimos, qulaylik nomini kiriting!", "error");
    return;
  }

  const payload = { title, description, status };

  try {
    let res;
    if (id) {
      res = await fetch(`/api/website/amenities/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/website/amenities', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Xatolik yuz berdi");
    }

    showToast(id ? "Qulaylik muvaffaqiyatli yangilandi!" : "Yangi qulaylik qo'shildi!");
    closeAmenityModal();
    await fetchAmenities();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Delete Amenity (/api/website/amenities/{id})
async function handleDeleteAmenity(id) {
  if (!confirm("Haqiqatan ham bu qulaylikni o'chirmoqchimisiz?")) return;

  try {
    const res = await fetch(`/api/website/amenities/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("O'chirishda xatolik yuz berdi");

    showToast("Qulaylik o'chirildi!");
    await fetchAmenities();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ==========================================================================
// 3. BIZNING JAMOA (TEAMS) LOGIC (/api/website/teams)
// ==========================================================================

async function fetchTeams() {
  try {
    const res = await fetch('/api/website/teams');
    if (!res.ok) throw new Error('Jamoa ma\'lumotlarini olishda xatolik');
    teamsList = await res.json();
    renderTeams();
  } catch (err) {
    console.error('Teams error:', err);
    const container = document.getElementById('teams-grid');
    if (container) {
      container.innerHTML = `<div class="empty-state">Jamoa a'zolarini yuklab bo'lmadi.</div>`;
    }
  }
}

function renderTeams() {
  syncAllCounts();
  const container = document.getElementById('teams-grid');
  if (!container) return;

  const searchTerm = (document.getElementById('team-search')?.value || '').toLowerCase();

  const filtered = teamsList.filter(t => 
    t.full_name.toLowerCase().includes(searchTerm) || 
    t.first_name.toLowerCase().includes(searchTerm) || 
    t.last_name.toLowerCase().includes(searchTerm) || 
    t.role.toLowerCase().includes(searchTerm)
  );

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="bi bi-people" style="font-size: 36px; color: var(--yellow-primary);"></i>
        <p style="margin-top: 8px;">Hech qanday jamoa a'zosi topilmadi.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(member => {
    const cleanImg = normalizeImageUrl(member.image, 'images/team/member1.svg');
    return `
    <div class="team-card">
      <div class="team-avatar-container">
        <img src="${escapeHtml(cleanImg)}" 
             alt="${escapeHtml(member.full_name || (member.first_name + ' ' + member.last_name))}" 
             class="team-avatar-img" 
             loading="lazy"
             onerror="this.onerror=null; this.src='images/team/member1.svg';">
      </div>

      <div class="team-content">
        <h4 class="team-name">${escapeHtml(member.full_name || (member.first_name + ' ' + member.last_name))}</h4>
        <div>
          <span class="team-role-badge">
            <i class="bi bi-briefcase text-yellow"></i> ${escapeHtml(member.role)}
          </span>
        </div>

        ${member.description ? `<p class="team-bio" style="font-size: 13px; color: var(--text-muted); margin-top: 6px; line-height: 1.4;">${escapeHtml(member.description)}</p>` : ''}

        <div class="team-footer">
          <span class="amenity-date"><i class="bi bi-clock"></i> ID: #${member.id}</span>
          <div class="amenity-actions">
            <button class="action-btn-sm" title="Tahrirlash" onclick="openTeamModal(${member.id})">
              <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="action-btn-sm delete-btn" title="O'chirish" onclick="handleDeleteTeam(${member.id})">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  `;
  }).join('');
}

// Open Team Modal
function openTeamModal(id = null) {
  const modal = document.getElementById('team-modal');
  const modalTitle = document.getElementById('team-modal-title');
  const form = document.getElementById('team-form');

  form.reset();

  if (id !== null && id !== undefined && id !== '') {
    const item = teamsList.find(t => String(t.id) === String(id));
    if (item) {
      document.getElementById('team-id').value = item.id;
      document.getElementById('team-first-name').value = item.first_name || '';
      document.getElementById('team-last-name').value = item.last_name || '';
      document.getElementById('team-role').value = item.role || '';
      document.getElementById('team-desc').value = item.description || '';
      
      const currentImage = item.image || '/images/team/member1.svg';
      document.getElementById('team-image-val').value = currentImage;
      document.getElementById('team-custom-url').value = currentImage;

      updateTeamImageDisplay(currentImage);
      modalTitle.innerHTML = '<i class="bi bi-pencil-square text-yellow"></i> <span>Jamoa A\'zosini Tahrirlash</span>';
    }
  } else {
    document.getElementById('team-id').value = '';
    document.getElementById('team-first-name').value = '';
    document.getElementById('team-last-name').value = '';
    document.getElementById('team-role').value = '';
    document.getElementById('team-desc').value = '';
    document.getElementById('team-custom-url').value = '';
    document.getElementById('team-image-val').value = '/images/team/member1.svg';
    updateTeamImageDisplay('/images/team/member1.svg');
    modalTitle.innerHTML = '<i class="bi bi-person-plus-fill text-yellow"></i> <span>Yangi Jamoa A\'zosi Qo\'shish</span>';
  }

  modal.classList.add('show');
}

function closeTeamModal() {
  const modal = document.getElementById('team-modal');
  if (modal) modal.classList.remove('show');
}

function handleTeamCustomUrlChange(url) {
  const cleanUrl = url.trim() || '/images/team/member1.svg';
  updateTeamImageDisplay(cleanUrl);
}

function updateTeamImageDisplay(imgSrc, label = null) {
  document.getElementById('team-image-val').value = imgSrc;
  const previewImg = document.getElementById('team-preview-img');
  const previewName = document.getElementById('team-preview-name');
  
  if (previewImg) {
    previewImg.src = normalizeImageUrl(imgSrc, 'images/team/member1.svg');
    previewImg.onerror = function() { this.onerror = null; this.src = 'images/team/member1.svg'; };
  }
  if (previewName) {
    previewName.innerText = label || ((imgSrc && (imgSrc.includes('/uploads/') || imgSrc.startsWith('http'))) ? 'Tanlangan/Yuklangan rasm' : imgSrc);
  }
}

// Save Team Member (/api/website/teams)
async function handleSaveTeam(event) {
  event.preventDefault();
  const id = document.getElementById('team-id').value;
  const first_name = document.getElementById('team-first-name').value.trim();
  const last_name = document.getElementById('team-last-name').value.trim();
  const role = document.getElementById('team-role').value.trim();
  const description = document.getElementById('team-desc').value.trim();
  const image = document.getElementById('team-image-val').value || '/images/team/member1.svg';

  if (!first_name || !last_name) {
    showToast("Iltimos, ism va familiyani kiriting!", "error");
    return;
  }
  if (!role) {
    showToast("Iltimos, yo'nalishi / lavozimini kiriting!", "error");
    return;
  }

  const payload = { first_name, last_name, role, description, image };

  try {
    let res;
    if (id) {
      res = await fetch(`/api/website/teams/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/website/teams', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Xatolik yuz berdi");
    }

    showToast(id ? "Jamoa a'zosi muvaffaqiyatli yangilandi!" : "Yangi jamoa a'zosi rasmi bilan qo'shildi!");
    closeTeamModal();
    await fetchTeams();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Delete Team Member (/api/website/teams/{id})
async function handleDeleteTeam(id) {
  if (!confirm("Haqiqatan ham bu jamoa a'zosini o'chirmoqchimisiz?")) return;

  try {
    const res = await fetch(`/api/website/teams/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("O'chirishda xatolik yuz berdi");

    showToast("Jamoa a'zosi muvaffaqiyatli o'chirildi!");
    await fetchTeams();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ==========================================================================
// 4. GALEREYA (GALLERY) LOGIC (/api/website/gallery)
// ==========================================================================

async function fetchGallery() {
  try {
    const res = await fetch('/api/website/gallery');
    if (!res.ok) throw new Error('Galereyani olishda xatolik');
    galleryList = await res.json();
    renderGallery();
  } catch (err) {
    console.error('Gallery error:', err);
    const container = document.getElementById('gallery-grid');
    if (container) {
      container.innerHTML = `<div class="empty-state">Galereya rasmlarini yuklab bo'lmadi.</div>`;
    }
  }
}

function renderGallery() {
  syncAllCounts();
  const container = document.getElementById('gallery-grid');
  if (!container) return;

  const searchTerm = (document.getElementById('gallery-search')?.value || '').toLowerCase();

  const filtered = galleryList.filter(g => 
    !searchTerm || (g.title && g.title.toLowerCase().includes(searchTerm))
  );

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <i class="bi bi-images" style="font-size: 36px; color: var(--yellow-primary);"></i>
        <p style="margin-top: 8px;">Galereyada rasmlar mavjud emas.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => {
    const cleanImg = normalizeImageUrl(item.image, 'images/gallery/photo1.svg');
    return `
    <div class="gallery-card">
      <div class="gallery-image-wrap">
        <img src="${escapeHtml(cleanImg)}" 
             alt="${escapeHtml(item.title || 'Galereya rasmi')}" 
             class="gallery-img" 
             loading="lazy"
             onerror="this.onerror=null; this.src='images/gallery/photo1.svg';">
        <button class="gallery-overlay-btn" title="Rasmni o'chirish" onclick="handleDeleteGallery(${item.id})">
          <i class="bi bi-trash-fill"></i>
        </button>
      </div>

      <div class="gallery-info">
        <span class="gallery-title-text" title="${escapeHtml(item.title || '')}">
          <i class="bi bi-image text-yellow" style="margin-right: 4px;"></i>
          ${escapeHtml(item.title || 'Rasm #' + item.id)}
        </span>
        <span class="gallery-date-text">${formatDate(item.created_at)}</span>
      </div>
    </div>
  `;
  }).join('');
}

function openGalleryModal() {
  const modal = document.getElementById('gallery-modal');
  const form = document.getElementById('gallery-form');
  form.reset();

  document.getElementById('gallery-image-val').value = '/images/gallery/photo1.svg';
  document.getElementById('gallery-custom-url').value = '';
  document.getElementById('gallery-title').value = '';
  updateGalleryImageDisplay('/images/gallery/photo1.svg');

  modal.classList.add('show');
}

function closeGalleryModal() {
  const modal = document.getElementById('gallery-modal');
  if (modal) modal.classList.remove('show');
}

function handleGalleryCustomUrlChange(url) {
  const cleanUrl = url.trim() || '/images/gallery/photo1.svg';
  updateGalleryImageDisplay(cleanUrl);
}

function updateGalleryImageDisplay(imgSrc, label = null) {
  document.getElementById('gallery-image-val').value = imgSrc;
  const previewImg = document.getElementById('gallery-preview-img');
  const previewName = document.getElementById('gallery-preview-name');
  
  if (previewImg) {
    previewImg.src = normalizeImageUrl(imgSrc, 'images/gallery/photo1.svg');
    previewImg.onerror = function() { this.onerror = null; this.src = 'images/gallery/photo1.svg'; };
  }
  if (previewName) {
    previewName.innerText = label || ((imgSrc && (imgSrc.includes('/uploads/') || imgSrc.startsWith('http'))) ? 'Tanlangan/Yuklangan rasm' : imgSrc);
  }
}

async function handleSaveGallery(event) {
  event.preventDefault();
  const image = document.getElementById('gallery-image-val').value;
  const title = document.getElementById('gallery-title').value.trim();

  if (!image) {
    showToast("Iltimos, rasm tanlang yoki yuklang!", "error");
    return;
  }

  const payload = { image, title };

  try {
    const res = await fetch('/api/website/gallery', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Rasmni qo'shishda xatolik");
    }

    showToast("Rasm galereyaga muvaffaqiyatli qo'shildi!");
    closeGalleryModal();
    await fetchGallery();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleDeleteGallery(id) {
  if (!confirm("Haqiqatan ham bu rasmni galereyadan o'chirmoqchimisiz?")) return;

  try {
    const res = await fetch(`/api/website/gallery/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("O'chirishda xatolik yuz berdi");

    showToast("Rasm galereyadan o'chirildi!");
    await fetchGallery();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Helper to automatically compress images client-side before upload to prevent HTTP 413
async function compressImageIfNeeded(file, maxDimension = 1600, maxSizeBytes = 950 * 1024) {
  if (!file || !file.type || !file.type.startsWith('image/') || file.type.includes('svg')) {
    return file;
  }

  // Agar rasm hajmi 950KB dan kichik bo'lsa, o'zgartirish shart emas
  if (file.size <= maxSizeBytes) {
    return file;
  }

  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          } else {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (blob && blob.size < file.size) {
              const newFileName = file.name.replace(/\.[^/.]+$/, "") + ".jpg";
              const compressedFile = new File([blob], newFileName, {
                type: 'image/jpeg',
                lastModified: Date.now()
              });
              resolve(compressedFile);
            } else {
              resolve(file);
            }
          },
          'image/jpeg',
          0.85
        );
      };
      img.onerror = () => resolve(file);
      img.src = e.target.result;
    };
    reader.onerror = () => resolve(file);
    reader.readAsDataURL(file);
  });
}

// Universal Direct File Upload to /api/website/upload (For Planets, Teams & Gallery)
async function handleFileUpload(event, type = 'planet') {
  let file = event.target.files && event.target.files[0];
  if (!file) return;

  try {
    if (file.type && file.type.startsWith('image/') && file.size > 950 * 1024) {
      showToast("Katta hajmdagi rasm avtomatik optimallashtirilmoqda...", "info");
      file = await compressImageIfNeeded(file);
    }

    const formData = new FormData();
    formData.append('file', file);

    showToast("Rasm serverga yuklanmoqda...", "info");
    const res = await fetch('/api/website/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      let errMsg = "Rasmni yuklab bo'lmadi";
      if (res.status === 413) {
        errMsg = "Fayl hajmi juda katta (413 Request Entity Too Large)! Serverda Nginx 'client_max_body_size' limiti oshirilishi kerak yoki kichikroq fayl tanlang.";
      } else {
        try {
          const err = await res.json();
          errMsg = err.detail || errMsg;
        } catch (e) {
          errMsg = `Server xatoligi: ${res.status} ${res.statusText}`;
        }
      }
      throw new Error(errMsg);
    }

    const data = await res.json();
    
    if (type === 'planet') {
      document.getElementById('planet-preset-select').value = 'custom';
      document.getElementById('custom-url-group').style.display = 'block';
      document.getElementById('planet-custom-url').value = data.url;
      updatePlanetImageDisplay(data.url, file.name);
    } else if (type === 'team') {
      document.getElementById('team-custom-url').value = data.url;
      updateTeamImageDisplay(data.url, file.name);
    } else if (type === 'gallery') {
      document.getElementById('gallery-custom-url').value = data.url;
      updateGalleryImageDisplay(data.url, file.name);
    }

    showToast("Rasm muvaffaqiyatli yuklandi!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ==========================================================================
// 5. XABARLAR (MESSAGES) LOGIC (/api/website/messages)
// ==========================================================================

async function fetchMessages() {
  try {
    const res = await fetch('/api/website/messages');
    if (!res.ok) throw new Error('Xabarlarni olishda xatolik');
    messagesList = await res.json();
    renderMessages();
    renderDashboardMessages();
  } catch (err) {
    console.error('Messages error:', err);
    document.getElementById('messages-list').innerHTML = `<div class="empty-state">Xabarlarni yuklab bo'lmadi.</div>`;
  }
}

function setMessageFilter(filter, btn) {
  messageFilter = filter;
  document.querySelectorAll('.filter-group .filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderMessages();
}

function filterMessages() {
  renderMessages();
}

function renderMessages() {
  syncAllCounts();
  const container = document.getElementById('messages-list');
  const searchTerm = (document.getElementById('message-search')?.value || '').toLowerCase();

  let filtered = messagesList.filter(m => {
    const matchesSearch = 
      m.name.toLowerCase().includes(searchTerm) ||
      m.phone.toLowerCase().includes(searchTerm) ||
      m.message.toLowerCase().includes(searchTerm);

    if (messageFilter === 'unread') {
      return matchesSearch && m.is_read === 0;
    }
    return matchesSearch;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="bi bi-chat-square-dots" style="font-size: 36px; color: var(--yellow-primary);"></i>
        <p style="margin-top: 10px;">Hech qanday xabar topilmadi.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(msg => `
    <div class="message-item ${msg.is_read === 0 ? 'unread' : ''}">
      <div class="message-sender">
        <div class="sender-name">
          ${escapeHtml(msg.name)}
          ${msg.is_read === 0 ? '<span class="badge-unread-pill">YANGI</span>' : ''}
        </div>
        <a href="tel:${escapeHtml(msg.phone)}" class="sender-phone">
          <i class="bi bi-telephone-fill"></i> ${escapeHtml(msg.phone)}
        </a>
      </div>

      <div class="message-body-wrap">
        <div class="message-text">
          ${escapeHtml(msg.message)}
        </div>
        <div class="message-meta">
          <span><i class="bi bi-clock-history"></i> ${msg.formatted_time || formatDate(msg.created_at)}</span>
          <span>•</span>
          <span style="color: ${msg.is_read === 0 ? 'var(--yellow-primary)' : 'var(--color-success)'}">
            <i class="bi bi-${msg.is_read === 0 ? 'envelope-fill' : 'envelope-open'}"></i>
            ${msg.is_read === 0 ? 'O\'qilmagan' : 'O\'qilgan'}
          </span>
        </div>
      </div>

      <div class="message-actions-col">
        ${msg.is_read === 0 ? `
          <button class="btn btn-success-outline" onclick="handleMarkAsRead(${msg.id})" title="O'qilgan deb belgilash">
            <i class="bi bi-check2"></i> O'qildi
          </button>
        ` : ''}
        <button class="btn btn-danger-outline" onclick="handleDeleteMessage(${msg.id})" title="Xabarni o'chirish">
          <i class="bi bi-trash"></i> O'chirish
        </button>
      </div>
    </div>
  `).join('');
}

function renderDashboardMessages() {
  const container = document.getElementById('dashboard-messages-list');
  const topList = messagesList.slice(0, 6);

  if (topList.length === 0) {
    container.innerHTML = '<div class="empty-state">Kelgan xabarlar mavjud emas.</div>';
    return;
  }

  container.innerHTML = topList.map(msg => {
    const initials = msg.name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase() || 'M';
    return `
      <div class="mini-item">
        <div class="mini-item-left">
          <div class="avatar-initials">${escapeHtml(initials)}</div>
          <div style="min-width: 0;">
            <div class="mini-item-title">
              ${escapeHtml(msg.name)} 
              ${msg.is_read === 0 ? '<span class="badge-unread-pill" style="margin-left: 6px;">Yangi</span>' : ''}
            </div>
            <div class="mini-item-sub">
              <i class="bi bi-telephone text-yellow"></i> ${escapeHtml(msg.phone)} • ${escapeHtml(msg.message.substring(0, 60))}...
            </div>
          </div>
        </div>
        <div class="amenity-date" style="flex-shrink: 0;"><i class="bi bi-clock"></i> ${msg.formatted_time || formatDate(msg.created_at)}</div>
      </div>
    `;
  }).join('');
}

// Mark Message as Read (/api/website/messages/{id}/read)
async function handleMarkAsRead(id) {
  try {
    const res = await fetch(`/api/website/messages/${id}/read`, { method: 'PATCH' });
    if (!res.ok) throw new Error("Holatni o'zgartirishda xatolik");

    showToast("Xabar o'qilgan deb belgilandi!");
    await fetchMessages();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Delete Message (/api/website/messages/{id})
async function handleDeleteMessage(id) {
  if (!confirm("Haqiqatan ham bu xabarni o'chirmoqchimisiz?")) return;

  try {
    const res = await fetch(`/api/website/messages/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("Xabarni o'chirishda xatolik");

    showToast("Xabar muvaffaqiyatli o'chirildi!");
    await fetchMessages();
    await fetchStats();
  } catch (err) {
    showToast(err.message, "error");
  }
}

// ==========================================
// UTILITIES
// ==========================================

function renderDashboard() {
  renderDashboardMessages();
}

function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const toastMsg = document.getElementById('toast-message');
  const toastIcon = document.getElementById('toast-icon');

  toastMsg.innerText = message;
  if (type === 'error') {
    toastIcon.className = 'bi bi-exclamation-triangle-fill text-danger';
    toast.style.borderColor = 'var(--color-danger)';
  } else if (type === 'info') {
    toastIcon.className = 'bi bi-info-circle-fill text-yellow';
    toast.style.borderColor = 'var(--yellow-primary)';
  } else {
    toastIcon.className = 'bi bi-check-circle-fill text-yellow';
    toast.style.borderColor = 'var(--yellow-primary)';
  }

  toast.classList.add('show');
  setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const s = String(dateStr).trim();
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?/);
  if (m) {
    const [, y, mo, d, hh, mm] = m;
    return `${d}.${mo}.${y}, ${hh}:${mm}`;
  }
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return dateStr;
  return date.toLocaleString('uz-UZ', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
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

// ==============================================================================
// ALLOMA AI CHAT LOGIC (GEMINI 3.6 FLASH)
// ==============================================================================
let aiChatHistory = [];

const PLANET_NAMES_MAP = {
  42: "Kognitiv",
  43: "Jismoniy va motorika",
  44: "Nutq va til",
  45: "Ijtimoiy",
  46: "Emotsional",
  47: "Axloqiy",
  48: "Ijodkorlik",
  49: "O'z-o'zini boshqarish",
  50: "Quyosh"
};

function selectPlanetAndAutoSpeak(planetId) {
  if (!planetId) return;
  const numId = parseInt(planetId);
  const selectEl = document.getElementById('ai-planet-select');
  if (selectEl) selectEl.value = numId;

  // Active chip tugmasini belgilash
  document.querySelectorAll('.planet-chip-btn').forEach(btn => {
    if (parseInt(btn.getAttribute('data-pid')) === numId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  const pName = PLANET_NAMES_MAP[numId] || `Sayyora`;
  const input = document.getElementById('ai-input-text');
  if (input) {
    input.value = `Menga ${pName} sayyorasi haqida gapirib ber: bu yerda nimalar bor va nima ish qilamiz?`;
    handleSendAdminAi(new Event('submit'));
  }
}

function sendAiPreset(promptText) {
  const input = document.getElementById('ai-input-text');
  if (input) {
    input.value = promptText;
    const form = document.getElementById('ai-chat-form');
    if (form) {
      handleSendAdminAi(new Event('submit'));
    }
  }
}

function setAiAge(age, btnEl) {
  const ageInput = document.getElementById('ai-child-age');
  if (ageInput) ageInput.value = age;
  document.querySelectorAll('.btn-age-chip').forEach(b => b.classList.remove('active'));
  if (btnEl) btnEl.classList.add('active');
  const planetSelect = document.getElementById('ai-planet-select');
  const currentPid = planetSelect ? planetSelect.value : null;
  if (currentPid) {
    selectPlanetAndAutoSpeak(currentPid);
  }
}

function clearAiChat() {
  aiChatHistory = [];
  const container = document.getElementById('ai-messages-container');
  if (container) {
    container.innerHTML = `
      <div class="ai-message-row bot">
        <div class="ai-bubble-avatar"><i class="bi bi-robot"></i></div>
        <div class="ai-bubble-body">
          <div class="ai-bubble-header">
            <span class="ai-bubble-name">Alloma AI</span>
            <span class="ai-bubble-time">Hozir</span>
          </div>
          <div class="ai-bubble-text">
            Assalomu alaykum! Suhbat tozalandi. Alloma AI sizning yangi savollaringizni kutmoqda! 🌟✨
          </div>
        </div>
      </div>
    `;
  }
  showToast('Suhbat tarixi tozalandi', 'info');
}

async function handleSendAdminAi(e) {
  if (e && e.preventDefault) e.preventDefault();
  const inputEl = document.getElementById('ai-input-text');
  const userText = inputEl ? inputEl.value.trim() : '';
  if (!userText) return;

  const childNameEl = document.getElementById('ai-child-name');
  const childAgeEl = document.getElementById('ai-child-age');
  const planetSelectEl = document.getElementById('ai-planet-select');
  const childName = childNameEl && childNameEl.value ? childNameEl.value.trim() : null;
  const childAge = childAgeEl && childAgeEl.value ? parseInt(childAgeEl.value) : null;
  const planetId = planetSelectEl && planetSelectEl.value ? parseInt(planetSelectEl.value) : null;

  const container = document.getElementById('ai-messages-container');
  const submitBtn = document.getElementById('ai-submit-btn');

  // 1. Display User Message
  appendAiBubble('user', userText, 'Siz', 'Hozir');
  if (inputEl) inputEl.value = '';

  // 2. Show Typing Indicator in Bot Bubble
  const typingId = 'ai-typing-' + Date.now();
  if (container) {
    const typingBubble = document.createElement('div');
    typingBubble.className = 'ai-message-row bot';
    typingBubble.id = typingId;
    typingBubble.innerHTML = `
      <div class="ai-bubble-avatar"><i class="bi bi-robot"></i></div>
      <div class="ai-bubble-body">
        <div class="ai-bubble-header">
          <span class="ai-bubble-name">Alloma AI</span>
          <span class="ai-bubble-time">O'ylamoqda...</span>
        </div>
        <div class="ai-bubble-text">
          <span class="ai-typing-indicator">
            <span class="ai-typing-dot"></span>
            <span class="ai-typing-dot"></span>
            <span class="ai-typing-dot"></span>
          </span>
        </div>
      </div>
    `;
    container.appendChild(typingBubble);
    container.scrollTop = container.scrollHeight;
  }

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> <span>Kutilmoqda...</span>';
  }

  const langSelect = document.getElementById('voice-lang-select');
  let selLang = 'uzb';
  if (langSelect && langSelect.value) {
    if (langSelect.value.startsWith('ru')) selLang = 'rus';
    else if (langSelect.value.startsWith('en')) selLang = 'eng';
    else selLang = 'uzb';
  }

  try {
    const payload = {
      message: userText,
      history: aiChatHistory,
      child_name: childName || undefined,
      child_age: childAge || undefined,
      planet_id: planetId || undefined,
      language: selLang
    };

    const res = await fetch('/api/website/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    // Remove typing bubble
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Server xatosi (${res.status})`);
    }

    const data = await res.json();
    const botResponse = data.response || 'Javob olindi.';
    const audioUrl = data.audio_url || null;

    // Append to local history
    aiChatHistory.push({ role: 'user', content: userText });
    aiChatHistory.push({ role: 'model', content: botResponse });

    // Typewriter effekti bilan matn chiqar
    appendAiBubble('bot', botResponse, 'Alloma AI', 'Hozir', audioUrl, true);

    // Audio: typewriter boshlangandan 600ms keyin chalish (matnni ko'rib ulgursin)
    if (audioUrl) {
      unlockAudio();
      setTimeout(() => { playNeuralAudio(audioUrl); }, 600);
    }
  } catch (err) {
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    appendAiBubble('bot', `⚠️ Kechirasiz, xatolik yuz berdi: ${err.message}. Iltimos, qayta urinib ko'ring.`, 'Alloma AI', 'Xato');
    showToast(`AI Xatolik: ${err.message}`, 'error');
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="bi bi-send-fill"></i> <span>Yuborish</span>';
    }
  }
}

let currentNeuralAudio = null;
let audioUnlocked = false;

// Birinchi user interaksiyada audio unlock qilish
function unlockAudio() {
  if (audioUnlocked) return;
  // Silent audio chalish orqali brauzer audio contextini ochish
  const silent = new Audio('data:audio/mp3;base64,//uQxAAAAAAAAAAAAAAAAAAAAAAASW5mbwAAAA8AAAABAAACcQCAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICA');
  silent.volume = 0.001;
  silent.play().then(() => {
    audioUnlocked = true;
    silent.pause();
  }).catch(() => {});
}

// Har qanday click/touch da audio unlock
document.addEventListener('click', unlockAudio, { once: false });
document.addEventListener('touchstart', unlockAudio, { once: false });

function playNeuralAudio(audioUrl) {
  if (!audioUrl) return;

  // Avvalgi audio to'xtatish
  if (currentNeuralAudio) {
    currentNeuralAudio.pause();
    currentNeuralAudio.currentTime = 0;
    currentNeuralAudio = null;
  }

  const micBtn = document.getElementById('voice-mic-btn');
  const statusTitle = document.getElementById('voice-status-title');

  const audio = new Audio(audioUrl);
  audio.volume = 1.0;
  currentNeuralAudio = audio;

  if (micBtn) micBtn.classList.add('speaking');
  if (statusTitle) statusTitle.innerText = "🔊 Alloma AI (O'g'il bola HD) javob bermoqda...";

  audio.onended = () => {
    if (micBtn) micBtn.classList.remove('speaking');
    if (statusTitle) statusTitle.innerText = "Mikrofonga bosing va bemalol gapiring!";
    currentNeuralAudio = null;
  };

  audio.onerror = () => {
    if (micBtn) micBtn.classList.remove('speaking');
    currentNeuralAudio = null;
  };

  // Darhol ijro et, agar autoplay blocklansa — kichik kechikish bilan qayta urini
  audio.play().catch(() => {
    setTimeout(() => {
      audio.play().catch(e => {
        console.warn('Audio ijro xatosi:', e);
        if (micBtn) micBtn.classList.remove('speaking');
      });
    }, 200);
  });
}

function appendAiBubble(role, text, name, time, audioUrl = null, isTypewriter = false) {
  const container = document.getElementById('ai-messages-container');
  if (!container) return;

  const row = document.createElement('div');
  row.className = `ai-message-row ${role}`;
  const icon = role === 'user' ? 'bi-person-fill' : 'bi-robot';
  const bubbleId = 'ai-txt-' + Date.now() + '-' + Math.floor(Math.random() * 1000);

  const ttsBtnHtml = (role === 'bot' && audioUrl)
    ? `<button type="button" class="bubble-tts-btn" onclick="playNeuralAudio('${audioUrl}')" title="Ovozda tinglash"><i class="bi bi-volume-up-fill"></i></button>`
    : '';

  row.innerHTML = `
    <div class="ai-bubble-avatar"><i class="bi ${icon}"></i></div>
    <div class="ai-bubble-body">
      <div class="ai-bubble-header">
        <span class="ai-bubble-name">${name}</span>
        <div class="ai-bubble-actions">
          ${ttsBtnHtml}
          <span class="ai-bubble-time">${time}</span>
        </div>
      </div>
      <div class="ai-bubble-text" id="${bubbleId}"></div>
    </div>
  `;

  container.appendChild(row);
  container.scrollTop = container.scrollHeight;

  const textEl = document.getElementById(bubbleId);

  // Typewriter effekti — dona-dona Gemini kabi matn chiqish
  if (isTypewriter && role === 'bot') {
    startTypewriter(textEl, text, container);
  } else {
    // Format bold and linebreaks directly
    const formattedText = escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    if (textEl) textEl.innerHTML = formattedText;
  }
}

function startTypewriter(element, fullText, container) {
  if (!element) return;

  const words = fullText.split(' ');
  let wordIndex = 0;
  element.innerHTML = '<span class="typewriter-cursor">▍</span>';

  const interval = setInterval(() => {
    if (wordIndex < words.length) {
      const currentChunk = words.slice(0, wordIndex + 1).join(' ');
      const formatted = escapeHtml(currentChunk)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');

      element.innerHTML = formatted + ' <span class="typewriter-cursor">▍</span>';
      wordIndex++;
      if (container) container.scrollTop = container.scrollHeight;
    } else {
      clearInterval(interval);
      const finalFormatted = escapeHtml(fullText)
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
      element.innerHTML = finalFormatted;
      if (container) container.scrollTop = container.scrollHeight;
    }
  }, 45); // Har 45ms da 1 ta so'z dona-dona chiqadi (Gemini AI kabi)
}

// ==============================================================================
// OVOZLI SUHBAT (SPEECH-TO-TEXT & TEXT-TO-SPEECH)
// ==============================================================================
let recognition = null;
let isRecording = false;
let currentVoiceLang = 'uz-UZ';

function changeVoiceLanguage(lang) {
  currentVoiceLang = lang;
  if (recognition) {
    recognition.lang = lang;
  }
  showToast(`Ovoz tili: ${lang}`, 'info');
}

function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    return null;
  }

  const rec = new SpeechRecognition();
  rec.continuous = false;
  rec.interimResults = true;
  rec.lang = currentVoiceLang || 'uz-UZ';

  rec.onstart = () => {
    isRecording = true;
    updateMicUiState(true);
  };

  rec.onresult = (event) => {
    let interimTranscript = '';
    let finalTranscript = '';

    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript;
      } else {
        interimTranscript += event.results[i][0].transcript;
      }
    }

    const transcriptBox = document.getElementById('live-transcript-box');
    const transcriptText = document.getElementById('live-transcript-text');
    if (transcriptBox && transcriptText) {
      transcriptBox.style.display = 'flex';
      transcriptText.innerText = finalTranscript || interimTranscript || '...';
    }

    if (finalTranscript && finalTranscript.trim()) {
      const inputEl = document.getElementById('ai-input-text');
      if (inputEl) inputEl.value = finalTranscript.trim();
      handleSendAdminAi(new Event('submit'));
    }
  };

  rec.onerror = (event) => {
    console.warn('Speech recognition xatosi:', event.error);
    isRecording = false;
    updateMicUiState(false);
    if (event.error === 'not-allowed') {
      showToast('Mikrofon ruxsati berilmadi! Iltimos, brauzerda mikrofonga ruxsat bering.', 'error');
    }
  };

  rec.onend = () => {
    isRecording = false;
    updateMicUiState(false);
  };

  return rec;
}

function toggleVoiceRecording() {
  // If browser is currently speaking, stop speech first
  if (window.speechSynthesis && window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
  }

  if (!recognition) {
    recognition = initSpeechRecognition();
  }

  if (!recognition) {
    showToast('Kechirasiz, brauzeringizda Ovozli yozib olish (Speech API) qo\'llab-quvvatlanmaydi.', 'error');
    return;
  }

  if (isRecording) {
    try { recognition.stop(); } catch (e) {}
    isRecording = false;
    updateMicUiState(false);
  } else {
    try {
      recognition.lang = currentVoiceLang || 'uz-UZ';
      recognition.start();
    } catch (e) {
      console.warn('Recognition start xatosi:', e);
    }
  }
}

function updateMicUiState(recording) {
  const micBtn = document.getElementById('voice-mic-btn');
  const micIcon = document.getElementById('voice-mic-icon');
  const statusTitle = document.getElementById('voice-status-title');
  const statusDesc = document.getElementById('voice-status-desc');
  const miniMicIcon = document.getElementById('ai-mic-mini-icon');

  if (recording) {
    if (micBtn) micBtn.classList.add('recording');
    if (micIcon) micIcon.className = 'bi bi-soundwave';
    if (miniMicIcon) miniMicIcon.className = 'bi bi-soundwave text-danger';
    if (statusTitle) statusTitle.innerText = '🎙️ Sizni tinglamoqdaman... Gapiring!';
    if (statusDesc) statusDesc.innerText = 'Gapirib bo\'lgach, AI avtomatik javob beradi ✨';
  } else {
    if (micBtn) micBtn.classList.remove('recording');
    if (micIcon) micIcon.className = 'bi bi-mic-fill';
    if (miniMicIcon) miniMicIcon.className = 'bi bi-mic-fill';
    if (statusTitle) statusTitle.innerText = 'Mikrofonga bosing va bemalol gapiring!';
    if (statusDesc) statusDesc.innerText = 'AI bolajonlarga mos tarzda ovoz chiqarib javob beradi 🎈';
  }
}

async function speakText(rawText) {
  // Markdown, emoji va keraksiz belgilarni tozalash
  const cleanText = rawText
    .replace(/[*#_`~>]/g, '')
    .replace(/\b(https?:\/\/\S+)/gi, '')
    .replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '')
    .replace(/\s+/g, ' ')
    .trim();

  if (!cleanText) return;

  const langSelect = document.getElementById('voice-lang-select');
  let selLang = 'uzb';
  if (langSelect && langSelect.value) {
    if (langSelect.value.startsWith('ru')) selLang = 'rus';
    else if (langSelect.value.startsWith('en')) selLang = 'eng';
    else selLang = 'uzb';
  }

  // 1. Backend Microsoft HD Neural Audio orqali o'qish (Haqiqiy o'zbekcha ovoz)
  try {
    const res = await fetch('/api/website/ai/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: cleanText, language: selLang })
    });
    if (res.ok) {
      const data = await res.json();
      if (data.audio_url) {
        unlockAudio();
        playNeuralAudio(data.audio_url);
        return;
      }
    }
  } catch (e) {
    console.warn('Backend TTS xatosi:', e);
  }

  // 2. Fallback: Agar offline yoki xatolik bo'lsa
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = selLang === 'rus' ? 'ru-RU' : selLang === 'eng' ? 'en-US' : 'uz-UZ';
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  }
}



// ==========================================================================
// FAQ (KO'P SO'RALADIGAN SAVOLLAR) BOSHQARUVI
// ==========================================================================

async function fetchFaqs() {
  try {
    const res = await fetch('/api/website/faqs');
    if (!res.ok) throw new Error('FAQ savollarni olishda xatolik');
    faqsList = await res.json();
    renderFaqs();
    syncAllCounts();
  } catch (err) {
    console.error('FAQ fetch error:', err);
    const container = document.getElementById('faqs-grid');
    if (container) {
      container.innerHTML = `<div class="empty-state">FAQ savollarini yuklashda xatolik yuz berdi.</div>`;
    }
  }
}

function renderFaqs() {
  const container = document.getElementById('faqs-grid');
  if (!container) return;

  const searchInput = document.getElementById('faq-search');
  const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

  let filtered = faqsList;
  if (query) {
    filtered = faqsList.filter(f => 
      (f.name && f.name.toLowerCase().includes(query)) ||
      (f.description && f.description.toLowerCase().includes(query))
    );
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1; padding: 40px; text-align: center;">
        <i class="bi bi-question-circle" style="font-size: 3rem; color: var(--text-muted); display: block; margin-bottom: 12px;"></i>
        <h4>Hech qanday FAQ savol topilmadi</h4>
        <p style="color: var(--text-secondary); margin-bottom: 16px;">Yangi savol-javob qo'shish uchun yuqoridagi tugmani bosing.</p>
        <button class="btn btn-yellow" onclick="openFaqModal()">
          <i class="bi bi-plus-circle-fill"></i> Yangi FAQ Qo'shish
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map((item, idx) => `
    <div class="card item-card faq-card ${item.status === 'inactive' ? 'item-inactive' : ''}" style="display: flex; flex-direction: column; justify-content: space-between; border-left: 4px solid ${item.status === 'active' ? '#eab308' : '#64748b'}; padding: 18px;">
      <div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 10px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span style="background: rgba(234, 179, 8, 0.15); color: #eab308; font-weight: 700; font-size: 12px; padding: 2px 8px; border-radius: 4px;">#${item.order_num || idx + 1}</span>
            <span class="status-badge ${item.status === 'active' ? 'status-active' : 'status-inactive'}">
              ${item.status === 'active' ? 'Faol' : 'Nofaol'}
            </span>
          </div>
          <div style="font-size: 11px; color: var(--text-muted);">
            ID: ${item.id}
          </div>
        </div>

        <h4 style="font-size: 1.05rem; font-weight: 600; color: #fff; margin-bottom: 8px; line-height: 1.4;">
          <i class="bi bi-patch-question text-yellow" style="margin-right: 4px;"></i> ${escapeHtml(item.name)}
        </h4>

        <p style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-wrap; margin-bottom: 16px;">
          ${escapeHtml(item.description)}
        </p>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 8px;">
        <button class="btn btn-sm ${item.status === 'active' ? 'btn-secondary' : 'btn-yellow'}" onclick="handleToggleFaqStatus(${item.id})" style="font-size: 11px; padding: 4px 8px;">
          <i class="bi ${item.status === 'active' ? 'bi-eye-slash' : 'bi-eye'}"></i> ${item.status === 'active' ? 'Yashirish' : 'Faollashtirish'}
        </button>

        <div style="display: flex; gap: 6px;">
          <button class="action-btn-sm" title="Tahrirlash" onclick="openFaqModal(${item.id})">
            <i class="bi bi-pencil-fill"></i>
          </button>
          <button class="action-btn-sm delete-btn" title="O'chirish" onclick="handleDeleteFaq(${item.id})">
            <i class="bi bi-trash-fill"></i>
          </button>
        </div>
      </div>
    </div>
  `).join('');
}

function openFaqModal(id = null) {
  const modal = document.getElementById('faq-modal');
  const modalTitle = document.getElementById('faq-modal-title');
  const form = document.getElementById('faq-form');

  if (form) form.reset();

  const descEl = document.getElementById('faq-description') || document.getElementById('faq-desc');
  const nameEl = document.getElementById('faq-name');
  const idEl = document.getElementById('faq-id');
  const statusEl = document.getElementById('faq-status');
  const orderEl = document.getElementById('faq-order');

  if (id) {
    const item = faqsList.find(f => f.id === id);
    if (item) {
      if (idEl) idEl.value = item.id;
      if (nameEl) nameEl.value = item.name || '';
      if (descEl) descEl.value = item.description || '';
      if (statusEl) statusEl.value = item.status || 'active';
      if (orderEl) orderEl.value = item.order_num || 0;
      if (modalTitle) modalTitle.innerHTML = '<i class="bi bi-pencil-square text-yellow"></i> <span>FAQ Savolni Tahrirlash</span>';
    }
  } else {
    if (idEl) idEl.value = '';
    if (statusEl) statusEl.value = 'active';
    if (orderEl) orderEl.value = faqsList.length + 1;
    if (modalTitle) modalTitle.innerHTML = '<i class="bi bi-plus-circle text-yellow"></i> <span>Yangi FAQ Savol Qo\'shish</span>';
  }

  if (modal) {
    modal.classList.add('show', 'active');
    modal.style.opacity = '1';
    modal.style.pointerEvents = 'auto';
    modal.style.display = 'flex';
  }
}

function closeFaqModal() {
  const modal = document.getElementById('faq-modal');
  if (modal) {
    modal.classList.remove('show', 'active');
    modal.style.opacity = '';
    modal.style.pointerEvents = '';
    modal.style.display = 'none';
  }
}

async function handleSaveFaq(event) {
  event.preventDefault();
  const id = document.getElementById('faq-id') ? document.getElementById('faq-id').value : '';
  const name = document.getElementById('faq-name') ? document.getElementById('faq-name').value.trim() : '';
  const descEl = document.getElementById('faq-description') || document.getElementById('faq-desc');
  const description = descEl ? descEl.value.trim() : '';
  const status = document.getElementById('faq-status') ? document.getElementById('faq-status').value : 'active';
  const order_num = parseInt(document.getElementById('faq-order') ? document.getElementById('faq-order').value : 0, 10) || 0;

  if (!name || !description) {
    showToast("Iltimos, savol sarlavhasi va javob matnini to'ldiring!", "error");
    return;
  }

  const payload = { name, description, status, order_num };
  const saveBtn = document.getElementById('save-faq-btn');
  if (saveBtn) saveBtn.disabled = true;

  try {
    let res;
    if (id) {
      res = await fetch(`/api/website/faqs/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/website/faqs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "FAQ saqlashda xatolik yuz berdi");
    }

    showToast(id ? "FAQ savol muvaffaqiyatli yangilandi!" : "Yangi FAQ savol muvaffaqiyatli qo'shildi!", "success");
    closeFaqModal();
    await fetchFaqs();
    await fetchStats();
  } catch (err) {
    showToast(err.message || "Xatolik yuz berdi!", "error");
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
}

async function handleDeleteFaq(id) {
  const item = faqsList.find(f => f.id === id);
  const name = item ? item.name : `#${id}`;
  if (!confirm(`Haqiqatan ham "${name}" savolini o'chirmoqchimisiz?`)) return;

  try {
    const res = await fetch(`/api/website/faqs/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("O'chirishda xatolik");
    showToast("FAQ savol muvaffaqiyatli o'chirildi!", "success");
    await fetchFaqs();
    await fetchStats();
  } catch (err) {
    showToast(err.message || "O'chirishda xatolik yuz berdi", "error");
  }
}

async function handleToggleFaqStatus(id) {
  const item = faqsList.find(f => f.id === id);
  if (!item) return;
  const newStatus = item.status === 'active' ? 'inactive' : 'active';

  try {
    const res = await fetch(`/api/website/faqs/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (!res.ok) throw new Error("Holatni o'zgartirishda xatolik");
    showToast(`Savol ${newStatus === 'active' ? 'faollashtirildi' : 'yashirildi'}!`, "success");
    await fetchFaqs();
    await fetchStats();
  } catch (err) {
    showToast("Xatolik yuz berdi", "error");
  }
}

// ==============================================================================
// INGLIZ TILI (URAN SAYYORASI — SO'ZLAR, KATEGORIYALAR VA TESTLAR BOSHQARUVI)
// ==============================================================================

async function fetchUranCategories() {
  try {
    const res = await fetch('/api/website/uran/categories');
    if (!res.ok) throw new Error("Uran kategoriyalarini yuklashda xatolik");
    uranCategoriesList = await res.json();
    populateUranCategoryDropdowns();
    renderUranCategories();
    syncAllCounts();
  } catch (err) {
    console.error("fetchUranCategories error:", err);
  }
}

async function fetchUranWords() {
  try {
    const res = await fetch('/api/website/uran/words');
    if (!res.ok) throw new Error("Ingliz tili so'zlarini yuklashda xatolik");
    uranWordsList = await res.json();
    renderUranWords();
    syncAllCounts();
  } catch (err) {
    console.error("fetchUranWords error:", err);
  }
}

function renderUranWords() {
  if (currentOpenCatId) {
    renderUranDetailWords();
  }
}

function populateUranCategoryDropdowns() {
  const modalSelect = document.getElementById('uran-word-category-select');
  if (modalSelect) {
    modalSelect.innerHTML = `<option value="" disabled selected>-- Mavzuni tanlang --</option>` +
      uranCategoriesList.map(c => `<option value="${c.id}">${c.name} (${c.name_en || ''})</option>`).join('');
  }
}

function renderUranCategories() {
  const container = document.getElementById('uran-categories-grid');
  if (!container) return;

  const searchInput = document.getElementById('uran-cat-search') || document.getElementById('uran-search-input');
  const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

  const filtered = uranCategoriesList.filter(c => {
    return (c.name || '').toLowerCase().includes(query) ||
           (c.name_en || '').toLowerCase().includes(query) ||
           (c.description || '').toLowerCase().includes(query);
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div class="empty-state" style="grid-column:1/-1; padding:40px; text-align:center;"><i class="bi bi-translate" style="font-size:3rem; color:var(--text-muted); display:block; margin-bottom:12px;"></i><h4>Qidiruv bo'yicha mavzular topilmadi</h4></div>`;
    return;
  }

  container.innerHTML = filtered.map(cat => {
    const isActive = (cat.status === 'active');
    const statusBadge = isActive 
      ? `<span class="badge" style="position: absolute; top: 8px; left: 8px; background: rgba(16, 185, 129, 0.25); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.5); font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"><i class="bi bi-unlock-fill"></i> #${cat.order_num || 0} Faol</span>`
      : `<span class="badge" style="position: absolute; top: 8px; left: 8px; background: rgba(239, 68, 68, 0.25); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.5); font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;"><i class="bi bi-lock-fill"></i> #${cat.order_num || 0} Qulflangan</span>`;

    const cardStyle = isActive 
      ? `cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; position: relative;`
      : `cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; position: relative; border: 1px dashed rgba(239, 68, 68, 0.4); opacity: 0.9;`;

    const catImg = normalizeImageUrl(cat.image, 'images/categories/fruits.png');
    return `
    <div class="card item-card" style="${cardStyle}" onclick="openUranCategoryDetail(${cat.id})">
      <div>
        <div class="card-image-box" style="background: rgba(15, 23, 42, 0.6); height: 130px; display: flex; align-items: center; justify-content: center; padding: 14px; border-bottom: 1px solid rgba(255,255,255,0.06); position: relative;">
          ${statusBadge}
          <img src="${escapeHtml(catImg)}" alt="${escapeHtml(cat.name)}" style="max-height: 85px; max-width: 85px; object-fit: contain; filter: drop-shadow(0 4px 10px rgba(0,0,0,0.3));" onerror="this.onerror=null; this.src='images/categories/fruits.png';">
          
          <div style="position: absolute; top: 8px; right: 8px; display: flex; gap: 4px;" onclick="event.stopPropagation()">
            <button class="action-btn-sm" title="Mavzuni Tahrirlash" onclick="openUranCategoryModal(${cat.id})">
              <i class="bi bi-pencil-fill text-yellow"></i>
            </button>
            <button class="action-btn-sm delete-btn" title="Mavzuni O'chirish" onclick="handleDeleteUranCategory(${cat.id}, '${escapeHtml(cat.name)}')">
              <i class="bi bi-trash-fill text-danger"></i>
            </button>
          </div>
        </div>
        <div class="card-content" style="padding: 16px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 4px;">
            <h4 style="font-size: 16px; font-weight: 800; color: #fff; margin: 0;">${escapeHtml(cat.name)}</h4>
            <span class="badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8; font-size: 11px; padding: 4px 8px; border-radius: 6px; font-weight: 700; white-space: nowrap;">
              ${cat.words_count || 0} ta so'z
            </span>
          </div>
          <p style="font-size: 12px; color: #38bdf8; font-weight: 700; margin: 0 0 6px 0;">${escapeHtml(cat.name_en || '')}</p>
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.4; margin: 0 0 14px 0;">${escapeHtml(cat.description || '')}</p>
        </div>
      </div>
      
      <div style="padding: 0 16px 16px 16px; display: flex; gap: 8px; flex-wrap: wrap;" onclick="event.stopPropagation()">
        <button class="btn btn-yellow" style="flex: 1; padding: 8px 10px; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 6px; font-weight: 700;" onclick="openUranCategoryDetail(${cat.id})">
          <i class="bi bi-book-half"></i> So'zlar & Test
        </button>
        <button class="btn btn-secondary" style="padding: 8px 10px; font-size: 13px; display: flex; align-items: center; gap: 5px;" onclick="openUranWordModal(${cat.id}, '${escapeHtml(cat.name)}')">
          <i class="bi bi-plus-lg text-yellow"></i> So'z Qo'sh
        </button>
      </div>
    </div>
  `;
  }).join('');
}

// ------------------------------------------------------------------------------
// DRILL-DOWN CATEGORY DETAIL VIEW
// ------------------------------------------------------------------------------

async function openUranCategoryDetail(catId) {
  currentOpenCatId = catId;
  const mainView = document.getElementById('uran-main-view');
  const detailView = document.getElementById('uran-detail-view');
  const grid = document.getElementById('uran-detail-words-grid');

  if (mainView) mainView.style.display = 'none';
  if (detailView) detailView.style.display = 'block';

  const cat = uranCategoriesList.find(c => c.id === catId) || { id: catId, name: `Mavzu #${catId}` };
  currentOpenCatName = cat.name || '';

  const titleEl = document.getElementById('uran-detail-title');
  const subEl = document.getElementById('uran-detail-subtitle');
  const descEl = document.getElementById('uran-detail-desc');
  const badgeEl = document.getElementById('uran-detail-badge');
  const imgEl = document.getElementById('uran-detail-img');
  const searchInput = document.getElementById('uran-detail-search');

  if (titleEl) titleEl.innerText = cat.name || '';
  const isCatActive = (cat.status === 'active');
  const statusHtml = isCatActive
    ? `<span style="background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-right: 6px;"><i class="bi bi-unlock-fill"></i> Faol</span>`
    : `<span style="background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 8px; border-radius: 6px; font-weight: 700; margin-right: 6px;"><i class="bi bi-lock-fill"></i> Qulflangan</span>`;

  if (badgeEl) badgeEl.innerHTML = `${statusHtml} ${cat.words_count || 0} ta so'z`;
  if (imgEl) {
    imgEl.src = normalizeImageUrl(cat.image, 'images/categories/fruits.png');
    imgEl.onerror = function() { this.onerror = null; this.src = 'images/categories/fruits.png'; };
  }
  if (searchInput) searchInput.value = '';

  if (grid) {
    grid.innerHTML = `<div style="grid-column: 1/-1; padding: 30px; text-align: center; color: var(--text-secondary);"><span class="spinner-border spinner-border-sm" style="margin-right: 8px;"></span> Mavzu so'zlari yuklanmoqda...</div>`;
  }

  try {
    const res = await fetch(`/mobile/planets/uran/category/${catId}`);
    if (!res.ok) throw new Error("Mavzu ma'lumotlarini olishda xatolik");
    currentCatDetailData = await res.json();
    
    const count = currentCatDetailData.words_count || (currentCatDetailData.words || []).length;
    if (badgeEl) badgeEl.innerHTML = `${statusHtml} ${count} ta so'z`;
    renderUranDetailWords();
  } catch (err) {
    console.error("openUranCategoryDetail error:", err);
    if (grid) {
      grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;"><i class="bi bi-exclamation-triangle text-danger"></i><p>${err.message}</p></div>`;
    }
  }
}

function closeUranCategoryDetail() {
  currentOpenCatId = null;
  currentOpenCatName = '';
  currentCatDetailData = null;
  const mainView = document.getElementById('uran-main-view');
  const detailView = document.getElementById('uran-detail-view');
  if (detailView) detailView.style.display = 'none';
  if (mainView) mainView.style.display = 'block';
  renderUranCategories();
}

function filterUranDetailWords() {
  renderUranDetailWords();
}

function renderUranDetailWords() {
  const grid = document.getElementById('uran-detail-words-grid');
  if (!grid || !currentCatDetailData) return;

  const searchInput = document.getElementById('uran-detail-search');
  const query = searchInput ? searchInput.value.trim().toLowerCase() : '';

  let words = currentCatDetailData.words || [];
  if (query) {
    words = words.filter(w =>
      (w.word_en && w.word_en.toLowerCase().includes(query)) ||
      (w.word_uz && w.word_uz.toLowerCase().includes(query)) ||
      (w.word_ru && w.word_ru.toLowerCase().includes(query)) ||
      (w.example_sentence && w.example_sentence.toLowerCase().includes(query)) ||
      (w.example_translation && w.example_translation.toLowerCase().includes(query))
    );
  }

  if (words.length === 0) {
    grid.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1; padding: 40px; text-align: center;">
        <i class="bi bi-translate" style="font-size: 3rem; color: var(--text-muted); display: block; margin-bottom: 12px;"></i>
        <h4>${query ? "Qidiruv bo'yicha so'z topilmadi" : "Ushbu mavzuda hozircha so'zlar yo'q"}</h4>
        <p style="color: var(--text-secondary); margin-bottom: 16px;">Yangi so'z qo'shish uchun quyidagi tugmani bosing.</p>
        <button class="btn btn-yellow" onclick="openUranWordModal(${currentOpenCatId}, '${escapeHtml(currentOpenCatName)}')">
          <i class="bi bi-plus-circle-fill"></i> + Shu Mavzuga So'z Qo'shish
        </button>
      </div>
    `;
    return;
  }

  grid.innerHTML = words.map((w, idx) => {
    const safeWordEn = escapeHtml(w.word_en || '');
    const pos = (w.part_of_speech || 'noun').toLowerCase();
    const posUz = w.part_of_speech_uz || (pos === 'adjective' ? 'Sifat' : (pos === 'verb' ? "Fe'l" : (pos === 'adverb' ? 'Ravish' : 'Ot')));

    let posBg = 'rgba(16, 185, 129, 0.15)';
    let posColor = '#34d399';
    let posBorder = 'rgba(16, 185, 129, 0.3)';
    if (pos === 'adjective') {
      posBg = 'rgba(245, 158, 11, 0.15)';
      posColor = '#fbbf24';
      posBorder = 'rgba(245, 158, 11, 0.3)';
    } else if (pos === 'verb') {
      posBg = 'rgba(236, 72, 153, 0.15)';
      posColor = '#f472b6';
      posBorder = 'rgba(236, 72, 153, 0.3)';
    } else if (pos === 'adverb') {
      posBg = 'rgba(139, 92, 246, 0.15)';
      posColor = '#a78bfa';
      posBorder = 'rgba(139, 92, 246, 0.3)';
    }

    const wordImgSrc = normalizeImageUrl(w.image || (currentCatDetailData && currentCatDetailData.image), 'images/categories/fruits.png');

    return `
      <div class="card item-card" style="display: flex; flex-direction: column; justify-content: space-between; border-left: 4px solid #6366f1; padding: 18px; background: rgba(30, 41, 59, 0.7); border-radius: 12px;">
        <div>
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
            <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
              <span class="badge" style="background: rgba(99, 102, 241, 0.2); color: #818cf8; font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 4px;">
                #${idx + 1}
              </span>
              <span class="badge" style="background: ${posBg}; color: ${posColor}; border: 1px solid ${posBorder}; font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 4px;">
                ${escapeHtml(posUz)} (${escapeHtml(pos)})
              </span>
            </div>
            <span style="font-size: 11px; color: var(--text-muted);">ID: ${w.id}</span>
          </div>

          <div style="display: flex; gap: 12px; align-items: center; margin-bottom: 12px;">
            <div style="width: 52px; height: 52px; min-width: 52px; border-radius: 10px; background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 4px;">
              <img src="${escapeHtml(wordImgSrc)}" alt="${safeWordEn}" style="max-height: 44px; max-width: 44px; object-fit: contain; filter: drop-shadow(0 2px 6px rgba(0,0,0,0.3));" onerror="this.onerror=null; this.src='images/categories/fruits.png';">
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <div style="display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap;">
                  <h3 style="font-size: 1.25rem; font-weight: 800; color: #fff; margin: 0;">${safeWordEn}</h3>
                  <span style="font-size: 13px; color: #94a3b8; font-style: italic;">${escapeHtml(w.transcription || '')}</span>
                </div>
                <button type="button" class="btn btn-sm btn-secondary" onclick="playWordAudio('${safeWordEn}')" title="Talaffuzni eshitish" style="padding: 4px 8px; border-radius: 6px;">
                  <i class="bi bi-volume-up-fill text-yellow"></i>
                </button>
              </div>

              <div style="margin-top: 4px; line-height: 1.3;">
                <p style="margin: 0; font-size: 15px; font-weight: 800; color: #38bdf8;">
                  🇺🇿 ${escapeHtml(w.word_uz || '')}
                </p>
                ${w.word_ru ? `<p style="margin: 2px 0 0 0; font-size: 12px; color: #94a3b8;">🇷🇺 ${escapeHtml(w.word_ru)}</p>` : ''}
              </div>
            </div>
          </div>

          ${w.example_sentence ? `
            <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px; margin-bottom: 14px; font-size: 12px;">
              <p style="margin: 0 0 4px 0; color: #e2e8f0; font-style: italic;">"${escapeHtml(w.example_sentence)}"</p>
              ${w.example_translation ? `<p style="margin: 0; color: #94a3b8;">— ${escapeHtml(w.example_translation)}</p>` : ''}
            </div>
          ` : ''}
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 6px;">
          <button class="action-btn-sm" title="Tahrirlash" onclick="openUranWordModal(${currentOpenCatId}, '${escapeHtml(currentOpenCatName)}', ${w.id})">
            <i class="bi bi-pencil-fill"></i>
          </button>
          <button class="action-btn-sm delete-btn" title="O'chirish" onclick="handleDeleteUranWord(${w.id}, '${safeWordEn}', ${currentOpenCatId})">
            <i class="bi bi-trash-fill"></i>
          </button>
        </div>
      </div>
    `;
  }).join('');
}

// ------------------------------------------------------------------------------
// MODALS AND ACTIONS
// ------------------------------------------------------------------------------

async function openUranCategoryWordsModal(catId) {
  openUranCategoryDetail(catId);
}

function closeUranModal() {
  const modal = document.getElementById('uran-words-modal');
  if (modal) modal.classList.remove('active');
}

// ------------------------------------------------------------------------------
// URAN KATEGORIYA BOSHQARUVI (ADD / EDIT / DELETE / IMAGE UPLOAD)
// ------------------------------------------------------------------------------

const PRESET_URAN_CATEGORY_IMAGES = [
  { name: "fruits.png", label: "Mevalar", path: "images/categories/fruits.png" },
  { name: "animals.png", label: "Hayvonlar", path: "images/categories/animals.png" },
  { name: "colors.png", label: "Ranglar", path: "images/categories/colors.png" },
  { name: "family.png", label: "Oila", path: "images/categories/family.png" },
  { name: "school.png", label: "Maktab", path: "images/categories/school.png" },
  { name: "clothes.png", label: "Kiyimlar", path: "images/categories/clothes.png" },
  { name: "nature.png", label: "Tabiat", path: "images/categories/nature.png" },
  { name: "transport.png", label: "Transport", path: "images/categories/transport.png" },
  { name: "home.png", label: "Uy", path: "images/categories/home.png" },
  { name: "professions.png", label: "Kasblar", path: "images/categories/professions.png" }
];

function updateUranCatImagePreview(path) {
  const clean = normalizeImageUrl(path, 'images/categories/fruits.png');
  const previewImg = document.getElementById('uran-cat-preview-img');
  const previewLabel = document.getElementById('uran-cat-img-preview-label');
  if (previewImg) {
    previewImg.src = clean;
    previewImg.onerror = function() { this.onerror = null; this.src = 'images/categories/fruits.png'; };
  }
  if (previewLabel) {
    const parts = (path || '').split('/');
    previewLabel.innerText = parts[parts.length - 1] || path || 'fruits.png';
  }
}

function selectUranPresetImage(path) {
  const input = document.getElementById('uran-cat-image');
  if (input) input.value = path;
  updateUranCatImagePreview(path);
  renderUranPresetImages(path);
}

function renderUranPresetImages(activePath) {
  const container = document.getElementById('uran-preset-images');
  if (!container) return;
  container.innerHTML = PRESET_URAN_CATEGORY_IMAGES.map(p => {
    const isSelected = activePath && activePath.includes(p.name);
    const pSrc = normalizeImageUrl(p.path, 'images/categories/' + p.name);
    return `
      <button type="button" class="btn btn-sm ${isSelected ? 'btn-yellow' : 'btn-secondary'}" 
        style="padding: 4px 8px; font-size: 11px; display: inline-flex; align-items: center; gap: 5px; border-radius: 6px; cursor: pointer;" 
        onclick="selectUranPresetImage('${p.path}')">
        <img src="${escapeHtml(pSrc)}" alt="${p.label}" style="width: 16px; height: 16px; object-fit: contain;" onerror="this.onerror=null; this.src='images/categories/${p.name}';">
        <span>${p.label}</span>
      </button>
    `;
  }).join('');
}

async function handleUploadUranCatImage(input) {
  let file = input.files && input.files[0];
  if (!file) return;

  const statusEl = document.getElementById('uran-cat-upload-status');
  if (statusEl) statusEl.innerText = "Yuklanmoqda...";

  try {
    if (file.type && file.type.startsWith('image/') && file.size > 950 * 1024) {
      file = await compressImageIfNeeded(file);
    }

    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('/api/website/uran/upload-image', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      let errMsg = "Rasm yuklashda xatolik";
      if (res.status === 413) {
        errMsg = "Fayl hajmi juda katta (413 Request Entity Too Large)!";
      } else {
        try {
          const err = await res.json();
          errMsg = err.detail || errMsg;
        } catch (e) {
          errMsg = `Server xatoligi: ${res.status} ${res.statusText}`;
        }
      }
      throw new Error(errMsg);
    }

    const data = await res.json();
    const uploadedUrl = data.relative_url || data.url;
    const imgInput = document.getElementById('uran-cat-image');
    if (imgInput) imgInput.value = uploadedUrl;
    updateUranCatImagePreview(uploadedUrl);
    if (statusEl) statusEl.innerHTML = `<span style="color: #10b981;">✅ ${file.name}</span>`;
    showToast("Kategoriya rasmi muvaffaqiyatli yuklandi!", "success");
  } catch (err) {
    console.error("handleUploadUranCatImage error:", err);
    if (statusEl) statusEl.innerHTML = `<span style="color: #ef4444;">❌ Xatolik</span>`;
    showToast(err.message || "Rasm yuklashda xatolik", "error");
  }
}

function openUranCategoryModal(catId = null) {
  const modal = document.getElementById('uran-category-modal');
  const titleEl = document.getElementById('uran-category-modal-title');
  const deleteBtn = document.getElementById('uran-cat-delete-btn');
  const statusEl = document.getElementById('uran-cat-upload-status');
  if (statusEl) statusEl.innerText = '';

  const idInput = document.getElementById('uran-cat-id');
  const nameInput = document.getElementById('uran-cat-name');
  const nameEnInput = document.getElementById('uran-cat-name-en');
  const nameRuInput = document.getElementById('uran-cat-name-ru');
  const orderInput = document.getElementById('uran-cat-order');
  const descInput = document.getElementById('uran-cat-desc');
  const imgInput = document.getElementById('uran-cat-image');
  const statusSelect = document.getElementById('uran-cat-status');

  if (catId) {
    const cat = uranCategoriesList.find(c => c.id === catId);
    if (cat) {
      if (idInput) idInput.value = cat.id;
      if (nameInput) nameInput.value = cat.name || '';
      if (nameEnInput) nameEnInput.value = cat.name_en || '';
      if (nameRuInput) nameRuInput.value = cat.name_ru || '';
      if (orderInput) orderInput.value = cat.order_num || 0;
      if (descInput) descInput.value = cat.description || '';
      const catImg = cat.image || '/images/categories/fruits.png';
      if (imgInput) imgInput.value = catImg;
      if (statusSelect) statusSelect.value = cat.status || 'active';
      updateUranCatImagePreview(catImg);
      renderUranPresetImages(catImg);

      if (titleEl) titleEl.innerHTML = `<i class="bi bi-pencil-square text-yellow"></i> "${escapeHtml(cat.name)}" Kategoriyasini Tahrirlash`;
      if (deleteBtn) deleteBtn.style.display = 'inline-flex';
    }
  } else {
    // New category
    if (idInput) idInput.value = '';
    if (nameInput) nameInput.value = '';
    if (nameEnInput) nameEnInput.value = '';
    if (nameRuInput) nameRuInput.value = '';
    if (orderInput) orderInput.value = (uranCategoriesList.length + 1);
    if (descInput) descInput.value = '';
    const defaultImg = '/images/categories/fruits.png';
    if (imgInput) imgInput.value = defaultImg;
    if (statusSelect) statusSelect.value = 'active';
    updateUranCatImagePreview(defaultImg);
    renderUranPresetImages(defaultImg);

    if (titleEl) titleEl.innerHTML = `<i class="bi bi-folder-plus text-yellow"></i> Yangi Kategoriya Qo'shish`;
    if (deleteBtn) deleteBtn.style.display = 'none';
  }

  if (modal) {
    modal.classList.add('show', 'active');
    modal.style.opacity = '1';
    modal.style.pointerEvents = 'auto';
    modal.style.display = 'flex';
  }
}

function closeUranCategoryModal() {
  const modal = document.getElementById('uran-category-modal');
  if (modal) {
    modal.classList.remove('show', 'active');
    modal.style.opacity = '';
    modal.style.pointerEvents = '';
    modal.style.display = 'none';
  }
}

async function handleSaveUranCategory(event) {
  event.preventDefault();
  const catId = document.getElementById('uran-cat-id').value;
  const name = document.getElementById('uran-cat-name').value.trim();
  const name_en = document.getElementById('uran-cat-name-en').value.trim();
  const name_ru = document.getElementById('uran-cat-name-ru').value.trim();
  const order_num = parseInt(document.getElementById('uran-cat-order').value, 10) || 0;
  const description = document.getElementById('uran-cat-desc').value.trim();
  let image = (document.getElementById('uran-cat-image').value || '').trim() || '/images/categories/fruits.png';
  if (image.endsWith('.svg') && image.includes('/images/categories/')) {
    image = image.replace('.svg', '.png');
  }
  const status = document.getElementById('uran-cat-status').value;

  if (!name) {
    showToast("Kategoriya o'zbekcha nomini kiriting!", "error");
    return;
  }
  if (!name_en) {
    showToast("Kategoriya inglizcha nomini kiriting!", "error");
    return;
  }

  const payload = {
    name,
    name_en,
    name_ru,
    image,
    description,
    order_num,
    status
  };

  const saveBtn = document.getElementById('save-uran-cat-btn');
  if (saveBtn) saveBtn.disabled = true;

  try {
    let res;
    if (catId) {
      res = await fetch(`/api/website/uran/categories/${catId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/website/uran/categories', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Kategoriyani saqlashda xatolik yuz berdi");
    }

    showToast(catId ? `"${name}" kategoriyasi muvaffaqiyatli yangilandi!` : `Yangi "${name}" kategoriyasi yaratildi! ✅`, "success");
    closeUranCategoryModal();

    await fetchUranCategories();

    // If inside detail view of this category, refresh header
    if (currentOpenCatId && String(currentOpenCatId) === String(catId)) {
      currentOpenCatName = name;
      const titleEl = document.getElementById('uran-detail-title');
      const subEl = document.getElementById('uran-detail-subtitle');
      const descEl = document.getElementById('uran-detail-desc');
      const imgEl = document.getElementById('uran-detail-img');
      if (titleEl) titleEl.innerText = name;
      if (subEl) subEl.innerText = name_en;
      if (descEl) descEl.innerText = description;
      if (imgEl) {
        imgEl.src = normalizeImageUrl(image, 'images/categories/fruits.png');
        imgEl.onerror = function() { this.onerror = null; this.src = 'images/categories/fruits.png'; };
      }
    }
  } catch (err) {
    console.error("handleSaveUranCategory error:", err);
    showToast(err.message || "Xatolik yuz berdi", "error");
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
}

async function handleDeleteUranCategory(catId, catName) {
  if (!catId) return;
  const nameStr = catName || `ID #${catId}`;
  if (!confirm(`Haqiqatan ham "${nameStr}" kategoriyasini va uning barcha so'zlarini o'chirmoqchimisiz?\nBu amalni qaytarib bo'lmaydi!`)) {
    return;
  }

  try {
    const res = await fetch(`/api/website/uran/categories/${catId}`, {
      method: 'DELETE'
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Kategoriyani o'chirishda xatolik");
    }

    showToast(`"${nameStr}" kategoriyasi muvaffaqiyatli o'chirildi! 🗑️`, "success");
    closeUranCategoryModal();

    if (currentOpenCatId && String(currentOpenCatId) === String(catId)) {
      closeUranCategoryDetail();
    }

    await Promise.all([fetchUranCategories(), fetchUranWords()]);
  } catch (err) {
    console.error("handleDeleteUranCategory error:", err);
    showToast(err.message || "O'chirishda xatolik yuz berdi", "error");
  }
}

function handleDeleteCurrentCatFromModal() {
  const catId = document.getElementById('uran-cat-id').value;
  const name = document.getElementById('uran-cat-name').value;
  if (catId) {
    handleDeleteUranCategory(catId, name);
  }
}

function handleDeleteCurrentWordFromModal() {
  const wordId = document.getElementById('uran-word-id').value;
  const wordEn = document.getElementById('uran-word-en').value;
  const catId = document.getElementById('uran-word-category-id').value || currentOpenCatId;
  if (wordId) {
    closeUranWordModal();
    handleDeleteUranWord(wordId, wordEn, catId);
  }
}

// ------------------------------------------------------------------------------
// URAN SO'ZLAR BOSHQARUVI (ADD / EDIT / DELETE)
// ------------------------------------------------------------------------------

function openUranWordModal(categoryId = null, categoryName = null, wordId = null) {
  const modal = document.getElementById('uran-word-modal');
  const form = document.getElementById('uran-word-form');
  const catLabel = document.getElementById('uran-word-modal-cat');
  const titleEl = document.getElementById('uran-word-modal-title');
  const catSelect = document.getElementById('uran-word-category-select');
  const deleteBtn = document.getElementById('uran-word-delete-btn');

  if (form) form.reset();
  populateUranCategoryDropdowns();

  const targetCatId = categoryId || currentOpenCatId || (uranCategoriesList.length > 0 ? uranCategoriesList[0].id : 1);
  const targetCatName = categoryName || currentOpenCatName || (uranCategoriesList.length > 0 ? uranCategoriesList[0].name : '');

  if (document.getElementById('uran-word-id')) {
    document.getElementById('uran-word-id').value = wordId || '';
  }
  if (document.getElementById('uran-word-category-id')) {
    document.getElementById('uran-word-category-id').value = targetCatId || '';
  }
  if (catSelect && targetCatId) {
    catSelect.value = String(targetCatId);
  }

  if (wordId) {
    const item = uranWordsList.find(w => w.id === wordId) || (currentCatDetailData && currentCatDetailData.words ? currentCatDetailData.words.find(w => w.id === wordId) : null);
    if (item) {
      if (catSelect) catSelect.value = String(item.category_id);
      if (document.getElementById('uran-word-en')) document.getElementById('uran-word-en').value = item.word_en || '';
      if (document.getElementById('uran-word-uz')) document.getElementById('uran-word-uz').value = item.word_uz || '';
      if (document.getElementById('uran-word-ru')) document.getElementById('uran-word-ru').value = item.word_ru || '';
      if (document.getElementById('uran-word-transcription')) document.getElementById('uran-word-transcription').value = item.transcription || '';
      if (document.getElementById('uran-word-pos')) document.getElementById('uran-word-pos').value = item.part_of_speech || 'noun';
      if (document.getElementById('uran-word-example')) document.getElementById('uran-word-example').value = item.example_sentence || '';
      if (document.getElementById('uran-word-example-uz')) document.getElementById('uran-word-example-uz').value = item.example_translation || '';
      if (document.getElementById('uran-word-image')) document.getElementById('uran-word-image').value = item.image || '';
      if (document.getElementById('uran-word-order')) document.getElementById('uran-word-order').value = item.order_num || 0;
      if (titleEl) titleEl.innerHTML = `<i class="bi bi-pencil-square text-yellow"></i> "${escapeHtml(item.word_en)}" So'zini Tahrirlash`;
      if (deleteBtn) deleteBtn.style.display = 'inline-flex';
    }
  } else {
    if (document.getElementById('uran-word-pos')) document.getElementById('uran-word-pos').value = 'noun';
    if (titleEl) titleEl.innerHTML = `<i class="bi bi-plus-circle text-yellow"></i> Yangi So'z Qo'shish`;
    if (deleteBtn) deleteBtn.style.display = 'none';
  }

  if (catLabel) {
    const selectedCatObj = uranCategoriesList.find(c => String(c.id) === String(targetCatId));
    const catDisplayName = selectedCatObj ? selectedCatObj.name : (targetCatName || '');
    catLabel.innerText = catDisplayName ? `Mavzu: ${catDisplayName}` : `Inglizcha so'z va uning o'zbekcha tarjimasini kiriting`;
  }

  if (modal) {
    modal.classList.add('show', 'active');
    modal.style.opacity = '1';
    modal.style.pointerEvents = 'auto';
    modal.style.display = 'flex';
  }
}

function closeUranWordModal() {
  const modal = document.getElementById('uran-word-modal');
  if (modal) {
    modal.classList.remove('show', 'active');
    modal.style.opacity = '';
    modal.style.pointerEvents = '';
    modal.style.display = 'none';
  }
}

async function handleSaveUranWord(event) {
  event.preventDefault();
  const wordId = document.getElementById('uran-word-id') ? document.getElementById('uran-word-id').value : '';
  const catSelect = document.getElementById('uran-word-category-select');
  const categoryId = catSelect ? catSelect.value : (currentOpenCatId || 1);
  const word_en = document.getElementById('uran-word-en').value.trim();
  const word_uz = document.getElementById('uran-word-uz').value.trim();
  const word_ru = document.getElementById('uran-word-ru').value.trim();
  const transcription = document.getElementById('uran-word-transcription').value.trim();
  const posSelect = document.getElementById('uran-word-pos');
  const part_of_speech = posSelect ? posSelect.value : 'noun';
  const posUzMap = {
    'noun': 'Ot',
    'adjective': 'Sifat',
    'verb': "Fe'l",
    'adverb': 'Ravish',
    'pronoun': 'Olmosh',
    'preposition': "Old ko'makchi",
    'other': 'Boshqa'
  };
  const part_of_speech_uz = posUzMap[part_of_speech] || 'Ot';
  const example_sentence = document.getElementById('uran-word-example').value.trim();
  const example_translation = document.getElementById('uran-word-example-uz').value.trim();
  const image = document.getElementById('uran-word-image') ? document.getElementById('uran-word-image').value.trim() : '';
  const order_num = document.getElementById('uran-word-order') ? parseInt(document.getElementById('uran-word-order').value, 10) || 0 : 0;

  if (!categoryId) {
    showToast("Iltimos, so'z tegishli bo'lgan mavzuni (kategoriyani) tanlang!", "error");
    return;
  }

  if (!word_en || !word_uz) {
    showToast("Inglizcha va O'zbekcha so'zlarni kiriting!", "error");
    return;
  }

  const payload = {
    category_id: parseInt(categoryId, 10),
    word_en, word_uz,
    word_ru: word_ru || null,
    transcription: transcription || null,
    part_of_speech,
    part_of_speech_uz,
    example_sentence: example_sentence || null,
    example_translation: example_translation || null,
    image: image || null,
    order_num: order_num
  };

  const saveBtn = document.getElementById('save-uran-word-btn');
  if (saveBtn) saveBtn.disabled = true;

  try {
    let res;
    if (wordId) {
      res = await fetch(`/api/website/uran/words/${wordId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/website/uran/words', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "So'z saqlashda xatolik");
    }

    showToast(wordId ? "So'z muvaffaqiyatli yangilandi!" : `"${word_en} → ${word_uz}" so'zi muvaffaqiyatli qo'shildi! ✅`, "success");
    closeUranWordModal();
    
    await Promise.all([fetchUranWords(), fetchUranCategories()]);

    if (currentOpenCatId) {
      await openUranCategoryDetail(currentOpenCatId);
    }
  } catch (err) {
    showToast(err.message || "Xatolik yuz berdi!", "error");
  } finally {
    if (saveBtn) saveBtn.disabled = false;
  }
}

async function handleDeleteUranWord(id, wordName = '', categoryId = null) {
  if (!confirm(`Haqiqatan ham "${wordName || '#' + id}" so'zini o'chirmoqchimisiz?`)) return;

  try {
    const res = await fetch(`/api/website/uran/words/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("So'zni o'chirishda xatolik");
    showToast("So'z muvaffaqiyatli o'chirildi!", "success");
    
    await Promise.all([fetchUranWords(), fetchUranCategories()]);

    if (currentOpenCatId) {
      await openUranCategoryDetail(currentOpenCatId);
    }
  } catch (err) {
    showToast(err.message || "O'chirishda xatolik yuz berdi", "error");
  }
}

async function handleAiSuggestWord() {
  const wordEnInput = document.getElementById('uran-word-en');
  const word = wordEnInput ? wordEnInput.value.trim() : '';

  if (!word) {
    showToast("Avval inglizcha so'zni yozing, keyin AI tugmasini bosing!", "warning");
    if (wordEnInput) wordEnInput.focus();
    return;
  }

  const aiBtn = document.getElementById('ai-suggest-btn');
  if (aiBtn) {
    aiBtn.disabled = true;
    aiBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Qidirilmoqda...';
  }

  try {
    const res = await fetch('/api/website/uran/ai-suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ word_en: word })
    });

    if (!res.ok) throw new Error("AI tarjima xizmatida xatolik");
    const data = await res.json();

    if (data.word_uz && document.getElementById('uran-word-uz')) {
      document.getElementById('uran-word-uz').value = data.word_uz;
    }
    if (data.word_ru && document.getElementById('uran-word-ru')) {
      document.getElementById('uran-word-ru').value = data.word_ru;
    }
    if (data.transcription && document.getElementById('uran-word-transcription')) {
      document.getElementById('uran-word-transcription').value = data.transcription;
    }
    if (data.part_of_speech && document.getElementById('uran-word-pos')) {
      document.getElementById('uran-word-pos').value = data.part_of_speech;
    }
    if (data.example_sentence && document.getElementById('uran-word-example')) {
      document.getElementById('uran-word-example').value = data.example_sentence;
    }
    if (data.example_translation && document.getElementById('uran-word-example-uz')) {
      document.getElementById('uran-word-example-uz').value = data.example_translation;
    }

    showToast(`"${word}" so'zining tarjimasi va misollari avtomatik to'ldirildi! ✨`, "success");
  } catch (err) {
    showToast(err.message || "AI dan ma'lumot olishda xatolik", "error");
  } finally {
    if (aiBtn) {
      aiBtn.disabled = false;
      aiBtn.innerHTML = '<i class="bi bi-stars"></i> AI Tarjima';
    }
  }
}

function playWordAudio(word) {
  if (!word) return;
  if (!('speechSynthesis' in window)) {
    showToast("Brauzeringiz ovozli talaffuzni qo'llab-quvvatlamaydi", "warning");
    return;
  }
  try {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = 'en-US';
    utterance.rate = 0.9;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  } catch (e) {
    console.error("Audio error:", e);
  }
}


// ==========================================================================
// KUTUBXONA VA VIDEO/AUDIO DARSLAR (LIBRARY) CRUD & MANAGEMENT
// ==========================================================================

async function fetchLibraryCategories() {
  try {
    const res = await fetch('/api/library/categories/');
    if (!res.ok) throw new Error("Kategoriyalarni olishda xatolik");
    libraryCategoriesList = await res.json();
    populateLibraryCategorySelects();
  } catch (err) {
    console.error("Library categories error:", err);
  }
}

function populateLibraryCategorySelects() {
  const modalSelect = document.getElementById('library-category-id');
  const filterSelect = document.getElementById('library-cat-filter');

  if (modalSelect && libraryCategoriesList.length > 0) {
    const currentVal = modalSelect.value;
    modalSelect.innerHTML = libraryCategoriesList.map(c => `
      <option value="${c.id}">${escapeHtml(c.icon || '📚')} ${escapeHtml(c.name)}</option>
    `).join('');
    if (currentVal && Array.from(modalSelect.options).some(o => o.value == currentVal)) {
      modalSelect.value = currentVal;
    }
  }

  if (filterSelect && libraryCategoriesList.length > 0) {
    const currentFilter = filterSelect.value;
    filterSelect.innerHTML = `
      <option value="">📚 Barcha Toifalar</option>
      ${libraryCategoriesList.map(c => `
        <option value="${c.id}">${escapeHtml(c.icon || '📚')} ${escapeHtml(c.name)}</option>
      `).join('')}
    `;
    if (currentFilter) filterSelect.value = currentFilter;
  }
}

async function fetchLibraryBooks() {
  const container = document.getElementById('library-grid');
  if (container && libraryList.length === 0) {
    container.innerHTML = `<div class="loading-state">Kitoblar va videolar yuklanmoqda...</div>`;
  }
  try {
    const res = await fetch('/api/library/books/?status=all&limit=100');
    if (!res.ok) throw new Error("Kutubxona kitoblarini olishda xatolik");
    libraryList = await res.json();
    renderLibraryBooks();
    syncAllCounts();
  } catch (err) {
    console.error("Fetch library books error:", err);
    if (container) {
      container.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;">Kutubxona kitoblarini yuklab bo'lmadi. Server faolligini tekshiring.</div>`;
    }
  }
}

function renderLibraryBooks() {
  syncAllCounts();
  const container = document.getElementById('library-grid');
  if (!container) return;

  const searchTerm = (document.getElementById('library-search')?.value || '').toLowerCase().trim();
  const catFilter = document.getElementById('library-cat-filter')?.value || '';
  const mediaFilter = document.getElementById('library-media-filter')?.value || 'all';
  const statusFilter = document.getElementById('library-status-filter')?.value || 'all';

  const filtered = libraryList.filter(item => {
    // Search
    const titleMatch = (item.title || '').toLowerCase().includes(searchTerm);
    const authorMatch = (item.author || '').toLowerCase().includes(searchTerm);
    const descMatch = (item.description || '').toLowerCase().includes(searchTerm);
    if (searchTerm && !titleMatch && !authorMatch && !descMatch) return false;

    // Category
    if (catFilter && item.category_id != catFilter) return false;

    // Media Filter
    const hasVideo = !!(item.video_url && item.video_url.trim());
    const hasAudio = !!(item.audio_url && item.audio_url.trim());
    if (mediaFilter === 'video' && !hasVideo) return false;
    if (mediaFilter === 'audio' && !hasAudio) return false;

    // Status Filter
    if (statusFilter !== 'all' && (item.status || 'active') !== statusFilter) return false;

    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1; padding: 40px; text-align: center;">
        <i class="bi bi-collection-play text-yellow" style="font-size: 42px;"></i>
        <h4 style="margin-top: 12px; font-weight: 700;">Hech qanday kitob yoki video topilmadi</h4>
        <p style="color: var(--text-muted); font-size: 13px; margin-top: 4px;">Qidiruv mezonlarini o'zgartiring yoki yangi kitob/video qo'shing.</p>
        <button class="btn btn-yellow" onclick="openLibraryModal()" style="margin-top: 14px;">
          <i class="bi bi-plus-circle-fill"></i> Yangi Qo'shish
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(item => {
    const cleanCover = toFullMediaUrl(item.cover_image || item.image || '/images/library/sariq_devni_minib.png');
    const hasVideo = !!(item.video_url && item.video_url.trim());
    const hasAudio = !!(item.audio_url && item.audio_url.trim());
    const isFeatured = !!item.is_featured;
    const isActive = (item.status || 'active') === 'active';

    return `
      <div class="library-card">
        <div class="library-cover-container">
          <img src="${escapeHtml(cleanCover)}" alt="${escapeHtml(item.title)}" class="library-cover-img" loading="lazy" onerror="this.src='/images/library/sariq_devni_minib.png'">
          
          <div class="library-badges-overlay">
            <span class="badge-status ${isActive ? 'active' : 'inactive'}">
              ${isActive ? '● Faol' : '● Nofaol'}
            </span>
            <div class="library-media-badges">
              ${isFeatured ? '<span class="badge-media featured"><i class="bi bi-star-fill"></i> Sara</span>' : ''}
              ${hasVideo ? '<span class="badge-media video"><i class="bi bi-film"></i> Video</span>' : ''}
              ${hasAudio ? '<span class="badge-media audio"><i class="bi bi-headphones"></i> Audio</span>' : ''}
            </div>
          </div>
        </div>

        <div class="library-card-content">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
            <span style="font-size: 11px; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.04em;">
              ${escapeHtml(item.category_name || 'Kutubxona')}
            </span>
            <span style="font-size: 11px; color: var(--text-dim);">
              <i class="bi bi-clock"></i> ${escapeHtml(item.duration_formatted || '10:00')}
            </span>
          </div>

          <h4 class="library-card-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</h4>
          <div class="library-card-author"><i class="bi bi-person-fill"></i> ${escapeHtml(item.author || 'Noma\'lum')}</div>
          
          <p class="library-card-desc">${escapeHtml(item.description || 'Tavsif mavjud emas')}</p>

          <div class="library-card-meta">
            <span><i class="bi bi-person-badge"></i> ${escapeHtml(item.target_age || '7-12 yosh')}</span>
            <span><i class="bi bi-headphones"></i> ${item.listen_count || 0} tinglash</span>
            <span><i class="bi bi-heart-fill" style="color: #ef4444;"></i> ${item.likes_count || 0}</span>
          </div>

          <div class="library-card-actions">
            ${hasVideo ? `
              <button type="button" class="btn-media-action play-video" onclick="openLibraryVideoPlayer(${item.id})" title="Videoni tomosha qilish">
                <i class="bi bi-play-circle-fill"></i> Video
              </button>
              <button type="button" class="action-btn-sm" onclick="downloadBookVideo(${item.id})" title="Videoni yuklab olish (.mp4)" style="color: var(--yellow-primary);">
                <i class="bi bi-cloud-arrow-down-fill"></i>
              </button>
            ` : ''}

            ${hasAudio ? `
              <button type="button" class="btn-media-action play-audio" onclick="playBookAudio('${escapeHtml(toFullMediaUrl(item.audio_url))}', '${escapeHtml(item.title)}')" title="Audioni eshitish">
                <i class="bi bi-headphones"></i> Audio
              </button>
              <button type="button" class="action-btn-sm" onclick="downloadBookAudio(${item.id})" title="Audioni yuklab olish (.mp3)" style="color: #818cf8;">
                <i class="bi bi-download"></i>
              </button>
            ` : ''}

            <button type="button" class="action-btn-sm" onclick="openLibraryModal(${item.id})" title="Tahrirlash">
              <i class="bi bi-pencil-square"></i>
            </button>
            <button type="button" class="action-btn-sm danger" onclick="handleDeleteLibraryBook(${item.id})" title="O'chirish">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Open Modal for Create or Edit
function openLibraryModal(id = null) {
  const modal = document.getElementById('library-modal');
  const modalTitle = document.getElementById('library-modal-title');
  const form = document.getElementById('library-form');
  const delBtn = document.getElementById('library-delete-btn');

  if (!modal || !form) return;
  form.reset();

  populateLibraryCategorySelects();

  if (id) {
    const item = libraryList.find(b => b.id === id);
    if (item) {
      document.getElementById('library-id').value = item.id;
      document.getElementById('library-title').value = item.title || '';
      document.getElementById('library-author').value = item.author || '';
      if (document.getElementById('library-category-id')) {
        document.getElementById('library-category-id').value = item.category_id || (libraryCategoriesList[0]?.id || 1);
      }
      if (document.getElementById('library-section')) {
        document.getElementById('library-section').value = item.section || 'eng-sara';
      }
      document.getElementById('library-target-age').value = item.target_age || '7-12 yosh';
      document.getElementById('library-duration-formatted').value = item.duration_formatted || '10:00';
      document.getElementById('library-duration-seconds').value = item.duration_seconds || 600;
      document.getElementById('library-status').value = item.status || 'active';
      document.getElementById('library-is-featured').checked = !!item.is_featured;

      const coverVal = item.cover_image || item.image || '/images/library/sariq_devni_minib.png';
      document.getElementById('library-cover-url').value = coverVal;
      updateLibraryCoverPreview(coverVal);

      const videoVal = item.video_url || '';
      document.getElementById('library-video-url').value = videoVal;
      updateLibraryVideoPreview(videoVal);

      const audioVal = item.audio_url || '';
      document.getElementById('library-audio-url').value = audioVal;
      updateLibraryAudioPreview(audioVal);

      document.getElementById('library-desc').value = item.description || '';
      document.getElementById('library-content').value = item.content || '';

      if (modalTitle) {
        modalTitle.innerHTML = '<i class="bi bi-pencil-square text-yellow"></i> <span>Kitob / Videoni Tahrirlash</span>';
      }
      if (delBtn) delBtn.style.display = 'inline-flex';
    }
  } else {
    document.getElementById('library-id').value = '';
    if (document.getElementById('library-category-id') && libraryCategoriesList.length > 0) {
      document.getElementById('library-category-id').value = libraryCategoriesList[0].id;
    }
    document.getElementById('library-section').value = 'eng-sara';
    document.getElementById('library-target-age').value = '7-12 yosh';
    document.getElementById('library-duration-formatted').value = '10:00';
    document.getElementById('library-duration-seconds').value = 600;
    document.getElementById('library-status').value = 'active';
    document.getElementById('library-is-featured').checked = false;

    document.getElementById('library-cover-url').value = '/images/library/sariq_devni_minib.png';
    updateLibraryCoverPreview('/images/library/sariq_devni_minib.png');

    document.getElementById('library-video-url').value = '';
    updateLibraryVideoPreview('');

    document.getElementById('library-audio-url').value = '';
    updateLibraryAudioPreview('');

    document.getElementById('library-desc').value = '';
    document.getElementById('library-content').value = '';

    if (modalTitle) {
      modalTitle.innerHTML = '<i class="bi bi-collection-play-fill text-yellow"></i> <span>Yangi Kitob / Video Qo\'shish</span>';
    }
    if (delBtn) delBtn.style.display = 'none';
  }

  modal.classList.add('show');
}

function closeLibraryModal() {
  const vidPlayer = document.getElementById('library-video-preview-player');
  if (vidPlayer) {
    try { vidPlayer.pause(); } catch(e) {}
    vidPlayer.src = '';
  }
  const audPlayer = document.getElementById('library-audio-preview-player');
  if (audPlayer) {
    try { audPlayer.pause(); } catch(e) {}
    audPlayer.src = '';
  }
  const modal = document.getElementById('library-modal');
  if (modal) modal.classList.remove('show');
}

function handleDurationFormattedChange(val) {
  if (!val) return;
  const parts = val.trim().split(':');
  if (parts.length === 2) {
    const mins = parseInt(parts[0], 10) || 0;
    const secs = parseInt(parts[1], 10) || 0;
    const totalSecs = (mins * 60) + secs;
    if (document.getElementById('library-duration-seconds')) {
      document.getElementById('library-duration-seconds').value = totalSecs;
    }
  }
}

// Cover Image Handlers
function updateLibraryCoverPreview(url) {
  const img = document.getElementById('library-cover-preview');
  const txt = document.getElementById('library-cover-name');
  const clean = toFullMediaUrl(url || '/images/library/sariq_devni_minib.png');
  if (img) img.src = clean;
  if (txt) txt.innerText = url || '/images/library/sariq_devni_minib.png';
}

async function handleLibraryCoverUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  showToast("Muqova rasmi yuklanmoqda...", "info");
  try {
    const res = await fetch('/api/library/upload-cover/', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Rasm yuklashda xatolik yuz berdi");
    }
    const data = await res.json();
    const url = data.path || data.url;
    document.getElementById('library-cover-url').value = url;
    updateLibraryCoverPreview(url);
    showToast("Muqova rasmi yuklandi!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

// Video Handlers
function updateLibraryVideoPreview(url) {
  const wrap = document.getElementById('library-video-preview-wrap');
  const player = document.getElementById('library-video-preview-player');
  if (!wrap || !player) return;

  if (url && url.trim()) {
    const fullUrl = toFullMediaUrl(url.trim());
    player.src = fullUrl;
    wrap.style.display = 'block';
  } else {
    try { player.pause(); } catch(e) {}
    player.src = '';
    wrap.style.display = 'none';
  }
}

function clearLibraryVideo() {
  if (document.getElementById('library-video-url')) document.getElementById('library-video-url').value = '';
  if (document.getElementById('library-video-file')) document.getElementById('library-video-file').value = '';
  updateLibraryVideoPreview('');
  showToast("Video havolasi tozalandi", "info");
}

async function handleLibraryVideoUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  if (file.size > 250 * 1024 * 1024) {
    showToast("Video hajmi 250MB dan oshmasligi kerak!", "error");
    event.target.value = '';
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  showToast(`Video yuklanmoqda (${(file.size / (1024*1024)).toFixed(1)} MB)... Iltimos kuting.`, "info");

  try {
    const res = await fetch('/api/library/upload-video/', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Video yuklashda xatolik yuz berdi");
    }

    const data = await res.json();
    const videoPath = data.path || data.video_url || data.url;
    if (document.getElementById('library-video-url')) {
      document.getElementById('library-video-url').value = videoPath;
    }
    updateLibraryVideoPreview(videoPath);
    showToast("🎬 Video muvaffaqiyatli yuklandi!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

function testPlayLibraryFormVideo() {
  const url = document.getElementById('library-video-url')?.value.trim();
  if (!url) {
    showToast("Avval video havolasini kiriting yoki video yuklang!", "warning");
    return;
  }
  const title = document.getElementById('library-title')?.value.trim() || 'Video Sinovi';
  openVideoPlayerDirect(url, title);
}

function downloadCurrentInputVideo() {
  const url = document.getElementById('library-video-url')?.value.trim();
  if (!url) {
    showToast("Yuklab olish uchun video manzili mavjud emas", "warning");
    return;
  }
  const dlUrl = `/api/library/download-file?file_url=${encodeURIComponent(url)}`;
  window.open(toFullMediaUrl(dlUrl), '_blank');
}

// Audio Handlers
function updateLibraryAudioPreview(url) {
  const wrap = document.getElementById('library-audio-preview-wrap');
  const player = document.getElementById('library-audio-preview-player');
  if (!wrap || !player) return;

  if (url && url.trim()) {
    player.src = toFullMediaUrl(url.trim());
    wrap.style.display = 'block';
  } else {
    try { player.pause(); } catch(e) {}
    player.src = '';
    wrap.style.display = 'none';
  }
}

function clearLibraryAudio() {
  if (document.getElementById('library-audio-url')) document.getElementById('library-audio-url').value = '';
  if (document.getElementById('library-audio-file')) document.getElementById('library-audio-file').value = '';
  updateLibraryAudioPreview('');
  showToast("Audio havolasi tozalandi", "info");
}

async function handleLibraryAudioUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  showToast("Audio yuklanmoqda...", "info");
  try {
    const res = await fetch('/api/library/upload-audio/', {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Audio yuklashda xatolik yuz berdi");
    }
    const data = await res.json();
    const audioPath = data.path || data.audio_url || data.url;
    document.getElementById('library-audio-url').value = audioPath;
    updateLibraryAudioPreview(audioPath);
    showToast("🎧 Audio fayl muvaffaqiyatli yuklandi!", "success");
  } catch (err) {
    showToast(err.message, "error");
  }
}

async function handleGenerateLibraryAudioTTS() {
  const bookId = document.getElementById('library-id')?.value;
  const title = document.getElementById('library-title')?.value.trim();
  const desc = document.getElementById('library-desc')?.value.trim();
  const content = document.getElementById('library-content')?.value.trim();

  if (!title && !content && !desc) {
    showToast("Audio yaratish uchun kitob nomi yoki tavsifini kiriting!", "warning");
    return;
  }

  if (bookId) {
    const btn = document.getElementById('library-tts-gen-btn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Yaratilmoqda...';
    }
    showToast("Matndan o'zbekcha audio generatsiya qilinmoqda (Edge-TTS)...", "info");

    try {
      const res = await fetch(`/api/library/books/${bookId}/generate-audio/`, { method: 'POST' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Audio generatsiyasida xatolik");
      }
      const data = await res.json();
      if (data.audio_url) {
        document.getElementById('library-audio-url').value = data.audio_url;
        updateLibraryAudioPreview(data.audio_url);
        showToast("Audio muvaffaqiyatli yaratildi va biriktirildi! 🎙️", "success");
      }
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-stars"></i> Matndan AI Ovoz';
      }
    }
  } else {
    showToast("Avval yangi kitobni saqlang, so'ng AI ovoz generatsiya qiling!", "info");
  }
}

// Save Library Book
async function handleSaveLibraryBook(event) {
  event.preventDefault();

  const id = document.getElementById('library-id').value;
  const title = document.getElementById('library-title').value.trim();
  const author = document.getElementById('library-author').value.trim();
  const category_id = parseInt(document.getElementById('library-category-id').value, 10) || 1;
  const section = document.getElementById('library-section').value;
  const target_age = document.getElementById('library-target-age').value.trim() || '7-12 yosh';
  const duration_formatted = document.getElementById('library-duration-formatted').value.trim() || '10:00';
  const duration_seconds = parseInt(document.getElementById('library-duration-seconds').value, 10) || 600;
  const status = document.getElementById('library-status').value;
  const is_featured = document.getElementById('library-is-featured').checked;
  const cover_image = document.getElementById('library-cover-url').value.trim() || '/images/library/sariq_devni_minib.png';
  const video_url = document.getElementById('library-video-url').value.trim();
  const audio_url = document.getElementById('library-audio-url').value.trim();
  const description = document.getElementById('library-desc').value.trim();
  const content = document.getElementById('library-content').value.trim();

  if (!title || !author || !description) {
    showToast("Iltimos, sarlavha, muallif va tavsifni to'ldiring!", "warning");
    return;
  }

  const payload = {
    category_id,
    title,
    author,
    cover_image,
    description,
    content,
    audio_url,
    video_url,
    duration_seconds,
    duration_formatted,
    target_age,
    is_featured,
    section,
    status
  };

  const saveBtn = document.getElementById('save-library-btn');
  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saqlanmoqda...';
  }

  try {
    let res;
    if (id) {
      res = await fetch(`/api/library/books/${id}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/library/books/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Kitobni saqlashda xatolik");
    }

    showToast(id ? "Kitob/video muvaffaqiyatli tahrirlandi! ✨" : "Yangi kitob/video muvaffaqiyatli qo'shildi! 🎉", "success");
    closeLibraryModal();
    await fetchLibraryBooks();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    if (saveBtn) {
      saveBtn.disabled = false;
      saveBtn.innerHTML = '<i class="bi bi-check2-circle"></i> Saqlash';
    }
  }
}

// Delete Book
async function handleDeleteLibraryBook(id) {
  const item = libraryList.find(b => b.id === id);
  const title = item ? item.title : 'ushbu kitobni';
  if (!confirm(`Haqiqatan ham "${title}"ni o'chirmoqchimisiz?`)) return;

  try {
    const res = await fetch(`/api/library/books/${id}/`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Kitobni o'chirishda xatolik");
    }
    showToast("Kitob muvaffaqiyatli o'chirildi", "success");
    await fetchLibraryBooks();
  } catch (err) {
    showToast(err.message, "error");
  }
}

function handleDeleteCurrentLibraryBookFromModal() {
  const id = document.getElementById('library-id')?.value;
  if (id) {
    closeLibraryModal();
    handleDeleteLibraryBook(parseInt(id, 10));
  }
}

// Fullscreen Cinema Video Player Modal
function openLibraryVideoPlayer(bookId) {
  const item = libraryList.find(b => b.id === bookId);
  if (!item || !item.video_url) {
    showToast("Ushbu darsda video mavjud emas", "warning");
    return;
  }

  currentModalBookId = bookId;
  currentModalVideoUrl = toFullMediaUrl(item.video_url);
  currentModalVideoTitle = item.title;

  const modal = document.getElementById('library-video-modal');
  const titleEl = document.getElementById('library-video-modal-title');
  const subEl = document.getElementById('library-video-modal-sub');
  const player = document.getElementById('library-modal-video-player');
  const fileInfo = document.getElementById('library-video-modal-filename');

  if (titleEl) titleEl.innerText = item.title;
  if (subEl) subEl.innerText = `${item.author} • ${item.category_name || 'Kutubxona'}`;
  if (fileInfo) fileInfo.innerText = item.video_url.split('/').pop() || 'video.mp4';

  if (player) {
    player.src = currentModalVideoUrl;
    player.play().catch(() => {});
  }

  if (modal) modal.classList.add('show');
}

function openVideoPlayerDirect(url, title = 'Video') {
  currentModalBookId = null;
  currentModalVideoUrl = toFullMediaUrl(url);
  currentModalVideoTitle = title;

  const modal = document.getElementById('library-video-modal');
  const titleEl = document.getElementById('library-video-modal-title');
  const subEl = document.getElementById('library-video-modal-sub');
  const player = document.getElementById('library-modal-video-player');
  const fileInfo = document.getElementById('library-video-modal-filename');

  if (titleEl) titleEl.innerText = title;
  if (subEl) subEl.innerText = 'Video Dars Preview';
  if (fileInfo) fileInfo.innerText = url.split('/').pop() || 'video.mp4';

  if (player) {
    player.src = currentModalVideoUrl;
    player.play().catch(() => {});
  }

  if (modal) modal.classList.add('show');
}

function closeLibraryVideoModal() {
  const player = document.getElementById('library-modal-video-player');
  if (player) {
    try { player.pause(); } catch(e) {}
    player.src = '';
  }
  const modal = document.getElementById('library-video-modal');
  if (modal) modal.classList.remove('show');
}

function downloadCurrentModalVideo() {
  if (currentModalBookId) {
    downloadBookVideo(currentModalBookId);
  } else if (currentModalVideoUrl) {
    const dlUrl = `/api/library/download-file?file_url=${encodeURIComponent(currentModalVideoUrl)}`;
    window.open(toFullMediaUrl(dlUrl), '_blank');
  }
}

function downloadBookVideo(bookId) {
  const dlUrl = `/api/library/books/${bookId}/download-video`;
  showToast("Videoni yuklab olish boshlandi... 🎬", "info");
  window.open(toFullMediaUrl(dlUrl), '_blank');
}

function downloadBookAudio(bookId) {
  const dlUrl = `/api/library/books/${bookId}/download-audio`;
  showToast("Audioni yuklab olish boshlandi... 🎧", "info");
  window.open(toFullMediaUrl(dlUrl), '_blank');
}

// Global Audio playback for single click
let currentGlobalAudio = null;
function playBookAudio(audioUrl, title = '') {
  if (!audioUrl) {
    showToast("Audio manzili topilmadi", "warning");
    return;
  }
  const fullUrl = toFullMediaUrl(audioUrl);
  if (currentGlobalAudio) {
    currentGlobalAudio.pause();
    currentGlobalAudio = null;
  }
  currentGlobalAudio = new Audio(fullUrl);
  currentGlobalAudio.play().then(() => {
    showToast(`🎧 Tinglanmoqda: ${title || 'Audio kitob'}`, "info");
  }).catch(e => {
    console.error("Audio playback error:", e);
    showToast("Audioni ijro etishda xatolik", "error");
  });
}


// Explicitly expose functions to window for inline onclick attributes
window.currentOpenCatId = currentOpenCatId;
window.currentOpenCatName = currentOpenCatName;
window.openUranWordModal = openUranWordModal;
window.closeUranWordModal = closeUranWordModal;
window.openUranCategoryDetail = openUranCategoryDetail;
window.closeUranCategoryDetail = closeUranCategoryDetail;
window.filterUranDetailWords = filterUranDetailWords;
window.renderUranCategories = renderUranCategories;
window.renderUranWords = renderUranWords;
window.renderUranDetailWords = renderUranDetailWords;
window.handleSaveUranWord = handleSaveUranWord;
window.handleDeleteUranWord = handleDeleteUranWord;
window.handleAiSuggestWord = handleAiSuggestWord;
window.playWordAudio = playWordAudio;
window.openFaqModal = openFaqModal;
window.closeFaqModal = closeFaqModal;
window.handleSaveFaq = handleSaveFaq;
window.handleDeleteFaq = handleDeleteFaq;
window.handleToggleFaqStatus = handleToggleFaqStatus;
window.renderFaqs = renderFaqs;
window.fetchFaqs = fetchFaqs;
window.switchTab = switchTab;

// Library Window Exports
window.fetchLibraryCategories = fetchLibraryCategories;
window.fetchLibraryBooks = fetchLibraryBooks;
window.renderLibraryBooks = renderLibraryBooks;
window.openLibraryModal = openLibraryModal;
window.closeLibraryModal = closeLibraryModal;
window.handleDurationFormattedChange = handleDurationFormattedChange;
window.updateLibraryCoverPreview = updateLibraryCoverPreview;
window.handleLibraryCoverUpload = handleLibraryCoverUpload;
window.updateLibraryVideoPreview = updateLibraryVideoPreview;
window.clearLibraryVideo = clearLibraryVideo;
window.handleLibraryVideoUpload = handleLibraryVideoUpload;
window.testPlayLibraryFormVideo = testPlayLibraryFormVideo;
window.downloadCurrentInputVideo = downloadCurrentInputVideo;
window.updateLibraryAudioPreview = updateLibraryAudioPreview;
window.clearLibraryAudio = clearLibraryAudio;
window.handleLibraryAudioUpload = handleLibraryAudioUpload;
window.handleGenerateLibraryAudioTTS = handleGenerateLibraryAudioTTS;
window.handleSaveLibraryBook = handleSaveLibraryBook;
window.handleDeleteLibraryBook = handleDeleteLibraryBook;
window.handleDeleteCurrentLibraryBookFromModal = handleDeleteCurrentLibraryBookFromModal;
window.openLibraryVideoPlayer = openLibraryVideoPlayer;
window.openVideoPlayerDirect = openVideoPlayerDirect;
window.closeLibraryVideoModal = closeLibraryVideoModal;
window.downloadCurrentModalVideo = downloadCurrentModalVideo;
window.downloadBookVideo = downloadBookVideo;
window.downloadBookAudio = downloadBookAudio;
window.playBookAudio = playBookAudio;

