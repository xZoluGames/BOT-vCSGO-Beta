# backend/core/config_profiles.py
class ConfigProfiles:
    BEGINNER = {
        "use_proxy": False,
        "use_database": False,
        "scrapers": ["waxpeer", "csdeals", "empire"],
        "update_interval": 300
    }
    
    ADVANCED = {
        "use_proxy": True,
        "use_database": True,
        "scrapers": "all",
        "update_interval": 60
    }