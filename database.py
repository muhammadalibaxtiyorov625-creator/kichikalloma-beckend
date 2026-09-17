import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Meta jadvali (Birinchi marta ochilganini tekshirish)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # 1. Sayyoralar jadvali (Planets - Rasmli)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS planets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            image TEXT DEFAULT '/images/planets/earth.svg',
            status TEXT DEFAULT 'active',
            is_blocked INTEGER DEFAULT 0,
            is_block INTEGER DEFAULT 0,
            gradient TEXT DEFAULT NULL,
            video TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Qulayliklar jadvali (Amenities)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS amenities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            icon TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Xabarlar jadvali (Messages)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 4. Jamoa jadvali (Teams)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL,
            description TEXT DEFAULT '',
            image TEXT DEFAULT '/images/team/member1.svg',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Agar teams jadvalida description bo'lmasa qo'shish
    cursor.execute("PRAGMA table_info(teams)")
    team_cols = [c["name"] for c in cursor.fetchall()]
    if "description" not in team_cols:
        cursor.execute("ALTER TABLE teams ADD COLUMN description TEXT DEFAULT ''")

    # Agar planets jadvalida qo'shimcha ustunlar bo'lmasa xavfsiz qo'shish
    cursor.execute("PRAGMA table_info(planets)")
    planet_cols = [c["name"] for c in cursor.fetchall()]
    if "is_blocked" not in planet_cols:
        cursor.execute("ALTER TABLE planets ADD COLUMN is_blocked INTEGER DEFAULT 0")
    if "is_block" not in planet_cols:
        cursor.execute("ALTER TABLE planets ADD COLUMN is_block INTEGER DEFAULT 0")
    if "gradient" not in planet_cols:
        cursor.execute("ALTER TABLE planets ADD COLUMN gradient TEXT DEFAULT NULL")
    if "video" not in planet_cols:
        cursor.execute("ALTER TABLE planets ADD COLUMN video TEXT DEFAULT NULL")

    # 5. Galereya jadvali (Gallery - Rasmlar to'plami)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT DEFAULT '',
            image TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Mobil Foydalanuvchilar (Mobile Users)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            passcode TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Agar users jadvali avval boshqa ustunlar bilan yaratilgan bo'lsa, xavfsiz ustun qo'shish
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [c["name"] for c in cursor.fetchall()]
    if "phone" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
    if "passcode" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN passcode TEXT")
    if "last_login" not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login DATETIME")

    # 7. OTP Kodlar jadvali (Mobile OTP Codes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_used INTEGER DEFAULT 0
        )
    """)

    # 8. Bolalar jadvali (Children Linked to Mobile User)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            year TEXT NOT NULL,
            gender TEXT NOT NULL,
            language TEXT DEFAULT 'uzb',
            avatar TEXT DEFAULT '/images/avatars/boy1.png',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Agar children jadvalida language va avatar ustunlari bo'lmasa xavfsiz qo'shish
    cursor.execute("PRAGMA table_info(children)")
    child_cols = [c["name"] for c in cursor.fetchall()]
    if "language" not in child_cols:
        cursor.execute("ALTER TABLE children ADD COLUMN language TEXT DEFAULT 'uzb'")
    if "avatar" not in child_cols:
        cursor.execute("ALTER TABLE children ADD COLUMN avatar TEXT DEFAULT '/images/avatars/boy1.png'")

    # 9. Farzand Faolligi va Vaqt Statistikasi (Child Activity & Screen Time)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            minutes_spent INTEGER DEFAULT 0,
            messages_count INTEGER DEFAULT 0,
            planet_id INTEGER DEFAULT 42,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE
        )
    """)

    # 10. AI Suhbat Tarixi (AI Chat History)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            audio_url TEXT DEFAULT NULL,
            planet_id INTEGER DEFAULT NULL,
            planet_name TEXT DEFAULT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # 11. Farzand Emotsiyalari va Kayfiyat Kundaligi (Neptune / Emotsiyalar Sayyorasi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_emotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            emotion_key TEXT NOT NULL,
            emotion_name TEXT NOT NULL,
            emoji TEXT NOT NULL DEFAULT '😊',
            color TEXT DEFAULT '#4FACFE',
            intensity INTEGER DEFAULT 3,
            note TEXT DEFAULT '',
            planet_id INTEGER DEFAULT 46,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Tekshirish: Baza birinchi marta yaratildimi?
    cursor.execute("SELECT value FROM system_meta WHERE key = 'seeded'")
    seeded_row = cursor.fetchone()

    if not seeded_row:
        # 1. Boshlang'ich 8 ta rasmli sayyoralar
        initial_planets = [
            ('Yer', 'Kognitiv ta\'lim — AI-ustoz bilan mustaqil fikrlash.', '/images/planets/earth.svg', 'active'),
            ('Mars', 'Jismoniy faollik — Video asosida harakat va mashqlar.', '/images/planets/mars.svg', 'active'),
            ('Uran', 'Ingliz tili — So\'z, talaffuz, test va mustahkamlash.', '/images/planets/cyan-rings.svg', 'active'),
            ('Venera', 'Virtual do\'kon — Oltin tangalar orqali buyumlar.', '/images/planets/coral.svg', 'active'),
            ('Neptun', 'Emotsional savodxonlik — Hissiyotlar daraxti va xotirjamlik.', '/images/planets/teal-moon.svg', 'active'),
            ('Saturn', 'Matematika va mantiq — Bosqichli masalalar va testlar.', '/images/planets/saturn.svg', 'active'),
            ('Merkuriy', 'Kelajak kasblari — Qiziqishlarni kashf etish va maqsad.', '/images/planets/purple.svg', 'active'),
            ('Yupiter', 'Taym-menejment — 20 daqiqa qoidasi va reja.', '/images/planets/deep-blue.svg', 'active')
        ]
        cursor.executemany(
            "INSERT INTO planets (title, description, image, status) VALUES (?, ?, ?, ?)",
            initial_planets
        )

        # 2. Boshlang'ich qulayliklar
        initial_amenities = [
            ('Ota-ona nazorati', 'Farzandingizning kunlik va haftalik faolligi, o\'rganishga sarflayotgan vaqti hamda umumiy rivojlanish darajasini aniq statistika va qulay hisobotlar orqali real vaqt rejimida kuzatib boring.', '', 'active'),
            ('Kichik odatlar, katta natijalar', 'Kundalik darslarni to\'g\'ri rejalashtirish, diqqat-e\'tiborni bir joyga jamlash va samarali tanaffuslarni tizimlashtirish orqali bolada barqaror o\'rganish ko\'nikmalarini shakllantiradi.', '', 'active'),
            ('Dars tayyorlashga yordam', 'Farzandingizga mantiqiy savollar va bosqichma-bosqich ko\'rsatmalar orqali masalaning tub mohiyatini tushunishga hamda mustaqil yechim topishga yo\'naltiradi.', '', 'active'),
            ('Xavfsiz raqamli muhit', 'Nomaqbul kontent va keraksiz chalg\'ituvchi omillardan to\'liq himoyalangan hudud: bola platformada erkin bilim kashf etadi va yangi narsalarni o\'rganadi, ota-ona esa uning xavfsizligidan ko\'ngli to\'q bo\'ladi.', '', 'active'),
            ('O\'z rivojlanish yo\'li', 'Har bir bolaning individual bilim darajasi va qobiliyatini hisobga olgan holda ortiqcha bosimsiz, o\'zining qulay tezligida va ishonch bilan o\'sadi.', '', 'active')
        ]
        cursor.executemany(
            "INSERT INTO amenities (title, description, icon, status) VALUES (?, ?, ?, ?)",
            initial_amenities
        )

        # 3. Boshlang'ich xabarlar
        initial_messages = [
            ('Ali Valiyev', '+998 90 123 45 67', 'Assalomu alaykum, sayyoralar dasturi bo\'yicha batafsil ma\'lumot olmoqchi edim.', 0),
            ('Dilnoza Karimova', '+998 93 987 65 43', 'Salom! Ota-ona nazorati qulayligi qanday ishlaydi?', 1),
            ('Javohir Toshmatov', '+998 99 555 12 34', 'Ta\'lim platformangiz juda zo\'r ishlangan ekan!', 0)
        ]
        cursor.executemany(
            "INSERT INTO messages (name, phone, message, is_read) VALUES (?, ?, ?, ?)",
            initial_messages
        )

        # 4. Boshlang'ich Jamoa a'zolari (Teams)
        initial_teams = [
            ('Shoxrux', 'Komiljonov', 'Founder, Project Manager', '/images/team/member1.svg'),
            ('Muhammadsodiq', 'Kozimov', 'Mobil dasturchi', '/images/team/member2.svg'),
            ('Jasurbek', 'Egamberdiyev', 'Filologiya fanlari doktori DSc', '/images/team/member3.svg'),
            ('Bobur', 'Qurbonov', 'UX/UI dizayner', '/images/team/member4.svg'),
            ('Oyatillo', 'Mahmudjonov', 'Grafik dizayner', '/images/team/member1.svg'),
            ('Muhammadali', 'Baxtiyorov', 'Dasturchi', '/images/team/member2.svg')
        ]
        cursor.executemany(
            "INSERT INTO teams (first_name, last_name, role, image) VALUES (?, ?, ?, ?)",
            initial_teams
        )

        # 5. Boshlang'ich Galereya rasmlari (Gallery)
        initial_gallery = [
            ('Interaktiv Dars Jarayoni', '/images/gallery/photo1.svg'),
            ('Mantiqiy O\'yinlar Mashg\'uloti', '/images/gallery/photo2.svg'),
            ('Ijodkorlik & San\'at To\'garagi', '/images/gallery/photo3.svg'),
            ('Rivojlanish Sayyoralari Ko\'rgazmasi', '/images/gallery/photo4.svg')
        ]
        cursor.executemany(
            "INSERT INTO gallery (title, image) VALUES (?, ?)",
            initial_gallery
        )

        cursor.execute("INSERT OR REPLACE INTO system_meta (key, value) VALUES ('seeded', '1')")

    # Mavjud bazadagi eski /img/ yo'llarini yangi /images/ ga to'g'rilash
    cursor.execute("UPDATE planets SET image = '/images/planets/earth.svg' WHERE image LIKE '%/img/earth%' OR image LIKE '%/planets/earth%'")
    cursor.execute("UPDATE planets SET image = '/images/planets/mars.svg' WHERE image LIKE '%/img/mars%' OR image LIKE '%/planets/mars%'")
    cursor.execute("UPDATE planets SET image = '/images/planets/cyan-rings.svg' WHERE image LIKE '%/img/uran%' OR image LIKE '%/planets/uran%'")
    cursor.execute("UPDATE planets SET image = '/images/planets/coral.svg' WHERE image LIKE '%/img/venera%' OR image LIKE '%/planets/venus%'")
    cursor.execute("UPDATE planets SET image = '/images/planets/teal-moon.svg' WHERE image LIKE '%/img/neptun%' OR image LIKE '%/planets/neptune%'")
    cursor.execute("UPDATE planets SET image = '/images/planets/saturn.svg' WHERE image LIKE '%/img/saturn%' OR image LIKE '%/planets/saturn%'")
    cursor.execute("UPDATE planets SET image = '/images/planets/purple.svg' WHERE image LIKE '%/img/merkuriy%' OR image LIKE '%/planets/mercury%'")
    cursor.execute("UPDATE planets SET image = '/images/planets/deep-blue.svg' WHERE image LIKE '%/img/jupiter%' OR image LIKE '%/planets/jupiter%'")

    cursor.execute("UPDATE teams SET image = '/images/team/member1.svg' WHERE image LIKE '%/img/team1%'")
    cursor.execute("UPDATE teams SET image = '/images/team/member2.svg' WHERE image LIKE '%/img/team2%'")
    cursor.execute("UPDATE teams SET image = '/images/team/member3.svg' WHERE image LIKE '%/img/team3%'")
    cursor.execute("UPDATE teams SET image = '/images/team/member4.svg' WHERE image LIKE '%/img/team4%'")
    cursor.execute("UPDATE teams SET image = '/images/team/member1.svg' WHERE image LIKE '%/img/team5%'")
    cursor.execute("UPDATE teams SET image = '/images/team/member2.svg' WHERE image LIKE '%/img/team6%'")

    # 11. FAQ (Ko'p so'raladigan savollar) jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            order_num INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tekshirish: FAQ jadvali bo'shmi? Bo'lsa boshlang'ich savollarni kiritamiz
    cursor.execute("SELECT COUNT(*) as cnt FROM faqs")
    faq_cnt = cursor.fetchone()["cnt"]
    if faq_cnt == 0:
        initial_faqs = [
            ("Kichik Alloma loyihasining asoschisi (founderi) va rahbari kim?", "Kichik Alloma loyihasining asoschisi, muallifi va bosh dasturchisi (Founder & Lead Developer, Project Manager) — Shoxrux Komiljonovdir (Komiljonov Shoxruxbek Komiljon o'g'li). Platforma 8 ta rivojlanish sayyorasi orqali bolalarga sun'iy intellektli kosmik ta'lim berish uchun yaratilgan. Rasmiy ma'lumotlar Vikipediya ensiklopediyasida e'lon qilingan: https://uz.wikipedia.org/w/index.php?title=Startup&oldid=6268714. Aloqa uchun: Telefon: +998 99 976 51 00, Email: kichikalloma@gmail.com, Veb-sayt: https://kichikalloma.uz", "active", 1),
            ("Kichik Alloma platformasi nima va u kimlar uchun mo'ljallangan?", "Kichik Alloma — 3 yoshdan 11 yoshgacha bo'lgan bolalarning aqliy, mantiqiy, nutqiy va ijodiy salohiyatini rivojlantiruvchi interaktiv ta'lim platformasidir. Platforma bolalarga sayyoralar bo'ylab qiziqarli o'yinlar, ertaklar, so'z boyligi va sun'iy intellekt orqali ta'lim beradi.", "active", 2),
            ("Alloma AI yordamchisi qanday ishlaydi va uning ovozli muloqot xususiyati bormi?", "Alloma AI — Google Gemini ilg'or sun'iy intellekt texnologiyasi asosida yaratilgan pedagogik yordamchidir. Bola unga mikrofon orqali ovozli savollar berishi, darslar haqida so'rashi, ertaklar eshitishi yoki yangi bilimlarni xavfsiz va tushunarli tilda o'rganishi mumkin.", "active", 3),
            ("Uran sayyorasida ingliz tilini qanday o'rganish mumkin (So'zlar, talaffuz va testlar)?", "Uran sayyorasi bolalarning chet tilini o'rganishi uchun mo'ljallangan bo'lib, 10 ta asosiy mavzu (Mevalar, Hayvonlar, Ranglar, Maktab, Oila va h.k.), har bir so'zning sof audio talaffuzi, rasmlar, transkripsiya va 4 ta variantli interaktiv test savollarini o'z ichiga oladi.", "active", 4),
            ("Ota-onalar farzandining ta'lim jarayonini qanday nazorat qiladi (Ota-onalar burchagi)?", "Maxsus himoyalangan 'Ota-onalar burchagi' orqali bolaning qaysi sayyoralarni o'rganganligi, kunlik sarflagan vaqti, test natijalari, so'z boyligi o'sishi va muvaffaqiyat hisobotlarini real vaqtda kuzatib borish mumkin.", "active", 5),
            ("Mobil ilovadan internet bo'lmaganda ham foydalanish mumkinmi (Offline rejim)?", "Ha! Yuklab olingan barcha sayyora darslari, audio ertaklar va ingliz tili so'zlari offline rejimda, internetsiz ham to'liq va uzluksiz ishlaydi. Sayr yoki safarda internet talab etilmaydi.", "active", 6)
        ]
        cursor.executemany(
            "INSERT INTO faqs (name, description, status, order_num) VALUES (?, ?, ?, ?)",
            initial_faqs
        )
        print("Boshlang'ich 6 ta FAQ savollari bazaga muvaffaqiyatli kiritildi.")

    # 12. Uran / Nutq va Til Sayyorasi — Kategoriyalar jadvali (Uran Categories)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uran_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_en TEXT DEFAULT '',
            name_ru TEXT DEFAULT '',
            image TEXT DEFAULT '/images/categories/fruits.png',
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            order_num INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 13. Uran / Nutq va Til Sayyorasi — So'zlar jadvali (Uran Words)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uran_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            word_uz TEXT NOT NULL,
            word_en TEXT NOT NULL,
            word_ru TEXT DEFAULT '',
            transcription TEXT DEFAULT '',
            part_of_speech TEXT DEFAULT 'noun',
            part_of_speech_uz TEXT DEFAULT 'Ot',
            image TEXT DEFAULT '',
            audio_url TEXT DEFAULT '',
            example_sentence TEXT DEFAULT '',
            example_translation TEXT DEFAULT '',
            order_num INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES uran_categories (id) ON DELETE CASCADE
        )
    """)

    # 13.1. Uran so'zlari jadvali migratsiyasi (part_of_speech va part_of_speech_uz)
    cursor.execute("PRAGMA table_info(uran_words)")
    uran_word_cols = [c["name"] for c in cursor.fetchall()]
    if "part_of_speech" not in uran_word_cols:
        cursor.execute("ALTER TABLE uran_words ADD COLUMN part_of_speech TEXT DEFAULT 'noun'")
    if "part_of_speech_uz" not in uran_word_cols:
        cursor.execute("ALTER TABLE uran_words ADD COLUMN part_of_speech_uz TEXT DEFAULT 'Ot'")

    # Ranglar va sifatlarni to'g'ri belgilash
    cursor.execute("""
        UPDATE uran_words 
        SET part_of_speech = 'adjective', part_of_speech_uz = 'Sifat' 
        WHERE category_id = 3 AND word_en IN ('Red', 'Blue', 'Green', 'Yellow', 'White', 'Black', 'Orange')
    """)

    # 14. Uran / Test Natijalari (Child Quiz Results)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_uran_quiz_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            score INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
            percentage REAL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # 14.1. Uran / Farzand O'rgangan So'zlari (Child Uran Learned Words)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_uran_learned_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            correct_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0,
            review_count INTEGER DEFAULT 1,
            last_learned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (word_id) REFERENCES uran_words (id) ON DELETE CASCADE,
            UNIQUE(child_id, word_id)
        )
    """)

    # Uran kategoriyalari bo'shmi? Bo'lsa boyitilgan boshlang'ich ma'lumotlar bilan to'ldiramiz
    cursor.execute("SELECT COUNT(*) as cnt FROM uran_categories")
    uran_cat_cnt = cursor.fetchone()["cnt"]
    if uran_cat_cnt == 0:
        initial_uran_data = [
            {
                "category": ("Meva va Sabzavotlar", "Fruits & Vegetables", "Фрукты и Овощи", "/images/categories/fruits.png", "Meva va sabzavotlarning inglizcha va o'zbekcha nomlarini o'rganamiz", "active", 1),
                "words": [
                    ("Olma", "Apple", "Яблоко", "[ˈæp.əl]", "An apple a day keeps the doctor away.", "Kuniga bitta olma shifokordan asraydi.", 1),
                    ("Banan", "Banana", "Банан", "[bəˈnæn.ə]", "Monkeys love sweet yellow bananas.", "Maymunlar shirin sariq bananlarni yaxshi ko'radi.", 2),
                    ("Apelsin", "Orange", "Апельсин", "[ˈɒr.ɪndʒ]", "Orange is full of healthy vitamin C.", "Apelsin foydali vitamin C ga boy.", 3),
                    ("Qulupnay", "Strawberry", "Клубника", "[ˈstrɔː.bər.i]", "Strawberries are red and very sweet.", "Qulupnaylar qizil va juda shirin.", 4),
                    ("Tarvuz", "Watermelon", "Арбуз", "[ˈwɔː.təˌmel.ən]", "Watermelon is a juicy summer fruit.", "Tarvuz sersuv yozgi mevadir.", 5),
                    ("Uzum", "Grape", "Виноград", "[ɡreɪp]", "Sweet grapes grow in big bunches.", "Shirin uzumlar katta shingil bo'lib o'sadi.", 6),
                    ("Limon", "Lemon", "Лимон", "[ˈlem.ən]", "Lemon has a fresh sour taste.", "Limon yangi nordon ta'mga ega.", 7),
                    ("Shaftoli", "Peach", "Персик", "[piːtʃ]", "Fresh peaches are soft and delicious.", "Yangi shaftolilar yumshoq va mazali.", 8),
                    ("Sabzi", "Carrot", "Морковь", "[ˈkær.ət]", "Rabbits like eating crunchy carrots.", "Quyonlar qarsildoq sabzini yeyishni yoqtiradi.", 9),
                    ("Pomidor", "Tomato", "Помидор", "[təˈmɑː.təʊ]", "Red tomatoes are used in fresh salad.", "Qizil pomidorlar yangi salatda ishlatiladi.", 10),
                    ("Bodring", "Cucumber", "Огурец", "[ˈkjuː.kʌm.bər]", "Cucumber is crispy, cool and green.", "Bodring qarsildoq, salqin va yashil.", 11),
                    ("Kartoshka", "Potato", "Картофель", "[pəˈteɪ.təʊ]", "Potatoes can be boiled or baked.", "Kartoshkani qaynatish yoki pishirish mumkin.", 12)
                ]
            },
            {
                "category": ("Hayvonlar olami", "Animals", "Животные", "/images/categories/animals.png", "Yovvoyi va uy hayvonlarining nomlarini o'rganamiz", "inactive", 2),
                "words": [
                    ("Sher", "Lion", "Лев", "[ˈlaɪ.ən]", "The lion is the king of the savanna.", "Sher savanna podshohidir.", 1),
                    ("Fil", "Elephant", "Слон", "[ˈel.ɪ.fənt]", "The elephant is the largest land animal.", "Fil quruqlikdagi eng katta hayvondir.", 2),
                    ("Yo'lbars", "Tiger", "Тигр", "[ˈtaɪ.ɡər]", "The tiger has beautiful striped fur.", "Yo'lbarsning go'zal chiziqli terisi bor.", 3),
                    ("Maymun", "Monkey", "Обезьяна", "[ˈmʌŋ.ki]", "The monkey swings cheerfully on branches.", "Maymun daraxt shoxlarida quvnoq uchadi.", 4),
                    ("Kuchuk", "Dog", "Собака", "[dɒɡ]", "The dog is a faithful friend to people.", "Kuchuk odamlarga sadoqatli do'stdir.", 5),
                    ("Mushuk", "Cat", "Кошка", "[kæt]", "The cat purrs softly when stroked.", "Mushuk silaganda ohista xurillaydi.", 6),
                    ("Ot", "Horse", "Лошадь", "[hɔːs]", "The horse gallops swiftly across the field.", "Ot dala bo'ylab chaqqon yuguradi.", 7),
                    ("Quyon", "Rabbit", "Кролик", "[ˈræb.ɪt]", "The rabbit has soft fur and long ears.", "Quyonning yumshoq yungi va uzun quloqlari bor.", 8),
                    ("Ayiq", "Bear", "Медведь", "[beər]", "The bear loves eating fresh forest berries.", "Ayiq yangi o'rmon mevalarini yeyishni yoqtiradi.", 9),
                    ("Jirafa", "Giraffe", "Жираф", "[dʒɪˈrɑːf]", "The giraffe reaches the highest green leaves.", "Jirafa eng baland yashil barglarga yetadi.", 10),
                    ("Bo'ri", "Wolf", "Волк", "[wʊlf]", "The grey wolf lives together in a pack.", "Kulrang bo'ri to'dada birga yashaydi.", 11),
                    ("Tulki", "Fox", "Лиса", "[fɒks]", "The cunning fox has a fluffy tail.", "Ayyor tulkining momiq dumi bor.", 12)
                ]
            },
            {
                "category": ("Ranglar va Shakllar", "Colors & Shapes", "Цвета и Формы", "/images/categories/colors.png", "Asosiy ranglar va geometrik shakllar", "inactive", 3),
                "words": [
                    ("Qizil", "Red", "Красный", "[red]", "The red apple is ripe and sweet.", "Qizil olma pishgan va shirin.", 1),
                    ("Ko'k", "Blue", "Синий", "[bluː]", "The clear summer sky is bright blue.", "Musaffo yozgi osmon yorqin ko'k rangda.", 2),
                    ("Yashil", "Green", "Зеленый", "[ɡriːn]", "Fresh green leaves grow on trees.", "Daraxtlarda yangi yashil barglar o'smoqda.", 3),
                    ("Sariq", "Yellow", "Желтый", "[ˈjel.əʊ]", "The morning sun shines bright yellow.", "Ertalabki quyosh yorqin sariq porlaydi.", 4),
                    ("Oq", "White", "Белый", "[waɪt]", "Soft white snow covers the garden.", "Yumshoq oq qor bog'ni qoplab olgan.", 5),
                    ("Qora", "Black", "Черный", "[blæk]", "The midnight sky is completely black.", "Yarim tunda osmon butunlay qora.", 6),
                    ("To'q sariq", "Orange", "Оранжевый", "[ˈɒr.ɪndʒ]", "Ripe oranges are bright orange.", "Pishgan apelsinlar yorqin to'q sariq.", 7),
                    ("Doira", "Circle", "Круг", "[ˈsɜː.kəl]", "The round wheel has a circle shape.", "Dumaloq g'ildirak doira shakliga ega.", 8),
                    ("Kvadrat", "Square", "Квадрат", "[skweər]", "A square box has four equal sides.", "Kvadrat qutining to'rtta teng tomoni bor.", 9),
                    ("Uchburchak", "Triangle", "Треугольник", "[ˈtraɪ.æŋ.ɡəl]", "A slice of yummy pizza is a triangle.", "Mazali pitssa bo'lagi uchburchakdir.", 10)
                ]
            },
            {
                "category": ("Oila va Inson", "Family & People", "Семья и Люди", "/images/categories/family.png", "Oila a'zolari va odamlar", "inactive", 4),
                "words": [
                    ("Ota", "Father", "Отец", "[ˈfɑː.ðər]", "My father helps me with my studies.", "Otam menga darslarimda yordam beradi.", 1),
                    ("Ona", "Mother", "Мать", "[ˈmʌð.ər]", "My mother gives the warmest hugs.", "Onam eng samimiy quchoq ochadi.", 2),
                    ("Aka / Uka", "Brother", "Брат", "[ˈbrʌð.ər]", "I love playing games with my brother.", "Men ukam bilan o'yin o'ynashni yaxshi ko'raman.", 3),
                    ("Opa / Singil", "Sister", "Сестра", "[ˈsɪs.tər]", "My sister shares her favorite toys.", "Singlim sevimli o'yinchoqlarini baham ko'radi.", 4),
                    ("Bobo", "Grandfather", "Дедушка", "[ˈɡræn.fɑː.ðər]", "Grandfather tells magical fairy tales.", "Bobom sehrli ertaklar aytib beradi.", 5),
                    ("Buvi", "Grandmother", "Бабушка", "[ˈɡræn.mʌð.ər]", "Grandmother bakes delicious honey cake.", "Buvim mazali asalli tort pishiradi.", 6),
                    ("O'g'il bola", "Boy", "Мальчик", "[bɔɪ]", "The brave boy solved the puzzle.", "Jasur o'g'il bola jumboqni yechdi.", 7),
                    ("Qiz bola", "Girl", "Девочка", "[ɡɜːl]", "The smart girl reads many books.", "Aqlli qiz bola ko'p kitob o'qiydi.", 8),
                    ("Chaqaloq", "Baby", "Малыш", "[ˈbeɪ.bi]", "The cute baby giggles cheerfully.", "Yoqimtoy chaqaloq quvnoq kuladi.", 9),
                    ("Do'st", "Friend", "Друг", "[frend]", "A true friend is always by your side.", "Haqiqiy do'st doimo yoningizda bo'ladi.", 10)
                ]
            },
            {
                "category": ("Maktab va O'qish", "School & Learning", "Школа и Учеба", "/images/categories/school.png", "Maktab anjomlari va ta'lim so'zlari", "inactive", 5),
                "words": [
                    ("Kitob", "Book", "Книга", "[bʊk]", "Reading books gives great wisdom.", "Kitob o'qish katta donolik beradi.", 1),
                    ("Ruchka", "Pen", "Ручка", "[pen]", "I write my exercises with a blue pen.", "Men mashqlarimni ko'k ruchkada yozaman.", 2),
                    ("Qalam", "Pencil", "Карандаш", "[ˈpen.səl]", "Draw a picture with this sharp pencil.", "Bu o'tkir qalam bilan rasm chizing.", 3),
                    ("Maktab", "School", "Школа", "[skuːl]", "We learn exciting knowledge at school.", "Biz maktabda ajoyib bilimlarni o'rganamiz.", 4),
                    ("O'qituvchi", "Teacher", "Учитель", "[ˈtiː.tʃər]", "Our teacher explains everything kindly.", "O'qituvchimiz hamma narsani mehribonlik bilan tushuntiradi.", 5),
                    ("O'quvchi", "Student", "Ученик", "[ˈstjuː.dənt]", "Every student listens carefully in class.", "Har bir o'quvchi darsda diqqat bilan tinglaydi.", 6),
                    ("Sumka", "Bag", "Сумка", "[bæɡ]", "Put your notebooks into your school bag.", "Daftarlaringizni maktab sumkangizga soling.", 7),
                    ("Parta", "Desk", "Парта", "[desk]", "Sit straight at your classroom desk.", "Sinf partangizda to'g'ri o'tiring.", 8),
                    ("Chizg'ich", "Ruler", "Линейка", "[ˈruː.lər]", "Use a ruler to draw a straight line.", "To'g'ri chiziq chizish uchun chizg'ichdan foydalaning.", 9),
                    ("O'chirg'ich", "Eraser", "Ластик", "[ɪˈreɪ.zər]", "An eraser cleans pencil marks neatly.", "O'chirg'ich qalam izlarini toza o'chiradi.", 10)
                ]
            },
            {
                "category": ("Kiyim-kechak", "Clothes", "Одежда", "/images/categories/clothes.png", "Kiyimlar va poyabzallar", "inactive", 6),
                "words": [
                    ("Ko'ylak", "Shirt", "Рубашка", "[ʃɜːt]", "I iron my clean white shirt.", "Men toza oq ko'ylagimni dazmollayman.", 1),
                    ("Futbolka", "T-shirt", "Футболка", "[ˈtiː.ʃɜːt]", "I wear a bright yellow T-shirt in summer.", "Yozda men yorqin sariq futbolka kiyaman.", 2),
                    ("Shim", "Pants", "Брюки", "[pænts]", "These warm pants are great for cold days.", "Bu issiq shim sovuq kunlar uchun ajoyib.", 3),
                    ("Poyabzal", "Shoes", "Обувь", "[ʃuːz]", "Tie your running shoes tightly.", "Yugurish poyabzalingizni mahkam bog'lang.", 4),
                    ("Bosh kiyim", "Hat", "Шляpa", "[hæt]", "Put on your hat on sunny days.", "Quyoshli kunlarda bosh kiyimingizni kiying.", 5),
                    ("Kurtka", "Jacket", "Куртка", "[ˈdʒæk.ɪt]", "Wear a thick jacket when going outside.", "Tashqariga chiqqanda qalin kurtka kiying.", 6),
                    ("Paypoq", "Socks", "Носки", "[sɒks]", "Soft cotton socks keep feet comfortable.", "Yumshoq paxta paypoqlar oyoqlarga qulaylik beradi.", 7),
                    ("Ko'ylak (ayollar)", "Dress", "Платье", "[dres]", "She wore a lovely pink dress.", "U chiroyli pushti ko'ylak kiyib oldi.", 8),
                    ("Etik", "Boots", "Сапоги", "[buːts]", "Rubber boots are perfect for rain.", "Rezina etiklar yomg'ir uchun juda mos.", 9),
                    ("Qo'lqop", "Gloves", "Перчатки", "[ɡlʌvz]", "Warm gloves protect hands from frost.", "Issiq qo'lqoplar qo'llarni sovuqdan asraydi.", 10)
                ]
            },
            {
                "category": ("Tabiat va Ob-havo", "Nature & Weather", "Природа и Погода", "/images/categories/nature.png", "Tabiat hodisalari va koinot", "inactive", 7),
                "words": [
                    ("Quyosh", "Sun", "Солнце", "[sʌn]", "The bright sun warms the Earth.", "Yorqin quyosh Yerni isitadi.", 1),
                    ("Oy", "Moon", "Луна", "[muːn]", "The silver moon shines at night.", "Kumushrang oy kechasi nur sochadi.", 2),
                    ("Yulduz", "Star", "Звезда", "[stɑːr]", "Stars twinkle brightly in the night sky.", "Yulduzlar tungi osmonda yorqin miltillaydi.", 3),
                    ("Daraxt", "Tree", "Дерево", "[triː]", "The green tree gives fresh oxygen.", "Yashil daraxt toza kislorod beradi.", 4),
                    ("Gul", "Flower", "Цветок", "[ˈflaʊ.ər]", "The red flower blooms in the garden.", "Qizil gul bog'da unib chiqadi.", 5),
                    ("Bulut", "Cloud", "Облако", "[klaʊd]", "Fluffy white clouds float in the sky.", "Momiq oq bulutlar osmonda suzadi.", 6),
                    ("Yomg'ir", "Rain", "Дождь", "[reɪn]", "Raindrops fall gently on the ground.", "Yomg'ir tomchilari yerga mayin yog'adi.", 7),
                    ("Qor", "Snow", "Снег", "[snəʊ]", "Children love playing in fresh snow.", "Bolalar yangi qorda o'ynashni yaxshi ko'radi.", 8),
                    ("Tog'", "Mountain", "Гора", "[ˈmaʊn.tɪn]", "The high mountain touches the blue sky.", "Baland tog' ko'k osmonga tegib turadi.", 9),
                    ("Dengiz", "Sea", "Море", "[siː]", "The blue sea is full of fascinating fish.", "Moviy dengiz ajoyib baliqlarga to'la.", 10)
                ]
            },
            {
                "category": ("Transport va Sayohat", "Transport & Travel", "Транспорт и Путешествия", "/images/categories/transport.png", "Transport vositalari va sayohat", "inactive", 8),
                "words": [
                    ("Mashina", "Car", "Машина", "[kɑːr]", "The fast electric car drives smoothly.", "Tezkor elektromobil ravon harakatlanadi.", 1),
                    ("Avtobus", "Bus", "Автобус", "[bʌs]", "The yellow bus carries passengers safely.", "Sariq avtobus yo'lovchilarni xavfsiz tashiydi.", 2),
                    ("Samolyot", "Airplane", "Самолет", "[ˈeə.pleɪn]", "The airplane flies high above the clouds.", "Samolyot bulutlardan balandda uchadi.", 3),
                    ("Poezd", "Train", "Поезд", "[treɪn]", "The fast train moves on strong steel rails.", "Tezkor poezd mustahkam po'lat relslarda yuradi.", 4),
                    ("Velosiped", "Bicycle", "Велосипед", "[ˈbaɪ.sɪ.kəl]", "Riding a bicycle is very good for health.", "Velosiped minish salomatlik uchun juda foydali.", 5),
                    ("Kema", "Ship", "Корабль", "[ʃɪp]", "The large ship crosses the deep ocean.", "Katta kema chuqur okeanni kesib o'tadi.", 6),
                    ("Vertolyot", "Helicopter", "Вертолет", "[ˈhel.ɪˌkɒp.tər]", "The rescue helicopter lands quickly.", "Qutqaruv vertolyoti tezda qo'nadi.", 7),
                    ("Raketa", "Rocket", "Ракета", "[ˈrɒk.ɪt]", "The space rocket journeys to distant planets.", "Koinot raketasi olis sayyoralarga yo'l oladi.", 8),
                    ("Qayiq", "Boat", "Лодка", "[bəʊt]", "We paddle a small boat on the quiet lake.", "Biz sokin ko'lda kichik qayiqda suzamiz.", 9),
                    ("Taksi", "Taxi", "Такси", "[ˈtæk.si]", "The yellow taxi arrived on time.", "Sariq taksi o'z vaqtida yetib keldi.", 10)
                ]
            },
            {
                "category": ("Uy va Buyumlar", "Home & Objects", "Дом и Вещи", "/images/categories/home.png", "Uy-ro'zg'or buyumlari va jihozlar", "inactive", 9),
                "words": [
                    ("Uy", "House", "Дом", "[haʊs]", "Our warm house is very welcoming.", "Bizning issiq uyimiz juda mehmondo'st.", 1),
                    ("Xona", "Room", "Комната", "[ruːm]", "My bright room is tidy and organized.", "Mening yorug' xonam ozoda va tartibli.", 2),
                    ("Eshik", "Door", "Дверь", "[dɔːr]", "Please close the room door quietly.", "Iltimos, xona eshigini ohista yoping.", 3),
                    ("Deraza", "Window", "Окно", "[ˈwɪn.dəʊ]", "Fresh breeze comes through the open window.", "Ochiq derazadan toza shabada keladi.", 4),
                    ("Stol", "Table", "Стол", "[ˈteɪ.bəl]", "We enjoy dinner together at the big table.", "Biz katta stolda birga kechki ovqat qilamiz.", 5),
                    ("Stul", "Chair", "Стул", "[tʃeər]", "Sit down on this comfortable chair.", "Bu qulay stulga o'tiring.", 6),
                    ("Karavot", "Bed", "Кровать", "[bed]", "Sleep peacefully in your cozy bed.", "Shinam karavotingizda tinch uxlang.", 7),
                    ("Soat", "Clock", "Часы", "[klɒk]", "The clock on the wall shows the exact time.", "Devordagi soat aniq vaqtni ko'rsatadi.", 8),
                    ("Chiroq", "Lamp", "Лампа", "[læmp]", "Turn on the reading lamp for your homework.", "Uy vazifangiz uchun dars chirog'ini yoqing.", 9),
                    ("Finjon", "Cup", "Чашка", "[kʌp]", "Drink sweet warm cocoa from your mug.", "Finjoningizdan shirin iliq kakao iching.", 10)
                ]
            },
            {
                "category": ("Kasblar", "Professions", "Профессии", "/images/categories/professions.png", "Kasblar va mutaxassisliklar", "inactive", 10),
                "words": [
                    ("Shifokor", "Doctor", "Врач", "[ˈdɒk.tər]", "The doctor helps people stay healthy.", "Shifokor odamlarga sog'lom bo'lishga yordam beradi.", 1),
                    ("O'qituvchi", "Teacher", "Учитель", "[ˈtiː.tʃər]", "The teacher inspires students to learn.", "O'qituvchi o'quvchilarni o'rganishga ilhomlantiradi.", 2),
                    ("Uchuvchi", "Pilot", "Пилот", "[ˈpaɪ.lət]", "The pilot flies airplanes to other countries.", "Uchuvchi samolyotlarni boshqa davlatlarga boshqaradi.", 3),
                    ("Kosmonavt", "Astronaut", "Космонавт", "[ˈæs.trə.nɔːt]", "The astronaut explores the universe in space.", "Kosmonavt koinotda borliqni tadqiq qiladi.", 4),
                    ("Politsiya", "Police", "Полицейский", "[pəˈliːs]", "Police officers protect our safety every day.", "Politsiya xodimlari har kuni xavfsizligimizni himoya qiladi.", 5),
                    ("O't o'chiruvchi", "Firefighter", "Пожарный", "[ˈfaɪəˌfaɪ.tər]", "The brave firefighter puts out fires.", "Jasur o't o'chiruvchi olovni o'chiradi.", 6),
                    ("Oshpaz", "Chef", "Повар", "[ʃef]", "The master chef cooks delicious food.", "Usta oshpaz mazali taomlar tayyorlaydi.", 7),
                    ("Rassom", "Artist", "Художник", "[ˈɑː.tɪst]", "The talented artist paints lively portraits.", "Iqtidorli rassom jonli portretlar chizadi.", 8),
                    ("Quruvchi", "Builder", "Строитель", "[ˈbɪl.dər]", "Builders construct sturdy new houses.", "Quruvchilar mustahkam yangi uylar qurishadi.", 9),
                    ("Haydovchi", "Driver", "Водитель", "[ˈdraɪ.vər]", "The driver drives passenger buses safely.", "Haydovchi yo'lovchi avtobuslarini xavfsiz boshqaradi.", 10)
                ]
            }
        ]

        for item in initial_uran_data:
            cat_tuple = item["category"]
            cursor.execute(
                "INSERT INTO uran_categories (name, name_en, name_ru, image, description, status, order_num) VALUES (?, ?, ?, ?, ?, ?, ?)",
                cat_tuple
            )
            cat_id = cursor.lastrowid
            cat_image = cat_tuple[3]
            words_to_insert = [
                (cat_id, w[0], w[1], w[2], w[3], cat_image, "", w[4], w[5], w[6])
                for w in item["words"]
            ]
            cursor.executemany(
                "INSERT INTO uran_words (category_id, word_uz, word_en, word_ru, transcription, image, audio_url, example_sentence, example_translation, order_num) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                words_to_insert
            )
        print("Boshlang'ich Uran (Nutq va Til) kategoriyalari va so'zlari muvaffaqiyatli kiritildi.")

    # 15. Farzand Tangalari va Balansi (Child Coins & Balance)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_coins (
            child_id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            total_coins INTEGER DEFAULT 0,
            lifetime_coins INTEGER DEFAULT 0,
            streak_days INTEGER DEFAULT 1,
            last_daily_bonus_date TEXT DEFAULT '',
            level INTEGER DEFAULT 1,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # 16. Tangalar Tranzaksiyalari Tarixi (Coin Transactions Ledger)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coin_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            source TEXT DEFAULT 'general',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # 17. Tangalar Do'koni Mahsulotlari (Coin Shop Items)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coin_shop_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_en TEXT DEFAULT '',
            title_ru TEXT DEFAULT '',
            description TEXT DEFAULT '',
            category TEXT NOT NULL DEFAULT 'avatar',
            cost_coins INTEGER NOT NULL DEFAULT 50,
            image TEXT DEFAULT '',
            icon TEXT DEFAULT '🎁',
            is_active INTEGER DEFAULT 1,
            order_num INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 18. Bolaning Sotib Olgan Buyumlari va Nishonlari (Child Purchased Items / Inventory)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_purchased_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            is_equipped INTEGER DEFAULT 0,
            purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES coin_shop_items (id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # 19. Kunlik Topshiriqlar va Missiyalar (Daily Missions / Quests)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_missions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_en TEXT DEFAULT '',
            title_ru TEXT DEFAULT '',
            description TEXT DEFAULT '',
            reward_coins INTEGER NOT NULL DEFAULT 10,
            icon TEXT DEFAULT '🎯',
            action_type TEXT NOT NULL,
            target_count INTEGER DEFAULT 1,
            order_num INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 20. Bolaning Kunlik Missiya Jarayoni (Child Mission Progress)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_mission_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            mission_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            current_count INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0,
            is_claimed INTEGER DEFAULT 0,
            claimed_at DATETIME DEFAULT NULL,
            FOREIGN KEY (mission_id) REFERENCES daily_missions (id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    # Do'kon mahsulotlari bo'shmi? Bo'lsa boshlang'ich qiziqarli mukofotlar bilan to'ldiramiz
    cursor.execute("SELECT COUNT(*) as cnt FROM coin_shop_items")
    shop_cnt = cursor.fetchone()["cnt"]
    if shop_cnt == 0:
        initial_shop_items = [
            ("Kosmik Astronavt Shlemi", "Space Astronaut Helmet", "Космический Шлем Астронавта", "Koinot bo'ylab sayohat uchun maxsus yaltiroq himoya shlemi", "avatar", 50, "/images/shop/astronaut_helmet.png", "🧑‍🚀", 1, 1),
            ("Oltin Alloma Toji", "Golden Alloma Crown", "Золотая Корона Алломы", "Eng ko'p kitob o'qigan va darslarni yaxshi o'zlashtirgan alloma toji", "avatar", 80, "/images/shop/gold_crown.png", "👑", 1, 2),
            ("Sehrli Bilimdon Ko'zoynagi", "Magic Scholar Glasses", "Волшебные Очки Знатока", "Barcha jumboqlarni bir zumda yechishga yordam beruvchi sehrli ko'zoynak", "avatar", 40, "/images/shop/smart_glasses.png", "👓", 1, 3),
            ("Kichik Qahramon Qanotlari", "Little Hero Wings", "Крылья Маленького Героя", "Yulduzlararo parvoz qilish uchun quvnoq nurli qanotlar", "avatar", 70, "/images/shop/hero_wings.png", "🪽", 1, 4),
            ("Koinot Bilimdoni Nishoni", "Space Explorer Badge", "Значок Космического Исследователя", "Barcha sayyoralarni ziyorat qilganlik uchun beriladigan maxsus nishon", "badge", 30, "/images/shop/badge_explorer.png", "🎖️", 1, 5),
            ("Nutq Ustasi Oltin Medali", "Speech Master Gold Medal", "Золотая Медаль Мастера Речи", "Uran sayyorasida 50 dan ortiq so'zni to'liq yod olganlik uchun medal", "badge", 60, "/images/shop/badge_speech.png", "🥇", 1, 6),
            ("Tezkor Mars Raketasi", "Super Mars Rocket", "Скоростная Ракета Марс", "Mobil ilova bosh sahifasida uchib yuruvchi interaktiv kosmik kema", "toy", 90, "/images/shop/toy_rocket.png", "🚀", 1, 7),
            ("Neon Yulduzli Koinot Mavzusi", "Neon Stars Space Theme", "Неоновая Космическая Тема", "Mobil ilova interfeysini yorqin neon yulduzli koinot ko'rinishiga o'tkazish", "planet_theme", 100, "/images/shop/theme_neon.png", "🌌", 1, 8),
            ("Sehrli Musiqiy Chodir", "Magic Musical Tent", "Волшебный Музыкальный Шатёр", "Darslarni quvnoq va sehrli kosmik kuylar jo'rligida bajarish effekti", "sound", 45, "/images/shop/sound_magic.png", "🎵", 1, 9)
        ]
        cursor.executemany(
            "INSERT INTO coin_shop_items (title, title_en, title_ru, description, category, cost_coins, image, icon, is_active, order_num) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            initial_shop_items
        )
        print("Boshlang'ich 9 ta tangalar do'koni mahsulotlari kiritildi.")

    # Kunlik topshiriqlar (Daily Missions) bo'shmi? Bo'lsa kiritamiz
    cursor.execute("SELECT COUNT(*) as cnt FROM daily_missions")
    mission_cnt = cursor.fetchone()["cnt"]
    if mission_cnt == 0:
        initial_missions = [
            ("Bugun ilovaga kirish", "Daily Login", "Ежедневный вход в приложение", "Har kuni mobil ilovani ochib ilm o'rganing va bonus tangalarga ega bo'ling", 10, "✨", "login", 1, 1, 1),
            ("Alloma AI bilan suhbatlashish", "Chat with Alloma AI", "Пообщаться с Аллома AI", "Sun'iy intellektga bitta qiziqarli savol bering yoki ovozli gaplashing", 15, "🤖", "chat_ai", 1, 2, 1),
            ("Uran sayyorasida test topshirish", "Complete Uran Quiz", "Пройти тест на планете Уран", "Ingliz tili so'z boyligi bo'yicha 1 ta testni a'lo bahoga yeching", 25, "🏆", "uran_quiz", 1, 3, 1),
            ("Bugungi kayfiyatni belgilash", "Record Daily Emotion", "Отметить сегодняшнее настроение", "Neptun sayyorasida bugungi hissiyotingizni qayd eting", 10, "😊", "emotion", 1, 4, 1),
            ("5 ta yangi so'z o'rganish", "Learn 5 New Words", "Выучить 5 новых слов", "Lug'atdan yangi 5 ta so'zning ovozli talaffuzini eshiting", 20, "📚", "learn_words", 5, 5, 1)
        ]
        cursor.executemany(
            "INSERT INTO daily_missions (title, title_en, title_ru, description, reward_coins, icon, action_type, target_count, order_num, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            initial_missions
        )
        print("Boshlang'ich 5 ta kunlik missiyalar kiritildi.")

    # 21. Kutubxona Kategoriyalari jadvali (Library Categories)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS library_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_en TEXT DEFAULT '',
            name_ru TEXT DEFAULT '',
            slug TEXT UNIQUE NOT NULL,
            icon TEXT DEFAULT '📚',
            order_num INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 22. Kutubxona Kitoblari jadvali (Library Books & Audiobooks)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS library_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            cover_image TEXT NOT NULL,
            description TEXT NOT NULL,
            content TEXT DEFAULT '',
            audio_url TEXT DEFAULT '',
            video_url TEXT DEFAULT '',
            duration_seconds INTEGER DEFAULT 0,
            duration_formatted TEXT DEFAULT '12:52',
            target_age TEXT DEFAULT '7-12 yosh',
            is_featured INTEGER DEFAULT 0,
            section TEXT DEFAULT 'eng-sara',
            listen_count INTEGER DEFAULT 0,
            likes_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'active',
            order_num INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES library_categories (id) ON DELETE CASCADE
        )
    """)

    # library_books jadvalida video_url ustuni mavjudligini tekshirish va xavfsiz qo'shish
    cursor.execute("PRAGMA table_info(library_books)")
    lib_book_cols = [c["name"] for c in cursor.fetchall()]
    if "video_url" not in lib_book_cols:
        cursor.execute("ALTER TABLE library_books ADD COLUMN video_url TEXT DEFAULT ''")

    # 23. Farzandning Tinglash / O'qish Progressi (Library Book Progress)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS library_book_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            progress_seconds INTEGER DEFAULT 0,
            progress_formatted TEXT DEFAULT '00:00',
            is_completed INTEGER DEFAULT 0,
            completed_at DATETIME DEFAULT NULL,
            last_listened_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES library_books (id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(child_id, book_id)
        )
    """)

    # 24. Farzandning Sevimli Kitoblari (Library Favorites)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS library_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES library_books (id) ON DELETE CASCADE,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(child_id, book_id)
        )
    """)

    # Kutubxona kategoriyalari bo'shmi? Bo'lsa kiritamiz
    cursor.execute("SELECT COUNT(*) as cnt FROM library_categories")
    lib_cat_cnt = cursor.fetchone()["cnt"]
    if lib_cat_cnt == 0:
        initial_lib_categories = [
            ("Barchasi", "All", "Все", "all", "🌟", 1, 1),
            ("Tabiat", "Nature", "Природа", "tabiat", "🌿", 2, 1),
            ("Hayvonlar", "Animals", "Животные", "hayvonlar", "🦁", 3, 1),
            ("Tarix", "History", "История", "tarix", "🏛️", 4, 1),
            ("Fan", "Science", "Наука", "fan", "🚀", 5, 1),
            ("Sarguzasht", "Adventure", "Приключения", "sarguzasht", "🧭", 6, 1),
            ("Ertaklar", "Fairy Tales", "Сказки", "ertaklar", "✨", 7, 1),
            ("Odob-axloq", "Morals", "Нравственность", "odob-axloq", "❤️", 8, 1)
        ]
        cursor.executemany(
            "INSERT INTO library_categories (name, name_en, name_ru, slug, icon, order_num, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)",
            initial_lib_categories
        )
        print("Boshlang'ich 8 ta kutubxona kategoriyalari kiritildi.")

    # Kutubxona kitoblari bo'shmi? Bo'lsa kiritamiz
    cursor.execute("SELECT COUNT(*) as cnt FROM library_books")
    lib_book_cnt = cursor.fetchone()["cnt"]
    if lib_book_cnt == 0:
        # Kategoriya ID larini olish
        cursor.execute("SELECT id, slug FROM library_categories")
        cat_map = {row["slug"]: row["id"] for row in cursor.fetchall()}

        sariq_dev_desc = (
            "Qissaning bosh qahramoni Hoshimjon o'qishni va dars qilishni yoqtirmaydigan, barcha ishni ertaga tashlaydigan dangasa bola. "
            "Tasodif tufayli u Sehrli qishloqdan kelgan Sariq dev bilan tanishib qoladi va uning yordamida o'zining barcha muammolarini osonlikcha hal qilmoqchi bo'ladi. "
            "Biroq tez orada dangasalik va oson yo'l bilan erishilgan muvaffaqiyatlar faqat boshni baloga qo'yishini tushunib yetadi. "
            "Kitob bolalarga mehnatsevarlik, halollik va ilmning muhimligini qiziqarli va ibratli tarzda o'rgatadi."
        )

        sariq_dev_content = (
            "1-bob. Sehrli shlyapa va dangasa Hoshimjon.\n\n"
            "Mening ismim Hoshimjon. Rostini aytsam, o'qishga unchalik xushim yo'q edi. Ertalab onam uyg'otganida yana besh daqiqa deb yotishni, "
            "kundalik darslarni keyinga qoldirishni yaxshi ko'rardim. Ammo bir kuni aql bovar qilmas mo'jiza yuz berdi. "
            "Sehrli qishloqdan kelgan Sariq dev mening do'stim bo'lib qoldi! U menga har qanday darsni o'qimasdan bilib olishim mumkinligini aytdi. "
            "Lekin o'z mehnating bilan o'rganilmagan bilim hech qanday baxt keltirmasligini tez orada anglab yetdim..."
        )

        initial_lib_books = [
            (
                cat_map.get("sarguzasht", 6),
                "Sariq devni minib",
                "Xudoyberdi To'xtaboyev",
                "/images/library/sariq_devni_minib.png",
                sariq_dev_desc,
                sariq_dev_content,
                "/audio/library/sariq_devni_minib.mp3",
                772,
                "12:52",
                "7-12 yosh",
                1,
                "sarguzasht",
                1280,
                342,
                "active",
                1
            ),
            (
                cat_map.get("tabiat", 2),
                "Fasllar",
                "Muallif",
                "/images/library/fasllar.png",
                "Tabiatning to'rt go'zal fasli — bahor nafasi, yozgi quyosh nurlari, oltin kuz va oppoq qorli qishning ajoyib sir-asrorlari haqidagi maftunkor bolalar kitobi.",
                "1-bob. Fasllar almashinuvi.\nBahor kelishi bilan tabiat uyg'onadi, daraxtlar kurtak yozadi. Yozda mevalar g'arq pishadi, kuzda esa barglar xazon bo'lib zaminni oltin rangga bo'yaydi. Qish o'zining oppoq qori bilan barcha tomonni toza libosga buraydi.",
                "/audio/library/fasllar.mp3",
                540,
                "09:00",
                "5-10 yosh",
                1,
                "eng-sara",
                940,
                215,
                "active",
                2
            ),
            (
                cat_map.get("sarguzasht", 6),
                "Shum bola",
                "G'afur G'ulom",
                "/images/library/shum_bola.png",
                "O'zbek bolalar adabiyotining durdona asari. Chaqqon, zukko va har qanday murakkab vaziyatdan quvnoq aqli bilan chiqib ketadigan bolakayning qiziqarli sarguzashtlari.",
                "E-e, xudo xayringizni bersin, qorako'zlarim! Men qariyb ellik yoshga kirganimda boshimdan kechirgan bu voqealarni yozayapman...",
                "/audio/library/shum_bola.mp3",
                840,
                "14:00",
                "9-14 yosh",
                1,
                "eng-sara",
                1420,
                480,
                "active",
                3
            ),
            (
                cat_map.get("fan", 5),
                "Kichkina Shahzoda",
                "Antuan de Sent-Ekzyuperi",
                "/images/library/kichkina_shahzoda.png",
                "Olis B-612 asteroididan kelgan mittivoy shahzodaning do'stlik, mehr-oqibat va koinot sirlari haqidagi butun dunyoga mashhur falsafiy ertak-qissasi.",
                "Faqat qalb bilangina ko'rish mumkin. Eng asosiy narsalar ko'zga ko'rinmaydi...",
                "/audio/library/kichkina_shahzoda.mp3",
                960,
                "16:00",
                "6-14 yosh",
                1,
                "eng-sara",
                1890,
                560,
                "active",
                4
            ),
            (
                cat_map.get("odob-axloq", 8),
                "Dunyoning ishlari",
                "O'tkir Hoshimov",
                "/images/library/dunyoning_ishlari.png",
                "Ona mehri, oilaviy qadriyatlar, insoniylik va beg'ubor bolalikning unutilmas iliq xotiralari haqida samimiy va ta'sirli hikoyalar to'plami.",
                "Ona qalbining tubida bolasi uchun tuganmas mehr va duolar mujassam...",
                "/audio/library/dunyoning_ishlari.mp3",
                680,
                "11:20",
                "8-14 yosh",
                0,
                "eng-sara",
                820,
                195,
                "active",
                5
            ),
            (
                cat_map.get("sarguzasht", 6),
                "Sehrli qalpoqcha",
                "Xudoyberdi To'xtaboyev",
                "/images/library/sehrli_qalpoqcha.png",
                "Sehrli qalpoqchani kiyib ko'rinmas bo'lib qolgan Hoshimjonning boshidan kechirgan ibratli va kulgili yangi sarguzashtlari.",
                "Sehrli qalpoqcha menga ko'p narsani o'rgatdi: birovning haqqiga ko'z olaytirmaslik va o'z mehnating bilan yashash eng oliy baxtdir.",
                "/audio/library/sehrli_qalpoqcha.mp3",
                720,
                "12:00",
                "7-12 yosh",
                1,
                "sarguzasht",
                1105,
                310,
                "active",
                6
            ),
            (
                cat_map.get("ertaklar", 7),
                "Ur to'qmoq",
                "O'zbek xalq ertagi",
                "/images/library/ur_toqmoq.png",
                "Halollik va mehnatsevar cholning sadoqatli laylakdan olgan sovg'alari — ochil dasturxon, qus oltin va adolat o'rnatuvchi sehrli to'qmoq haqidagi xalq ertagi.",
                "Bir bor ekan, bir yo'q ekan, qadim o'tgan zamonda bir mehnatkash bechora chol bilan kampir yashagan ekan...",
                "/audio/library/ur_toqmoq.mp3",
                480,
                "08:00",
                "4-9 yosh",
                0,
                "ertaklar",
                750,
                160,
                "active",
                7
            ),
            (
                cat_map.get("ertaklar", 7),
                "Zumrad va Qimmat",
                "O'zbek xalq ertagi",
                "/images/library/zumrad_va_qimmat.png",
                "Mehribon, odobli va chaqqon Zumrad hamda dangasa, xudbin Qimmat haqidagi tarbiyaviy, mashhur o'zbek xalq ertagi.",
                "Bor ekan-u, yo'q ekan, bir ota-onaning Zumrad ismli aqlli, mehnatkash qizi bor ekan...",
                "/audio/library/zumrad_va_qimmat.mp3",
                510,
                "08:30",
                "4-9 yosh",
                1,
                "ertaklar",
                1340,
                410,
                "active",
                8
            ),
            (
                cat_map.get("tarix", 4),
                "Alpomish jasorati",
                "O'zbek xalq dostoni",
                "/images/library/alpomish.png",
                "El-yurt himoyachisi, mard va yengilmas bahodir Alpomishning jasorati hamda sadoqati haqidagi afsonaviy doston bolalar uchun tushunarli uslubda.",
                "Qo'ng'irot elida Hakimbek ismli yosh pahlavon ulg'aydi. Uning mardligi va jasorati tillarda doston bo'ldi...",
                "/audio/library/alpomish.mp3",
                790,
                "13:10",
                "8-14 yosh",
                0,
                "sarguzasht",
                670,
                190,
                "active",
                9
            ),
            (
                cat_map.get("hayvonlar", 3),
                "Hayvonlar sirlari va O'rmon allomalari",
                "Bolalar ensiklopediyasi",
                "/images/library/hayvonlar_olami.png",
                "Sher, ayiq, qushlar va dovyurak chumolilarning qiziqarli dunyosi, qanday birga yashashi va tabiatdagi beqiyos o'rni haqida ilmiy va qiziqarli hikoyalar.",
                "O'rmon — minglab turli jonivorlarning katta va mehrli uyidir. Har bir hayvonning o'z tili, o'z vazifasi bor...",
                "/audio/library/hayvonlar_olami.mp3",
                600,
                "10:00",
                "5-11 yosh",
                1,
                "eng-sara",
                890,
                245,
                "active",
                10
            )
        ]

        cursor.executemany("""
            INSERT INTO library_books (
                category_id, title, author, cover_image, description, content,
                audio_url, duration_seconds, duration_formatted, target_age,
                is_featured, section, listen_count, likes_count, status, order_num
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_lib_books)
        print("Boshlang'ich 10 ta kutubxona kitoblari kiritildi.")

    # 25. Farzandning Ochilgan / Sotib Olgan Avatarlari (Child Unlocked Avatars)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_unlocked_avatars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            child_id INTEGER NOT NULL,
            avatar_key TEXT NOT NULL,
            cost_coins INTEGER DEFAULT 0,
            purchased_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            UNIQUE(child_id, avatar_key)
        )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()


