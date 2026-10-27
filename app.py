from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime
import os
import requests

app = Flask(__name__)

# آرایه نشان‌های زودیاک (هر نشان 30 درجه است)
zodiac_signs = [
    "حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله", 
    "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت"
]

def get_zodiac_sign(degree):
    index = int(degree / 30)
    return zodiac_signs[index]

def get_coordinates(city_name):
    # استفاده از API فوق‌سریع و بدون محدودیت برای پیدا کردن شهر
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        response = requests.get(url, timeout=5)
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            lat = data["results"][0]["latitude"]
            lon = data["results"][0]["longitude"]
            return lat, lon
    except:
        pass
    return None, None

@app.route('/', methods=['GET'])
def home():
    return "موتور محاسبات آسترولوژی فعال است. نسخه 2.0 (نقشه‌یاب سریع)"

@app.route('/calculate', methods=['POST'])
def calculate_chart():
    try:
        data = request.json
        city = data.get('city')
        date_str = data.get('date') # Format: YYYY-MM-DD
        time_str = data.get('time') # Format: HH:MM
        
        if not city or not date_str or not time_str:
            return jsonify({"error": "لطفاً شهر، تاریخ و ساعت را ارسال کنید."}), 400

        # ۱. تبدیل نام شهر به مختصات جغرافیایی (سیستم جدید)
        lat, lon = get_coordinates(city)
        if lat is None:
            return jsonify({"error": f"مختصات شهر '{city}' پیدا نشد. لطفاً املای انگلیسی شهر را بررسی کنید (مثال: Tehran)."}), 404
            
        # ۲. محاسبه زمان جولیان (Julian Day)
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
