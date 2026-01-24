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

        context_parts.append("\n=== PLANETARY POSITIONS ===")

        # Key planets with retrograde check
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
                retrograde = planet.get('retrograde', False)
                retro_mark = " (R)" if retrograde else ""
                context_parts.append(f"{hindi_name}{retro_mark}: {position:.1f}° in {sign}, {house} house")

        # Add Rahu/Ketu (Lunar Nodes) - Critical for Vedic astrology
        context_parts.append("\n=== RAHU/KETU (Karmic Axis) ===")
        rahu = None
        ketu = None
        # Try different attribute names for lunar nodes
        for attr in ['true_north_lunar_node', 'mean_node', 'true_node']:
            if hasattr(natal_chart, attr):
                rahu = getattr(natal_chart, attr)
                if rahu is not None:
                    break
        for attr in ['true_south_lunar_node', 'mean_south_node']:
            if hasattr(natal_chart, attr):
                ketu = getattr(natal_chart, attr)
                if ketu is not None:
                    break

        if rahu:
            # Handle both dict and object attribute access
            rahu_sign = rahu.get('sign', 'Unknown') if isinstance(rahu, dict) else getattr(rahu, 'sign', 'Unknown')
            rahu_house = rahu.get('house', 'Unknown') if isinstance(rahu, dict) else getattr(rahu, 'house', 'Unknown')
            rahu_pos = rahu.get('position', 0) if isinstance(rahu, dict) else getattr(rahu, 'position', 0)
            context_parts.append(f"Rahu (North Node): {rahu_pos:.1f}° in {rahu_sign}, {rahu_house}")

        if ketu:
            ketu_sign = ketu.get('sign', 'Unknown') if isinstance(ketu, dict) else getattr(ketu, 'sign', 'Unknown')
            ketu_house = ketu.get('house', 'Unknown') if isinstance(ketu, dict) else getattr(ketu, 'house', 'Unknown')
            ketu_pos = ketu.get('position', 0) if isinstance(ketu, dict) else getattr(ketu, 'position', 0)
            context_parts.append(f"Ketu (South Node): {ketu_pos:.1f}° in {ketu_sign}, {ketu_house}")

        if not rahu and not ketu:
            context_parts.append("Rahu/Ketu: Data not available")

        # ALL 12 houses with meanings
        context_parts.append("\n=== ALL 12 HOUSES ===")
        house_attrs = {
            1: ("first_house", "1st (Self, body, personality)"),
            2: ("second_house", "2nd (Wealth, family, speech)"),
            3: ("third_house", "3rd (Siblings, courage, communication)"),
            4: ("fourth_house", "4th (Mother, home, happiness)"),
            5: ("fifth_house", "5th (Children, creativity, romance)"),
            6: ("sixth_house", "6th (Health issues, enemies, debts)"),
            7: ("seventh_house", "7th (Marriage, partnerships, spouse)"),
            8: ("eighth_house", "8th (Transformation, death, inheritance)"),
            9: ("ninth_house", "9th (Father, luck, dharma)"),
            10: ("tenth_house", "10th (Career, status, profession)"),
            11: ("eleventh_house", "11th (Gains, friends, achievements)"),
            12: ("twelfth_house", "12th (Losses, moksha, foreign travel)")
        }

        for house_num, (house_attr, description) in house_attrs.items():
            if hasattr(natal_chart, house_attr):
                house = getattr(natal_chart, house_attr)
                if house:
                    # Handle both dict and object attribute access
                    sign = house.get('sign', 'Unknown') if isinstance(house, dict) else getattr(house, 'sign', 'Unknown')
                    context_parts.append(f"{description}: {sign}")

        # Topic-specific analysis guides
        context_parts.append("\n=== INTERPRETATION GUIDE ===")
        context_parts.append("CAREER: 10th house + Sun + Saturn + 6th house (job)")
        context_parts.append("MONEY: 2nd house (savings) + 11th house (gains) + Jupiter")
        context_parts.append("MARRIAGE: 7th house + Venus + 5th house (romance)")
        context_parts.append("HEALTH: 1st house + 6th house + Moon (mind) + Mars (energy)")
        context_parts.append("EDUCATION: 4th house + 5th house + Mercury + Jupiter")
        context_parts.append("FOREIGN: 12th house + 9th house + Rahu")
        context_parts.append("SPIRITUAL: 12th house + 9th house + Ketu + Jupiter")

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
    