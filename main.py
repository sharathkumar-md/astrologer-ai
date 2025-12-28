import sys
import json
import time
from database import UserDatabase
from astro_engine import AstroEngine
from llm_bridge import LLMBridge
import config

class AstraBot:
    def __init__(self):
        self.db = UserDatabase(config.DB_NAME)
        self.astro = AstroEngine()
        self.llm = LLMBridge()
        self.current_user_id = None
        self.current_natal_chart = None
        self.current_location = None
        self.current_lat = None
        self.current_lon = None
        self.current_tz = None
        self.conversation_history = []  # Track conversation context
    
    def display_banner(self):
        print("\n" + "="*60)
        print("✨ ASTRA - Your Cosmic Companion ✨".center(60))
        print("Vedic Astrology meets AI Wisdom".center(60))
        print("="*60 + "\n")
    
    def get_location_data(self, location):
        print(f"\nSearching for '{location}'...")
        location_data = self.astro.get_location_data(location)
        
        if location_data:
            lat, lon, tz_str = location_data
            print(f"✓ Found: {location}")
            print(f"  Coordinates: ({lat:.4f}, {lon:.4f})")
            print(f"  Timezone: {tz_str}")
            return location_data
        
        print(f"\n✗ Location '{location}' not found.")
        print("Please try again with more details (e.g., 'City, State, Country')")
        return None
    
    def create_new_user(self):
        print("\n--- Create New Birth Chart ---")
        name = input("Enter your name: ").strip()
        
        print("\nBirth Date (DD/MM/YYYY):")
        date_str = input("Date: ").strip()
        day, month, year = map(int, date_str.split('/'))
        
        print("\nBirth Time (HH:MM in 24-hour format):")
        time_str = input("Time: ").strip()
        hour, minute = map(int, time_str.split(':'))
        
        location_data = None
        while not location_data:
            location = input("\nBirth Location (City, State, Country): ").strip()
            location_data = self.get_location_data(location)
        
        lat, lon, tz_str = location_data
        
        print("\nGenerating your birth chart...")
        natal_chart = self.astro.create_natal_chart(
            name, year, month, day, hour, minute, location, lat, lon, tz_str
        )
        
        chart_data = self.astro.get_chart_data(natal_chart)
        
        user_id = self.db.add_user(
            name, date_str, time_str, location, lat, lon, tz_str, chart_data
        )
        
        print(f"\n✓ Birth chart created successfully! User ID: {user_id}")
        return user_id, natal_chart, location, lat, lon, tz_str
    
    def select_user(self):
        users = self.db.list_users()
        
        if not users:
            print("\nNo users found. Let's create your birth chart!")
            return self.create_new_user()
        
        print("\n--- Existing Users ---")
        for user_id, name, birth_date in users:
            print(f"{user_id}. {name} (Born: {birth_date})")
        
        print(f"{len(users) + 1}. Create New User")
        
        while True:
            try:
                choice = int(input("\nSelect user (enter number): "))
                break
            except ValueError:
                print("❌ Please enter a valid number!")
                continue
        
        if choice == len(users) + 1:
            return self.create_new_user()
        else:
            user_data = self.db.get_user(choice)
            if user_data:
                user_id, name, birth_date, birth_time, birth_location, lat, lon, tz_str, natal_chart_json, created_at = user_data
                
                day, month, year = map(int, birth_date.split('/'))
                hour, minute = map(int, birth_time.split(':'))
                
                natal_chart = self.astro.create_natal_chart(
                    name, year, month, day, hour, minute, birth_location, lat, lon, tz_str
                )
                
                # Load last 20 messages from database
                self.conversation_history = self.db.get_conversation_history(user_id, limit=20)
                
                print(f"\n✓ Loaded chart for {name}")
                if self.conversation_history:
                    print(f"✓ Loaded {len(self.conversation_history)//2} previous conversations")
                return user_id, natal_chart, birth_location, lat, lon, tz_str
            else:
                print("Invalid selection!")
                sys.exit(1)
    
    def chat_loop(self):
        print("\n" + "-"*60)
        print("You can now ask Astra anything about your life and emotions.")
        print("Type 'exit' to end the session.")
        print("-"*60 + "\n")
        
        while True:
            query = input("You: ").strip()
            
            if query.lower() in ['exit', 'quit', 'bye']:
                print("\nAstra: May the stars guide you always. Until we meet again! 🌟\n")
                break
            
            if not query:
                continue
            
            print("\nAstra is consulting the cosmos...\n")
            
            natal_context = self.astro.build_natal_context(self.current_natal_chart)
            transit_chart = self.astro.get_transit_chart(self.current_location, self.current_lat, self.current_lon, self.current_tz)
            transit_context = self.astro.build_transit_context(transit_chart, self.current_natal_chart)
            
            # Pass conversation history to maintain context
            response = self.llm.generate_response(natal_context, transit_context, query, self.conversation_history)
            
            # Split response into multiple messages if it contains |||
            if '|||' in response:
                messages = [msg.strip() for msg in response.split('|||') if msg.strip()]
                for i, msg in enumerate(messages):
                    if i > 0:  # Add small delay between messages for natural feel
                        time.sleep(0.5)
                    print(f"Astra: {msg}\n")
                # Store the full response in conversation history
                full_response = ' '.join(messages)
            else:
                print(f"Astra: {response}\n")
                full_response = response
            
            # Add to conversation history (keep last 20 messages for context)
            self.conversation_history.append({"role": "user", "content": query})
            self.conversation_history.append({"role": "assistant", "content": full_response})
            if len(self.conversation_history) > 40:  # Keep last 20 exchanges (40 messages)
                self.conversation_history = self.conversation_history[-40:]
            
            # Save to database
            self.db.add_conversation(self.current_user_id, query, full_response)
    
    def run(self):
        self.display_banner()
        
        self.current_user_id, self.current_natal_chart, self.current_location, self.current_lat, self.current_lon, self.current_tz = self.select_user()
        self.chat_loop()

if __name__ == "__main__":
    bot = AstraBot()
    bot.run()
