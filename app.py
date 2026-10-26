from flask import Flask, request, jsonify
import swisseph as swe
from geopy.geocoders import Nominatim
from datetime import datetime
import os

app = Flask(__name__)

# آرایه نشان‌های زودیاک (هر نشان 30 درجه است)
zodiac_signs = [
    "حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله", 
    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت"
]

def get_zodiac_sign(degree):
    index = int(degree / 30)
    return zodiac_signs[index]

@app.route('/', methods=['GET'])
def home():
    return "موتور محاسبات آسترولوژی فعال است. لطفاً داده‌ها را به /calculate ارسال کنید."

@app.route('/calculate', methods=['POST'])
def calculate_chart():
    try:
        data = request.json
        city = data.get('city')
        date_str = data.get('date') # Format: YYYY-MM-DD
        time_str = data.get('time') # Format: HH:MM
        
        if not city or not date_str or not time_str:
            return jsonify({"error": "لطفاً شهر، تاریخ و ساعت را ارسال کنید."}), 400

        # ۱. تبدیل نام شهر به مختصات جغرافیایی
        geolocator = Nominatim(user_agent="astro_engine_prod")
        location = geolocator.geocode(city)
        if not location:
            return jsonify({"error": f"مختصات شهر {city} پیدا نشد."}), 404
            
        lat, lon = location.latitude, location.longitude
        
        # ۲. محاسبه زمان جولیان (Julian Day) برای Swiss Ephemeris
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        # اضافه کردن فرمول دقیق تبدیل زمان (بدون در نظر گرفتن پیچیدگی‌های Timezone در این نسخه ساده)
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + (dt.minute/60.0))
        
        # ۳. محاسبه مختصات سیارات
        sun_pos, _ = swe.calc_ut(jd, swe.SUN)
        moon_pos, _ = swe.calc_ut(jd, swe.MOON)
        
        # ۴. محاسبه رایزینگ و خانه‌ها (سیستم پلاسیدوس 'P')
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        ascendant_degree = ascmc[0]
        
        # ۵. خروجی نهایی به صورت JSON
        result = {
            "sun_sign": get_zodiac_sign(sun_pos[0]),
            "moon_sign": get_zodiac_sign(moon_pos[0]),
            "ascendant_sign": get_zodiac_sign(ascendant_degree),
            "location": {
                "city": city,
                "latitude": round(lat, 4),
                "longitude": round(lon, 4)
            }
        }
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # پورت برای سرورهای ابری روی 10000 یا 8080 تنظیم می‌شود
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)