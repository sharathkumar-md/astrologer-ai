"""
Vedic Astrology Remedies Database
Contains remedies (Upay) for each planet including mantras, gemstones, donations, and rituals
"""

from typing import Dict, List, Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# Planet Remedies Database
PLANET_REMEDIES = {
    "sun": {
        "hindi_name": "Surya",
        "day": "Sunday (Ravivar)",
        "color": "Red, Orange, Saffron",
        "metal": "Gold, Copper",
        "gemstone": {
            "primary": "Ruby (Manik)",
            "alternative": "Red Garnet, Red Spinel"
        },
        "mantra": {
            "beej": "Om Hraam Hreem Hraum Sah Suryaya Namah",
            "simple": "Om Suryaya Namah",
            "count": 7000
        },
        "donation": {
            "items": ["Wheat", "Jaggery (Gur)", "Red cloth", "Copper vessel", "Red flowers"],
            "to_whom": "Father figure, elderly person, temple priest",
            "day": "Sunday morning before noon"
        },
        "fasting": "Sunday (eat once after sunset)",
        "worship": "Surya Namaskar at sunrise, offer water to Sun",
        "weak_signs": ["Libra (debilitated)", "Aquarius"],
        "strong_signs": ["Aries (exalted)", "Leo (own sign)"],
        "health_issues": "Heart, eyes, bones, vitality, father's health"
    },

    "moon": {
        "hindi_name": "Chandra",
        "day": "Monday (Somvar)",
        "color": "White, Silver, Light Blue",
        "metal": "Silver",
        "gemstone": {
            "primary": "Pearl (Moti)",
            "alternative": "Moonstone, White Coral"
        },
        "mantra": {
            "beej": "Om Shraam Shreem Shraum Sah Chandraya Namah",
            "simple": "Om Chandraya Namah",
            "count": 11000
        },
        "donation": {
            "items": ["Rice", "White cloth", "Silver", "Milk", "White flowers", "Curd"],
            "to_whom": "Mother figure, women, poor people",
            "day": "Monday evening"
        },
        "fasting": "Monday (white foods only)",
        "worship": "Worship Lord Shiva, offer milk to Shivling",
        "weak_signs": ["Scorpio (debilitated)"],
        "strong_signs": ["Taurus (exalted)", "Cancer (own sign)"],
        "health_issues": "Mental health, emotions, sleep, mother's health, fluids in body"
    },

    "mars": {
        "hindi_name": "Mangal",
        "day": "Tuesday (Mangalvar)",
        "color": "Red, Coral, Orange",
        "metal": "Copper, Gold",
        "gemstone": {
            "primary": "Red Coral (Moonga)",
            "alternative": "Carnelian, Red Jasper"
        },
        "mantra": {
            "beej": "Om Kraam Kreem Kraum Sah Bhaumaya Namah",
            "simple": "Om Angarakaya Namah",
            "count": 10000
        },
        "donation": {
            "items": ["Red lentils (Masoor dal)", "Red cloth", "Copper", "Jaggery", "Red flowers"],
            "to_whom": "Celibate people, soldiers, athletes",
            "day": "Tuesday"
        },
        "fasting": "Tuesday (avoid salt)",
        "worship": "Worship Hanuman, recite Hanuman Chalisa",
        "weak_signs": ["Cancer (debilitated)"],
        "strong_signs": ["Capricorn (exalted)", "Aries, Scorpio (own signs)"],
        "health_issues": "Blood, accidents, surgery, anger, siblings",
        "special_dosha": "Mangal Dosha - affects marriage if Mars in 1st, 4th, 7th, 8th, or 12th house"
    },

    "mercury": {
        "hindi_name": "Budh",
        "day": "Wednesday (Budhvar)",
        "color": "Green, Light Green",
        "metal": "Bronze, Brass",
        "gemstone": {
            "primary": "Emerald (Panna)",
            "alternative": "Green Tourmaline, Peridot"
        },
        "mantra": {
            "beej": "Om Braam Breem Braum Sah Budhaya Namah",
            "simple": "Om Budhaya Namah",
            "count": 9000
        },
        "donation": {
            "items": ["Green moong dal", "Green cloth", "Green vegetables", "Books", "Stationery"],
            "to_whom": "Students, scholars, writers",
            "day": "Wednesday"
        },
        "fasting": "Wednesday (green foods)",
        "worship": "Worship Lord Vishnu, chant Vishnu Sahasranama",
        "weak_signs": ["Pisces (debilitated)"],
        "strong_signs": ["Virgo (exalted and own sign)", "Gemini (own sign)"],
        "health_issues": "Nervous system, speech, skin, intelligence, communication"
    },

    "jupiter": {
        "hindi_name": "Guru/Brihaspati",
        "day": "Thursday (Guruvar)",
        "color": "Yellow, Gold, Saffron",
        "metal": "Gold",
        "gemstone": {
            "primary": "Yellow Sapphire (Pukhraj)",
            "alternative": "Yellow Topaz, Citrine"
        },
        "mantra": {
            "beej": "Om Graam Greem Graum Sah Gurave Namah",
            "simple": "Om Brihaspataye Namah",
            "count": 19000
        },
        "donation": {
            "items": ["Yellow items", "Turmeric", "Chana dal", "Yellow cloth", "Books", "Gold"],
            "to_whom": "Teachers, Brahmins, elderly scholars, priests",
            "day": "Thursday"
        },
        "fasting": "Thursday (banana, yellow foods)",
        "worship": "Worship Lord Vishnu/Dakshinamurthy, visit temple",
        "weak_signs": ["Capricorn (debilitated)"],
        "strong_signs": ["Cancer (exalted)", "Sagittarius, Pisces (own signs)"],
        "health_issues": "Liver, fat, diabetes, children, wealth, wisdom"
    },

    "venus": {
        "hindi_name": "Shukra",
        "day": "Friday (Shukravar)",
        "color": "White, Pink, Light Blue",
        "metal": "Silver, Platinum",
        "gemstone": {
            "primary": "Diamond (Heera)",
            "alternative": "White Sapphire, Zircon, Opal"
        },
        "mantra": {
            "beej": "Om Draam Dreem Draum Sah Shukraya Namah",
            "simple": "Om Shukraya Namah",
            "count": 16000
        },
        "donation": {
            "items": ["White items", "Rice", "Sugar", "White cloth", "Perfume", "Ghee", "Curd"],
            "to_whom": "Women, artists, young girls",
            "day": "Friday"
        },
        "fasting": "Friday (white/sweet foods)",
        "worship": "Worship Goddess Lakshmi, recite Lakshmi Stotram",
        "weak_signs": ["Virgo (debilitated)"],
        "strong_signs": ["Pisces (exalted)", "Taurus, Libra (own signs)"],
        "health_issues": "Reproductive system, kidneys, beauty, marriage, luxury"
    },

    "saturn": {
        "hindi_name": "Shani",
        "day": "Saturday (Shanivar)",
        "color": "Black, Dark Blue, Navy",
        "metal": "Iron, Steel",
        "gemstone": {
            "primary": "Blue Sapphire (Neelam) - WEAR WITH CAUTION",
            "alternative": "Amethyst, Lapis Lazuli (safer alternatives)"
        },
        "mantra": {
            "beej": "Om Praam Preem Praum Sah Shanaischaraya Namah",
            "simple": "Om Shanaischaraya Namah",
            "count": 23000
        },
        "donation": {
            "items": ["Black sesame (til)", "Mustard oil", "Iron items", "Black cloth", "Urad dal"],
            "to_whom": "Servants, laborers, poor, handicapped, elderly",
            "day": "Saturday evening"
        },
        "fasting": "Saturday (eat once, avoid salt)",
        "worship": "Worship Lord Hanuman (Tuesday/Saturday), visit Shani temple",
        "weak_signs": ["Aries (debilitated)"],
        "strong_signs": ["Libra (exalted)", "Capricorn, Aquarius (own signs)"],
        "health_issues": "Bones, joints, chronic diseases, delays, longevity, karma",
        "special_period": "Sade Sati - 7.5 years when Saturn transits over Moon sign"
    },

    "rahu": {
        "hindi_name": "Rahu",
        "day": "Saturday (shared with Saturn)",
        "color": "Smoke-colored, Dark Blue, Black",
        "metal": "Lead, Mixed metals",
        "gemstone": {
            "primary": "Hessonite Garnet (Gomed)",
            "alternative": "Orange Zircon"
        },
        "mantra": {
            "beej": "Om Bhraam Bhreem Bhraum Sah Rahave Namah",
            "simple": "Om Rahave Namah",
            "count": 18000
        },
        "donation": {
            "items": ["Black/blue cloth", "Mustard oil", "Radish", "Blanket", "Coconut"],
            "to_whom": "Sweepers, outcastes, foreigners",
            "day": "Saturday or during eclipse"
        },
        "fasting": "Saturday",
        "worship": "Worship Goddess Durga, recite Durga Chalisa",
        "health_issues": "Mysterious diseases, mental confusion, obsessions, addictions",
        "nature": "Shadow planet - amplifies the house it sits in, creates illusions and desires"
    },

    "ketu": {
        "hindi_name": "Ketu",
        "day": "Tuesday (shared with Mars) or Thursday",
        "color": "Grey, Smoke",
        "metal": "Mixed metals",
        "gemstone": {
            "primary": "Cat's Eye (Lehsunia)",
            "alternative": "Tiger's Eye"
        },
        "mantra": {
            "beej": "Om Sraam Sreem Sraum Sah Ketave Namah",
            "simple": "Om Ketave Namah",
            "count": 17000
        },
        "donation": {
            "items": ["Seven grains mixture", "Blanket", "Grey/brown cloth", "Sesame"],
            "to_whom": "Sadhus, spiritual people, beggars",
            "day": "Tuesday or during eclipse"
        },
        "fasting": "Tuesday or during Ketu periods",
        "worship": "Worship Lord Ganesha, recite Ganesha Atharvashirsha",
        "health_issues": "Mysterious ailments, surgeries, spiritual issues, past karma",
        "nature": "Shadow planet - brings detachment, spirituality, moksha, past life karma"
    }
}


# Dosha (Affliction) Remedies
DOSHA_REMEDIES = {
    "mangal_dosha": {
        "name": "Mangal Dosha / Kuja Dosha",
        "description": "Mars in 1st, 4th, 7th, 8th, or 12th house from Ascendant/Moon",
        "effects": "Delays in marriage, conflicts with spouse, accidents",
        "remedies": [
            "Worship Hanuman on Tuesdays",
            "Recite Hanuman Chalisa daily",
            "Donate red items on Tuesday",
            "Wear Red Coral after consultation",
            "Kumbh Vivah (symbolic marriage to tree/pot) before actual marriage",
            "Marry a Manglik person (doshas cancel out)"
        ]
    },
    "kalsarp_dosha": {
        "name": "Kalsarp Dosha",
        "description": "All planets between Rahu and Ketu axis",
        "effects": "Obstacles in life, sudden setbacks, mental stress",
        "remedies": [
            "Kalsarp Dosha Puja at Trimbakeshwar or Ujjain",
            "Worship Lord Shiva with milk abhishek",
            "Recite Maha Mrityunjaya Mantra 108 times daily",
            "Keep fast on Nag Panchami",
            "Donate to snake-related charities"
        ]
    },
    "pitra_dosha": {
        "name": "Pitra Dosha",
        "description": "Sun/Moon afflicted by Rahu/Ketu, issues with ancestors",
        "effects": "Problems with children, career obstacles, family conflicts",
        "remedies": [
            "Perform Shraddh for ancestors",
            "Offer Pind Daan at Gaya",
            "Feed Brahmins on Amavasya",
            "Donate food to poor on father's death anniversary",
            "Plant Peepal tree and water it regularly"
        ]
    },
    "sade_sati": {
        "name": "Sade Sati",
        "description": "7.5 years Saturn transit over Moon sign (before, on, after)",
        "effects": "Challenges, delays, health issues, mental stress",
        "remedies": [
            "Recite Shani Mantra on Saturdays",
            "Donate black items on Saturday evening",
            "Worship Hanuman (protector from Saturn)",
            "Pour mustard oil on Shani idol",
            "Help servants and laborers",
            "Be patient - this period teaches valuable lessons"
        ]
    }
}


def get_planet_remedy(planet_name: str) -> Optional[Dict]:
    """
    Get remedies for a specific planet

    Args:
        planet_name: Name of planet (sun, moon, mars, etc.)

    Returns:
        Dictionary of remedies or None if planet not found
    """
    planet_key = planet_name.lower().strip()

    # Handle Hindi names
    hindi_to_english = {
        "surya": "sun",
        "chandra": "moon",
        "mangal": "mars",
        "budh": "mercury",
        "guru": "jupiter",
        "brihaspati": "jupiter",
        "shukra": "venus",
        "shani": "saturn"
    }

    if planet_key in hindi_to_english:
        planet_key = hindi_to_english[planet_key]

    return PLANET_REMEDIES.get(planet_key)


def get_dosha_remedy(dosha_name: str) -> Optional[Dict]:
    """
    Get remedies for a specific dosha

    Args:
        dosha_name: Name of dosha (mangal_dosha, kalsarp_dosha, etc.)

    Returns:
        Dictionary of remedies or None if dosha not found
    """
    dosha_key = dosha_name.lower().strip().replace(" ", "_")
    return DOSHA_REMEDIES.get(dosha_key)


def get_gemstone_for_planet(planet_name: str) -> Optional[Dict]:
    """
    Get gemstone recommendation for a planet

    Args:
        planet_name: Name of planet

    Returns:
        Gemstone info dict or None
    """
    remedy = get_planet_remedy(planet_name)
    if remedy:
        return remedy.get("gemstone")
    return None


def get_mantra_for_planet(planet_name: str) -> Optional[Dict]:
    """
    Get mantra for a planet

    Args:
        planet_name: Name of planet

    Returns:
        Mantra info dict or None
    """
    remedy = get_planet_remedy(planet_name)
    if remedy:
        return remedy.get("mantra")
    return None


def format_remedy_for_response(planet_name: str) -> str:
    """
    Format remedy information for LLM response

    Args:
        planet_name: Name of planet

    Returns:
        Formatted string for LLM to use
    """
    remedy = get_planet_remedy(planet_name)
    if not remedy:
        return f"Remedies for {planet_name} not found."

    hindi = remedy.get("hindi_name", planet_name)
    day = remedy.get("day", "")
    mantra = remedy.get("mantra", {}).get("simple", "")
    gemstone = remedy.get("gemstone", {}).get("primary", "")
    donation = remedy.get("donation", {}).get("items", [])

    result = f"""
{hindi} Remedies:
- Day: {day}
- Mantra: {mantra}
- Gemstone: {gemstone}
- Donate: {', '.join(donation[:3])}
"""
    return result.strip()


def get_all_planet_remedies() -> Dict:
    """Get all planet remedies"""
    return PLANET_REMEDIES


def get_all_dosha_remedies() -> Dict:
    """Get all dosha remedies"""
    return DOSHA_REMEDIES
