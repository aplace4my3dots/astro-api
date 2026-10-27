from flask import Flask, request, jsonify
import swisseph as swe
from datetime import datetime
import os
import requests

app = Flask(__name__)

zodiac_signs = ["حمل", "ثور", "جوزا", "سرطان", "اسد", "سنبله", "میزان", "عقرب", "قوس", "جدی", "دلو", "حوت"]

def get_zodiac_sign(degree):
    index = int(degree / 30)
    return zodiac_signs[index]

def get_coordinates(city_name):
    # سیستم نقشه‌یاب فوق‌سریع بدون قطعی
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        response = requests.get(url, timeout=5)
        data = response.json()
        if "results" in data and len(data["results"]) > 0:
            return data["results"][0]["latitude"], data["results"][0]["longitude"]
    except:
        pass
    return None, None

@app.route('/', methods=['GET'])
def home():
    return "موتور محاسبات آسترولوژی فعال است. نسخه نهایی و پایدار."

@app.route('/calculate', methods=['POST'])
def calculate_chart():
    try:
        data = request.json
        city = data.get('city')
        date_str = data.get('date')
        time_str = data.get('time')
        
        if not city or not date_str or not time_str:
            return jsonify({"error": "لطفاً شهر، تاریخ و ساعت را کامل وارد کنید."}), 400

        lat, lon = get_coordinates(city)
        if lat is None:
            return jsonify({"error": f"مختصات شهر '{city}' پیدا نشد. نام شهر را به انگلیسی تایپ کنید."}), 404
            
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + (dt.minute/60.0))
        
        sun_pos, _ = swe.calc_ut(jd, swe.SUN)
        moon_pos, _ = swe.calc_ut(jd, swe.MOON)
        cusps, ascmc = swe.houses(jd, lat, lon, b'P')
        
        return jsonify({
            "sun_sign": get_zodiac_sign(sun_pos[0]),
            "moon_sign": get_zodiac_sign(moon_pos[0]),
            "ascendant_sign": get_zodiac_sign(ascmc[0]),
            "location": {"city": city, "lat": round(lat, 4), "lon": round(lon, 4)}
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
