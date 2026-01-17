from kerykeion import AstrologicalSubject, KerykeionChartSVG, NatalAspects
from datetime import datetime
import pytz
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from timezonefinder import TimezoneFinder

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AstroEngine:
    def __init__(self):
        # Nominatim for geocoding (free, no API key needed)
        self.geolocator = Nominatim(
            user_agent="astra_astrology_app/1.0",
            timeout=20
        )
        self.tf = TimezoneFinder()

    def get_location_data(self, location):
        """
        Get location coordinates using Nominatim (free geocoding).

        Args:
            location: Location string (e.g., "Mumbai, India")

        Returns:
            Tuple of (latitude, longitude, timezone) or None
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(2)  # Rate limiting

                location_data = self.geolocator.geocode(
                    location,
                    timeout=15,
                    exactly_one=True
                )

                if location_data:
                    lat = location_data.latitude
                    lon = location_data.longitude
                    tz_str = self.tf.timezone_at(lat=lat, lng=lon) or "UTC"

                    logger.info(f"Location found: {location} -> ({lat}, {lon}, {tz_str})")
                    return lat, lon, tz_str

            except (GeocoderTimedOut, GeocoderServiceError) as e:
                logger.warning(f"Geocoding attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return None
                continue
            except Exception as e:
                logger.error(f"Geocoding error: {e}")
                return None

        logger.error(f"Location not found: {location}")
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
        
        context_parts.append("\n=== PLANETARY POSITIONS (Use these for analysis) ===")
        
        # Focus on key planets for predictions
        key_planets = {
            'sun': 'Surya/Sun',
            'moon': 'Chandra/Moon',
            'mars': 'Mangal/Mars',
            'mercury': 'Budh/Mercury',
            'jupiter': 'Guru/Jupiter',
            'venus': 'Shukra/Venus',
            'saturn': 'Shani/Saturn'
        }
        
        for planet_name, hindi_name in key_planets.items():
            if hasattr(natal_chart, planet_name):
                planet = getattr(natal_chart, planet_name)
                sign = planet.get('sign', 'Unknown')
                house = planet.get('house', 'Unknown')
                position = planet.get('position', 0)
                context_parts.append(f"{hindi_name}: {position:.1f}° in {sign} sign, {house} house")
        
        # Add house rulers and key information
        context_parts.append("\n=== KEY HOUSES (Analyze based on question) ===")
        house_meanings = {
            1: "1st house (Self, personality, health)",
            2: "2nd house (Wealth, family, speech)",
            4: "4th house (Mother, home, happiness)",
            5: "5th house (Children, creativity, intelligence)",
            7: "7th house (Marriage, partnerships, spouse)",
            8: "8th house (Transformation, sudden events, risk)",
            9: "9th house (Father, luck, higher learning)",
            10: "10th house (Career, status, profession)",
            11: "11th house (Gains, achievements, friends)"
        }
        
        for house_num, description in house_meanings.items():
            house_attr = f"house{house_num}" if house_num > 1 else "first_house"
            if hasattr(natal_chart, house_attr):
                house = getattr(natal_chart, house_attr)
                sign = house.get('sign', 'Unknown')
                context_parts.append(f"{description}: {sign} sign")
        
        context_parts.append("\n=== ANALYSIS TIPS ===")
        context_parts.append("- For career: Check 10th house, Sun, Saturn, and 2nd/11th houses")
        context_parts.append("- For business: Check 2nd, 10th, 11th houses, Mars, Jupiter, Mercury")
        context_parts.append("- For marriage: Check 7th house, Venus, and Moon")
        context_parts.append("- For partnerships: Check 7th house and Venus")
        context_parts.append("- Planets in 8th house indicate risk-taking ability")
        context_parts.append("- Strong Jupiter = good for expansion/growth")
        context_parts.append("- Strong Saturn = discipline but delays")
        
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
    