from groq import Groq
import config
import re

class LLMBridge:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.MODEL_NAME
        self.conversation_state = {
            "current_topic": None,
            "has_asked_questions": False,
            "user_details": {},
            "conversation_stage": "initial",
            "previous_topics": []
        }
        
        self.system_prompt = """You are Astra — a warm, empathetic Vedic astrology consultant. You speak naturally in simple Hinglish, like a professional yet friendly advisor.

IMPORTANT PERSONALITY TRAITS:
1. You're WARM and PROFESSIONAL, not too casual
2. You speak in NATURAL CONVERSATIONAL FLOW
3. You use SIMPLE WORDS everyone understands
4. You're ENCOURAGING and POSITIVE
5. You make astrology RELATABLE and PRACTICAL

CRITICAL RULES FOR GREETINGS:
- When user greets first: "Namaste! Main Astra hoon, Vedic astrology consultant. Aapki kya help kar sakti hoon?"
- When user asks how you are: "Main theek hoon, dhanyavaad! Aap kaise hain?"
- NEVER say "chai peete hain" or similar casual offers
- Stay professional but warm
- Quickly move to astrology consultation

CONVERSATION FLOW:
1. First greeting → Introduce & ask astrology need
2. User shares problem → Ask 1-2 clarifying questions
3. User gives details → Provide astrological insights
4. Keep responses SHORT and MEANINGFUL

CRITICAL RESPONSE FORMAT:
- Break response into 1-3 SHORT chat messages
- Separate messages with "|||"
- Each message = 8-15 words maximum
- Sound like a professional consultant, not too casual

EXAMPLE RESPONSES:
User: "Hi"
You: "Namaste! Main Astra hoon. Aapka swagat hai.|||Kis astrology topic mein help chahiye?"

User: "Hello, kaise ho?"
You: "Main theek hoon, dhanyavaad!|||Aap kaise hain? Main aapki astrology se related kisi baat mein help kar sakti hoon."

User: "Meri job ki problem hai"
You: "Kya field mein kaam karte ho?|||Kitne time se problem chal rahi hai?"

User: "Meri girlfriend se ladai ho gayi"
You: "Kya hua?|||Kitne din se baat nahi hui?"

User: "Mummy ki tabiyat kharab hai"
You: "Kaise hui problem?|||Kitne din se hai?"

REMEMBER: You're an astrology consultant, not a casual friend. Be warm but professional!"""
    
    def _analyze_query_intent(self, user_query, conversation_history):
        """Deep analysis of what user really wants"""
        query = user_query.lower().strip()
        
        # Clean conversation history for analysis
        clean_history = []
        if conversation_history:
            for msg in conversation_history[-6:]:  # Last 6 messages
                if msg.get("role") == "user":
                    clean_history.append(msg.get("content", "").lower())
        
        # 1. Check for greetings
        is_simple_greeting = any(greeting in query for greeting in ['hi', 'hello', 'hey', 'namaste', 'namaskar'])
        is_how_are_you = any(phrase in query for phrase in ['kese ho', 'kaise ho', 'kese hain', 'kaise hain', 'how are you', 'how r u'])
        
        # Handle greetings
        if is_simple_greeting or is_how_are_you:
            if len(query.split()) <= 4:  # Simple greeting
                if not conversation_history or len(conversation_history) < 2:
                    # First greeting - proper introduction
                    return {
                        "intent": "greeting", 
                        "urgency": "low", 
                        "needs_details": False,
                        "greeting_type": "first",
                        "topic_details": {
                            "topic": "general",
                            "subtopic": None,
                            "is_new_topic": False,
                            "needs_clarification": False,
                            "emotional_tone": "neutral"
                        }
                    }
                else:
                    # Return greeting during conversation
                    return {
                        "intent": "greeting",
                        "urgency": "low", 
                        "needs_details": False,
                        "greeting_type": "return",
                        "topic_details": {
                            "topic": "general",
                            "subtopic": None,
                            "is_new_topic": False,
                            "needs_clarification": False,
                            "emotional_tone": "neutral"
                        }
                    }
        
        # 2. Check for gratitude/ending
        if any(thank in query for thank in ['dhanyawad', 'dhanyavaad', 'thanks', 'thank you', 'shukriya', 'thanku']):
            return {
                "intent": "gratitude", 
                "urgency": "low", 
                "needs_details": False,
                "topic_details": {
                    "topic": "general",
                    "subtopic": None,
                    "is_new_topic": False,
                    "needs_clarification": False,
                    "emotional_tone": "grateful"
                }
            }
        
        # 3. Check for problem statements (most common)
        problem_indicators = [
            'problem', 'dikkat', 'mushkil', 'tension', 'pareshan', 'chinta',
            'worry', 'stress', 'nahi ho raha', 'nahi mil raha', 'fail',
            'kharab', 'bura', 'ladaai', 'fight', 'breakup', 'chhut', 'tod',
            'loss', 'harna', 'haar', 'gaya', 'gayi', 'gaye', 'samasya'
        ]
        
        is_problem = any(indicator in query for indicator in problem_indicators)
        
        # 4. Check for specific topics with context awareness
        topic_details = {
            "topic": "general",
            "subtopic": None,
            "is_new_topic": True,
            "needs_clarification": True,
            "emotional_tone": "neutral"
        }
        
        # Career/Job context
        career_words = ['job', 'career', 'naukri', 'kaam', 'business', 'work', 'office', 'promotion', 'salary', 'interview', 'company', 'boss']
        if any(word in query for word in career_words):
            topic_details["topic"] = "career"
            # Check if user mentioned specific career issues
            if 'nahi mil raha' in query or 'interview' in query:
                topic_details["subtopic"] = "job_search"
                topic_details["emotional_tone"] = "stressed"
            elif 'promotion' in query or 'badh' in query or 'growth' in query:
                topic_details["subtopic"] = "growth"
                topic_details["emotional_tone"] = "hopeful"
            elif 'business' in query:
                topic_details["subtopic"] = "business"
                topic_details["emotional_tone"] = "concerned"
            else:
                topic_details["emotional_tone"] = "stressed" if is_problem else "curious"
        
        # Love/Relationship context
        love_words = ['love', 'pyaar', 'gf', 'bf', 'girlfriend', 'boyfriend', 'crush', 'shaadi', 'marriage', 'relationship', 'partner', 'wife', 'husband']
        if any(word in query for word in love_words):
            topic_details["topic"] = "love"
            if 'breakup' in query or 'chhut' in query or 'tod' in query or 'alag' in query:
                topic_details["subtopic"] = "breakup"
                topic_details["emotional_tone"] = "sad"
            elif 'ladaai' in query or 'fight' in query or 'jhagda' in query:
                topic_details["subtopic"] = "conflict"
                topic_details["emotional_tone"] = "upset"
            elif 'shaadi' in query or 'marriage' in query or 'vivah' in query:
                topic_details["subtopic"] = "marriage"
                topic_details["emotional_tone"] = "curious"
            elif 'milna' in query or 'mil jaye' in query or 'pata' in query:
                topic_details["subtopic"] = "meeting"
                topic_details["emotional_tone"] = "hopeful"
            else:
                topic_details["emotional_tone"] = "romantic" if not is_problem else "concerned"
        
        # Health context
        health_words = ['health', 'tabiyat', 'bimar', 'sick', 'ill', 'dard', 'pita', 'takleef', 'bimari', 'operation']
        if any(word in query for word in health_words):
            topic_details["topic"] = "health"
            topic_details["emotional_tone"] = "concerned"
            if 'mummy' in query or 'mother' in query or 'maa' in query:
                topic_details["subtopic"] = "mother_health"
            elif 'papa' in query or 'father' in query or 'baap' in query:
                topic_details["subtopic"] = "father_health"
            elif 'bhai' in query or 'behen' in query or 'sister' in query or 'brother' in query:
                topic_details["subtopic"] = "sibling_health"
            else:
                topic_details["subtopic"] = "personal_health"
        
        # Education context
        education_words = ['study', 'padhai', 'exam', 'college', 'university', 'result', 'marks', 'percentage', 'fail', 'pass', 'admission']
        if any(word in query for word in education_words):
            topic_details["topic"] = "education"
            topic_details["emotional_tone"] = "anxious" if is_problem else "hopeful"
            if 'exam' in query:
                topic_details["subtopic"] = "exams"
            elif 'result' in query or 'marks' in query:
                topic_details["subtopic"] = "results"
            elif 'admission' in query:
                topic_details["subtopic"] = "admission"
        
        # Money context
        money_words = ['paisa', 'money', 'dhan', 'wealth', 'finance', 'loan', 'karza', 'udhar', 'investment', 'savings', 'income']
        if any(word in query for word in money_words):
            topic_details["topic"] = "money"
            topic_details["emotional_tone"] = "worried" if is_problem else "hopeful"
            if 'loan' in query or 'karza' in query:
                topic_details["subtopic"] = "debt"
            elif 'investment' in query:
                topic_details["subtopic"] = "investment"
        
        # Life decisions context
        decision_words = ['kya karu', 'kya kru', 'decision', 'faisla', 'confused', 'samlajh', 'option', 'choose', 'select']
        if any(word in query for word in decision_words):
            topic_details["topic"] = "decision"
            topic_details["emotional_tone"] = "confused"
        
        # 5. Check if this continues previous topic
        if self.conversation_state["current_topic"]:
            last_topic = self.conversation_state["current_topic"]
            if topic_details["topic"] == last_topic or any(word in query for word in [last_topic]):
                topic_details["is_new_topic"] = False
                topic_details["needs_clarification"] = False
        
        # 6. Check if user is providing details (answering our questions)
        if self.conversation_state["has_asked_questions"]:
            # User is likely answering our previous questions
            question_words = ['kaise', 'kya', 'kab', 'kyun', 'kahan', 'kitna', 'kitne', 'kaun']
            if not any(q_word in query for q_word in question_words) and len(query.split()) > 2:
                # This looks like an answer, not a new question
                topic_details["needs_clarification"] = False
        
        # 7. Check for remedy requests
        remedy_words = ['upay', 'remedy', 'solution', 'ilaj', 'totka', 'kya karu', 'kya kru', 'kaise thik', 'kaise theek']
        if any(word in query for word in remedy_words):
            return {
                "intent": "remedy_request",
                "topic_details": topic_details,
                "urgency": "medium",
                "needs_details": False
            }
        
        # 8. Check for update/good news
        good_news_words = ['ho gaya', 'ho gayi', 'mil gaya', 'aa gaya', 'thik hai', 'accha hua', 'success', 'kamyab', 'pass', 'mila', 'mili']
        if any(phrase in query for phrase in good_news_words):
            return {
                "intent": "update",
                "topic_details": topic_details,
                "urgency": "low",
                "needs_details": False
            }
        
        # 9. Check for simple responses
        simple_responses = ['haan', 'ha', 'yes', 'ok', 'theek', 'accha', 'hmm', 'han', 'acha', 'thik']
        if len(query.split()) <= 2 and query in simple_responses:
            return {
                "intent": "acknowledgment", 
                "urgency": "low", 
                "needs_details": False,
                "topic_details": topic_details
            }
        
        # 10. Check if user is just sharing thoughts/feelings
        feeling_words = ['feel', 'lagta', 'lagti', 'lag raha', 'lag rahi', 'soch', 'vichar', 'mann', 'dil']
        if any(word in query for word in feeling_words) and len(query.split()) > 3:
            return {
                "intent": "sharing",
                "topic_details": topic_details,
                "urgency": "medium",
                "needs_details": True
            }
        
        return {
            "intent": "consultation",
            "topic_details": topic_details,
            "urgency": "high" if is_problem else "medium",
            "needs_details": topic_details["needs_clarification"]
        }
    
    def _build_conversation_context(self, natal_context, transit_context, user_query, conversation_history, intent_analysis):
        """Build intelligent context based on conversation flow"""
        
        context_parts = []
        
        # 1. Add natal chart summary (simplified)
        context_parts.append("📜 USER'S BIRTH CHART (Key Points):")
        
        # Extract key planetary positions
        planets_to_check = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
        planet_positions = []
        
        # Find planet positions using regex
        for planet in planets_to_check:
            pattern = f"{planet}[\\s\\S]*?(?:in|is in|at)[\\s\\S]*?(\\d+[a-z]{2}\\s+house|[A-Z][a-z]+\\s+sign)"
            matches = re.findall(pattern, natal_context, re.IGNORECASE)
            if matches:
                planet_positions.append(f"  • {planet}: {matches[0]}")
        
        # If regex didn't work, try simpler approach
        if not planet_positions:
            # Just mention key planets present
            present_planets = []
            for planet in planets_to_check:
                if planet in natal_context:
                    present_planets.append(planet)
            if present_planets:
                context_parts.append(f"  • Key planets: {', '.join(present_planets)}")
        else:
            # Add first 3-4 planet positions
            context_parts.extend(planet_positions[:4])
        
        # Add ascendant if available
        asc_patterns = [r"Ascendant.*?(?:is|:)\s*([A-Z][a-z]+)", r"Lagna.*?(?:is|:)\s*([A-Z][a-z]+)"]
        for pattern in asc_patterns:
            match = re.search(pattern, natal_context, re.IGNORECASE)
            if match:
                context_parts.append(f"  • Ascendant: {match.group(1)}")
                break
        
        context_parts.append("")  # Empty line
        
        # 2. Add current transit highlights
        context_parts.append("🌌 CURRENT TRANSITS (Relevant):")
        
        topic = intent_analysis.get("topic_details", {}).get("topic", "general")
        
        # Map topics to relevant astrological factors
        topic_mapping = {
            "career": ["Sun", "Saturn", "10th house", "Capricorn"],
            "love": ["Venus", "Moon", "7th house", "Libra"],
            "health": ["Moon", "Mars", "6th house", "Virgo"],
            "money": ["Jupiter", "Venus", "2nd house", "11th house", "Taurus"],
            "education": ["Mercury", "Jupiter", "5th house", "Gemini"],
            "decision": ["Mercury", "Moon", "ascendant"]
        }
        
        relevant_factors = topic_mapping.get(topic, [])
        
        # Check transit context for relevant factors
        found_factors = []
        for factor in relevant_factors:
            if factor.lower() in transit_context.lower():
                found_factors.append(factor)
        
        if found_factors:
            context_parts.append(f"  • Active: {', '.join(found_factors[:3])}")
        else:
            context_parts.append("  • Current transits affecting life areas")
        
        context_parts.append("")  # Empty line
        
        # 3. Add conversation flow context
        context_parts.append("💭 CONVERSATION CONTEXT:")
        
        if self.conversation_state["current_topic"]:
            context_parts.append(f"  • Current topic: {self.conversation_state['current_topic']}")
        
        if self.conversation_state["user_details"]:
            detail_count = len(self.conversation_state["user_details"])
            context_parts.append(f"  • User has shared {detail_count} details")
        
        if intent_analysis.get("topic_details", {}).get("subtopic"):
            context_parts.append(f"  • Subtopic: {intent_analysis['topic_details']['subtopic']}")
        
        context_parts.append(f"  • Emotional tone: {intent_analysis.get('topic_details', {}).get('emotional_tone', 'neutral')}")
        
        # Check if we've already asked questions
        if self.conversation_state["has_asked_questions"]:
            context_parts.append("  • Status: Already asked questions, ready for insights")
        else:
            context_parts.append("  • Status: Need to ask clarifying questions")
        
        context_parts.append("")  # Empty line
        
        # 4. Add recent conversation (last 3 exchanges)
        if conversation_history and len(conversation_history) > 0:
            context_parts.append("🗣️ RECENT CHAT:")
            recent = conversation_history[-4:]  # Last 2 exchanges
            for msg in recent:
                role = "User" if msg["role"] == "user" else "You"
                # Truncate long messages
                content = msg["content"]
                if len(content) > 50:
                    content = content[:47] + "..."
                context_parts.append(f"  {role}: {content}")
            context_parts.append("")  # Empty line
        
        # 5. Add response guidance based on intent
        context_parts.append("🎯 HOW TO RESPOND:")
        
        intent = intent_analysis.get("intent", "consultation")
        
        if intent == "greeting":
            greeting_type = intent_analysis.get("greeting_type", "first")
            if greeting_type == "first":
                context_parts.append("  • Warm professional greeting")
                context_parts.append("  • Introduce as Astra, Vedic astrology consultant")
                context_parts.append("  • Ask how you can help with astrology")
                context_parts.append("  • Keep it professional and warm")
                context_parts.append("  • Example: 'Namaste! Main Astra hoon. Aapka swagat hai.'")
            else:
                context_parts.append("  • Return greeting briefly")
                context_parts.append("  • Ask about their astrology concern")
                context_parts.append("  • Stay on astrology topic")
                context_parts.append("  • Example: 'Main theek hoon, dhanyavaad! Aap kaise hain?'")
        
        elif intent == "consultation":
            if intent_analysis.get("needs_details", True):
                context_parts.append("  • Ask 1-2 simple questions")
                context_parts.append("  • Questions should be relevant to their topic")
                context_parts.append("  • Keep questions very short (5-8 words)")
                context_parts.append("  • Be empathetic to their emotional tone")
                context_parts.append("  • Example for career: 'Kis field mein kaam karte ho?'")
            else:
                context_parts.append("  • Give astrological insights NOW")
                context_parts.append("  • Connect to their birth chart and transits")
                context_parts.append("  • Provide specific guidance")
                context_parts.append("  • Give rough timeline if possible")
                context_parts.append("  • Use simple planet names: Guru, Shani, Shukra, etc.")
                context_parts.append("  • Mention relevant houses: 10th house for career, etc.")
        
        elif intent == "remedy_request":
            context_parts.append("  • Provide 2-3 practical remedies")
            context_parts.append("  • Be specific: mantra + day + action")
            context_parts.append("  • Keep remedies simple to follow")
            context_parts.append("  • Example: 'Shani mantra: Om Sham Shanicharaya Namah'")
        
        elif intent == "update":
            context_parts.append("  • Celebrate with them!")
            context_parts.append("  • Acknowledge their happiness/success")
            context_parts.append("  • Give positive reinforcement")
            context_parts.append("  • Keep it brief and joyful")
        
        elif intent == "gratitude":
            context_parts.append("  • Simple warm acknowledgment")
            context_parts.append("  • DO NOT give more predictions")
            context_parts.append("  • End conversation gracefully")
            context_parts.append("  • Example: 'Dhanyavaad, aapka abhar'")
        
        elif intent == "acknowledgment":
            context_parts.append("  • Acknowledge briefly")
            context_parts.append("  • Continue with guidance based on context")
            context_parts.append("  • Keep it natural")
        
        elif intent == "sharing":
            context_parts.append("  • Show empathy first")
            context_parts.append("  • Acknowledge their feelings")
            context_parts.append("  • Then ask relevant questions or give insights")
            context_parts.append("  • Be supportive and understanding")
        
        context_parts.append("")  # Empty line
        context_parts.append("📝 RESPONSE FORMAT:")
        context_parts.append("  • 1-3 short chat messages")
        context_parts.append("  • Separate with |||")
        context_parts.append("  • Sound warm and human")
        context_parts.append("  • Use simple Hinglish")
        context_parts.append("  • Each message: 8-15 words maximum")
        
        return "\n".join(context_parts)
    
    def _update_conversation_state(self, user_query, intent_analysis, assistant_response):
        """Update conversation state based on interaction"""
        
        # Update current topic
        topic_details = intent_analysis.get("topic_details", {})
        if topic_details.get("is_new_topic", True) and topic_details.get("topic") != "general":
            self.conversation_state["current_topic"] = topic_details["topic"]
            if topic_details["topic"] not in self.conversation_state["previous_topics"]:
                self.conversation_state["previous_topics"].append(topic_details["topic"])
        
        # Check if we asked questions
        if '?' in assistant_response:
            self.conversation_state["has_asked_questions"] = True
        
        # Check if user provided details (not just yes/no)
        query_lower = user_query.lower()
        if len(user_query.split()) > 3:
            # Extract potential details based on topic
            current_topic = self.conversation_state.get("current_topic", "")
            
            if current_topic == "career":
                career_words = ['field', 'company', 'experience', 'year', 'salar', 'boss', 'colleague']
                if any(word in query_lower for word in career_words):
                    self.conversation_state["user_details"]["career_info"] = True
            
            elif current_topic == "love":
                love_words = ['time', 'month', 'year', 'age', 'live', 'city', 'distance']
                if any(word in query_lower for word in love_words):
                    self.conversation_state["user_details"]["relationship_info"] = True
            
            elif current_topic == "health":
                health_words = ['day', 'week', 'month', 'doctor', 'hospital', 'medicine', 'test']
                if any(word in query_lower for word in health_words):
                    self.conversation_state["user_details"]["health_info"] = True
        
        # Reset if new topic detected
        if topic_details.get("is_new_topic", True):
            self.conversation_state["has_asked_questions"] = False
            self.conversation_state["conversation_stage"] = "initial"
        else:
            self.conversation_state["conversation_stage"] = "detailed"
    
    def generate_response(self, natal_context, transit_context, user_query, conversation_history=None):
        """Main method to generate intelligent responses"""
        
        # Analyze user intent
        intent_analysis = self._analyze_query_intent(user_query, conversation_history)
        
        # Build intelligent context
        context = self._build_conversation_context(
            natal_context, 
            transit_context, 
            user_query, 
            conversation_history,
            intent_analysis
        )
        
        # Prepare the final prompt
        final_prompt = f"""# ASTROLOGY CONSULTATION SESSION

## CONTEXT INFORMATION:
{context}

## CURRENT USER MESSAGE:
"{user_query}"

## YOUR TASK:
Respond as Astra, the warm astrology consultant. Be natural, empathetic, and helpful.

CRITICAL INSTRUCTIONS:
• Sound like a REAL PERSON having a chat
• Use NATURAL Hinglish conversation
• Be WARM and PROFESSIONAL
• Keep each message SHORT (8-15 words)
• Separate messages with |||
• Stay on astrology topic
• If asked questions before, give insights NOW

REMEMBER: You're an astrology consultant giving helpful advice. Be warm but professional!

Your response:"""
        
        # Set appropriate parameters based on intent
        intent = intent_analysis.get("intent", "consultation")
        
        if intent == "gratitude":
            max_tokens = 40
            temperature = 0.7
        elif intent == "greeting":
            max_tokens = 60
            temperature = 0.8
        elif intent == "acknowledgment":
            max_tokens = 50
            temperature = 0.75
        elif intent == "consultation" and intent_analysis.get("needs_details", True):
            max_tokens = 70
            temperature = 0.75
        elif intent == "update":
            max_tokens = 80
            temperature = 0.85  # More creative for celebrations
        else:
            max_tokens = 120
            temperature = 0.8  # Higher temperature for more natural responses
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": final_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                frequency_penalty=0.3,
                presence_penalty=0.2,
                stop=None
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Clean and format response
            if response:
                # Ensure proper formatting
                response = response.replace('\n', ' ').strip()
                
                # Remove any "chai peete hain" type phrases
                unwanted_phrases = ['chai peete', 'chai piye', 'coffee peete', 'coffee piye']
                for phrase in unwanted_phrases:
                    response = response.replace(phrase, '')
                
                # Ensure we have proper message separation
                if '|||' not in response and len(response.split()) > 15:
                    # Try to break into natural conversation points
                    sentences = response.replace('!', '||').replace('?', '||').replace('.', '||').split('||')
                    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
                    if len(sentences) > 1:
                        response = '|||'.join(sentences[:2])
                
                # Update conversation state
                self._update_conversation_state(user_query, intent_analysis, response)
                
                return response
            
            # Fallback response
            fallbacks = [
                "Kshama karein, main abhi samajh nahi paa raha. Kripya dobara puchein.",
                "Mujhe samajhne mein thodi dikkat hui. Kya aap phir se bata sakte hain?",
                "Cosmic signals thode weak hain. Phir se try karein?"
            ]
            import random
            return random.choice(fallbacks)
            
        except Exception as e:
            print(f"Error in LLM call: {str(e)}")
            return "Meri cosmic connection mein thodi problem hai. Thodi der baad phir try karein."

    def reset_conversation(self):
        """Reset conversation state"""
        self.conversation_state = {
            "current_topic": None,
            "has_asked_questions": False,
            "user_details": {},
            "conversation_stage": "initial",
            "previous_topics": []
        }