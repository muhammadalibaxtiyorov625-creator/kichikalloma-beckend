/**
 * ============================================================================
 * KICHIK ALLOMA — ULTRA-PRECISE 3D COSMIC PARTICLE ENGINE
 * ============================================================================
 * Har bir slayd mavzusiga 100% mos keluvchi aniq 3D zarracha shakllari:
 * - Uran: Sayyora -> Hayvon panjasi -> Olma/Meva -> Mikrofon -> Olmos Quiz -> Cheksizlik
 * - Yer: Globus -> Neyron AI Yadro -> OCR Kamera -> Soat 20:00 -> Oltin Tanga -> Qalqon
 * - Saturn: Halqalar -> Matematik Misollar (+,×,=) -> 3D Kub -> Lampa -> Kubok -> Pog'onali Grafik
 * - Yupiter: Gaz Giganti -> Reja Ro'yxati -> Qalin Tasdiq (✔) -> Olov (Flame) -> Sektorli Diagramma -> Radar
 * - Venera: Olovli Sfera -> Skafandr Bosh kiyimi -> Qirollik Toji -> 3D Xona -> Xazina Sandig'i -> Qulf
 * - Mars: Qizil Sayyora -> Yoga/Cho'zilish -> Yuguruvchi Atlet -> Muvozanat Tarozi -> Sport Medali -> Yurak Pulsi
 * - Merkuriy: Kraterli Shar -> 8 Qirrali Spektr -> Kino Kamera -> Mo'yqalam -> Sevimli Yulduz -> Kompas
 * - Neptun: Moviy Girdob -> Tabassum/Yurak -> Ochiq Kundalik -> Lotos Guli -> To'lqin Grafigi -> Mayoq
 */

const Cosmic3D = (() => {
  const PARTICLE_COUNT = 6500;

  const PLANET_UNIVERSE = {
    'uran': {
      shape: 'uran',
      color: '#06b6d4',
      glow: 'rgba(6, 182, 212, 0.45)',
      border: 'rgba(6, 182, 212, 0.25)',
      slides: [
        {
          morphType: 'uran_planet',
          badge: "01 / 06 • INGLIZ TILI",
          title: "URAN SAYYORASI",
          subtitle: "English Vocabulary — So'z Boyligi",
          desc: "Vizual, audio va test asosida bolalarning ingliz tili so'z boyligini rivojlantiruvchi muz giganti sayyorasi.",
          pills: ["10 ta Mavzu", "106+ Nativ So'z", "Audio STT Talaffuz", "Spaced Repetition"]
        },
        {
          morphType: 'animal_paw',
          badge: "02 / 06 • MAVZU: ANIMALS",
          title: "HAYVONLAR DUNYOSI",
          subtitle: "Animals & Nature Vocabulary",
          desc: "Bolajonlar hayvonlarning multik rasmlari, inglizcha yozilishi va toza talaffuzini o'rganadilar.",
          pills: ["🐶 Dog — It", "🐱 Cat — Mushuk", "🦁 Lion — Sher", "🐘 Elephant — Fil", "🐟 Fish — Baliq", "🐦 Bird — Qush"]
        },
        {
          morphType: 'apple_fruit',
          badge: "03 / 06 • MAVZU: FOOD & SCHOOL",
          title: "KUNDALIK SO'ZLAR",
          subtitle: "Food, Drinks & School Items",
          desc: "Maktab va oilada ishlatiladigan eng muhim so'zlarni xotirada mustahkamlash bosqichi.",
          pills: ["🍎 Apple — Olma", "🍌 Banana — Banan", "🍞 Bread — Non", "📚 Book — Kitob", "✏️ Pencil — Qalam", "🏫 School — Maktab"]
        },
        {
          morphType: 'microphone',
          badge: "04 / 06 • AUDIOLASHTIRISH",
          title: "OVOZLI TALAFFUZ (STT)",
          subtitle: "Speech Recognition & Pronunciation",
          desc: "Bola so'zning nativ talaffuzini eshitadi va mikrofon orqali qaytaradi. AI to'g'ri talaffuzni tekshiradi.",
          pills: ["Nativ Britaniya/AQSH ovozi", "Ovoz tahlili (STT)", "Qayta takrorlash", "Sof talaffuz"]
        },
        {
          morphType: 'diamond_quiz',
          badge: "05 / 06 • AMALIYOT",
          title: "4 VARIANTLI TEST",
          subtitle: "Interactive Quiz & Gold Coin",
          desc: "Mavzu oxirida rasmga mos so'zni topish va testlarni yechish. Muvaffaqiyatli topshirilganda mukofot beriladi.",
          pills: ["✅ To'g'ri javoblar", "🪙 +25 Gold Coin", "Xatoni tahlil qilish", "Reyting o'sishi"]
        },
        {
          morphType: 'infinity_loop',
          badge: "06 / 06 • MUSTAHKAMLASH",
          title: "SPACED REPETITION",
          subtitle: "Intervalli Xotira Tizimi",
          desc: "O'rganilgan so'zlar unutilmasligi uchun ma'lum kunlardan keyin avtomatik takrorlatib turiladi.",
          pills: ["1-kun takrorlash", "3-kun mustahkamlash", "7-kun yakuniy test", "100% Xotira"]
        }
      ]
    },

    'earth': {
      shape: 'earth',
      color: '#38bdf8',
      glow: 'rgba(56, 189, 248, 0.45)',
      border: 'rgba(56, 189, 248, 0.25)',
      slides: [
        {
          morphType: 'earth_globe',
          badge: "01 / 06 • KOGNITIV TA'LIM",
          title: "YER (ZAMIN)",
          subtitle: "Kognitiv Ta'lim va AI Tutor",
          desc: "Kichik Allomaning asosiy akademik markazi. Bola AI bilan individual dars qiladi va tushunmagan mavzularini o'rganadi.",
          pills: ["AI Tutor", "Sokratik usul", "20 daqiqa limit", "Parent Panel"]
        },
        {
          morphType: 'neural_brain',
          badge: "02 / 06 • SO'RASH VA O'RGANISH",
          title: "SOKRATIK METODIKA",
          subtitle: "AI Tayyor Javob Bermaydi",
          desc: "AI bolaning o'rniga ishlab bermasdan, masalani qadam-baqadam tushunishga va mustaqil yechishga undaydi.",
          pills: ["Yo'naltiruvchi savollar", "Mustaqil fikrlash", "Matematika & Ona tili", "Qadamma-qadam tushuntirish"]
        },
        {
          morphType: 'camera_scanner',
          badge: "03 / 06 • FOTO VA OCR",
          title: "RASM ORQALI TOPSHIRIQ",
          subtitle: "Daftar va Kitob Tahlili (OCR)",
          desc: "Bola misol yoki qiyin matnni rasmga olib yuboradi. AI rasmni o'qib, o'quvchiga tushunarli tilda tahlil qiladi.",
          pills: ["Kamera orqali yuborish", "OCR matn tanish", "O'zbek tilida izoh", "Xatosiz dars tayyorlash"]
        },
        {
          morphType: 'clock_20min',
          badge: "04 / 06 • XAVFSIZLIK VA VAQT",
          title: "20 DAQIQALIK LIMIT",
          subtitle: "Kunlik Qat'iy AI Balansi",
          desc: "Har bir bola uchun kuniga maksimal 20:00 daqiqa AI vaqti beriladi. Ekranda real-time MM:SS hisoblab boriladi.",
          pills: ["⏱️ 20:00 Countdown", "Bo'lib-bo'lib ishlatish", "Serverda tekshiruv", "Ekranga bog'lanmaslik"]
        },
        {
          morphType: 'gold_coin_star',
          badge: "05 / 06 • MUKOFOT TIZIMI",
          title: "DARS VA GOLD COIN",
          subtitle: "Har Bir Yutuq Uchun Rag'bat",
          desc: "AI bilan darsni muvaffaqiyatli yakunlagan bolaga Gold Coin beriladi va Venera do'konida sarflanadi.",
          pills: ["🪙 Gold Coin jamg'arish", "Akademik o'sish", "Streak saqlash", "Avatar kiyintirish"]
        },
        {
          morphType: 'shield_protection',
          badge: "06 / 06 • OTA-ONA NAZORATI",
          title: "PARENT DASHBOARD",
          subtitle: "To'liq Shaffoflik va Xavfsizlik",
          desc: "Ota-ona bugungi AI foydalanish vaqtini, berilgan savollar mavzularini va rivojlanish grafigini ko'rib boradi.",
          pills: ["AI vaqti hisoboti", "Qiziqishlar tahlili", "Haftalik o'sish", "Parent Gate himoyasi"]
        }
      ]
    },

    'saturn': {
      shape: 'saturn',
      color: '#f59e0b',
      glow: 'rgba(245, 158, 11, 0.45)',
      border: 'rgba(245, 158, 11, 0.25)',
      slides: [
        {
          morphType: 'saturn_rings',
          badge: "01 / 06 • MATEMATIKA",
          title: "SATURN SAYYORASI",
          subtitle: "Matematika va Mantiqiy Fikrlash",
          desc: "Muz va tosh halqalari bilan bezatilgan sayyora — bolaning hisoblash, mantiq va fazoviy tasavvurini o'stiradi.",
          pills: ["Arifmetika", "Mantiqiy savollar", "Adaptiv testlar", "Gold Coin"]
        },
        {
          morphType: 'math_symbols',
          badge: "02 / 06 • TEZKOR HISOBLASH",
          title: "ARIFMETIK MASHQLAR",
          subtitle: "Yoshga Moslashtirilgan Darslar",
          desc: "Qo'shish (+), ayirish (−), ko'paytirish (×) va bo'lish (÷) amallarini o'yin shaklida o'zlashtirish.",
          pills: ["1-sinf: 8 + 5 = 13", "3-sinf: 48 ÷ 6 = 8", "5-sinf: (x + 4)² = 36", "Mental arifmetika"]
        },
        {
          morphType: 'rubiks_cube',
          badge: "03 / 06 • MANTIQIY TAHLIL",
          title: "FAZOVIY BOSHJUMBOQLAR",
          subtitle: "Logic Patterns & Deduction",
          desc: "Ketma-ketliklar, geometrik shakllar, rebuslar va fazoviy mantiqiy masalalarni yechish.",
          pills: ["2, 4, 8, ?, 32", "Shakl simmetriyasi", "Rebus va boshqotirma", "Deduktiv fikrlash"]
        },
        {
          morphType: 'lightbulb_idea',
          badge: "04 / 06 • DO'STONA YONDASHUV",
          title: "JAZOSIZ TA'LIM",
          subtitle: "Xatoni Tushuntiruvchi Feedback",
          desc: "Xato javob berilganda ball ayirilmaydi yoki jazolanmaydi. Qayerda xato bo'lgani tushuntirilib, qayta imkon beriladi.",
          pills: ["Do'stona izoh", "Qayta urinish", "Stresssiz o'rganish", "Mukammal tushunish"]
        },
        {
          morphType: 'trophy_cup',
          badge: "05 / 06 • MUKOFOT",
          title: "SATURN OLTIMARI",
          subtitle: "Gold Coin va Reyting",
          desc: "To'liq to'g'ri yechilgan bloklar uchun 🪙 Gold Coin beriladi va bola yangi liga pog'onalariga ko'tariladi.",
          pills: ["🪙 +50 Gold Coin", "Matematik nishonlar", "Sinf reytingi", "Haftalik chempionat"]
        },
        {
          morphType: 'stairs_chart',
          badge: "06 / 06 • PROGRESS",
          title: "NATIJALAR GRAFIGI",
          subtitle: "Aniqlik Foizi va Tahlil",
          desc: "Bola va ota-ona qaysi mavzularda o'sish borligini va qaysi mavzuda ko'proq mashq kerakligini ko'radi.",
          pills: ["Aniqlik: 94%", "Yechish tezligi", "O'sish grafigi", "Tavsiyalar"]
        }
      ]
    },

    'jupiter': {
      shape: 'jupiter',
      color: '#eab308',
      glow: 'rgba(234, 179, 8, 0.45)',
      border: 'rgba(234, 179, 8, 0.25)',
      slides: [
        {
          morphType: 'jupiter_giant',
          badge: "01 / 06 • INTIZOM",
          title: "YUPITER SAYYORASI",
          subtitle: "O'z-o'zini Boshqarish va Reja",
          desc: "Bolaning kunni rejalashtirish, vaqtini boshqarish va vazifalarni intizom bilan bajarish ko'nikmasini shakllantiradi.",
          pills: ["Kunlik reja", "Vazifalar", "Streak", "Intizom"]
        },
        {
          morphType: 'clipboard_plan',
          badge: "02 / 06 • REJA TUZISH",
          title: "KUNLIK REJA EKRANI",
          subtitle: "Vazifalar va Kategoriyalar",
          desc: "Bola ertalab kunlik rejasini tuzadi: vazifaga nom, vaqt va tayyor toifalardan birini biriktiradi.",
          pills: ["📚 Dars qilish", "📖 Kitob o'qish", "🏃 Sport mashqi", "🏠 Uy ishi", "🎮 Dam olish"]
        },
        {
          morphType: 'big_checkmark',
          badge: "03 / 06 • BAJARISH",
          title: "VAZIFANI BELGILASH",
          subtitle: "Har Bir Bajarilgan Ish Uchun Coin",
          desc: "Kechqurun bola bajargan ishlarini tasdiqlaydi va har bir intizomli harakat uchun mukofotlanadi.",
          pills: ["✅ Bajarildi belgisi", "🪙 +20 Gold Coin", "Kunlik qoniqish", "O'ziga ishonch"]
        },
        {
          morphType: 'fire_streak',
          badge: "04 / 06 • STREAK TIZIMI",
          title: "KETMA-KET KUNLAR",
          subtitle: "Doimiy Faollik Zanjiri",
          desc: "Har kuni reja tuzib bajargan bolaning Streak zanjiri o'sib boradi. O'tkazib yuborilgan kun uchun dalda beriladi.",
          pills: ["🔥 7 kunlik Streak", "Oltin mukofot", "Jazolovsiz muhit", "Odat shakllanishi"]
        },
        {
          morphType: 'pie_chart_slices',
          badge: "05 / 06 • TAHLIL",
          title: "VAQTNI HIS QILISH",
          subtitle: "O'z Vaqtini Baholash",
          desc: "Bola haftalik hisobotlar orqali o'z vaqtini qanday foydali o'tkazganini mustaqil tahlil qiladi.",
          pills: ["Foydali vaqt: 85%", "Haftalik diagramma", "Mustaqillik", "Tartibli kun"]
        },
        {
          morphType: 'radar_target',
          badge: "06 / 06 • HISOBOT",
          title: "PARENT PANEL INTEGRATSIYA",
          subtitle: "Ota-onaga Oylik Intizom Hisoboti",
          desc: "Ota-ona bolaning rejalashtirish ko'nikmasi qanday rivojlanayotganini yagona dashboardda kuzatib boradi.",
          pills: ["Reja bajarilishi", "Kategoriyalar nisbati", "Oylik tahlil", "Xotirjamlik"]
        }
      ]
    },

    'venera': {
      shape: 'venus',
      color: '#f97316',
      glow: 'rgba(249, 115, 22, 0.45)',
      border: 'rgba(249, 115, 22, 0.25)',
      slides: [
        {
          morphType: 'venus_swirl',
          badge: "01 / 06 • VIRTUAL STORE",
          title: "VENERA DO'KONI",
          subtitle: "Gold Coin Virtual Do'koni",
          desc: "Barcha sayyoralarda o'qib, mashq qilib ishlab topilgan Gold Coin'lar sarflanadigan virtual do'kon.",
          pills: ["Kiyimlar", "Aksessuarlar", "Emojilar", "Inventory"]
        },
        {
          morphType: 'helmet_suit',
          badge: "02 / 06 • AVATAR KIYIMLARI",
          title: "KOSMIK SKAFANDRLAR",
          subtitle: "Har Xil Uslubdagi Liboslar",
          desc: "Olim xalati, fazogir skafandri, sehrgar kiyimi va bayramona liboslar bilan avatarni bezatish.",
          pills: ["👨‍🚀 Fazogir skafandri", "🧙‍♂️ Sehrgar libosi", "👑 Qirollik toji", "🎨 Rassom formasi"]
        },
        {
          morphType: 'royal_crown',
          badge: "03 / 06 • AKSESSUARLAR",
          title: "BEZAKLAR VA BUYUMLAR",
          subtitle: "Ko'zoynak, Qanot va Quloqchinlar",
          desc: "Avatar uchun yuzlab noyob aksessuarlar. Har bir buyum bolaning shaxsiy ijodiy didini ifodalaydi.",
          pills: ["👓 Koinot ko'zoynagi", "🎧 Neon quloqchin", "🪽 Kosmik qanot", "⭐ Oltin nishon"]
        },
        {
          morphType: 'isometric_room',
          badge: "04 / 06 • VIRTUAL XONA",
          title: "STANSIYANI BEZASH",
          subtitle: "Shaxsiy Kosmik Xona Dizayni",
          desc: "Bola o'z virtual xonasini mebellar, devor rasmlari va yorug'lik effektlari bilan o'zi loyihalaydi.",
          pills: ["🛋️ Kosmik divan", "🖼️ Galaktika rasmlari", "💡 Neon chiroqlar", "🪴 Oy o'simliklari"]
        },
        {
          morphType: 'treasure_chest',
          badge: "05 / 06 • INVENTORY",
          title: "BUYUMLAR SANDIG'I",
          subtitle: "Barcha Xaridlar Bir Joyda",
          desc: "Sotib olingan barcha kiyim va bezaklar inventoryda xavfsiz saqlanadi. Istalgan vaqtda kiyish mumkin.",
          pills: ["🎒 Shaxsiy inventar", "Tez almashtirish", "Kolleksiyalar", "Cheksiz saqlash"]
        },
        {
          morphType: 'lock_shield',
          badge: "06 / 06 • XAVFSIZ IQTISODIYOT",
          title: "100% XAVFSIZ GAMIFIKATSIYA",
          subtitle: "Faqat Kosmetik Buyumlar",
          desc: "Buyumlar real pulga sotilmaydi yoki o'girilmaydi. Akademik ustunlik bermaydi — faqat ijodiy motivatsiya.",
          pills: ["Real pul yo'q", "Donatsiz tizim", "Faqat bilim evaziga", "Bolalar himoyasi"]
        }
      ]
    },

    'mars': {
      shape: 'mars',
      color: '#ef4444',
      glow: 'rgba(239, 68, 68, 0.45)',
      border: 'rgba(239, 68, 68, 0.25)',
      slides: [
        {
          morphType: 'mars_planet',
          badge: "01 / 06 • JISMONIY FAOLLIK",
          title: "MARS SAYYORASI",
          subtitle: "Harakat va Jismoniy Mashqlar",
          desc: "Bolani ekran qarshisidan real jismoniy harakatga olib chiqadigan interaktiv mashqlar maydoni.",
          pills: ["Cho'zilish", "Yengil kardio", "Muvozanat", "Gold Coin"]
        },
        {
          morphType: 'yoga_stretch',
          badge: "02 / 06 • ERTALABKI BADANTARBIYA",
          title: "CHO'ZILISH MASHQLARI",
          subtitle: "Stretching & Warm-up",
          desc: "Bo'yin, yelka, qo'l va oyoqlar uchun bolalarbop yengil cho'zilish va ertalabki uyg'onish mashqlari.",
          pills: ["🤸 Yelka aylantirish", "🦵 Oyoq cho'zilishi", "🧘 To'g'ri qaddi-qomat", "5-10 daqiqa"]
        },
        {
          morphType: 'runner_athlete',
          badge: "03 / 06 • RITM VA HARAKAT",
          title: "YENGIL KARDIO VA RAQS",
          subtitle: "Quvnoq Musiqa Ostida Harakat",
          desc: "Joyida yugurish, sakrash, ritmik harakatlar va quvnoq musiqa ostida kayfiyatni ko'tarish.",
          pills: ["🏃 Joyida yugurish", "⭐ Yulduzcha sakrash", "💃 Ritmik harakat", "Energiya to'plash"]
        },
        {
          morphType: 'balance_scale',
          badge: "04 / 06 • CHAQONLIK",
          title: "MUVOZANAT VA KOORDINATSIYA",
          subtitle: "Balance & Motor Skills",
          desc: "Bir oyoqda turish, fazoviy harakatlar va to'p bilan o'yinlar orqali bolaning epchilligini oshirish.",
          pills: ["🦩 Bir oyoqda muvozanat", "🎯 To'p tutish", "⚡ Tezkor reaksiya", "Chaqqonlik"]
        },
        {
          morphType: 'sport_medal',
          badge: "05 / 06 • MUKOFOT",
          title: "HARAKAT UCHUN COIN",
          subtitle: "Har Bir Video — Oltin Mukofot",
          desc: "Video bilan birgalikda mashqni bajargan bolaga 🪙 Gold Coin beriladi va kunlik faollik hisoblanadi.",
          pills: ["🪙 +30 Gold Coin", "Kunlik faollik", "Sog'lom turmush", "Sport yutuqlari"]
        },
        {
          morphType: 'heartbeat_pulse',
          badge: "06 / 06 • SALOMATLIK",
          title: "XAVFSIZ VA SOG'LOM",
          subtitle: "Bolalarbop Xavfsizlik Qoidalari",
          desc: "Mashqdan oldin xavfsiz joy tanlash va to'g'ri nafas olish bo'yicha ko'rsatma. Tibbiy tashxis emas.",
          pills: ["To'g'ri nafas olish", "Xavfsiz mashqlar", "Haftalik 120 daqiqa", "Parent Panel"]
        }
      ]
    },

    'mercury': {
      shape: 'mercury',
      color: '#94a3b8',
      glow: 'rgba(148, 163, 184, 0.45)',
      border: 'rgba(148, 163, 184, 0.25)',
      slides: [
        {
          morphType: 'mercury_planet',
          badge: "01 / 06 • KASBLAR",
          title: "MERKURIY SAYYORASI",
          subtitle: "Ijodkorlik va Kelajak Kasblari",
          desc: "Bolaning ijodiy qiziqishlari va kelajak kasblari haqidagi tasavvurini kengaytiruvchi kashfiyotlar sayyorasi.",
          pills: ["8 ta Kasb toifasi", "Videolar", "Mini-quizlar", "Qiziqishlar"]
        },
        {
          morphType: 'profession_fan',
          badge: "02 / 06 • 8 TA KASB SOHASI",
          title: "KASBLAR SPEKTRI",
          subtitle: "Fan, IT, San'at va Tibbiyot",
          desc: "Dasturchi, shifokor, me'mor, rassom, kosmonavt va ekolog kasblarining qiziqarli tomonlari.",
          pills: ["🔬 Olim", "💻 IT Dasturchi", "🏥 Shifokor", "🎨 Rassom", "⚙️ Muhandis", "🌿 Ekolog"]
        },
        {
          morphType: 'movie_camera',
          badge: "03 / 06 • INTERAKTIV VIDEOLAR",
          title: "KASB EGALARI HAYOTI",
          subtitle: "Qisqa va Bolalarbop Videolar",
          desc: "Har bir kasb vakili nima ish qilishi va bu kasb uchun qanday bilimlar kerakligi ko'rsatiladi.",
          pills: ["2-3 daqiqalik rolik", "Amaliy misollar", "Qanday bilim kerak?", "Bolalar uchun sodda"]
        },
        {
          morphType: 'paint_brush',
          badge: "04 / 06 • IJODIY TOPSHIRIQLAR",
          title: "MINI-QUIZ VA AMALIYOT",
          subtitle: "Qiziqishlarni Sinab Ko'rish",
          desc: "Videodan keyin qisqa 3-5 savolli mini-quiz yoki amaliy ijodiy topshiriq beriladi.",
          pills: ["🎯 Qiziqarli savollar", "🎨 Rasm chizish", "💡 O'z loyihasini tuzish", "🪙 +20 Gold Coin"]
        },
        {
          morphType: 'fav_star',
          badge: "05 / 06 • SEVIMLILAR",
          title: "MENING QIZIQISHLARIM",
          subtitle: "Yoqqan Kasblarni Saqlash",
          desc: "Bola o'ziga yoqqan kasblarni xatcho'piga saqlaydi va o'z qiziqish yo'nalishini shakllantiradi.",
          pills: ["❤️ Sevimli kasblar", "Profil xatcho'plari", "Qayta tomosha", "Do'stlar bilan ulashish"]
        },
        {
          morphType: 'compass_8point',
          badge: "06 / 06 • TAVSIYALAR",
          title: "OTA-ONAGA TAVSIYALAR",
          subtitle: "Farzandning Tug'ma Qobiliyatlari",
          desc: "Bola faolligi asosida Parent Panel'da ota-onaga bolaning qaysi sohalarga moyilligi borligi ko'rsatiladi.",
          pills: ["Qobiliyat xaritasi", "To'garak tavsiyalari", "Ijodiy tahlil", "Parent Gate"]
        }
      ]
    },

    'neptune': {
      shape: 'neptune',
      color: '#3b82f6',
      glow: 'rgba(59, 130, 246, 0.45)',
      border: 'rgba(59, 130, 246, 0.25)',
      slides: [
        {
          morphType: 'neptune_vortex',
          badge: "01 / 06 • EMOTSIYA",
          title: "NEPTUN SAYYORASI",
          subtitle: "Emotsional Savodxonlik Sayyorasi",
          desc: "Bolaning o'z hissiyotlarini tanishi, nomlashi va yozma ravishda ifodalashiga yordam beradigan xavfsiz makon.",
          pills: ["Hissiyot tanlash", "Kundalik", "Xavfsiz muhit", "Parent Panel"]
        },
        {
          morphType: 'smile_heart_face',
          badge: "02 / 06 • HISSIYOTNI TANISH",
          title: "HISSIYOTNI NOMLASH",
          subtitle: "'Hozir Qanday His Qilyapman?'",
          desc: "Bola yoshiga mos emotsiya belgisini tanlab, o'z ichki holatini ifoda qilishni o'rganadi.",
          pills: ["😊 Xursand", "😔 Xafa", "😠 Jahli chiqqan", "😰 Xavotirda", "😴 Charchagan", "🤩 Hayajonda"]
        },
        {
          morphType: 'open_journal',
          badge: "03 / 06 • SHAXSIY KUNDALIK",
          title: "MATNLI QAYD YOZISH",
          subtitle: "Hukm Qilinmaydigan Makon",
          desc: "Bola ko'nglidan o'tayotgan fikrlarni yozib qoldiradi. Neptun bolani aslo baholamaydi yoki jazolamaydi.",
          pills: ["📝 Shaxsiy yozuvlar", "Sana va vaqt", "Xavfsiz saqlash", "Xotirjamlik"]
        },
        {
          morphType: 'lotus_zen',
          badge: "04 / 06 • XAVFSIZLIK",
          title: "AI CHAT EMAS (XAVFSIZ)",
          subtitle: "Bolaning O'z Hissiyotlari Bilan Qolishi",
          desc: "Neptunda AI bola bilan bahslashmaydi yoki maslahat bermaydi. Bu bolaning o'z shaxsiy xavfsiz maydoni.",
          pills: ["Robot aralashmaydi", "Sof shaxsiy xona", "Emotsional erkinlik", "Hukmsiz muhit"]
        },
        {
          morphType: 'sine_wave_mood',
          badge: "05 / 06 • TAHLIL",
          title: "EMOTSIYALAR TARIXI",
          subtitle: "O'zgarishlar Grafigi",
          desc: "Bola oldingi kunlardagi kayfiyatini ko'rib, o'z kechinmalarini yaxshiroq tushuna boshlaydi.",
          pills: ["Haftalik kayfiyat", "Quvonchli kunlar", "O'zini anglash", "Emotsional savodxonlik"]
        },
        {
          morphType: 'lighthouse_beacon',
          badge: "06 / 06 • PARENT ADVISOR",
          title: "PARENT PANEL MASLAHATI",
          subtitle: "Ota-onaga Ehtiyotkor Tavsiyalar",
          desc: "Emotsional trendlar ota-onaga ko'rinadi. AI maslahatchi bolani qo'llab-quvvatlash bo'yicha tavsiya beradi.",
          pills: ["Emotsional xarita", "Ehtiyotkor maslahat", "Xavfsizlik signali", "Mehr va e'tibor"]
        }
      ]
    },

    'satellite': {
      shape: 'satellite',
      color: '#8b5cf6',
      glow: 'rgba(139, 92, 246, 0.45)',
      border: 'rgba(139, 92, 246, 0.25)',
      slides: [
        {
          morphType: 'satellite_body',
          badge: "01 / 04 • TEXNOLOGIYA",
          title: "SUN'IY YO'LDOSH",
          subtitle: "Kosmik Aloqa va Internet",
          desc: "Yer orbitasida 9,000 dan ortiq sun'iy yo'ldosh aylanmoqda. GPS, internet, televideniye va ob-havo bashorati vositasi.",
          pills: ["GPS Navigatsiya", "Global Internet", "Ob-havo", "Kosmik aloqa"]
        },
        {
          morphType: 'gps_satellite',
          badge: "02 / 04 • NAVIGATSIYA",
          title: "GPS VA XARITALAR",
          subtitle: "Pozitsiyani 1 Metrgacha Aniqlash",
          desc: "Har bir telefondagi xarita kamida 4 ta sun'iy yo'ldoshning signali orqali ishlaydi.",
          pills: ["🛰️ 4 ta yo'ldosh signali", "24 soat uzluksiz", "Dunyoni bilish", "Tezkor aloqa"]
        },
        {
          morphType: 'radar_dish',
          badge: "03 / 04 • METEOROLOGIYA",
          title: "OB-HAVO MONITORINGI",
          subtitle: "Iqlim va Bo'ronlar Tahlili",
          desc: "Meteorologik yo'ldoshlar bulutlar va shamollarni kuzatib, yomg'ir va qor yog'ishini oldindan aytib beradi.",
          pills: ["Bo'ron ogohlantirishi", "Harorat xaritasi", "Iqlim o'rganish", "Ekologiya"]
        },
        {
          morphType: 'space_telescope',
          badge: "04 / 04 • ILM-FAN",
          title: "JAMES WEBB VA HUBBLE",
          subtitle: "Koinotning Cheksiz Suratlari",
          desc: "Kosmik teleskoplar milliardlab yorug'lik yili uzoqdagi yangi yulduz va galaktikalarni kashf etadi.",
          pills: ["🔭 Kosmik teleskop", "Uzoq galaktikalar", "Koinot sirlari", "Kelajak texnologiyasi"]
        }
      ]
    },

    'astronaut': {
      shape: 'astronaut',
      color: '#ec4899',
      glow: 'rgba(236, 72, 153, 0.45)',
      border: 'rgba(236, 72, 153, 0.25)',
      slides: [
        {
          morphType: 'astronaut_full',
          badge: "01 / 04 • TADQIQOTCHI",
          title: "3D FAZOGIR",
          subtitle: "Kichik Alloma • Koinot Sayohatchisi",
          desc: "Koinotni tadqiq qiluvchi, sayyoralarga parvoz etuvchi dovyurak yosh olim va kashfiyotchi.",
          pills: ["Skafandr", "Vaznsizlik", "ISS Stansiyasi", "Jasorat"]
        },
        {
          morphType: 'cosmic_helmet',
          badge: "02 / 04 • SKAFANDR",
          title: "14 QATLAMLI HIMOYACHI",
          subtitle: "-150°C dan +120°C gacha Chidamli",
          desc: "Fazogir skafandri maxsus kislorod, bosim va harorat moslamalari bilan jihozlangan mustahkam kostyumdir.",
          pills: ["👨‍🚀 14 ta mustahkam qatlam", "8 soat kislorod", "Mikrometeorit himoyasi", "Ochiq faza"]
        },
        {
          morphType: 'floating_zero_g',
          badge: "03 / 04 • VAZNSIZLIK",
          title: "VAZNSIZLIK PARVOZI",
          subtitle: "Qush Kabi Erkin Suzish",
          desc: "Fazoda tortishish kuchi bo'lmagani sababli fazogirlar stansiya ichida erkin suzib yurishadi.",
          pills: ["Zero-G muhiti", "Qiziqarli tajribalar", "Suzuvchi suyuqliklar", "Kosmik uyqu"]
        },
        {
          morphType: 'supernova_star',
          badge: "04 / 04 • SHIOR",
          title: "ILM — CHEKSIZ KOINOT!",
          subtitle: "Kichik Alloma Bilan Koinotga",
          desc: "Har bir bola yosh olim va kashfiyotchi bo'lishi, orzular sari baland parvoz etishi mumkin!",
          pills: ["🌟 Bilim nuri", "🚀 Yangi marralar", "🏆 Kichik Alloma", "Kelajak senga bog'liq!"]
        }
      ]
    },

    'logo': {
      shape: 'logo',
      color: '#facc15',
      glow: 'rgba(250, 204, 21, 0.45)',
      border: 'rgba(250, 204, 21, 0.25)',
      slides: [
        {
          morphType: 'alloma_star_logo',
          badge: "01 / 04 • ASOSIY",
          title: "KICHIK ALLOMA",
          subtitle: "8 Sayyorali Rivojlanish Ekotizimi",
          desc: "7–11 yoshdagi bolalar uchun AI asosidagi ta'lim va rivojlanish ekotizimi. 8 ta sayyora = 8 ta rivojlanish yo'nalishi.",
          pills: ["8 ta Sayyora", "Gold Coin", "AI Tutor", "Parent Panel"]
        },
        {
          morphType: 'academic_triad',
          badge: "02 / 04 • YER & SATURN & URAN",
          title: "AKADEMIK BILIMLAR",
          subtitle: "AI Tutor, Matematika va Ingliz Tili",
          desc: "Yer sayyorasida AI Tutor darslarga yordam beradi, Saturnda matematika yechiladi, Uranda inglizcha so'zlar o'rganiladi.",
          pills: ["Yer: AI Tutor", "Saturn: Matematika", "Uran: English Vocab", "Gold Coin mukofoti"]
        },
        {
          morphType: 'activity_triad',
          badge: "03 / 04 • YUPITER & MARS & MERKURIY",
          title: "INTIZOM VA FAOLLIK",
          subtitle: "Rejalashtirish, Sport va Kasblar",
          desc: "Yupiterda kunlik reja tuziladi, Marsda jismoniy mashqlar bajariladi, Merkuriyda kelajak kasblari kashf qilinadi.",
          pills: ["Yupiter: Kunlik reja", "Mars: Jismoniy harakat", "Merkuriy: 8 ta kasb", "Sog'lom hayot"]
        },
        {
          morphType: 'store_emotions',
          badge: "04 / 04 • VENERA & NEPTUN",
          title: "DO'KON VA EMOTSIYA",
          subtitle: "Virtual Xaridlar va Hissiyotlar",
          desc: "Venerada Gold Coin sarflanadi, Neptunda esa bola o'z hissiyotlarini tushunib, xavfsiz qayd qilib boradi.",
          pills: ["Venera: Virtual do'kon", "Neptun: Emotsiyalar", "Parent Dashboard", "Do'stona muhit"]
        }
      ]
    }
  };

  let scene, camera, renderer, particleGeometry, particleMaterial, particleSystem;
  let currentPositions = new Float32Array(PARTICLE_COUNT * 3);
  let targetPositions = new Float32Array(PARTICLE_COUNT * 3);
  let currentColors = new Float32Array(PARTICLE_COUNT * 3);
  let targetColors = new Float32Array(PARTICLE_COUNT * 3);

  let isInitialized = false;
  let animationFrameId = null;
  let isDragging = false;
  let previousMousePosition = { x: 0, y: 0 };
  let rotationVelocity = { x: 0.001, y: 0.003 };

  let activePlanetKey = 'logo';
  let currentSlideIndex = 0;
  let isTransitioning = false;
  let lastScrollTime = 0;

  function createParticleTexture() {
    const c = document.createElement('canvas');
    c.width = 64; c.height = 64;
    const ctx = c.getContext('2d');
    const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.25, 'rgba(255,240,180,0.95)');
    g.addColorStop(0.55, 'rgba(160,220,255,0.45)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, 64, 64);
    const t = new THREE.Texture(c);
    t.needsUpdate = true;
    return t;
  }

  // MATHEMATICAL 3D PROCEDURAL GENERATORS FOR EVERY EXACT TOPIC
  function generatePreciseSlideShape(morphType, planetColor) {
    const positions = new Float32Array(PARTICLE_COUNT * 3);
    const colors = new Float32Array(PARTICLE_COUNT * 3);
    const isDesktop = window.innerWidth > 900;
    const xOff = isDesktop ? 36 : 0;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const idx = i * 3;
      let x = 0, y = 0, z = 0, r = 1, g = 1, b = 1;
      const u = Math.random(), v = Math.random();
      const theta = u * 2 * Math.PI, phi = Math.acos(2 * v - 1);

      switch(morphType) {
        // --- 1. ANIMAL PAW (Uran Slide 2) ---
        case 'animal_paw': {
          const pad = i % 5;
          if (pad === 0) {
            // Main big palm pad
            const a = Math.random() * Math.PI * 2;
            const rad = Math.sqrt(Math.random()) * 32;
            x = Math.cos(a) * rad;
            y = Math.sin(a) * rad * 0.8 - 14;
            z = (Math.random() - 0.5) * 16;
            r = 0.2; g = 0.95; b = 1.0;
          } else {
            // 4 toe pads
            const toeIdx = pad - 1;
            const toeAngle = -Math.PI * 0.75 + (toeIdx * Math.PI * 0.5);
            const toeDist = 38;
            const toeR = Math.sqrt(Math.random()) * 13;
            const a = Math.random() * Math.PI * 2;
            x = Math.cos(toeAngle) * toeDist + Math.cos(a) * toeR;
            y = Math.sin(toeAngle) * toeDist + Math.sin(a) * toeR + 18;
            z = (Math.random() - 0.5) * 14;
            r = 0.45; g = 1.0; b = 0.9;
          }
          break;
        }

        // --- 2. APPLE / FRUIT (Uran Slide 3) ---
        case 'apple_fruit': {
          if (i < PARTICLE_COUNT * 0.85) {
            // Apple body contour
            const rApple = 44 * (1 - 0.18 * Math.cos(theta) * Math.sin(phi));
            x = rApple * Math.sin(phi) * Math.cos(theta);
            y = rApple * Math.sin(phi) * Math.sin(theta) - 6;
            z = rApple * Math.cos(phi);
            r = 0.25; g = 0.92; b = 1.0;
          } else {
            // Apple leaf and stem
            const tLeaf = Math.random();
            x = 8 + tLeaf * 22;
            y = 38 + Math.sin(tLeaf * Math.PI) * 12;
            z = (Math.random() - 0.5) * 6;
            r = 0.1; g = 1.0; b = 0.5; // Emerald leaf
          }
          break;
        }

        // --- 3. MICROPHONE (Uran Slide 4) ---
        case 'microphone': {
          if (i < PARTICLE_COUNT * 0.5) {
            // Mic sphere head with grid
            const rad = 26;
            x = rad * Math.sin(phi) * Math.cos(theta);
            y = rad * Math.sin(phi) * Math.sin(theta) + 28;
            z = rad * Math.cos(phi);
            r = 0.3; g = 0.85; b = 1.0;
          } else if (i < PARTICLE_COUNT * 0.8) {
            // Mic body cylinder
            const h = (Math.random() - 0.5) * 44;
            const a = Math.random() * Math.PI * 2;
            x = Math.cos(a) * 12;
            y = h - 14;
            z = Math.sin(a) * 12;
            r = 0.2; g = 0.65; b = 0.95;
          } else {
            // Sound wave concentric arcs
            const arcR = 48 + Math.random() * 26;
            const arcA = -0.6 + Math.random() * 1.2;
            const side = (i % 2 === 0) ? 1 : -1;
            x = side * Math.cos(arcA) * arcR;
            y = 28 + Math.sin(arcA) * arcR * 0.7;
            z = (Math.random() - 0.5) * 10;
            r = 0.6; g = 0.95; b = 1.0;
          }
          break;
        }

        // --- 4. DIAMOND QUIZ (Uran Slide 5) ---
        case 'diamond_quiz': {
          const h = (Math.random() - 0.5) * 85;
          const rBase = (1 - Math.abs(h) / 52) * 54;
          const face = (i % 8) * (Math.PI / 4);
          x = Math.cos(face + (Math.random() - 0.5) * 0.3) * rBase;
          y = h;
          z = Math.sin(face + (Math.random() - 0.5) * 0.3) * rBase;
          r = 0.05; g = 0.92; b = 0.98;
          break;
        }

        // --- 5. INFINITY LOOP (Uran Slide 6) ---
        case 'infinity_loop': {
          const t = (i / PARTICLE_COUNT) * Math.PI * 2;
          const scale = 54;
          x = (scale * Math.cos(t)) / (1 + Math.sin(t) * Math.sin(t));
          y = (scale * Math.sin(t) * Math.cos(t)) / (1 + Math.sin(t) * Math.sin(t));
          z = Math.sin(t * 3) * 18 + (Math.random() - 0.5) * 8;
          r = 0.2; g = 0.98; b = 0.92;
          break;
        }

        // --- 6. NEURAL BRAIN (Yer Slide 2) ---
        case 'neural_brain': {
          const hemisphere = (i % 2 === 0) ? -1 : 1;
          const rad = 32 + Math.random() * 26;
          x = hemisphere * (14 + rad * Math.abs(Math.sin(phi) * Math.cos(theta)));
          y = rad * Math.sin(phi) * Math.sin(theta);
          z = rad * Math.cos(phi);
          if (i % 6 === 0) {
            x *= 1.35; y *= 1.35; z *= 1.35; // Firing synaptic bursts
            r = 1.0; g = 0.9; b = 0.3;
          } else {
            r = 0.2; g = 0.75; b = 1.0;
          }
          break;
        }

        // --- 7. CAMERA SCANNER (Yer Slide 3) ---
        case 'camera_scanner': {
          if (i < PARTICLE_COUNT * 0.45) {
            // Camera lens cylinder
            const rad = 28 + Math.random() * 8;
            const a = Math.random() * Math.PI * 2;
            x = Math.cos(a) * rad;
            y = Math.sin(a) * rad;
            z = (Math.random() - 0.5) * 20 + 20;
            r = 0.3; g = 0.8; b = 1.0;
          } else {
            // Laser scanning fan plane
            const py = -40 + Math.random() * 80;
            const px = (Math.random() - 0.5) * 90;
            x = px;
            y = py;
            z = -15 + Math.sin(px * 0.1) * 8;
            r = 0.15; g = 1.0; b = 0.5; // Green laser rays
          }
          break;
        }

        // --- 8. CLOCK 20:00 (Yer Slide 4) ---
        case 'clock_20min': {
          if (i < PARTICLE_COUNT * 0.7) {
            // Outer clock dial
            const a = Math.random() * Math.PI * 2;
            const rDial = 56 + (Math.random() - 0.5) * 8;
            x = Math.cos(a) * rDial;
            y = Math.sin(a) * rDial;
            z = (Math.random() - 0.5) * 10;
            r = 0.98; g = 0.85; b = 0.2;
          } else {
            // Hour hand and minute hand
            const isMinute = (i % 2 === 0);
            const handAngle = isMinute ? Math.PI / 2 : Math.PI * 0.15;
            const handLen = isMinute ? Math.random() * 44 : Math.random() * 28;
            x = Math.cos(handAngle) * handLen;
            y = Math.sin(handAngle) * handLen;
            z = 2;
            r = 1.0; g = 1.0; b = 1.0;
          }
          break;
        }

        // --- 9. MATH SYMBOLS +, ×, = (Saturn Slide 2) ---
        case 'math_symbols': {
          const sym = i % 3;
          if (sym === 0) {
            // Plus (+) sign on top left
            const isVert = (Math.random() > 0.5);
            x = -28 + (isVert ? (Math.random() - 0.5) * 6 : (Math.random() - 0.5) * 28);
            y = 24 + (isVert ? (Math.random() - 0.5) * 28 : (Math.random() - 0.5) * 6);
            z = (Math.random() - 0.5) * 10;
            r = 0.98; g = 0.8; b = 0.2;
          } else if (sym === 1) {
            // Multiply (×) sign on top right
            const t = (Math.random() - 0.5) * 26;
            const isDiag1 = (Math.random() > 0.5);
            x = 28 + (isDiag1 ? t : t);
            y = 24 + (isDiag1 ? t : -t);
            z = (Math.random() - 0.5) * 10;
            r = 0.98; g = 0.5; b = 0.15;
          } else {
            // Equals (=) sign on bottom center
            const isTopBar = (Math.random() > 0.5);
            x = (Math.random() - 0.5) * 36;
            y = -22 + (isTopBar ? 6 : -6);
            z = (Math.random() - 0.5) * 10;
            r = 1.0; g = 0.95; b = 0.3;
          }
          break;
        }

        // --- 10. RUBIK'S CUBE (Saturn Slide 3) ---
        case 'rubiks_cube': {
          const side = i % 6;
          const u1 = (Math.random() - 0.5) * 60;
          const u2 = (Math.random() - 0.5) * 60;
          if (side === 0) { x = 30; y = u1; z = u2; }
          else if (side === 1) { x = -30; y = u1; z = u2; }
          else if (side === 2) { y = 30; x = u1; z = u2; }
          else if (side === 3) { y = -30; x = u1; z = u2; }
          else if (side === 4) { z = 30; x = u1; y = u2; }
          else { z = -30; x = u1; y = u2; }
          r = 0.98; g = 0.75; b = 0.2;
          break;
        }

        // --- 11. LIGHTBULB (Saturn Slide 4) ---
        case 'lightbulb_idea': {
          if (i < PARTICLE_COUNT * 0.6) {
            // Bulb globe top
            const rad = 36;
            x = rad * Math.sin(phi) * Math.cos(theta);
            y = rad * Math.sin(phi) * Math.sin(theta) + 16;
            z = rad * Math.cos(phi);
            r = 1.0; g = 0.92; b = 0.25;
          } else if (i < PARTICLE_COUNT * 0.85) {
            // Screw base
            const h = -24 + Math.random() * 20;
            const a = Math.random() * Math.PI * 2;
            const rBase = 14 + (h + 24) * 0.3;
            x = Math.cos(a) * rBase;
            y = h;
            z = Math.sin(a) * rBase;
            r = 0.85; g = 0.88; b = 0.95;
          } else {
            // Filament radiant rays
            const a = Math.random() * Math.PI * 2;
            const rayDist = 48 + Math.random() * 24;
            x = Math.cos(a) * rayDist;
            y = 16 + Math.sin(a) * rayDist;
            z = (Math.random() - 0.5) * 8;
            r = 1.0; g = 0.8; b = 0.1;
          }
          break;
        }

        // --- 12. TROPHY CUP (Saturn Slide 5) ---
        case 'trophy_cup': {
          const py = (Math.random() - 0.5) * 80;
          if (py > 0) {
            // Cup bowl
            const rCup = 18 + py * 0.65;
            const a = Math.random() * Math.PI * 2;
            x = Math.cos(a) * rCup;
            y = py;
            z = Math.sin(a) * rCup;
            r = 1.0; g = 0.85; b = 0.15;
          } else if (py > -22) {
            // Stem
            const a = Math.random() * Math.PI * 2;
            x = Math.cos(a) * 8;
            y = py;
            z = Math.sin(a) * 8;
            r = 0.95; g = 0.75; b = 0.1;
          } else {
            // Base pedestal
            const rPed = 32 + (-22 - py) * 0.6;
            const a = Math.random() * Math.PI * 2;
            x = Math.cos(a) * rPed;
            y = py;
            z = Math.sin(a) * rPed;
            r = 1.0; g = 0.85; b = 0.2;
          }
          break;
        }

        // --- 13. STAIRS CHART (Saturn Slide 6) ---
        case 'stairs_chart': {
          const barIdx = Math.floor(Math.random() * 5); // 5 rising bars
          const barX = -36 + barIdx * 18;
          const barH = 20 + barIdx * 16;
          x = barX + (Math.random() - 0.5) * 12;
          y = -40 + Math.random() * barH;
          z = (Math.random() - 0.5) * 14;
          r = 0.4 + barIdx * 0.12; g = 0.85; b = 0.2 + barIdx * 0.15;
          break;
        }

        // --- 14. CHECKLIST / CLIPBOARD (Yupiter Slide 2) ---
        case 'clipboard_plan': {
          const px = (Math.random() - 0.5) * 58;
          const py = (Math.random() - 0.5) * 78;
          x = px;
          y = py;
          z = (Math.random() - 0.5) * 6;
          r = 0.98; g = 0.85; b = 0.25;
          break;
        }

        // --- 15. BIG CHECKMARK (Yupiter Slide 3) ---
        case 'big_checkmark': {
          const t = Math.random();
          if (t < 0.35) {
            // Left short stroke
            const subT = t / 0.35;
            x = -36 + subT * 18;
            y = 8 - subT * 26;
          } else {
            // Right long stroke
            const subT = (t - 0.35) / 0.65;
            x = -18 + subT * 54;
            y = -18 + subT * 56;
          }
          z = (Math.random() - 0.5) * 14;
          x += (Math.random() - 0.5) * 8;
          y += (Math.random() - 0.5) * 8;
          r = 0.15; g = 0.98; b = 0.45; // Glowing green check
          break;
        }

        // --- 16. FIRE STREAK (Yupiter Slide 4) ---
        case 'fire_streak': {
          const t = Math.random();
          const py = -40 + t * 85;
          const widthAtY = Math.sin(t * Math.PI) * (38 * (1 - t * 0.45));
          x = (Math.random() - 0.5) * 2 * widthAtY;
          y = py;
          z = (Math.random() - 0.5) * widthAtY * 0.6;
          r = 1.0; g = 0.3 + t * 0.6; b = 0.05; // Fire gradient: orange-yellow
          break;
        }

        // --- 17. ROYAL CROWN (Venera Slide 3) ---
        case 'royal_crown': {
          const a = Math.random() * Math.PI * 2;
          const py = -20 + Math.random() * 45;
          const peaks = Math.sin(a * 5) * 18;
          const rCrown = 38;
          x = Math.cos(a) * rCrown;
          y = py + (py > 0 ? peaks : 0);
          z = Math.sin(a) * rCrown;
          r = 1.0; g = 0.85; b = 0.15; // Golden crown
          break;
        }

        // --- 18. RUNNER ATHLETE (Mars Slide 3) ---
        case 'runner_athlete': {
          const bodyPart = i % 4;
          if (bodyPart === 0) {
            // Torso & head
            const h = (Math.random() - 0.5) * 36;
            x = h * 0.4 + 6;
            y = 12 + h;
            z = (Math.random() - 0.5) * 12;
          } else if (bodyPart === 1) {
            // Front leg
            const t = Math.random();
            x = 6 + t * 32;
            y = -4 - t * 30;
            z = 6;
          } else if (bodyPart === 2) {
            // Back leg
            const t = Math.random();
            x = -4 - t * 34;
            y = -4 - t * 24;
            z = -6;
          } else {
            // Arms in motion
            const t = (Math.random() - 0.5) * 44;
            x = 8 + t;
            y = 20 + Math.abs(t) * 0.4;
            z = t * 0.6;
          }
          r = 1.0; g = 0.25; b = 0.15; // Red runner
          break;
        }

        // --- 19. SMILE & HEART (Neptun Slide 2) ---
        case 'smile_heart_face': {
          const t = Math.random() * Math.PI * 2;
          const hx = 16 * Math.pow(Math.sin(t), 3);
          const hy = 13 * Math.cos(t) - 5 * Math.cos(2*t) - 2 * Math.cos(3*t) - Math.cos(4*t);
          const scale = 3.2;
          x = hx * scale + (Math.random() - 0.5) * 8;
          y = hy * scale + (Math.random() - 0.5) * 8;
          z = (Math.random() - 0.5) * 18;
          r = 0.3; g = 0.75; b = 1.0;
          break;
        }

        // --- 20. OPEN JOURNAL (Neptun Slide 3) ---
        case 'open_journal': {
          const side = (i % 2 === 0) ? -1 : 1;
          const pageW = Math.random() * 38;
          const pageH = (Math.random() - 0.5) * 58;
          const curve = Math.sin(pageW * 0.08) * 14;
          x = side * pageW;
          y = pageH;
          z = curve + (Math.random() - 0.5) * 4;
          r = 0.5; g = 0.85; b = 1.0;
          break;
        }

        // --- 21. LIGHTHOUSE BEACON (Neptun Slide 6) ---
        case 'lighthouse_beacon': {
          if (i < PARTICLE_COUNT * 0.6) {
            // Tower cone
            const py = -45 + Math.random() * 75;
            const rTower = 24 * (1 - (py + 45) / 100);
            const a = Math.random() * Math.PI * 2;
            x = Math.cos(a) * rTower;
            y = py;
            z = Math.sin(a) * rTower;
            r = 0.35; g = 0.75; b = 1.0;
          } else {
            // Radiant light beam fan
            const beamDist = 30 + Math.random() * 60;
            const beamAngle = -0.4 + Math.random() * 0.8;
            x = Math.cos(beamAngle) * beamDist + 10;
            y = 30 + Math.sin(beamAngle) * beamDist * 0.3;
            z = (Math.random() - 0.5) * 16;
            r = 1.0; g = 0.95; b = 0.4;
          }
          break;
        }

        // --- DEFAULT: Full Procedural Planet Sphere with Features ---
        default: {
          const rad = 58;
          x = rad * Math.sin(phi) * Math.cos(theta);
          y = rad * Math.sin(phi) * Math.sin(theta);
          z = rad * Math.cos(phi);
          r = 0.2; g = 0.8; b = 0.98;
        }
      }

      positions[idx] = x + xOff;
      positions[idx + 1] = y;
      positions[idx + 2] = z;

      colors[idx] = r;
      colors[idx + 1] = g;
      colors[idx + 2] = b;
    }

    return { positions, colors };
  }

  function initScene() {
    const container = document.getElementById('cosmic-3d-canvas-container');
    if (!container) return;
    container.innerHTML = '';

    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x020307, 0.002);
    camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 1, 2000);
    camera.position.z = 210;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const init = generatePreciseSlideShape('alloma_star_logo', '#facc15');
    currentPositions.set(init.positions);
    targetPositions.set(init.positions);
    currentColors.set(init.colors);
    targetColors.set(init.colors);

    particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute('position', new THREE.BufferAttribute(currentPositions, 3));
    particleGeometry.setAttribute('color', new THREE.BufferAttribute(currentColors, 3));
    particleMaterial = new THREE.PointsMaterial({
      size: 3.6,
      map: createParticleTexture(),
      vertexColors: true,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    });
    particleSystem = new THREE.Points(particleGeometry, particleMaterial);
    scene.add(particleSystem);

    // Stars
    const sp = new Float32Array(1600 * 3);
    for (let i = 0; i < 1600 * 3; i += 3) {
      sp[i] = (Math.random() - 0.5) * 1400;
      sp[i + 1] = (Math.random() - 0.5) * 1400;
      sp[i + 2] = (Math.random() - 0.5) * 1400;
    }
    const sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.BufferAttribute(sp, 3));
    scene.add(new THREE.Points(sg, new THREE.PointsMaterial({
      size: 1.8,
      color: 0xffffff,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    })));

    setupEventListeners(container);
    isInitialized = true;
  }

  function animate() {
    animationFrameId = requestAnimationFrame(animate);
    if (!particleSystem) return;

    const posA = particleGeometry.attributes.position;
    const colA = particleGeometry.attributes.color;
    const lerpSpeed = 0.06;
    for (let i = 0; i < PARTICLE_COUNT * 3; i++) {
      posA.array[i] += (targetPositions[i] - posA.array[i]) * lerpSpeed;
      colA.array[i] += (targetColors[i] - colA.array[i]) * lerpSpeed;
    }
    posA.needsUpdate = true;
    colA.needsUpdate = true;

    if (!isDragging) {
      particleSystem.rotation.y += rotationVelocity.y;
      particleSystem.rotation.x += rotationVelocity.x;
      rotationVelocity.x *= 0.98;
      rotationVelocity.y = rotationVelocity.y * 0.98 + 0.003 * 0.02;
    }
    renderer.render(scene, camera);
  }

  function setupEventListeners(container) {
    window.addEventListener('resize', onWindowResize);

    // 3D Canvas drag rotation
    container.addEventListener('mousedown', (e) => {
      isDragging = true;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener('mousemove', (e) => {
      if (!isDragging || !particleSystem) return;
      const dx = e.clientX - previousMousePosition.x;
      const dy = e.clientY - previousMousePosition.y;
      particleSystem.rotation.y += dx * 0.008;
      particleSystem.rotation.x += dy * 0.008;
      rotationVelocity.y = dx * 0.004;
      rotationVelocity.x = dy * 0.004;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    });
    window.addEventListener('mouseup', () => { isDragging = false; });

    let touchStartY = 0;
    container.addEventListener('touchstart', (e) => {
      isDragging = true;
      touchStartY = e.touches[0].clientY;
      previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (!isDragging || !particleSystem) return;
      const dx = e.touches[0].clientX - previousMousePosition.x;
      const dy = e.touches[0].clientY - previousMousePosition.y;
      particleSystem.rotation.y += dx * 0.008;
      particleSystem.rotation.x += dy * 0.008;
      rotationVelocity.y = dx * 0.004;
      rotationVelocity.x = dy * 0.004;
      previousMousePosition = { x: e.touches[0].clientX, y: e.touches[0].clientY };
    }, { passive: true });

    window.addEventListener('touchend', (e) => {
      isDragging = false;
      if (e.changedTouches && e.changedTouches.length > 0) {
        const diff = e.changedTouches[0].clientY - touchStartY;
        if (Math.abs(diff) > 45) {
          if (diff < 0) nextSlide();
          else prevSlide();
        }
      }
    });

    // MOUSE WHEEL: Smooth slide-based morphing like the video!
    window.addEventListener('wheel', (e) => {
      const modal = document.getElementById('cosmic-3d-modal');
      if (!modal || !modal.classList.contains('active')) return;
      
      const now = Date.now();
      if (now - lastScrollTime > 380) {
        lastScrollTime = now;
        if (e.deltaY > 0) {
          nextSlide();
        } else {
          prevSlide();
        }
      }
    }, { passive: true });

    // Keyboard navigation
    window.addEventListener('keydown', (e) => {
      const modal = document.getElementById('cosmic-3d-modal');
      if (!modal || !modal.classList.contains('active')) return;

      if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
        e.preventDefault();
        nextSlide();
      } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        prevSlide();
      } else if (e.key === 'Escape') {
        closeUniverse();
      }
    });
  }

  function onWindowResize() {
    if (!camera || !renderer) return;
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    const pData = PLANET_UNIVERSE[activePlanetKey] || PLANET_UNIVERSE['logo'];
    const slide = pData.slides[currentSlideIndex] || pData.slides[0];
    const ns = generatePreciseSlideShape(slide.morphType, pData.color);
    targetPositions.set(ns.positions);
  }

  function goToSlide(idx, direction = 'up') {
    const planetData = PLANET_UNIVERSE[activePlanetKey] || PLANET_UNIVERSE['logo'];
    if (!planetData.slides[idx] || isTransitioning) return;

    isTransitioning = true;
    currentSlideIndex = idx;
    const slide = planetData.slides[idx];

    // 3D Shockwave pulse: burst particles
    if (particleGeometry) {
      const pos = particleGeometry.attributes.position.array;
      for (let i = 0; i < PARTICLE_COUNT * 3; i += 3) {
        pos[i] += (Math.random() - 0.5) * 45;
        pos[i + 1] += (Math.random() - 0.5) * 45;
        pos[i + 2] += (Math.random() - 0.5) * 45;
      }
      particleGeometry.attributes.position.needsUpdate = true;
    }

    // Dynamic 3D Morph for THIS EXACT SLIDE TOPIC!
    const ns = generatePreciseSlideShape(slide.morphType, planetData.color);
    targetPositions.set(ns.positions);
    targetColors.set(ns.colors);

    // Apply CSS Variables for dynamic planet theme colors & glow
    const modal = document.getElementById('cosmic-3d-modal');
    if (modal) {
      modal.style.setProperty('--planet-color', planetData.color);
      modal.style.setProperty('--planet-glow', planetData.glow);
      modal.style.setProperty('--planet-border', planetData.border);
    }

    // Animate text slide exit & enter
    const block = document.getElementById('cosmic-text-block');
    const exitClass = direction === 'up' ? 'slide-exit-up' : 'slide-exit-down';
    const enterClass = direction === 'up' ? 'slide-enter-up' : 'slide-enter-down';

    if (block) {
      block.className = `cosmic-text-block ${exitClass}`;
    }

    setTimeout(() => {
      const set = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.innerText = val;
      };

      set('cosmic-slide-badge', slide.badge);
      set('cosmic-slide-title', slide.title);
      set('cosmic-slide-subtitle', slide.subtitle);
      set('cosmic-slide-desc', slide.desc);

      const grid = document.getElementById('cosmic-items-grid');
      if (grid && slide.pills) {
        grid.innerHTML = slide.pills.map((p, pIdx) => `
          <div class="cosmic-pill-tag" style="animation-delay: ${pIdx * 0.07}s">${p}</div>
        `).join('');
      }

      renderIndicators();

      if (block) {
        block.className = `cosmic-text-block ${enterClass}`;
      }
      setTimeout(() => { isTransitioning = false; }, 280);
    }, 180);
  }

  function renderIndicators() {
    const planetData = PLANET_UNIVERSE[activePlanetKey] || PLANET_UNIVERSE['logo'];
    const container = document.getElementById('cosmic-steps-indicator');
    if (!container) return;

    container.innerHTML = planetData.slides.map((_, i) => `
      <div class="cosmic-step-dot ${i === currentSlideIndex ? 'active' : ''}" onclick="Cosmic3D.goToSlide(${i})"></div>
    `).join('');

    const statusEl = document.getElementById('cosmic-scroll-status');
    if (statusEl) {
      statusEl.innerHTML = `<span>${currentSlideIndex + 1} / ${planetData.slides.length} • Skroll qiling</span>`;
    }
  }

  function nextSlide() {
    const planetData = PLANET_UNIVERSE[activePlanetKey] || PLANET_UNIVERSE['logo'];
    const nextIdx = (currentSlideIndex + 1) % planetData.slides.length;
    goToSlide(nextIdx, 'up');
  }

  function prevSlide() {
    const planetData = PLANET_UNIVERSE[activePlanetKey] || PLANET_UNIVERSE['logo'];
    const prevIdx = (currentSlideIndex - 1 + planetData.slides.length) % planetData.slides.length;
    goToSlide(prevIdx, 'down');
  }

  // ALWAYS STARTS AT SLIDE 0 FOR ANY PLANET!
  function openUniverse(rawKey = 'logo') {
    let key = (rawKey || 'logo').toString().toLowerCase().trim();
    if (key.includes('vener') || key === 'venus') key = 'venera';
    else if (key.includes('merkur') || key === 'mercury') key = 'mercury';
    else if (key.includes('yer') || key.includes('zamin') || key === 'earth') key = 'earth';
    else if (key.includes('yupiter') || key === 'jupiter') key = 'jupiter';
    else if (key.includes('saturn')) key = 'saturn';
    else if (key.includes('uran') || key === 'uranus') key = 'uran';
    else if (key.includes('mars')) key = 'mars';
    else if (key.includes('neptun') || key === 'neptune') key = 'neptune';
    else if (key.includes('sun') || key.includes('quyosh')) key = 'logo';
    else if (key.includes('satellit')) key = 'satellite';
    else if (key.includes('astronaut') || key.includes('fazogir')) key = 'astronaut';
    
    if (!PLANET_UNIVERSE[key]) key = 'logo';

    activePlanetKey = key;
    currentSlideIndex = 0; // Har doim 0-bosqichdan boshlanishi kafolatlangan!

    const modal = document.getElementById('cosmic-3d-modal');
    if (!modal) return;
    modal.classList.add('active');

    if (!isInitialized) {
      initScene();
    } else {
      onWindowResize();
    }

    if (!animationFrameId) animate();
    goToSlide(0, 'up');
  }

  function closeUniverse() {
    const modal = document.getElementById('cosmic-3d-modal');
    if (modal) modal.classList.remove('active');
  }

  return {
    open: openUniverse,
    close: closeUniverse,
    goToSlide: goToSlide,
    nextSlide: nextSlide,
    prevSlide: prevSlide
  };
})();

window.Cosmic3D = Cosmic3D;
window.openCosmicUniverse = (key = 'logo') => Cosmic3D.open(key);
window.closeCosmicUniverse = () => Cosmic3D.close();
window.nextCosmicSlide = () => Cosmic3D.nextSlide();
window.prevCosmicSlide = () => Cosmic3D.prevSlide();
