import hashlib
import os
import random
import json
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
from supabase import create_client, Client
from dotenv import load_dotenv

# Load .env file (if it exists)
load_dotenv()

# Get Supabase credentials (from .env OR hardcoded fallback)
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# FALLBACK - use hardcoded values if .env didn't work
if not SUPABASE_URL:
    SUPABASE_URL = "https://nhcufwzsmszlsyjdcbha.supabase.co"
    print("⚠️ Using hardcoded SUPABASE_URL")
if not SUPABASE_KEY:
    SUPABASE_KEY = "sb_publishable_OfbvsapvYIGpPvU-WbgLDA_xDR8rOkR"
    print("⚠️ Using hardcoded SUPABASE_KEY")

# Debug - verify they exist
print(f"✅ SUPABASE_URL: {SUPABASE_URL[:30]}...")
print(f"✅ SUPABASE_KEY: {SUPABASE_KEY[:20]}...")

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== CREATE APP =====
app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = os.environ.get('SECRET_KEY', 'enkh2345')
CORS(app, supports_credentials=True)

# ... rest of your code continues here

# ===== NOW THE REST OF THE CODE =====
DATA_DIR = 'user_data'
os.makedirs(DATA_DIR, exist_ok=True)

CREATOR_USERNAME = "CREATOR"
CREATOR_PASSWORD = "CREATORENKH2345"

CUSTOM_UNITS_FILE = os.path.join(DATA_DIR, 'custom_units.json')

def load_custom_units():
    if os.path.exists(CUSTOM_UNITS_FILE):
        with open(CUSTOM_UNITS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"Language": {"English": []}, "Math": {"Math": []}}

def save_custom_units(data):
    with open(CUSTOM_UNITS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

CUSTOM_UNITS = load_custom_units()

def get_user_file(username):
    safe_name = "".join(c for c in username if c.isalnum() or c in '_-').lower()
    return os.path.join(DATA_DIR, f"{safe_name}.json")

def load_user_data(username):
    try:
        result = supabase.table('users').select('*').eq('username', username).execute()
        if result.data:
            data = result.data[0]
            # Add missing fields for compatibility
            if 'vocabulary_learned' not in data: data['vocabulary_learned'] = []
            if 'boost_multiplier' not in data: data['boost_multiplier'] = 1
            if 'boost_expires' not in data: data['boost_expires'] = None
            if 'math_ui_language' not in data: data['math_ui_language'] = 'English'
            if 'admin_locked_hearts' not in data: data['admin_locked_hearts'] = False
            return data
        return None
    except Exception as e:
        print(f"Error loading user: {e}")
        return None

def save_user_data(username, data):
    try:
        data_copy = data.copy()
        data_copy.pop('username', None)
        data_copy.pop('vocabulary_learned', None)  # Remove if present
        
        existing = supabase.table('users').select('username').eq('username', username).execute()
        
        if existing.data:
            supabase.table('users').update(data_copy).eq('username', username).execute()
        else:
            data_copy['username'] = username
            supabase.table('users').insert(data_copy).execute()
    except Exception as e:
        print(f"Error saving user: {e}")
def is_creator(username):
    return username.upper() == CREATOR_USERNAME

def create_new_user(username, password, role="student"):
    return {
        "username": username,
        "password": hashlib.sha256(password.encode()).hexdigest(),
        "learning_language": "English",
        "learning_subject": "Language",
        "math_ui_language": "English",
        "role": role,  # "student", "teacher", or "creator"
        "streak": 0,
        "last_active": None,
        "total_xp": 0,
        "hearts": 5,
        "last_heart_refill": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "boost_multiplier": 1,
        "boost_expires": None,
        "chests_earned": 0,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "progress": {},
        "chests_claimed": [],
        "is_creator": (username.upper() == CREATOR_USERNAME),
        "vocabulary_learned": []
    }

ENGLISH_UNITS = [{"id": i, "name": name, "lessons": 5, "chest_at": 3} for i, name in enumerate([
    "Greetings", "Family", "Food & Drink", "Colors", "Animals", "Clothing", "Weather", "Time", "Places", "Actions",
    "Feelings", "Shopping", "Travel", "Health", "Work", "School", "Hobbies", "Sports", "Music", "Movies",
    "Technology", "Nature", "City Life", "Transport", "Restaurant", "Hotel", "Emergency", "Directions", "Money",
    "Phone Calls", "Email", "Relationships", "Personality", "Body Parts", "Medical", "Dating", "Marriage",
    "Children", "Pets", "Home", "Furniture", "Cooking", "Baking", "Holidays", "Celebrations", "Culture",
    "History", "Politics", "Environment", "Future"
], 1)]

MATH_UNITS = []
for i in range(1, 51):
    if i <= 15: diff = "Хялбар"
    elif i <= 35: diff = "Дунд"
    elif i <= 45: diff = "Хэцүү"
    else: diff = "Маш хэцүү"
    MATH_UNITS.append({"id": i, "name": f"{diff} Математик {i}", "lessons": 5, "chest_at": 3})

# ===== COMPLETE 50 UNITS - 100% REAL VOCABULARY =====
VOCAB_WORDS = {
    # UNITS 1-24: ALREADY REAL (KEEP AS IS)
    1: [("Hello", "Сайн уу"), ("Goodbye", "Баяртай"), ("Please", "Гуйя"), ("Thank you", "Баярлалаа"), ("Yes", "Тийм"), ("No", "Үгүй"), ("How are you?", "Чи ямар байна?"), ("I'm fine", "Би зүгээр"), ("What's your name?", "Таны нэр хэн бэ?"), ("My name is...", "Миний нэр..."), ("Nice to meet you", "Танилцахад таатай байна"), ("Good morning", "Өглөөний мэнд"), ("Good night", "Сайхан амраарай"), ("See you later", "Дараа уулзья"), ("Welcome", "Тавтай морил")],
    2: [("Mother", "Ээж"), ("Father", "Аав"), ("Brother", "Ах/дүү"), ("Sister", "Эгч/дүү"), ("Family", "Гэр бүл"), ("Grandmother", "Эмээ"), ("Grandfather", "Өвөө"), ("Uncle", "Авга ах"), ("Aunt", "Авга эгч"), ("Cousin", "Үеэл"), ("Son", "Хүү"), ("Daughter", "Охин"), ("Husband", "Нөхөр"), ("Wife", "Эхнэр"), ("Baby", "Хүүхэд"), ("Parents", "Эцэг эх"), ("Children", "Хүүхдүүд"), ("Grandparents", "Эмээ өвөө"), ("Relative", "Хамаатан"), ("Twin", "Ихэр")],
    3: [("Water", "Ус"), ("Food", "Хоол"), ("Bread", "Талх"), ("Milk", "Сүү"), ("Apple", "Алим"), ("Banana", "Гадил"), ("Meat", "Мах"), ("Rice", "Будаа"), ("Coffee", "Кофе"), ("Tea", "Цай"), ("Juice", "Шүүс"), ("Egg", "Өндөг"), ("Cheese", "Бяслаг"), ("Chicken", "Тахиа"), ("Fish", "Загас"), ("Soup", "Шөл"), ("Salad", "Салат"), ("Pizza", "Пицца"), ("Cake", "Бялуу"), ("Ice cream", "Зайрмаг"), ("Breakfast", "Өглөөний хоол"), ("Lunch", "Үдийн хоол"), ("Dinner", "Оройн хоол"), ("Dessert", "Амттан"), ("Hungry", "Өлссөн"), ("Thirsty", "Цангасан"), ("Delicious", "Амттай"), ("Spicy", "Халуун ногоотой"), ("Sweet", "Чихэрлэг"), ("Sour", "Исгэлэн")],
    4: [("Red", "Улаан"), ("Blue", "Цэнхэр"), ("Green", "Ногоон"), ("Yellow", "Шар"), ("Black", "Хар"), ("White", "Цагаан"), ("Pink", "Ягаан"), ("Purple", "Нил ягаан"), ("Orange", "Улбар шар"), ("Brown", "Бор"), ("Gray", "Саарал"), ("Gold", "Алтан"), ("Silver", "Мөнгөн"), ("Dark", "Харанхуй"), ("Light", "Гэрэлтэй"), ("Bright", "Цайвар"), ("Colorful", "Өнгөлөг"), ("Circle", "Тойрог"), ("Square", "Дөрвөлжин"), ("Triangle", "Гурвалжин"), ("Rectangle", "Таван өнцөг"), ("Round", "Бөөрөнхий"), ("Straight", "Шулуун"), ("Curved", "Музгар")],
    5: [("Dog", "Нохой"), ("Cat", "Муур"), ("Bird", "Шувуу"), ("Fish", "Загас"), ("Horse", "Морь"), ("Cow", "Үхэр"), ("Pig", "Гахай"), ("Sheep", "Хонь"), ("Elephant", "Заан"), ("Lion", "Арслан"), ("Tiger", "Бар"), ("Monkey", "Сармагчин"), ("Bear", "Баавгай"), ("Rabbit", "Туулай"), ("Mouse", "Хулгана"), ("Snake", "Могой"), ("Frog", "Мэлхий"), ("Duck", "Нугас"), ("Chicken", "Тахиа"), ("Bee", "Зөгий"), ("Butterfly", "Эрвээхэй"), ("Spider", "Аалз"), ("Wolf", "Чоно"), ("Fox", "Үнэг"), ("Deer", "Буга")],
    6: [("Shirt", "Цамц"), ("Pants", "Өмд"), ("Dress", "Даашинз"), ("Shoes", "Гутал"), ("Hat", "Малгай"), ("Socks", "Оймс"), ("Jacket", "Хүрэм"), ("Coat", "Пальто"), ("Sweater", "Ноосон цамц"), ("Skirt", "Банзал"), ("Jeans", "Жинс"), ("T-shirt", "Футболк"), ("Shorts", "Шорт"), ("Gloves", "Бээлий"), ("Scarf", "Ороолт"), ("Belt", "Бүс"), ("Tie", "Зангиа"), ("Suit", "Костюм"), ("Uniform", "Дүрэмт хувцас"), ("Pajamas", "Унтлагын хувцас"), ("Underwear", "Дотуур хувцас"), ("Boots", "Гутал"), ("Sandals", "Шаахай"), ("Sneakers", "Пүүз"), ("Fashion", "Загвар")],
    7: [("Sunny", "Нарлаг"), ("Rainy", "Бороотой"), ("Cloudy", "Бүрхэг"), ("Windy", "Салхитай"), ("Snowy", "Цастай"), ("Hot", "Халуун"), ("Cold", "Хүйтэн"), ("Warm", "Дулаан"), ("Cool", "Сэрүүн"), ("Storm", "Шуурга"), ("Fog", "Манан"), ("Rainbow", "Солонго"), ("Thunder", "Аянга"), ("Lightning", "Цахилгаан"), ("Temperature", "Температур"), ("Humid", "Чийглэг"), ("Dry", "Хуурай"), ("Freezing", "Хөлдүү"), ("Breeze", "Сэвшээ салхи"), ("Hurricane", "Хар салхи"), ("Flood", "Үер"), ("Drought", "Ган"), ("Weather forecast", "Цаг агаарын урьдчилсан мэдээ"), ("Climate", "Уур амьсгал"), ("Season", "Улирал")],
    8: [("Morning", "Өглөө"), ("Afternoon", "Үдээс хойш"), ("Evening", "Орой"), ("Night", "Шөнө"), ("Today", "Өнөөдөр"), ("Tomorrow", "Маргааш"), ("Yesterday", "Өчигдөр"), ("Week", "Долоо хоног"), ("Month", "Сар"), ("Year", "Жил"), ("Hour", "Цаг"), ("Minute", "Минут"), ("Second", "Секунд"), ("Clock", "Цаг"), ("Calendar", "Календарь"), ("Monday", "Даваа"), ("Tuesday", "Мягмар"), ("Wednesday", "Лхагва"), ("Thursday", "Пүрэв"), ("Friday", "Баасан"), ("Saturday", "Бямба"), ("Sunday", "Ням"), ("January", "Нэгдүгээр сар"), ("December", "Арванхоёрдугаар сар"), ("Midnight", "Шөнө дунд"), ("Noon", "Үд дунд"), ("Sunrise", "Нар мандах"), ("Sunset", "Нар жаргах")],
    9: [("House", "Байшин"), ("School", "Сургууль"), ("Hospital", "Эмнэлэг"), ("Store", "Дэлгүүр"), ("Park", "Цэцэрлэг"), ("Restaurant", "Ресторан"), ("Bank", "Банк"), ("Hotel", "Зочид буудал"), ("Airport", "Нисэх онгоцны буудал"), ("Station", "Буудал"), ("Library", "Номын сан"), ("Museum", "Музей"), ("Church", "Сүм"), ("Market", "Зах"), ("Office", "Оффис"), ("Street", "Гудамж"), ("Road", "Зам"), ("Bridge", "Гүүр"), ("Building", "Барилга"), ("City", "Хот"), ("Town", "Хотхон"), ("Village", "Тосгон"), ("Country", "Улс"), ("Beach", "Далайн эрэг"), ("Mountain", "Уул"), ("Forest", "Ой"), ("River", "Гол"), ("Lake", "Нуур"), ("Ocean", "Далай")],
    10: [("Run", "Гүйх"), ("Walk", "Алхах"), ("Eat", "Идэх"), ("Drink", "Уух"), ("Sleep", "Унтах"), ("Wake up", "Сэрэх"), ("Read", "Унших"), ("Write", "Бичих"), ("Speak", "Ярих"), ("Listen", "Сонсох"), ("Watch", "Үзэх"), ("Play", "Тоглох"), ("Work", "Ажиллах"), ("Study", "Сурах"), ("Cook", "Хоол хийх"), ("Clean", "Цэвэрлэх"), ("Wash", "Угаах"), ("Open", "Нээх"), ("Close", "Хаах"), ("Push", "Түлхэх"), ("Pull", "Татах"), ("Throw", "Шидэх"), ("Catch", "Барих"), ("Jump", "Үсрэх"), ("Dance", "Бүжиглэх"), ("Sing", "Дуулах"), ("Laugh", "Инээх"), ("Cry", "Уйлах"), ("Smile", "Инээмсэглэх"), ("Think", "Бодох")],
    11: [("Happy", "Аз жаргалтай"), ("Sad", "Гунигтай"), ("Angry", "Ууртай"), ("Tired", "Ядарсан"), ("Hungry", "Өлссөн"), ("Thirsty", "Цангасан"), ("Excited", "Баяртай"), ("Bored", "Уйтгартай"), ("Scared", "Айсан"), ("Surprised", "Гайхсан"), ("Proud", "Бахархсан"), ("Nervous", "Сандарсан"), ("Calm", "Тайван"), ("Confused", "Андуу"), ("Lonely", "Ганцаардсан"), ("Love", "Хайр"), ("Hate", "Үзэн ядах"), ("Jealous", "Атаархсан"), ("Shy", "Ичимхий"), ("Brave", "Зоригтой"), ("Kind", "Эелдэг"), ("Mean", "Муухай"), ("Friendly", "Найрсаг"), ("Serious", "Ноцтой"), ("Funny", "Хөгжилтэй")],
    12: [("Buy", "Худалдаж авах"), ("Sell", "Зарах"), ("Price", "Үнэ"), ("Money", "Мөнгө"), ("Cheap", "Хямд"), ("Expensive", "Үнэтэй"), ("Discount", "Хямдрал"), ("Receipt", "Баримт"), ("Cash", "Бэлэн мөнгө"), ("Card", "Карт"), ("Size", "Хэмжээ"), ("Color", "Өнгө"), ("Try on", "Өмсөж үзэх"), ("Fit", "Таарах"), ("Return", "Буцаах"), ("Exchange", "Солих"), ("Refund", "Мөнгө буцаалт"), ("Sale", "Хямдрал"), ("Shopping", "Дэлгүүр хэсэх"), ("Mall", "Худалдааны төв"), ("Customer", "Үйлчлүүлэгч"), ("Cashier", "Кассчин"), ("Bag", "Цүнх"), ("Wallet", "Түрийвч"), ("Credit card", "Зээлийн карт")],
    13: [("Travel", "Аялах"), ("Trip", "Аялал"), ("Ticket", "Тасалбар"), ("Passport", "Паспорт"), ("Visa", "Виз"), ("Luggage", "Ачаа"), ("Flight", "Нислэг"), ("Train", "Галт тэрэг"), ("Bus", "Автобус"), ("Taxi", "Такси"), ("Map", "Газрын зураг"), ("Destination", "Очих газар"), ("Tourist", "Жуулчин"), ("Guide", "Хөтөч"), ("Adventure", "Адал явдал"), ("Hotel", "Зочид буудал"), ("Reservation", "Захиалга"), ("Check-in", "Бүртгүүлэх"), ("Departure", "Явах"), ("Arrival", "Ирэх"), ("Suitcase", "Чемодан"), ("Backpack", "Үүргэвч"), ("Camera", "Камер"), ("Souvenir", "Бэлэг дурсгал")],
    14: [("Doctor", "Эмч"), ("Nurse", "Сувилагч"), ("Medicine", "Эм"), ("Pain", "Өвдөлт"), ("Headache", "Толгой өвдөх"), ("Fever", "Халуурах"), ("Cough", "Ханиалга"), ("Sick", "Өвчтэй"), ("Healthy", "Эрүүл"), ("Exercise", "Дасгал"), ("Diet", "Хоолны дэглэм"), ("Sleep", "Унтах"), ("Rest", "Амрах"), ("Emergency", "Яаралтай"), ("Ambulance", "Түргэн тусламж"), ("Hospital", "Эмнэлэг"), ("Pharmacy", "Эмийн сан"), ("Prescription", "Жор"), ("Vaccine", "Вакцин"), ("Virus", "Вирус"), ("Infection", "Халдвар"), ("Allergy", "Харшил"), ("Blood", "Цус"), ("Heart", "Зүрх"), ("Bone", "Яс")],
    15: [("Job", "Ажил"), ("Work", "Ажиллах"), ("Office", "Оффис"), ("Boss", "Дарга"), ("Employee", "Ажилтан"), ("Salary", "Цалин"), ("Meeting", "Уулзалт"), ("Interview", "Ярилцлага"), ("Resume", "Анкет"), ("Career", "Мэргэжил"), ("Colleague", "Хамт ажиллагч"), ("Promotion", "Дэвших"), ("Retire", "Тэтгэвэрт гарах"), ("Business", "Бизнес"), ("Customer", "Үйлчлүүлэгч"), ("Contract", "Гэрээ"), ("Deadline", "Эцсийн хугацаа"), ("Project", "Төсөл"), ("Team", "Баг"), ("Manager", "Менежер"), ("Assistant", "Туслах"), ("Full-time", "Бүтэн цагийн"), ("Part-time", "Цагийн"), ("Overtime", "Илүү цаг"), ("Break", "Завсарлага")],
    16: [("Teacher", "Багш"), ("Student", "Оюутан"), ("Classroom", "Анги"), ("Book", "Ном"), ("Pen", "Үзэг"), ("Pencil", "Харандаа"), ("Notebook", "Дэвтэр"), ("Desk", "Ширээ"), ("Chair", "Сандал"), ("Board", "Самбар"), ("Homework", "Гэрийн даалгавар"), ("Exam", "Шалгалт"), ("Grade", "Дүн"), ("Lesson", "Хичээл"), ("Subject", "Хичээлийн сэдэв"), ("Graduate", "Төгсөх"), ("Principal", "Захирал"), ("Semester", "Улирал"), ("Scholarship", "Тэтгэлэг"), ("Tuition", "Сургалтын төлбөр")],
    17: [("Reading", "Ном унших"), ("Drawing", "Зурах"), ("Painting", "Будах"), ("Gardening", "Цэцэрлэгжүүлэлт"), ("Cooking", "Хоол хийх"), ("Baking", "Жигнэх"), ("Knitting", "Сүлжих"), ("Photography", "Гэрэл зураг"), ("Collecting", "Цуглуулах"), ("Fishing", "Загасчлах"), ("Hiking", "Явган аялал"), ("Camping", "Зуслан"), ("Chess", "Шатар"), ("Puzzle", "Оньсого"), ("Origami", "Цаасан нугалаа"), ("Pottery", "Шаазан эдлэл"), ("Calligraphy", "Уран бичлэг"), ("Sculpting", "Баримал"), ("Weaving", "Нэхэх"), ("Embroidery", "Хатгамал")],
    18: [("Soccer", "Хөлбөмбөг"), ("Basketball", "Сагсан бөмбөг"), ("Tennis", "Теннис"), ("Swimming", "сэлэх"), ("Running", "Гүйлт"), ("Cycling", "Дугуй унах"), ("Volleyball", "Волейбол"), ("Baseball", "Бейсбол"), ("Golf", "Гольф"), ("Boxing", "Бокс"), ("Wrestling", "Бөх"), ("Skiing", "Цана"), ("Skating", "Тэшүүр"), ("Yoga", "Иог"), ("Gymnastics", "Гимнастик"), ("Archery", "Байт харваа"), ("Fencing", "Туялзуур сэлэм"), ("Surfing", "Далайн давалгаа"), ("Skateboarding", "Скейтборд"), ("Marathon", "Марафон")],
    19: [("Song", "Дуу"), ("Singer", "Дуучин"), ("Band", "Хамтлаг"), ("Guitar", "Гитар"), ("Piano", "Төгөлдөр хуур"), ("Drums", "Бөмбөр"), ("Violin", "Хийл"), ("Concert", "Тоглолт"), ("Melody", "Ая"), ("Rhythm", "Хэмнэл"), ("Lyrics", "Үг"), ("Album", "Цомог"), ("Radio", "Радио"), ("Headphones", "Чихэвч"), ("Microphone", "Микрофон"), ("Speaker", "Чанга яригч"), ("Orchestra", "Найрал хөгжим"), ("Chorus", "Найрал дуу"), ("Composer", "Хөгжмийн зохиолч"), ("Conductor", "Удирдаач")],
    20: [("Film", "Кино"), ("Actor", "Жүжигчин"), ("Actress", "Эмэгтэй жүжигчин"), ("Director", "Найруулагч"), ("Scene", "Дүр зураг"), ("Plot", "Үйл явдал"), ("Cinema", "Кино театр"), ("Ticket", "Тасалбар"), ("Popcorn", "Попкорн"), ("Trailer", "Трейлер"), ("Comedy", "Инээдмийн"), ("Drama", "Драм"), ("Action", "Тулаант"), ("Horror", "Аймшгийн"), ("Documentary", "Баримтат"), ("Animation", "Хүүхэлдэй"), ("Subtitles", "Хадмал орчуулга"), ("Credits", "Төгсгөлийн бичлэг"), ("Premiere", "Нээлт"), ("Box office", "Киноны орлого")],
    21: [("Computer", "Компьютер"), ("Phone", "Утас"), ("Internet", "Интернет"), ("Website", "Вэбсайт"), ("Email", "И-мэйл"), ("Password", "Нууц үг"), ("Download", "Татах"), ("Upload", "Оруулах"), ("Software", "Программ"), ("Hardware", "Техник хангамж"), ("Screen", "Дэлгэц"), ("Keyboard", "Гар"), ("Mouse", "Хулгана"), ("Wifi", "Вайфай"), ("Bluetooth", "Блютүүт"), ("App", "Апп"), ("Social media", "Олон нийтийн сүлжээ"), ("Virus", "Вирус"), ("Hacker", "Хакер"), ("Firewall", "Галт хана")],
    22: [("Tree", "Мод"), ("Flower", "Цэцэг"), ("Grass", "Өвс"), ("Leaf", "Навч"), ("Forest", "Ой"), ("Mountain", "Уул"), ("River", "Гол"), ("Lake", "Нуур"), ("Ocean", "Далай"), ("Sky", "Тэнгэр"), ("Cloud", "Үүл"), ("Rain", "Бороо"), ("Sun", "Нар"), ("Moon", "Сар"), ("Star", "Од"), ("Planet", "Гариг"), ("Earth", "Дэлхий"), ("Desert", "Цөл"), ("Volcano", "Галт уул"), ("Waterfall", "Хүрхрээ")],
    23: [("Street", "Гудамж"), ("Traffic", "Замын хөдөлгөөн"), ("Subway", "Метро"), ("Apartment", "Орон сууц"), ("Elevator", "Цахилгаан шат"), ("Noise", "Чимээ"), ("Pollution", "Бохирдол"), ("Crowd", "Цугласан хүмүүс"), ("Neighbor", "Хөрш"), ("Downtown", "Хотын төв"), ("Skyscraper", "Тэнгэр баганадсан барилга"), ("Sidewalk", "Явган зам"), ("Crosswalk", "Явган хүний гарц"), ("Trash", "Хог"), ("Recycling", "Дахин боловсруулалт"), ("Commute", "Ажилдаа явах"), ("Rush hour", "Ачааллын цаг"), ("Suburb", "Хотын зах"), ("Slum", "Ядуусын хороолол"), ("Square", "Талбай")],
    24: [("Car", "Машин"), ("Bus", "Автобус"), ("Train", "Галт тэрэг"), ("Plane", "Онгоц"), ("Boat", "Завь"), ("Bicycle", "Унадаг дугуй"), ("Motorcycle", "Мотоцикл"), ("Walk", "Явган"), ("Driver", "Жолооч"), ("Passenger", "Зорчигч"), ("Garage", "Гараж"), ("Parking", "Зогсоол"), ("Highway", "Хурдны зам"), ("Traffic light", "Гэрлэн дохио"), ("Roundabout", "Тойрог зам"), ("Tunnel", "Хонгил"), ("Bridge", "Гүүр"), ("Helicopter", "Нисдэг тэрэг"), ("Ferry", "Гарам"), ("Scooter", "Скутер")],
    
    # UNITS 25-50: 100% REAL CONTENT
    25: [("Menu", "Цэс"), ("Waiter", "Зөөгч"), ("Order", "Захиалах"), ("Bill", "Тооцоо"), ("Tip", "Гарын мөнгө"), ("Appetizer", "Зууш"), ("Main course", "Үндсэн хоол"), ("Dessert", "Амттан"), ("Drink", "Ундаа"), ("Reservation", "Захиалга"), ("Table", "Ширээ"), ("Knife", "Хутга"), ("Fork", "Сэрээ"), ("Spoon", "Халбага"), ("Napkin", "Амны алчуур"), ("Delicious", "Амттай"), ("Spicy", "Халуун ногоотой"), ("Vegetarian", "Цагаан хоолтон"), ("Rare", "Дутуу болсон"), ("Well-done", "Сайн болсон")],
    26: [("Check-in", "Бүртгүүлэх"), ("Check-out", "Гарах"), ("Room key", "Өрөөний түлхүүр"), ("Lobby", "Лобби"), ("Elevator", "Цахилгаан шат"), ("Reception", "Хүлээн авах"), ("Single room", "1 хүний өрөө"), ("Double room", "2 хүний өрөө"), ("Suite", "Люкс өрөө"), ("Breakfast included", "Өглөөний хоолтой"), ("Room service", "Өрөөний үйлчилгээ"), ("Do not disturb", "Бүү саад хий"), ("Towel", "Алчуур"), ("Pillow", "Дэр"), ("Blanket", "Хөнжил"), ("Air conditioning", "Агааржуулагч"), ("Heater", "Халаагуур"), ("Balcony", "Тагт"), ("View", "Харагдац"), ("Luggage", "Ачаа")],
    27: [("Help!", "Туслаарай!"), ("Police", "Цагдаа"), ("Ambulance", "Түргэн тусламж"), ("Fire", "Гал"), ("Danger", "Аюул"), ("Emergency exit", "Яаралтай гарах хаалга"), ("Call 911", "911 рүү залга"), ("Accident", "Осол"), ("Injury", "Гэмтэл"), ("Bleeding", "Цус алдах"), ("Broken", "Хугарсан"), ("Lost", "Төөрсөн"), ("Stolen", "Хулгайд алдсан"), ("Earthquake", "Газар хөдлөлт"), ("Flood", "Үер"), ("Storm", "Шуурга"), ("Evacuate", "Нүүлгэн шилжүүлэх"), ("Safe", "Аюулгүй"), ("First aid", "Анхны тусламж"), ("Emergency kit", "Яаралтай тусламжийн хэрэгсэл")],
    28: [("Left", "Зүүн"), ("Right", "Баруун"), ("Straight", "Шулуун"), ("Turn", "Эргэх"), ("Near", "Ойр"), ("Far", "Хол"), ("Next to", "Хажууд"), ("Across from", "Эсрэг талд"), ("Between", "Дунд"), ("Corner", "Булан"), ("Block", "Хороолол"), ("Intersection", "Уулзвар"), ("Traffic light", "Гэрлэн дохио"), ("Stop sign", "Зогс тэмдэг"), ("Map", "Газрын зураг"), ("GPS", "Жи Пи Эс"), ("Address", "Хаяг"), ("Landmark", "Тэмдэгт газар"), ("North", "Хойд"), ("South", "Өмнөд"), ("East", "Зүүн"), ("West", "Баруун")],
    29: [("Money", "Мөнгө"), ("Dollar", "Доллар"), ("Cent", "Цент"), ("Coin", "Зоос"), ("Bill", "Дэвсгэрт"), ("Expensive", "Үнэтэй"), ("Cheap", "Хямд"), ("Save", "Хадгалах"), ("Spend", "Зарцуулах"), ("Earn", "Олох"), ("Bank", "Банк"), ("Account", "Данс"), ("Deposit", "Хадгалуулах"), ("Withdraw", "Гаргах"), ("Loan", "Зээл"), ("Debt", "Өр"), ("Interest", "Хүү"), ("Tax", "Татвар"), ("Budget", "Төсөв"), ("Currency", "Валют")],
    30: [("Hello?", "Сайн уу?"), ("Speaking", "Би байна"), ("Who's calling?", "Хэн байна?"), ("Wrong number", "Буруу дугаар"), ("Call back", "Буцаж залгах"), ("Hang up", "Утсаа таслах"), ("Busy", "Завгүй"), ("Voicemail", "Дуут шуудан"), ("Text message", "Мессеж"), ("Ringtone", "Дуудлагын ая"), ("Silent mode", "Чимээгүй горим"), ("Speaker", "Чанга яригч"), ("Reception", "Хүлээн авалт"), ("Bad connection", "Холболт муу"), ("Battery", "Батарей"), ("Charger", "Цэнэглэгч"), ("Phone number", "Утасны дугаар"), ("Area code", "Бүсийн код"), ("International call", "Олон улсын дуудлага"), ("Missed call", "Хариулаагүй дуудлага")],
    31: [("Email", "И-мэйл"), ("Inbox", "Ирсэн"), ("Sent", "Илгээсэн"), ("Drafts", "Ноорог"), ("Spam", "Спам"), ("Subject", "Гарчиг"), ("Attachment", "Хавсралт"), ("Reply", "Хариу бичих"), ("Forward", "Дамжуулах"), ("Delete", "Устгах"), ("Archive", "Архивлах"), ("Compose", "Бичих"), ("Signature", "Гарын үсэг"), ("CC", "Хуулбар"), ("BCC", "Нууц хуулбар"), ("Recipient", "Хүлээн авагч"), ("Sender", "Илгээгч"), ("Draft", "Ноорог"), ("Trash", "Хогийн сав"), ("Refresh", "Шинэчлэх")],
    32: [("Friend", "Найз"), ("Best friend", "Хамгийн сайн найз"), ("Boyfriend", "Найз залуу"), ("Girlfriend", "Найз охин"), ("Married", "Гэрлэсэн"), ("Single", "Ганц бие"), ("Divorced", "Салсан"), ("Widow", "Бэлэвсэн"), ("Engaged", "Сүй тавьсан"), ("Relationship", "Харилцаа"), ("Trust", "Итгэл"), ("Loyalty", "Үнэнч байдал"), ("Argument", "Маргаан"), ("Apology", "Уучлалт"), ("Forgive", "Уучлах"), ("Break up", "Салах"), ("Get along", "Таарах"), ("Hug", "Тэврэх"), ("Kiss", "Үнсэх"), ("Love", "Хайр")],
    33: [("Kind", "Эелдэг"), ("Funny", "Хөгжилтэй"), ("Serious", "Ноцтой"), ("Lazy", "Залхуу"), ("Hardworking", "Хөдөлмөрч"), ("Shy", "Ичимхий"), ("Outgoing", "Нээлттэй"), ("Confident", "Өөртөө итгэлтэй"), ("Arrogant", "Бардам"), ("Humble", "Даруу"), ("Honest", "Шударга"), ("Loyal", "Үнэнч"), ("Patient", "Тэвчээртэй"), ("Impatient", "Тэвчээргүй"), ("Creative", "Бүтээлч"), ("Organized", "Зохион байгуулалттай"), ("Messy", "Замбараагүй"), ("Optimistic", "Өөдрөг"), ("Pessimistic", "Гутранги"), ("Curious", "Сониуч")],
    34: [("Head", "Толгой"), ("Hair", "Үс"), ("Face", "Нүүр"), ("Eye", "Нүд"), ("Nose", "Хамар"), ("Mouth", "Ам"), ("Ear", "Чих"), ("Neck", "Хүзүү"), ("Shoulder", "Мөр"), ("Arm", "Гар"), ("Hand", "Гарын сарвуу"), ("Finger", "Хуруу"), ("Chest", "Цээж"), ("Back", "Нуруу"), ("Stomach", "Гэдэс"), ("Leg", "Хөл"), ("Knee", "Өвдөг"), ("Foot", "Хөлийн сарвуу"), ("Toe", "Хөлийн хуруу"), ("Heart", "Зүрх")],
    35: [("Fever", "Халуурах"), ("Cough", "Ханиалга"), ("Cold", "Ханиад"), ("Flu", "Томуу"), ("Headache", "Толгой өвдөх"), ("Prescription", "Жор"), ("Pharmacy", "Эмийн сан"), ("Pill", "Эм"), ("Medicine", "Эм"), ("Vaccine", "Вакцин"), ("Injection", "Тариа"), ("Surgery", "Мэс засал"), ("X-ray", "Рентген"), ("Blood test", "Цусны шинжилгээ"), ("Insurance", "Даатгал"), ("Patient", "Өвчтөн"), ("Symptom", "Шинж тэмдэг"), ("Diagnosis", "Онош"), ("Treatment", "Эмчилгээ"), ("Recovery", "Эдгэрэлт")],
    36: [("Date", "Болзоо"), ("Crush", "Дурлал"), ("Flirt", "Сээтэгнэх"), ("Romantic", "Романтик"), ("Break up", "Салах"), ("First date", "Анхны болзоо"), ("Blind date", "Танихгүй хүнтэй болзох"), ("Online dating", "Онлайн болзоо"), ("Match", "Тохирох"), ("Chemistry", "Хими"), ("Attraction", "Татагдах"), ("Compliment", "Магтаал"), ("Ghosting", "Алга болох"), ("Heartbroken", "Зүрх шархалсан"), ("Move on", "Цааш явах"), ("Jealous", "Атаархсан"), ("Flowers", "Цэцэг"), ("Chocolate", "Шоколад"), ("Romance", "Романс"), ("Propose", "Гэрлэх санал тавих")],
    37: [("Wedding", "Хурим"), ("Ring", "Бөгж"), ("Vows", "Амлалт"), ("Honeymoon", "Бал сар"), ("Divorce", "Салалт"), ("Bride", "Бэр"), ("Groom", "Хүргэн"), ("Bridesmaid", "Бэрийн хамсаа"), ("Best man", "Хүргэний хамсаа"), ("Ceremony", "Ёслол"), ("Reception", "Хүлээн авалт"), ("Anniversary", "Ой"), ("Marriage", "Гэрлэлт"), ("Couple", "Хос"), ("Husband", "Нөхөр"), ("Wife", "Эхнэр"), ("In-laws", "Хадам эцэг эх"), ("Newlyweds", "Шинээр гэрлэсэн хосууд"), ("Engagement", "Сүй тавилт"), ("Proposal", "Гэрлэх санал")],
    38: [("Baby", "Хүүхэд"), ("Toddler", "Бага насны хүүхэд"), ("Teenager", "Өсвөр насны хүүхэд"), ("Diaper", "Живх"), ("Stroller", "Хүүхдийн тэрэг"), ("Crib", "Хүүхдийн ор"), ("Pacifier", "Хөхүүр"), ("Bottle", "Лонх"), ("Babysitter", "Хүүхэд харагч"), ("Daycare", "Цэцэрлэг"), ("Kindergarten", "Цэцэрлэг"), ("Elementary school", "Бага сургууль"), ("Toys", "Тоглоом"), ("Playground", "Тоглоомын талбай"), ("Nursery", "Хүүхдийн өрөө"), ("Onesie", "Хүүхдийн хувцас"), ("Rattle", "Шажигнуур"), ("Teething", "Шүдлэх"), ("Colic", "Гэдэс өвдөх"), ("Lullaby", "Бүүвэйн дуу")],
    39: [("Leash", "Оосор"), ("Vet", "Мал эмнэлэг"), ("Cage", "Тор"), ("Aquarium", "Аквариум"), ("Grooming", "Үс засалт"), ("Pet food", "Тэжээвэр амьтны хоол"), ("Litter box", "Муурын бие засах хайрцаг"), ("Scratching post", "Маажуур"), ("Dog house", "Нохойн байр"), ("Collar", "Хүзүүвч"), ("Tag", "Гэрийн хаяг"), ("Microchip", "Микрочип"), ("Vaccination", "Вакцинжуулалт"), ("Spay", "Үргүйжүүлэх"), ("Neuter", "Ариутгах"), ("Flea", "Бөөс"), ("Tick", "Хачиг"), ("Shedding", "Үс гүйх"), ("Bark", "Хуцах"), ("Meow", "Мяав")],
    40: [("Living room", "Зочны өрөө"), ("Kitchen", "Гал тогоо"), ("Bathroom", "Угаалгын өрөө"), ("Bedroom", "Унтлагын өрөө"), ("Garage", "Гараж"), ("Attic", "Дээврийн өрөө"), ("Basement", "Зоорийн давхар"), ("Yard", "Хашаа"), ("Garden", "Цэцэрлэг"), ("Porch", "Саравч"), ("Balcony", "Тагт"), ("Hallway", "Коридор"), ("Closet", "Шүүгээ"), ("Pantry", "Агуулах"), ("Laundry room", "Угаалгын өрөө"), ("Fence", "Хашаа"), ("Mailbox", "Шуудангийн хайрцаг"), ("Doorbell", "Хаалганы хонх"), ("Welcome mat", "Тавтай морил дэвсгэр"), ("Fireplace", "Зуух")],
    41: [("Table", "Ширээ"), ("Chair", "Сандал"), ("Sofa", "Буйдан"), ("Bed", "Ор"), ("Wardrobe", "Хувцасны шүүгээ"), ("Dresser", "Шүүгээ"), ("Nightstand", "Орны дэргэдэх ширээ"), ("Desk", "Бичгийн ширээ"), ("Bookshelf", "Номын тавиур"), ("Cabinet", "Шүүгээ"), ("Mirror", "Толь"), ("Lamp", "Ширээний чийдэн"), ("Carpet", "Хивс"), ("Curtains", "Хөшиг"), ("Blinds", "Наалт"), ("Cushion", "Дэр"), ("Mattress", "Гудас"), ("Pillow", "Дэр"), ("Blanket", "Хөнжил"), ("Drawer", "Шургуулга")],
    42: [("Recipe", "Жор"), ("Ingredient", "Орц"), ("Boil", "Буцалгах"), ("Fry", "Шарах"), ("Bake", "Жигнэх"), ("Roast", "Шарах"), ("Grill", "Шарах"), ("Steam", "Жигнэх"), ("Simmer", "Бага гал дээр буцалгах"), ("Stir", "Хутгах"), ("Mix", "Холих"), ("Chop", "Хэрчих"), ("Slice", "Зүсэх"), ("Dice", "Шоо хэрчих"), ("Peel", "Хальслах"), ("Grate", "Үрэх"), ("Measure", "Хэмжих"), ("Taste", "Амтлах"), ("Seasoning", "Амтлагч"), ("Marinate", "Дэвтээх")],
    43: [("Flour", "Гурил"), ("Sugar", "Элсэн чихэр"), ("Oven", "Зуух"), ("Dough", "Зуурмаг"), ("Cookies", "Жигнэмэг"), ("Cake", "Бялуу"), ("Bread", "Талх"), ("Pastry", "Боов"), ("Pie", "Бялуу"), ("Muffin", "Маффин"), ("Cupcake", "Аягатай бялуу"), ("Icing", "Чихрийн өнгөлгөө"), ("Frosting", "Цөцгийн тос"), ("Yeast", "Мөөгөнцөр"), ("Baking powder", "Жигнэх нунтаг"), ("Baking soda", "Хүнсний сод"), ("Vanilla", "Ваниль"), ("Cinnamon", "Шанц"), ("Whisk", "Хумслагч"), ("Rolling pin", "Ганжуур")],
    44: [("Christmas", "Зул сар"), ("Easter", "Улаан өндөгний баяр"), ("Halloween", "Хэллоуин"), ("Thanksgiving", "Талархлын баяр"), ("New Year", "Шинэ жил"), ("Valentine's Day", "Гэгээн Валентины өдөр"), ("Mother's Day", "Ээжүүдийн баяр"), ("Father's Day", "Аавуудын баяр"), ("Independence Day", "Тусгаар тогтнолын өдөр"), ("Holiday", "Амралтын өдөр"), ("Vacation", "Амралт"), ("Celebration", "Тэмдэглэл"), ("Fireworks", "Салют"), ("Parade", "Жагсаал"), ("Tradition", "Уламжлал"), ("Decorations", "Чимэглэл"), ("Presents", "Бэлэг"), ("Feast", "Найр"), ("Family gathering", "Гэр бүлийн цугларалт"), ("Festival", "Наадам")],
    45: [("Birthday", "Төрсөн өдөр"), ("Anniversary", "Ой"), ("Party", "Үдэшлэг"), ("Gift", "Бэлэг"), ("Cake", "Бялуу"), ("Candles", "Лаа"), ("Balloons", "Бөмбөлөг"), ("Invitation", "Урилга"), ("Guest", "Зочин"), ("Host", "Зохион байгуулагч"), ("Surprise", "Гэнэтийн бэлэг"), ("Toast", "Хундага өргөх"), ("Cheers", "Мэнд хүргэе"), ("Celebrate", "Тэмдэглэх"), ("Graduation", "Төгсөлт"), ("Wedding", "Хурим"), ("Baby shower", "Хүүхэд угтах үдэшлэг"), ("Retirement", "Тэтгэвэрт гарах"), ("Congrats", "Баяр хүргэе"), ("Wish", "Хүсэл")],
    46: [("Tradition", "Уламжлал"), ("Custom", "Ёс заншил"), ("Festival", "Наадам"), ("Art", "Урлаг"), ("Music", "Хөгжим"), ("Dance", "Бүжиг"), ("Literature", "Уран зохиол"), ("Poetry", "Яруу найраг"), ("Theater", "Театр"), ("Museum", "Музей"), ("Heritage", "Өв"), ("History", "Түүх"), ("Ancestors", "Өвөг дээдэс"), ("Folklore", "Ардын аман зохиол"), ("Myth", "Домог"), ("Legend", "Түүхэн домог"), ("Religion", "Шашин"), ("Belief", "Итгэл үнэмшил"), ("Values", "Үнэт зүйлс"), ("Identity", "Өвөрмөц байдал")],
    47: [("Past", "Өнгөрсөн"), ("Ancient", "Эртний"), ("War", "Дайн"), ("King", "Хаан"), ("Queen", "Хатан"), ("Revolution", "Хувьсгал"), ("Independence", "Тусгаар тогтнол"), ("Colony", "Колони"), ("Empire", "Эзэнт гүрэн"), ("Civilization", "Соёл иргэншил"), ("Century", "Зуун"), ("Decade", "Арван жил"), ("Era", "Эрин үе"), ("Timeline", "Цаг хугацааны хэлхээс"), ("Artifact", "Олдвор"), ("Archaeology", "Археологи"), ("Discovery", "Нээлт"), ("Invention", "Шинэ бүтээл"), ("Industrial", "Аж үйлдвэрийн"), ("Modern", "Орчин үеийн")],
    48: [("Vote", "Санал өгөх"), ("President", "Ерөнхийлөгч"), ("Law", "Хууль"), ("Government", "Засгийн газар"), ("Election", "Сонгууль"), ("Democracy", "Ардчилал"), ("Republic", "Бүгд найрамдах улс"), ("Constitution", "Үндсэн хууль"), ("Congress", "Конгресс"), ("Parliament", "Парламент"), ("Senate", "Сенат"), ("Mayor", "Хотын дарга"), ("Governor", "Захирагч"), ("Policy", "Бодлого"), ("Rights", "Эрх"), ("Freedom", "Эрх чөлөө"), ("Justice", "Шударга ёс"), ("Court", "Шүүх"), ("Judge", "Шүүгч"), ("Citizen", "Иргэн")],
    49: [("Pollution", "Бохирдол"), ("Recycle", "Дахин боловсруулах"), ("Climate", "Уур амьсгал"), ("Energy", "Эрчим хүч"), ("Planet", "Гариг"), ("Global warming", "Дэлхийн дулаарал"), ("Greenhouse", "Хүлэмж"), ("Carbon", "Нүүрстөрөгч"), ("Emission", "Ялгарал"), ("Renewable", "Сэргээгдэх"), ("Solar", "Нарны"), ("Wind", "Салхины"), ("Conservation", "Хамгаалал"), ("Ecosystem", "Экосистем"), ("Wildlife", "Зэрлэг амьтад"), ("Endangered", "Ховордсон"), ("Extinction", "Устгал"), ("Stable", "Тогтвортой"), ("Organic", "Органик"), ("Compost", "Бордоо")],
    50: [("Future", "Ирээдүй"), ("Robot", "Робот"), ("Spaceship", "Сансрын хөлөг"), ("Predict", "Урьдчилан таамаглах"), ("Hope", "Найдвар"), ("Dream", "Мөрөөдөл"), ("Goal", "Зорилго"), ("Plan", "Төлөвлөгөө"), ("Technology", "Технологи"), ("Artificial intelligence", "Хиймэл оюун ухаан"), ("Virtual reality", "Виртуал бодит байдал"), ("Mars", "Ангараг"), ("Colony", "Колони"), ("Innovation", "Инновац"), ("Progress", "Дэвшил"), ("Change", "Өөрчлөлт"), ("Tomorrow", "Маргааш"), ("Next generation", "Дараагийн үе"), ("Legacy", "Өв"), ("Destiny", "Хувь тавилан")],
}

# ===== GRAMMAR RULES =====
GRAMMAR_RULES = {
    1: [{"q": "I ___ a student.", "opts": ["am", "is", "are"], "ans": "am"}, {"q": "She ___ happy.", "opts": ["is", "am", "are"], "ans": "is"}, {"q": "They ___ friends.", "opts": ["are", "is", "am"], "ans": "are"}],
    2: [{"q": "This is ___ book.", "opts": ["my", "I", "me"], "ans": "my"}, {"q": "___ name is Sarah.", "opts": ["Her", "She", "Hers"], "ans": "Her"}],
    3: [{"q": "I would like ___ apple.", "opts": ["an", "a", "the"], "ans": "an"}, {"q": "___ sun is bright.", "opts": ["The", "A", "An"], "ans": "The"}],
}
for i in range(4, 51):
    GRAMMAR_RULES[i] = [
        {"q": f"She ___ to school every day.", "opts": ["goes", "go", "going"], "ans": "goes"},
        {"q": f"They ___ playing now.", "opts": ["are", "is", "am"], "ans": "are"},
    ]

# ===== REAL LISTENING PHRASES FOR ALL UNITS =====
LISTENING_PHRASES = {
    1: ["Hello, how are you?", "My name is John.", "Nice to meet you.", "Where are you from?", "I am learning English."],
    2: ["This is my mother.", "My father works hard.", "I have two brothers.", "Her sister is a doctor.", "We are a big family."],
    3: ["I would like some water.", "This food is delicious.", "Can I have the menu?", "I'll have coffee please.", "The cake is very sweet."],
    4: ["The sky is blue.", "I like red roses.", "Her dress is yellow.", "Black is my favorite color.", "The grass is green."],
    5: ["I have a dog.", "Cats are cute.", "Birds can fly.", "Fish live in water.", "Horses run fast."],
    6: ["I need a new shirt.", "These pants are too long.", "She bought a beautiful dress.", "Where are my shoes?", "Put on your jacket."],
    7: ["It is sunny today.", "Tomorrow will be rainy.", "The weather is cold.", "I love warm summer days.", "There is a storm coming."],
    8: ["Good morning.", "I will see you tomorrow.", "What time is it?", "My birthday is in January.", "We met last week."],
    9: ["I live in a house.", "The school is nearby.", "Let's go to the park.", "The hospital is on Main Street.", "Where is the nearest bank?"],
    10: ["I run every morning.", "She walks to school.", "We eat dinner at seven.", "He drinks coffee.", "The baby sleeps all day."],
    11: ["I am so happy today.", "She feels sad.", "He is angry about the news.", "I'm tired after work.", "Are you hungry?"],
      12: ["How much does this cost?", "I want to buy a new bag.", "Do you accept credit cards?", "This shirt is too expensive.", "Where is the fitting room?"],
    13: ["I love to travel.", "We booked a flight to Paris.", "Do you have your passport?", "The train leaves at noon.", "Where is the bus station?"],
    14: ["I have a headache.", "She has a fever.", "You need to see a doctor.", "Take this medicine.", "Get some rest."],
    15: ["I have a new job.", "She works in an office.", "My boss is very nice.", "We have a meeting at ten.", "He got a promotion."],
    16: ["The teacher is kind.", "Students are studying.", "Please open your book.", "Homework is due tomorrow.", "I passed the exam."],
    17: ["I like reading books.", "She enjoys painting.", "He goes fishing on weekends.", "We love hiking in the mountains.", "Cooking is fun."],
    18: ["I play soccer.", "She swims very well.", "He runs marathons.", "We watch basketball games.", "Yoga is relaxing."],
    19: ["I love this song.", "She plays the guitar.", "He is a famous singer.", "We went to a concert.", "The band was amazing."],
    20: ["Let's watch a movie.", "That actor is great.", "The plot was interesting.", "I love comedy films.", "Horror movies scare me."],
    21: ["I use my computer daily.", "My phone is new.", "The internet is slow.", "I sent you an email.", "What is the wifi password?"],
    22: ["The tree is tall.", "I love flowers.", "The mountains are beautiful.", "We walked through the forest.", "The ocean is vast."],
    23: ["The streets are crowded.", "Traffic is terrible.", "I take the subway to work.", "My apartment is small.", "The city never sleeps."],
    24: ["I drive a car.", "She takes the bus.", "He rides a bicycle.", "We are waiting for the train.", "The plane is landing."],
    25: ["I would like a table for two.", "What is the special today?", "Can I see the menu?", "The food was delicious.", "I'll pay the bill."],
    26: ["I have a reservation.", "What time is check in?", "Do you have any rooms available?", "I need a wake up call.", "Where is the elevator?"],
    27: ["Help me please.", "Call an ambulance.", "There is a fire.", "I am lost.", "This is an emergency."],
    28: ["Turn left at the corner.", "Go straight ahead.", "It is on your right.", "How far is the station?", "Can you show me on the map?"],
    29: ["I need to save money.", "This is too expensive.", "Do you have change?", "I paid with cash.", "She earns a good salary."],
    30: ["Hello, who is speaking?", "I will call you back.", "Sorry, wrong number.", "The line is busy.", "I left you a voicemail."],
    31: ["I sent you an email.", "Did you get my attachment?", "Please reply as soon as possible.", "Check your inbox.", "I deleted the spam."],
    32: ["She is my best friend.", "He is my boyfriend.", "We are married.", "They got divorced.", "I love you."],
    33: ["She is very kind.", "He is so funny.", "My boss is serious.", "I am a bit shy.", "You are very brave."],
    34: ["My head hurts.", "She has beautiful eyes.", "He broke his arm.", "I have a stomach ache.", "My back is sore."],
    35: ["I have a fever.", "She has a bad cough.", "You need a prescription.", "The pharmacy is closed.", "I have health insurance."],
    36: ["We went on a date.", "I have a crush on her.", "He is so romantic.", "They broke up last week.", "Will you marry me?"],
    37: ["The wedding was beautiful.", "She wore a white dress.", "They exchanged rings.", "They went on a honeymoon.", "They just celebrated their anniversary."],
    38: ["The baby is crying.", "She has two children.", "He is a teenager now.", "I need to change the diaper.", "We need a babysitter."],
    39: ["I have a dog and a cat.", "We took our pet to the vet.", "The dog needs a walk.", "The cat is sleeping.", "I love animals."],
    40: ["I live in a house.", "The kitchen is big.", "My bedroom is upstairs.", "We have a nice garden.", "The garage is full."],
    41: ["We bought a new table.", "The sofa is comfortable.", "I need a new bed.", "The bookshelf is full of books.", "She opened the drawer."],
    42: ["I am cooking dinner.", "Follow the recipe.", "Boil the water.", "Fry the onions.", "Bake the cake."],
    43: ["I love baking bread.", "Add some flour and sugar.", "Preheat the oven.", "Knead the dough.", "The cookies smell amazing."],
    44: ["Merry Christmas.", "Happy New Year.", "Trick or treat.", "Happy Thanksgiving.", "Happy Valentine's Day."],
    45: ["Happy birthday to you.", "Congratulations on your graduation.", "Best wishes on your anniversary.", "Surprise.", "Let's celebrate."],
    46: ["It is a family tradition.", "We respect our customs.", "I love learning about culture.", "The festival is next week.", "She studies art history."],
    47: ["In the past.", "Ancient civilizations.", "The war ended.", "The king ruled.", "The industrial revolution changed everything."],
    48: ["I will vote today.", "Who is the president?", "The government passed a new law.", "Freedom is important.", "We have rights."],
    49: ["Pollution is a big problem.", "Please recycle.", "Climate change is real.", "We need renewable energy.", "Save the planet."],
    50: ["I hope for a better future.", "Robots will help us.", "I dream of traveling to space.", "What will happen tomorrow?", "Never stop dreaming."],
}
def generate_question(unit_id):
    lesson_type = random.choice(["vocabulary", "grammar", "listening"])
    
    if lesson_type == "vocabulary":
        # Get words for this unit
        words = VOCAB_WORDS.get(unit_id, VOCAB_WORDS[1])
        if not words or len(words) < 4:
            words = VOCAB_WORDS[1]
        
        # Pick a random word from the unit
        word_pair = random.choice(words)
        english_word = word_pair[0]
        correct_mongolian = word_pair[1]
        
        # Get wrong answers - ONLY from the SAME unit to keep related vocabulary
        other_words = [w for w in words if w[1] != correct_mongolian]
        
        # If not enough wrong answers in this unit, get from unit 1
        if len(other_words) < 3:
            # Get from unit 1 as backup
            backup_words = VOCAB_WORDS[1]
            for w in backup_words:
                if w[1] not in [correct_mongolian] and w[1] not in [ow[1] for ow in other_words]:
                    other_words.append(w)
                    if len(other_words) >= 3:
                        break
        
        # Randomly pick 3 wrong answers
        wrongs = random.sample(other_words, min(3, len(other_words)))
        wrong_meanings = [w[1] for w in wrongs]
        
        # Create options
        opts = wrong_meanings + [correct_mongolian]
        random.shuffle(opts)
        
        return {
            "type": "vocabulary", 
            "q": f"What does '{english_word}' mean?", 
            "opts": opts, 
            "ans": correct_mongolian
        }
        
    elif lesson_type == "grammar":
        rules = GRAMMAR_RULES.get(unit_id, GRAMMAR_RULES[1])
        return {"type": "grammar", **random.choice(rules)}
        
    else:  # listening
        phrases = LISTENING_PHRASES.get(unit_id, LISTENING_PHRASES[1])
        phrase = random.choice(phrases)
        return {"type": "listening", "q": "Type what you hear:", "audio": phrase, "ans": phrase}

def generate_math_question(unit_id):
    if unit_id <= 15: a, b, op = random.randint(1, 10), random.randint(1, 10), random.choice(['+', '-'])
    elif unit_id <= 35: a, b, op = random.randint(10, 50), random.randint(5, 25), '×'
    else: a, b, op = random.randint(20, 100), random.randint(5, 20), '÷'
    if op == '+': ans, q = a + b, f"{a} + {b} = ?"
    elif op == '-':
        if a < b: a, b = b, a
        ans, q = a - b, f"{a} - {b} = ?"
    elif op == '×': ans, q = a * b, f"{a} × {b} = ?"
    else: ans, q = round(a / b, 1), f"{a} ÷ {b} = ?"
    wrongs = []
    for _ in range(3):
        w = round(ans + random.uniform(-ans*0.3, ans*0.3), 1) if isinstance(ans, float) else ans + random.randint(-10, 10)
        if w != ans and w not in wrongs: wrongs.append(w)
    while len(wrongs) < 3: wrongs.append(ans + len(wrongs) + 1)
    opts = [str(ans)] + [str(w) for w in wrongs]
    random.shuffle(opts)
    return {"q": q, "opts": opts, "ans": str(ans)}
def check_heart_refill(user_data, force_no_refill=False):
    hearts = user_data.get("hearts", 5)
    
    if force_no_refill:
        return user_data
    
    if hearts >= 5:
        user_data["hearts"] = 5
        user_data["last_heart_refill"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return user_data
    
    last_refill = user_data.get("last_heart_refill")
    if last_refill:
        try:
            last_dt = datetime.strptime(last_refill, '%Y-%m-%d %H:%M:%S')
            minutes_passed = (datetime.now() - last_dt).total_seconds() / 60
            hearts_to_add = int(minutes_passed / 180)
            
            if hearts_to_add > 0:
                new_hearts = min(5, hearts + hearts_to_add)
                if new_hearts > hearts:
                    user_data["hearts"] = new_hearts
                    user_data["last_heart_refill"] = (datetime.now() - timedelta(minutes=minutes_passed % 180)).strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
    else:
        user_data["last_heart_refill"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return user_data

def load_chests(u):
    try: return [i['unit_id'] for i in supabase.table('chests_claimed').select('unit_id').eq('username',u).execute().data]
    except: return []

def save_chest(u,uid):
    try: supabase.table('chests_claimed').insert({'username':u,'unit_id':uid}).execute()
    except: pass

# ===== ROUTES =====
@app.route('/')
def index(): return send_from_directory('static', 'index.html' if 'username' not in session else 'home.html')

@app.route('/home')
def home(): return send_from_directory('static', 'index.html' if 'username' not in session else 'home.html')

@app.route('/unit/<int:unit_id>')
def unit(unit_id): return send_from_directory('static', 'index.html' if 'username' not in session else 'unit.html')

@app.route('/exercise')
def exercise(): return send_from_directory('static', 'index.html' if 'username' not in session else 'exercise.html')

@app.route('/profile')
def profile(): return send_from_directory('static', 'index.html' if 'username' not in session else 'profile.html')

@app.route('/admin')
def admin_panel():
    if 'username' not in session: return send_from_directory('static', 'index.html')
    if not is_creator(session['username']): return "Access Denied", 403
    return send_from_directory('static', 'admin.html')
@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    username = d.get('username', '').strip()
    password = d.get('password', '')
    teacher_code = d.get('teacher_code', '').strip().upper()
    
    print(f"DEBUG: Username = {username}")           # ← ADD THIS LINE
    print(f"DEBUG: Teacher code entered = {teacher_code}")  # ← ADD THIS LINE
    
    if not username or not password:
        return jsonify({"success": False, "message": "Missing fields"}), 400
    
    if load_user_data(username):
        return jsonify({"success": False, "message": "Username taken"}), 400
    
    # Creator account
    if username.upper() == CREATOR_USERNAME:
        if password != CREATOR_PASSWORD:
            return jsonify({"success": False, "message": "Invalid creator password"}), 400
        role = "creator"
    # Teacher account - special code!
    elif teacher_code == "TEACHER2026":
        print("✅ TEACHER CODE MATCHED!")   # ← ADD THIS LINE
        role = "teacher"
    else:
        print(f"❌ Teacher code '{teacher_code}' did not match 'TEACHER2026'")  # ← ADD THIS LINE
        role = "student"
    
    save_user_data(username, create_new_user(username, password, role))
    return jsonify({"success": True, "role": role})
@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    username = d.get('username', '').strip()
    password = d.get('password', '')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Missing fields"}), 400
    
    user = load_user_data(username)
    if not user:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    if user['password'] != hashlib.sha256(password.encode()).hexdigest():
        return jsonify({"success": False, "message": "Invalid credentials"}), 401
    
    session['username'] = username
    
    # Update streak
    today = date.today()
    last = user.get('last_active')
    streak = user.get('streak', 0)
    
    if last:
        try:
            last_date = datetime.strptime(last, '%Y-%m-%d').date()
            diff = (today - last_date).days
            if diff == 1:
                streak += 1
            elif diff > 1:
                streak = 1
        except:
            streak = 1
    else:
        streak = 1
    
    user['streak'] = streak
    user['last_active'] = today.isoformat()
    user = check_heart_refill(user)
    save_user_data(username, user)
    
    return jsonify({
        "success": True,
        "is_creator": is_creator(username),
        "role": user.get('role', 'student')
    })
@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route('/api/user', methods=['GET'])
def get_user():
    user = load_user_data(session['username'])
    user = check_heart_refill(user)
    save_user_data(session['username'], user)
    return jsonify({
        "username": user['username'],
        "role": user.get('role', 'student'),  # ← ADD THIS!
        "is_creator": user.get('is_creator', False),
        "hearts": user['hearts'],
        "total_xp": user['total_xp'],
        "streak": user['streak'],
        "subject": user['learning_subject']
    })

@app.route('/api/units', methods=['GET'])
def units():
    username = session['username']
    user = load_user_data(username)
    sub = user['learning_subject']
    units_data = ENGLISH_UNITS if sub == 'Language' else MATH_UNITS
    units_list = []
    
    # Load progress from Supabase
    user_progress = load_progress(username, sub)
    
    for u in units_data:
        completed = sum(1 for i in range(1, u['lessons']+1) if user_progress.get(f"{sub}:{u['id']}:{i}", {}).get('completed'))
        unlocked = u['id'] == 1 or is_creator(session['username']) or (units_list[-1]['completed'] >= 1 if units_list else False)
        units_list.append({"id": u['id'], "name": u['name'], "completed": completed, "total": u['lessons'], "unlocked": unlocked, "has_chest": u.get('chest_at') is not None})
    return jsonify({"units": units_list})

@app.route('/api/set-subject', methods=['POST'])
def set_subject():
    d = request.json
    user = load_user_data(session['username'])
    user['learning_subject'] = d['subject']
    if d.get('math_ui_language'): 
        user['math_ui_language'] = d['math_ui_language']
    save_user_data(session['username'], user)
    return jsonify({"success": True})  # ← MUST KEEP THIS

@app.route('/api/unit/<int:unit_id>/lessons', methods=['GET'])
def lessons(unit_id):
    user = load_user_data(session['username'])
    sub = user['learning_subject']
    units = ENGLISH_UNITS if sub == 'Language' else MATH_UNITS
    unit = next((u for u in units if u['id'] == unit_id), {"name": f"Unit {unit_id}", "lessons": 5, "chest_at": 3})
    chest_claimed = unit_id in user.get('chests_claimed', [])
    lessons_list = []
    for i in range(1, unit['lessons']+1):
        comp = user['progress'].get(f"{sub}:{unit_id}:{i}", {}).get('completed', False)
        unlocked = i == 1 or is_creator(session['username']) or (lessons_list[-1]['completed'] if lessons_list else True)
        has_chest = (i == unit.get('chest_at', 3)) and not chest_claimed
        lessons_list.append({"id": i, "title": f"Lesson {i}", "completed": comp, "unlocked": unlocked, "has_chest": has_chest})
    return jsonify({"unit_name": unit['name'], "lessons": lessons_list})

@app.route('/api/lesson/<int:unit_id>/<int:lesson_id>', methods=['GET'])
def get_lesson(unit_id, lesson_id):
    user = load_user_data(session['username'])
    user = check_heart_refill(user)
    save_user_data(session['username'], user)
    if user['hearts'] <= 0 and not is_creator(session['username']): return jsonify({"error": "No hearts left!"}), 403
    sub = user['learning_subject']
    questions = [generate_question(unit_id) if sub == 'Language' else generate_math_question(unit_id) for _ in range(5)]
    return jsonify({"questions": questions, "hearts": user['hearts'] if not is_creator(session['username']) else 999})

@app.route('/api/update-hearts', methods=['POST'])
def update_hearts():
    d = request.json
    user = load_user_data(session['username'])
    if not is_creator(session['username']): user['hearts'] = max(0, d['hearts'])
    save_user_data(session['username'], user)
    return jsonify({"success": True})

@app.route('/api/complete-lesson', methods=['POST'])
def complete_lesson():
    d = request.json
    username = session['username']
    user = load_user_data(username)
    sub = user['learning_subject']
    
    # Update XP
    user['total_xp'] = user.get('total_xp', 0) + (d['score'] * 5)
    
    # Save progress to Supabase (instead of user['progress'])
    save_progress(username, sub, d['unit_id'], d['lesson_id'], True, d['score'])
    
    chest_reward = None
    if d['lesson_id'] == 3 and d['unit_id'] not in load_chests(username):  # Check Supabase for chests
        reward = random.choice([{"type": "hearts", "value": 1}, {"type": "xp", "value": 100}])
        if reward['type'] == 'hearts': 
            user['hearts'] = min(5, user['hearts'] + reward['value'])
        else: 
            user['total_xp'] += reward['value']
        
        # Save chest to Supabase
        save_chest(username, d['unit_id'])
        user['chests_earned'] = user.get('chests_earned', 0) + 1
        chest_reward = {"name": f"+{reward['value']} {reward['type']}"}
    
    # Save user data (XP, hearts, etc.)
    save_user_data(username, user)
    
    return jsonify({"success": True, "xp_earned": d['score'] * 5, "hearts": user['hearts'], "chest_reward": chest_reward})
@app.route('/api/subjects', methods=['GET'])
def subjects(): return jsonify({"subjects": [{"id": "Language", "name": "Language", "icon": "🌍"}, {"id": "Math", "name": "Математик", "icon": "🔢"}]})

@app.route('/api/languages', methods=['GET'])
def languages():
    return jsonify({"languages": [
        {"code": "English", "name": "English", "flag": "🇬🇧"},
        {"code": "Spanish", "name": "Spanish", "flag": "🇪🇸"},
        {"code": "French", "name": "French", "flag": "🇫🇷"}
    ]})

@app.route('/api/math-ui-languages', methods=['GET'])
def math_ui(): return jsonify({"languages": [{"code": "English", "name": "English UI", "flag": "🇬🇧"}, {"code": "Mongolian", "name": "Монгол UI", "flag": "🇲🇳"}]})

@app.route('/api/refill-hearts', methods=['POST'])
def refill_hearts():
    user = load_user_data(session['username'])
    if is_creator(session['username']): user['hearts'] = 999
    elif user['total_xp'] >= 500:
        user['total_xp'] -= 500
        user['hearts'] = 5
    else: return jsonify({"success": False, "message": "Not enough XP!"})
    save_user_data(session['username'], user)
    return jsonify({"success": True, "hearts": user['hearts']})

@app.route('/api/profile-stats', methods=['GET'])
def profile_stats():
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    user_data = load_user_data(session['username'])
    if not user_data: return jsonify({"error": "User not found"}), 404
    user_data = check_heart_refill(user_data)
    save_user_data(session['username'], user_data)
    lessons_completed = sum(1 for v in user_data.get("progress", {}).values() if v.get("completed", False))
    return jsonify({
        "username": user_data["username"],
        "display_name": "👑 Dear Creator" if is_creator(session['username']) else "Hello",
        "is_creator": user_data.get("is_creator", False),
        "learning_language": user_data.get("learning_language", "English"),
        "subject": user_data.get("learning_subject", "Language"),
        "streak": user_data.get("streak", 0),
        "total_xp": user_data.get("total_xp", 0),
        "hearts": user_data.get("hearts", 5),
        "chests_earned": user_data.get("chests_earned", 0),
        "lessons_completed": lessons_completed,
        "member_since": user_data.get("created_at", "Today").split()[0]
    })

# ===== ADMIN ROUTES =====
@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    if 'username' not in session: 
        return jsonify({"error": "Not logged in"}), 401
    if not is_creator(session['username']): 
        return jsonify({"error": "Not creator"}), 403
    
    users = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json') and filename != 'custom_units.json':
            username = filename[:-5]
            user_data = load_user_data(username)
            if user_data:
                # Calculate lessons completed
                lessons_completed = 0
                for key, value in user_data.get("progress", {}).items():
                    if value.get("completed", False):
                        lessons_completed += 1
                
                users.append({
                    "username": username,
                    "is_creator": user_data.get("is_creator", False),
                    "streak": user_data.get("streak", 0),
                    "total_xp": user_data.get("total_xp", 0),
                    "hearts": user_data.get("hearts", 5),
                    "lessons_completed": lessons_completed
                })
    
    return jsonify({"users": users})

@app.route('/api/admin/user/<username>', methods=['GET'])
def admin_get_user(username):
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    if not is_creator(session['username']): return jsonify({"error": "Not creator"}), 403
    user_data = load_user_data(username)
    if not user_data: return jsonify({"error": "User not found"}), 404
    
    user_data = check_heart_refill(user_data, force_no_refill=True)
    
    return jsonify({
        "username": username, 
        "hearts": user_data.get("hearts", 5), 
        "total_xp": user_data.get("total_xp", 0), 
        "streak": user_data.get("streak", 0), 
        "chests_earned": user_data.get("chests_earned", 0), 
        "learning_language": user_data.get("learning_language", "English"), 
        "learning_subject": user_data.get("learning_subject", "Language")
    })
    
@app.route('/api/admin/user/<username>/delete', methods=['POST'])
def admin_delete_user(username):
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    if not is_creator(session['username']): return jsonify({"error": "Not creator"}), 403
    if username.upper() == CREATOR_USERNAME: return jsonify({"error": "Cannot delete creator"}), 400
    filepath = get_user_file(username)
    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"success": True})
    return jsonify({"error": "User not found"}), 404

@app.route('/api/admin/user/<username>/reset-progress', methods=['POST'])
def admin_reset_progress(username):
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    if not is_creator(session['username']): return jsonify({"error": "Not creator"}), 403
    user_data = load_user_data(username)
    if not user_data: return jsonify({"error": "User not found"}), 404
    user_data['progress'] = {}
    user_data['chests_claimed'] = []
    user_data['chests_earned'] = 0
    save_user_data(username, user_data)
    return jsonify({"success": True})

@app.route('/api/admin/user/<username>/full', methods=['GET'])
def admin_get_user_full(username):
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    if not is_creator(session['username']): return jsonify({"error": "Not creator"}), 403
    user_data = load_user_data(username)
    if not user_data: return jsonify({"error": "User not found"}), 404
    
    # DON'T auto-refill for admin view
    user_data = check_heart_refill(user_data, force_no_refill=True)
    
    return jsonify({
        "username": username,
        "progress": user_data.get("progress", {}),
        "learning_subject": user_data.get("learning_subject", "Language"),
        "hearts": user_data.get("hearts", 5),
        "total_xp": user_data.get("total_xp", 0)
    })
@app.route('/api/admin/user/<username>/update', methods=['POST'])
def admin_update_user(username):
    if 'username' not in session: 
        return jsonify({"error": "Not logged in"}), 401
    if not is_creator(session['username']): 
        return jsonify({"error": "Not creator"}), 403
    user_data = load_user_data(username)
    if not user_data: 
        return jsonify({"error": "User not found"}), 404
    d = request.json
    
    if 'hearts' in d: 
        user_data['hearts'] = max(0, min(999, int(d['hearts'])))       
        user_data['last_heart_refill'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if 'total_xp' in d: 
        user_data['total_xp'] = max(0, int(d['total_xp']))
    if 'streak' in d: 
        user_data['streak'] = max(0, int(d['streak']))
    if 'chests_earned' in d: 
        user_data['chests_earned'] = max(0, int(d['chests_earned']))
    if 'learning_language' in d: 
        user_data['learning_language'] = d['learning_language']
    if 'learning_subject' in d: 
        user_data['learning_subject'] = d['learning_subject']
    
    save_user_data(username, user_data)
    return jsonify({"success": True})
@app.route('/api/admin/user/<username>/update-progress', methods=['POST'])
def admin_update_progress(username):
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    if not is_creator(session['username']): return jsonify({"error": "Not creator"}), 403
    user_data = load_user_data(username)
    if not user_data: return jsonify({"error": "User not found"}), 404
    d = request.json
    if 'progress' in d:
        user_data['progress'] = d['progress']
    save_user_data(username, user_data)
    return jsonify({"success": True})
# ===== TEACHER ROUTES =====
def is_teacher(username):
    user_data = load_user_data(username)
    return user_data and user_data.get("role") in ["teacher", "creator"]

@app.route('/teacher')
def teacher_panel():
    if 'username' not in session: return send_from_directory('static', 'index.html')
    if not is_teacher(session['username']): return "Access Denied", 403
    return send_from_directory('static', 'teacher.html')

@app.route('/api/teacher/students', methods=['GET'])
def teacher_get_students():
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    if not is_teacher(session['username']): return jsonify({"error": "Not authorized"}), 403
    students = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json') and filename != 'custom_units.json':
            username = filename[:-5]
            data = load_user_data(username)
            if data and data.get("role") == "student":
                lessons = sum(1 for v in data.get("progress", {}).values() if v.get("completed", False))
                students.append({
                    "username": username,
                    "streak": data.get("streak", 0),
                    "total_xp": data.get("total_xp", 0),
                    "hearts": data.get("hearts", 5),
                    "lessons_completed": lessons,
                    "learning_language": data.get("learning_language", "English")
                })
    return jsonify({"students": students})

@app.route('/api/teacher/student/<username>/reset-password', methods=['POST'])
def teacher_reset_password(username):
    if 'username' not in session: return jsonify({"error": "Not logged in"}), 401
    if not is_teacher(session['username']): return jsonify({"error": "Not authorized"}), 403
    target = load_user_data(username)
    if not target or target.get("role") != "student":
        return jsonify({"error": "Invalid student"}), 404
    new_password = request.json.get("new_password", "eagle123")
    target["password"] = hashlib.sha256(new_password.encode()).hexdigest()
    save_user_data(username, target)
    return jsonify({"success": True, "message": f"Password reset to: {new_password}"})
application = app

if __name__ == '__main__':
    print("🦅 EagleLearn Ready! http://localhost:5000")
    print("👑 Creator: CREATOR / CREATORENKH2345")
    print("👨‍🏫 Teacher code: TEACHER2026")
    print("📚 50 UNITS WITH FULL LIBRARY!")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
