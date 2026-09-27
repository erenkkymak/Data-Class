import sqlite3
import random
import time
import math
import itertools
from datetime import datetime, timedelta

DB_NAME = "Data-Class.db"
SEED = 42

TABLES = [
    ("Orders_10k", 10_000),
    ("Orders_100k", 100_000),
    ("ORDERS_1M", 1_000_000),
    ("ORDERS_10m", 10_000_000),
]

# Turkiye'nin 81 ili ve TUIK nufus verileri (yaklasik guncel nufus)
CITY_POPULATIONS = [
    ("Adana", 2274106), ("Adiyaman", 604978), ("Afyonkarahisar", 751344), ("Agri", 510626),
    ("Amasya", 339529), ("Ankara", 5803482), ("Antalya", 2688004), ("Artvin", 172356),
    ("Aydin", 1148241), ("Balikesir", 1257590), ("Bilecik", 228058), ("Bingol", 285655),
    ("Bitlis", 353988), ("Bolu", 320824), ("Burdur", 277452), ("Bursa", 3194720),
    ("Canakkale", 559383), ("Cankiri", 195766), ("Corum", 524130), ("Denizli", 1056332),
    ("Diyarbakir", 1804880), ("Edirne", 413903), ("Elazig", 604411), ("Erzincan", 239223),
    ("Erzurum", 749993), ("Eskisehir", 906617), ("Gaziantep", 2154051), ("Giresun", 450862),
    ("Gumushane", 148539), ("Hakkari", 275333), ("Hatay", 1544640), ("Isparta", 445325),
    ("Mersin", 1938389), ("Istanbul", 15655924), ("Izmir", 4462056), ("Kars", 278335),
    ("Kastamonu", 378115), ("Kayseri", 1441523), ("Kirklareli", 373118), ("Kirsehir", 247179),
    ("Kocaeli", 2079072), ("Konya", 2296347), ("Kutahya", 575670), ("Malatya", 742725),
    ("Manisa", 1468279), ("Kahramanmaras", 1116618), ("Mardin", 870374), ("Mugla", 1048185),
    ("Mus", 399202), ("Nevsehir", 310011), ("Nigde", 365735), ("Ordu", 763190),
    ("Rize", 350506), ("Sakarya", 1080080), ("Samsun", 1368488), ("Siirt", 331311),
    ("Sinop", 220799), ("Sivas", 634924), ("Tekirdag", 1142451), ("Tokat", 596454),
    ("Trabzon", 818023), ("Tunceli", 86560), ("Sanliurfa", 2170110), ("Usak", 375454),
    ("Van", 1128749), ("Yozgat", 418442), ("Zonguldak", 588510), ("Aksaray", 433055),
    ("Bayburt", 84241), ("Karaman", 260040), ("Kirikkale", 277046), ("Batman", 634491),
    ("Sirnak", 557605), ("Bartin", 203351), ("Ardahan", 92819), ("Igdir", 203594),
    ("Yalova", 296333), ("Karabuk", 252058), ("Kilis", 147919), ("Osmaniye", 559405),
    ("Duzce", 405131)
]

CITIES = [item[0] for item in CITY_POPULATIONS]
POPULATIONS = [item[1] for item in CITY_POPULATIONS]
CUM_WEIGHTS = list(itertools.accumulate(POPULATIONS))

# Son 1095 gun (3 yil)
END_DATE = datetime(2026, 9, 23)
START_DATE = END_DATE - timedelta(days=1094)
DATE_STRS = [(START_DATE + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1095)]
NUM_DATES = len(DATE_STRS)

# Log-normal medyan 640 TL -> mu = ln(640), sigma = 0.5
MU_AMOUNT = math.log(640.0)
SIGMA_AMOUNT = 0.5

def generate_batch(start_id, batch_size, customer_pool_size):
    r_randint = random.randint
    r_random = random.random
    r_lognorm = random.lognormvariate
    r_round = round
    date_strs = DATE_STRS
    num_dates = NUM_DATES
    mu = MU_AMOUNT
    sigma = SIGMA_AMOUNT

    # Sehirleri nufus agirliklarina gore toplu sec
    batch_cities = random.choices(CITIES, cum_weights=CUM_WEIGHTS, k=batch_size)

    batch = []
    for i in range(batch_size):
        order_id = start_id + i
        customer_id = r_randint(1, customer_pool_size)
        order_date = date_strs[r_randint(0, num_dates - 1)]
        amount = r_round(r_lognorm(mu, sigma), 2)
        
        # En buyuk 50 satici %38 hacim, kalan 10.950 satici %62 hacim
        if r_random() < 0.38:
            seller_id = r_randint(1, 50)
        else:
            seller_id = r_randint(51, 11_000)
            
        city = batch_cities[i]
        batch.append((order_id, customer_id, order_date, amount, seller_id, city))
    return batch

def main():
    print(f"Connecting to SQLite database: {DB_NAME}...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # SQLite Performans Pragma Ayarlari
    cursor.execute("PRAGMA synchronous = OFF;")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA cache_size = -64000;")  # 64 MB RAM cache
    cursor.execute("PRAGMA temp_store = MEMORY;")

    overall_start = time.time()

    for table_name, target_count in TABLES:
        customer_pool_size = max(1, target_count // 20)
        print(f"\n--- Tablo: {table_name} ---")
        print(f"Hedef Satir: {target_count:,} | Musteri Havuzu (N/20): {customer_pool_size:,}")

        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                order_date TEXT,
                amount REAL,
                seller_id INTEGER,
                city TEXT
            );
        """)

        # Her tablo icin tohumu sifirla (deterministik ve sabit)
        random.seed(SEED)

        batch_size = 100_000 if target_count >= 100_000 else 10_000
        inserted = 0
        t0 = time.time()

        conn.execute("BEGIN TRANSACTION;")
        while inserted < target_count:
            current_batch_size = min(batch_size, target_count - inserted)
            batch_data = generate_batch(inserted + 1, current_batch_size, customer_pool_size)
            cursor.executemany(
                f"INSERT INTO {table_name} (order_id, customer_id, order_date, amount, seller_id, city) VALUES (?, ?, ?, ?, ?, ?);",
                batch_data
            )
            inserted += current_batch_size

            elapsed = time.time() - t0
            rate = inserted / elapsed if elapsed > 0 else 0
            pct = (inserted / target_count) * 100
            print(f"\r[{table_name}] {inserted:,} / {target_count:,} ({pct:.1f}%) - {rate:,.0f} rows/sec", end="", flush=True)

        conn.commit()
        table_time = time.time() - t0
        print(f"\nTamamlandi: {table_name} ({table_time:.2f} saniye).")

    conn.close()
    total_time = time.time() - overall_start
    print(f"\nTum tablolar yeni kurallara gore basariyla olusturuldu! (Toplam sure: {total_time:.2f} sn)")

if __name__ == "__main__":
    main()
