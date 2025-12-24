from kerykeion import AstrologicalSubject, KerykeionChartSVG, NatalAspects
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timezonefinder import TimezoneFinder

class AstroEngine:
    def __init__(self):
        self.geolocator = Nominatim(user_agent="astra_astrology_bot")
        self.tf = TimezoneFinder()
    
    def get_location_data(self, location):
        try:
            location_data = self.geolocator.geocode(location, timeout=10, addressdetails=True)
            if location_data:
                lat = location_data.latitude
                lon = location_data.longitude
                tz_str = self.tf.timezone_at(lat=lat, lng=lon)
                return lat, lon, tz_str
            return None
        except (GeocoderTimedOut, GeocoderServiceError):
            return None
    
    def create_natal_chart(self, name, year, month, day, hour, minute, location, lat, lon, tz_str):
        subject = AstrologicalSubject(
            name=name,
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            city=location,
            lat=lat,
            lng=lon,
            tz_str=tz_str
        )
        return subject
    
    def get_chart_data(self, chart):
        """Extract chart data in a serializable format"""
        chart_data = {
            "planets": [],
            "houses": []
        }
        
        # Get planet data
        planet_names = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
        for planet_name in planet_names:
            if hasattr(chart, planet_name):
                planet = getattr(chart, planet_name)
                chart_data["planets"].append({
                    "name": planet_name.capitalize(),
                    "sign": planet.get("sign", ""),
                    "position": planet.get("position", 0),
                    "house": planet.get("house", "")
                })
        
        # Get house data
        for i in range(1, 13):
            house_attr = f"house{i}" if i > 1 else "first_house"
            if hasattr(chart, house_attr):
                house = getattr(chart, house_attr)
                chart_data["houses"].append({
                    "number": i,
                    "sign": house.get("sign", ""),
                    "position": house.get("position", 0)
                })
        
        return chart_data
    
    def get_transit_chart(self, location, lat, lon, tz_str):
        now = datetime.now(pytz.timezone(tz_str))
        transit = AstrologicalSubject(
            name="Transit",
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            city=location,
            lat=lat,
            lng=lon,
            tz_str=tz_str
        )
        return transit
    
    def build_natal_context(self, natal_chart):
        context_parts = []
        context_parts.append(f"Birth Chart for {natal_chart.name}")
        context_parts.append(f"Born: {natal_chart.day}/{natal_chart.month}/{natal_chart.year} at {natal_chart.hour}:{natal_chart.minute} in {natal_chart.city}")
        
        # Get ascendant
        if hasattr(natal_chart, 'first_house'):
            first_house = natal_chart.first_house
            context_parts.append(f"Ascendant (Lagna): {first_house.get('sign', 'Unknown')}")
        
        context_parts.append("\nKey Planetary Positions:")
        
        # Focus on key planets for predictions
        key_planets = {
            'sun': 'Sun (career, authority, father)',
            'moon': 'Moon (mind, emotions, mother)',
            'mars': 'Mangal (energy, courage, action)',
            'mercury': 'Mercury (communication, intelligence)',
            'jupiter': 'Guru (wisdom, growth, luck)',
            'venus': 'Shukra (love, relationships, luxury)',
            'saturn': 'Shani (discipline, karma, delays)',
            'rahu': 'Rahu (ambition, foreign, sudden events)',
            'ketu': 'Ketu (spirituality, detachment, past karma)'
        }
        
        for planet_name, description in key_planets.items():
            if hasattr(natal_chart, planet_name):
                planet = getattr(natal_chart, planet_name)
                context_parts.append(f"{description}: {planet.get('position', 0):.1f}° in {planet.get('sign', 'Unknown')}, {planet.get('house', 'Unknown')} house")
        
        # Add important house information
        context_parts.append("\nKey Houses:")
        important_houses = {
            1: "1st house (self, personality)",
            7: "7th house (relationships, marriage)",
            10: "10th house (career, status)",
            11: "11th house (gains, achievements)"
        }
        
        for house_num, description in important_houses.items():
            house_attr = f"house{house_num}" if house_num > 1 else "first_house"
            if hasattr(natal_chart, house_attr):
                house = getattr(natal_chart, house_attr)
                context_parts.append(f"{description}: {house.get('sign', 'Unknown')} sign")
        
        return "\n".join(context_parts)
    
    def build_transit_context(self, transit_chart, natal_chart):
        context_parts = []
        context_parts.append(f"\nCurrent Transits ({transit_chart.day}/{transit_chart.month}/{transit_chart.year}):")
        
        try:
            aspects = NatalAspects(natal_chart)
            
            if hasattr(aspects, 'all_aspects') and aspects.all_aspects:
                for aspect in aspects.all_aspects:
                    context_parts.append(f"{aspect['p1_name']} {aspect['aspect']} {aspect['p2_name']} (orb: {aspect['orbit']:.2f}°)")
        except Exception as e:
            context_parts.append(f"Aspects calculation unavailable")
        
        planet_names = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
        
        for planet_name in planet_names:
            if hasattr(transit_chart, planet_name):
                planet = getattr(transit_chart, planet_name)
                context_parts.append(f"Transit {planet_name.capitalize()} at {planet.get('position', 0):.1f}° in {planet.get('sign', 'Unknown')}")
        
        return "\n".join(context_parts)
