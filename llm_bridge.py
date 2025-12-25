from groq import Groq
import config

class LLMBridge:
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.MODEL_NAME
        
        self.system_prompt = """You are Astra — a warm, empathetic Vedic astrology consultant who speaks naturally in simple Hinglish.

RESPONSE FORMAT:
Break your response into 1-3 SHORT separate messages, like a real chat conversation.
Separate each message with "|||"

Example: "Aap kya jaanna chahte hai?|||Batao, kya problem hai?"

🚨 CRITICAL RULES 🚨
1. When user says "dhanyawad" (thank you) - ONLY say "Dhanyavaad, aapka abhar" or "Khush raho" - NOTHING ELSE! NO predictions! NO house analysis!
2. When user asks for "solution" or "upay" - Give SPECIFIC remedies (mantras, days, actions) based on the problem context
3. After asking questions ONCE, STOP asking and give predictions
4. STAY ON TOPIC - Career question = only career talk, Love question = only love talk

CONVERSATION FLOW - CRITICAL FOR ALL TOPICS:

1. FIRST RESPONSE TO ANY QUESTION - ASK 1-2 SIMPLE QUESTIONS, DON'T PREDICT YET!
   - Career: "Kis field mein kaam karte ho?|||Kya problem hai?"
   - Love: "Kya hua?|||Kitne time se saath ho?"
   - Health: "Kya hua?|||Kisko problem hai?"
   - Money: "Kitna chahiye?|||Kab tak?"
   - Education: "Kaun sa exam hai?|||Kya tension hai?"
   - Life Decision: "Kya options hain?|||Kya confusion hai?"
   - Keep questions VERY SHORT and SIMPLE
   - Use easy Hindi words, avoid difficult Hinglish
   - ONLY after they answer, then give astrological predictions!
   
2. AFTER THEY ANSWER ONCE - GIVE PREDICTIONS, DON'T ASK MORE QUESTIONS!
   - User answered your questions? NOW give astrological insights!
   - Don't keep asking questions repeatedly
   - Move to chart analysis and predictions
   - Be confident and give timelines
   
3. USE CHART DATA AND GIVE PREDICTIONS
   - Connect their situation to the chart
   - Use planet names: "Guru", "Shani", "Mangal", "Shukra", "Rahu", "Ketu"
   - Give timelines: "August 2028 tak", "agle 6 mahine", "March 2026 mein"
   - Reference relevant houses:
     * Career: 10th house, Sun, Saturn
     * Love/Marriage: 7th house, Venus, Moon
     * Health/Mother: 4th house, Moon, 6th house
     * Health/Father: 9th house, Sun
     * Money: 11th house (gains), 2nd house (wealth), Jupiter
     * Education: 5th house, Mercury, Jupiter

4. STAY ON TOPIC - DON'T MIX SUBJECTS
   - If asking about love, ONLY talk about love
   - If asking about career, ONLY talk about career
   - If asking about health, ONLY talk about health
   - Focus on what they're asking RIGHT NOW

5. KEEP MESSAGES VERY SHORT (5-12 words each)
   - One clear thought per message
   - Simple, easy Hinglish (not difficult)
   - Warm and friendly tone
   - Maximum 1-3 messages per response

6. WHEN USER ASKS FOR REMEDIES/SOLUTIONS:
   - Give SPECIFIC remedies based on the problem
   - Career: "Surya ko jal chadao", "Shani mantra: Om Sham Shanicharaya Namah"
   - Love: "Shukra mantra jap karo", "Friday ko white kapde pehno"
   - Health: "Chandra mantra jap karo", "Monday ko doodh peeyo"
   - Money: "Guru mantra jap karo", "Thursday ko daan karo"
   - Education: "Budh mantra jap karo", "Wednesday ko green pehno"
   - Include: Which planet, which day, what action
   - Keep remedies PRACTICAL and SIMPLE

7. WHEN USER SAYS THANK YOU (dhanyawad):
   - ONLY say "Dhanyavaad, aapka abhar" or "Khush raho, hamesha"
   - DO NOT give more predictions
   - DO NOT analyze houses
   - DO NOT ask more questions
   - Just acknowledge warmly and STOP

REMEMBER: Ask 1-2 simple questions in first response. After user answers ONCE, give predictions. Don't keep asking questions repeatedly!"""
    
    def generate_response(self, natal_context, transit_context, user_query, conversation_history=None):
        query_lower = user_query.lower()
        
        # Detect CAREER topics
        asking_about_career = any(word in query_lower for word in [
            'job', 'career', 'kaam', 'naukri', 'business', 'work', 'office',
            'promotion', 'salary', 'interview', 'company', 'boss', 'colleague'
        ])
        
        # Detect LOVE/RELATIONSHIP topics
        asking_about_love = any(word in query_lower for word in [
            'love', 'pyaar', 'relationship', 'gf', 'bf', 'girlfriend', 'boyfriend',
            'crush', 'propose', 'breakup', 'ladayi', 'fight', 'shaadi', 'marriage',
            'partner', 'husband', 'wife', 'divorce', 'affair'
        ])
        
        # Detect HEALTH/FAMILY topics
        asking_about_health = any(word in query_lower for word in [
            'tabiyat', 'health', 'bimar', 'sick', 'theek', 'thik', 'illness',
            'mummy', 'papa', 'mother', 'father', 'bhai', 'behen', 'family',
            'parivar', 'dadi', 'dada', 'nani', 'nana', 'beta', 'beti'
        ])
        
        # Detect MONEY/FINANCE topics
        asking_about_money = any(word in query_lower for word in [
            'paisa', 'money', 'dhan', 'wealth', 'finance', 'loan', 'debt',
            'investment', 'savings', 'income', 'loss', 'profit', 'business'
        ])
        
        # Detect EDUCATION/STUDY topics
        asking_about_education = any(word in query_lower for word in [
            'study', 'padhai', 'exam', 'college', 'university', 'degree',
            'course', 'admission', 'result', 'marks', 'fail', 'pass'
        ])
        
        # Detect LIFE DECISIONS topics
        asking_about_decision = any(phrase in query_lower for phrase in [
            'kya karu', 'kya kru', 'decision', 'faisla', 'choose', 'select',
            'confused', 'samajh nahi', 'kaise', 'should i', 'kya chahiye'
        ])
        
        # Detect if user is sharing a problem/concern (ANY TOPIC)
        sharing_problem = any(phrase in query_lower for phrase in [
            'mann nhi lag rha', 'man nahi lag raha', 'pasand nahi', 'problem hai',
            'dikkat hai', 'mushkil hai', 'pareshan hun', 'tension hai',
            'confused hun', 'samajh nahi aa raha', 'dar lag raha',
            'chinta hai', 'worry hai', 'stress hai', 'kharab hai', 'theek nahi',
            'bimar hai', 'sick hai', 'upset hun', 'sad hun', 'dukhi hun',
            'nahi mil raha', 'nahi ho raha', 'fail ho raha', 'galat ja raha'
        ])
        
        # Check if this is the FIRST mention of ANY topic (no previous context)
        is_first_mention = (asking_about_career or asking_about_love or asking_about_health or 
                           asking_about_money or asking_about_education or asking_about_decision or 
                           sharing_problem) and (not conversation_history or len(conversation_history) < 2)
        
        # Detect if asking about change/switch
        asking_about_change = any(phrase in query_lower for phrase in [
            'badal', 'change', 'switch', 'chhod', 'chod', 'quit',
            'naya', 'different', 'alag', 'kuch aur', 'leave'
        ])
        
        # Simple acknowledgments - don't overthink
        simple_acknowledgments = ['haan', 'ha', 'yes', 'ok', 'okay', 'theek', 'thik', 'achha', 'accha', 'hmm', 'han']
        is_simple_acknowledgment = query_lower.strip() in simple_acknowledgments and len(query_lower.split()) <= 2
        
        # Simple negations
        simple_negations = ['nhi', 'nahi', 'no', 'na', 'naa']
        is_simple_negation = query_lower.strip() in simple_negations and len(query_lower.split()) <= 2
        
        # Gratitude - should end conversation gracefully
        is_gratitude = any(word in query_lower for word in ['dhanyawad', 'dhanyavaad', 'thanks', 'thank you', 'shukriya', 'thanku', 'thnx', 'thx'])
        
        # Detect greeting (only simple greetings, NOT "how are you" questions)
        is_simple_greeting = len(user_query.split()) <= 2 and any(greeting in query_lower for greeting in [
            'hi', 'hello', 'hey', 'namaste', 'namaskar'
        ])
        
        # Detect "how are you" type questions separately
        is_how_are_you = any(phrase in query_lower for phrase in [
            'kese ho', 'kaise ho', 'kese hain', 'kaise hain', 'how are you', 'how r u', 'kese h', 'kaise h'
        ])
        
        # Detect remedy request - user wants solutions
        asking_for_remedy = any(phrase in query_lower for phrase in [
            'upay', 'remedy', 'remedies', 'solution', 'totka', 'ilaj',
            'kya karu', 'kya kru', 'kya karoon', 'kya chahiye',
            'iske liye kya', 'kaise thik', 'kaise theek', 'koi solution',
            'koi upay', 'kaise solve', 'kaise door', 'kaise sudhar'
        ])
        
        # Check if user is asking for remedy in context of a specific problem
        remedy_context = ""
        if asking_for_remedy and conversation_history:
            # Look at recent conversation to understand what problem they want remedy for
            for msg in reversed(conversation_history[-6:]):
                if msg.get("role") == "assistant":
                    msg_lower = msg.get("content", "").lower()
                    if "career" in msg_lower or "job" in msg_lower or "10th house" in msg_lower:
                        remedy_context = "career"
                        break
                    elif "love" in msg_lower or "relationship" in msg_lower or "7th house" in msg_lower:
                        remedy_context = "love"
                        break
                    elif "health" in msg_lower or "tabiyat" in msg_lower or "bimar" in msg_lower:
                        remedy_context = "health"
                        break
                    elif "money" in msg_lower or "paisa" in msg_lower or "11th house" in msg_lower:
                        remedy_context = "money"
                        break
                    elif "education" in msg_lower or "study" in msg_lower or "exam" in msg_lower:
                        remedy_context = "education"
                        break
        
        # Set max tokens and guidance based on context
        max_tokens = 100  # Reduced for shorter responses
        response_guidance = ""
        
        # Check if we already asked questions in ANY previous message
        already_asked_questions = False
        question_count = 0
        if conversation_history and len(conversation_history) >= 1:
            # Check ALL assistant messages for questions
            for msg in conversation_history:
                if msg.get("role") == "assistant":
                    msg_lower = msg.get("content", "").lower()
                    # Count question marks or question words
                    if '?' in msg_lower or any(q in msg_lower for q in ['kya hua', 'kab se', 'kaise', 'batao', 'kyun', 'kaunsa', 'kis']):
                        question_count += 1
            
            # If we asked questions even ONCE in the entire conversation, stop asking
            already_asked_questions = question_count > 0
        
        # Check if user provided ANY details (even short ones)
        user_provided_details = len(user_query.split()) > 3
        
        # FIRST MENTION - Ask questions for ANY topic (but only if we haven't asked before!)
        if is_first_mention and not already_asked_questions:
            max_tokens = 80  # Reduced for shorter responses
            
            if asking_about_career:
                response_guidance = "User asked about career/job. Give 1-2 VERY SHORT messages: (1) 'Kis field mein kaam karte ho?' (2) 'Kya problem hai?' Keep it simple. Use |||"
            elif asking_about_love:
                response_guidance = "User asked about love/relationship. Give 1-2 VERY SHORT messages: (1) 'Kya hua?' (2) 'Kitne time se saath ho?' Keep it simple. Use |||"
            elif asking_about_health:
                response_guidance = "User asked about health/family. Give 1-2 VERY SHORT messages: (1) 'Kya hua?' (2) 'Kisko problem hai?' Keep it simple. Use |||"
            elif asking_about_money:
                response_guidance = "User asked about money/finance. Give 1-2 VERY SHORT messages: (1) 'Kitna chahiye?' (2) 'Kab tak?' Keep it simple. Use |||"
            elif asking_about_education:
                response_guidance = "User asked about education/study. Give 1-2 VERY SHORT messages: (1) 'Kaun sa exam hai?' (2) 'Kya tension hai?' Keep it simple. Use |||"
            elif asking_about_decision:
                response_guidance = "User is confused about a decision. Give 1-2 VERY SHORT messages: (1) 'Kya options hain?' (2) 'Kya confusion hai?' Keep it simple. Use |||"
            else:
                response_guidance = "User shared something. Give 1-2 VERY SHORT messages asking about their situation. Use |||"
        
        # AFTER QUESTIONS ASKED OR USER PROVIDED DETAILS - Now give predictions!
        elif (already_asked_questions or user_provided_details) and (asking_about_career or asking_about_love or asking_about_health or 
                                         asking_about_money or asking_about_education or asking_about_decision):
            max_tokens = 120  # Reduced for shorter responses
            
            if asking_about_career:
                response_guidance = "User answered about CAREER/JOB. Give 2-3 VERY SHORT messages ONLY about career: (1) Acknowledge (2) Check 10th house for CAREER (3) Give timeline. NO remedies! NO relationship talk! ONLY CAREER! Use |||"
            elif asking_about_love:
                response_guidance = "User answered about LOVE/RELATIONSHIP. Give 2-3 VERY SHORT messages ONLY about love: (1) Acknowledge (2) Check 7th house for RELATIONSHIP (3) Give timeline. NO career talk! ONLY LOVE! Use |||"
            elif asking_about_health:
                response_guidance = "User answered about HEALTH. Give 2-3 VERY SHORT messages ONLY about health: (1) Show empathy (2) Check relevant house for HEALTH (3) Give timeline. NO career/money talk! ONLY HEALTH! Use |||"
            elif asking_about_money:
                response_guidance = "User answered about MONEY. Give 2-3 VERY SHORT messages ONLY about money: (1) Acknowledge (2) Check 11th house for MONEY (3) Give timeline. NO career/love talk! ONLY MONEY! Use |||"
            elif asking_about_education:
                response_guidance = "User answered about EDUCATION. Give 2-3 VERY SHORT messages ONLY about education: (1) Show support (2) Check 5th house for EDUCATION (3) Give timeline. NO career/love talk! ONLY EDUCATION! Use |||"
            elif asking_about_decision:
                response_guidance = "User answered about DECISION. Give 2-3 VERY SHORT messages ONLY about their decision: (1) Acknowledge (2) Which option is better (3) Best timing. Use |||"
        
        # GRATITUDE - End conversation gracefully, DON'T give more predictions
        elif is_gratitude:
            max_tokens = 50
            response_guidance = "User said thank you. Give 1 VERY short message: 'Dhanyavaad, aapka abhar' or 'Khush raho, hamesha' - THAT'S IT! NO predictions! NO questions! NO house analysis! Just acknowledge warmly and STOP."
        
        # CHANGE/SWITCH questions
        elif asking_about_change:
            if not already_asked_questions:
                max_tokens = 80
                response_guidance = "User wants to make a change. DON'T predict yet! Ask 1-2 simple questions: What change? Why? Use |||"
            else:
                max_tokens = 120
                response_guidance = "User answered about change. Give 2-3 SHORT insights: (1) Check timing (2) Best time to change (3) Encouraging advice. Use |||"
        
        # REMEDY requests - Give specific solutions based on context
        elif asking_for_remedy:
            max_tokens = 150
            if remedy_context == "career":
                response_guidance = "User wants CAREER remedy. Give 2-3 SHORT messages with SPECIFIC career remedies: (1) Sun/Saturn remedy (2) Practical action (3) Best day/time. Examples: 'Surya ko jal chadao', 'Shani mantra jap karo', 'Saturday ko daan karo'. Use |||"
            elif remedy_context == "love":
                response_guidance = "User wants LOVE remedy. Give 2-3 SHORT messages with SPECIFIC love remedies: (1) Venus remedy (2) Practical action (3) Best day. Examples: 'Shukra mantra jap karo', 'Friday ko white kapde pehno', 'Gulab jal use karo'. Use |||"
            elif remedy_context == "health":
                response_guidance = "User wants HEALTH remedy. Give 2-3 SHORT messages with SPECIFIC health remedies: (1) Moon remedy (2) Practical action (3) Diet advice. Examples: 'Chandra mantra jap karo', 'Monday ko doodh peeyo', 'Meditation karo'. Use |||"
            elif remedy_context == "money":
                response_guidance = "User wants MONEY remedy. Give 2-3 SHORT messages with SPECIFIC money remedies: (1) Jupiter remedy (2) Practical action (3) Best day. Examples: 'Guru mantra jap karo', 'Thursday ko daan karo', 'Haldi use karo'. Use |||"
            elif remedy_context == "education":
                response_guidance = "User wants EDUCATION remedy. Give 2-3 SHORT messages with SPECIFIC study remedies: (1) Mercury remedy (2) Study tips (3) Best time. Examples: 'Budh mantra jap karo', 'Wednesday ko green pehno', 'Subah padho'. Use |||"
            else:
                response_guidance = "User wants general remedy. Give 2-3 SHORT messages with PRACTICAL remedies based on their chart. Be specific! Use |||"
        
        # SIMPLE responses
        elif is_simple_acknowledgment:
            max_tokens = 60
            response_guidance = "Give 1-2 VERY short messages: acknowledge, ask if they want to know anything else. Use |||"
        elif is_simple_negation:
            max_tokens = 80
            response_guidance = "Give 1-2 VERY short messages: accept gracefully, give ONE positive insight. Use |||"
        elif is_simple_greeting and not conversation_history:
            max_tokens = 50
            response_guidance = "Give 1-2 VERY short messages: Say 'Namaste! Main Astra hoon' then ask 'Aap kya jaanna chahte hai?' Use |||"
        elif is_how_are_you:
            max_tokens = 60
            response_guidance = "User asked how you are. Give 1-2 VERY short messages: Say 'Main theek hoon, dhanyavaad!' then ask 'Aap kaise hain?' Use |||"
        
        # DEFAULT - General questions
        else:
            max_tokens = 100
            response_guidance = "Give 1-3 VERY SHORT confident messages using their chart data. Keep it simple and different. Use |||"
        
        # Build context with topic tracking
        context_summary = ""
        current_topic = "general"
        already_mentioned = []
        
        if conversation_history and len(conversation_history) > 0:
            context_summary = "\n=== RECENT CONVERSATION ===\n"
            for msg in conversation_history[-8:]:  # Increased to 8 for better context
                role = "User" if msg["role"] == "user" else "You"
                context_summary += f"{role}: {msg['content']}\n"
                
                # Track what was already mentioned to avoid repetition
                if msg["role"] == "assistant":
                    msg_lower = msg["content"].lower()
                    if "10th house" in msg_lower:
                        already_mentioned.append("10th house strong")
                    if "11th house" in msg_lower:
                        already_mentioned.append("11th house gains")
                    if "guru" in msg_lower or "jupiter" in msg_lower:
                        already_mentioned.append("Jupiter/Guru position")
                    if "shani" in msg_lower or "saturn" in msg_lower:
                        already_mentioned.append("Saturn/Shani position")
                
                # Detect topic from conversation
                if msg["role"] == "user":
                    msg_lower = msg["content"].lower()
                    if any(word in msg_lower for word in ['mummy', 'papa', 'father', 'mother', 'bhai', 'behen', 'family', 'parivar', 'tabiyat', 'health', 'bimar', 'sick']):
                        current_topic = "family_health"
                    elif any(word in msg_lower for word in ['love', 'pyaar', 'relationship', 'gf', 'bf', 'ladayi', 'breakup', 'shaadi', 'marriage', 'partner']):
                        current_topic = "relationship"
                    elif any(word in msg_lower for word in ['job', 'career', 'kaam', 'naukri', 'business', 'work', 'office', 'promotion', 'salary']):
                        current_topic = "career"
                    elif any(word in msg_lower for word in ['paisa', 'money', 'dhan', 'wealth', 'finance', 'loan', 'investment']):
                        current_topic = "finance"
                    elif any(word in msg_lower for word in ['study', 'padhai', 'exam', 'college', 'university', 'degree', 'course']):
                        current_topic = "education"
                    elif any(word in msg_lower for word in ['decision', 'faisla', 'confused', 'kya karu', 'choose']):
                        current_topic = "life_decision"
            
            context_summary += f"\n⚠️ CURRENT TOPIC: {current_topic}\n"
            if already_mentioned:
                context_summary += f"⚠️ ALREADY MENTIONED (DON'T REPEAT): {', '.join(already_mentioned)}\n"
            context_summary += "\n🚨 CRITICAL - STAY ON TOPIC! 🚨\n"
            context_summary += "🚨 If user asked about CAREER, talk ONLY about career/job - NO relationships, NO health!\n"
            context_summary += "🚨 If user asked about LOVE, talk ONLY about love/relationship - NO career, NO money!\n"
            context_summary += "🚨 If user asked about HEALTH, talk ONLY about health - NO career, NO relationships!\n"
            context_summary += "🚨 DON'T give remedies unless user specifically asks for them!\n"
            context_summary += "🚨 Answer ONLY what the user is asking about RIGHT NOW!\n"
            context_summary += "🚨 If user says THANK YOU (dhanyawad), ONLY acknowledge - NO predictions, NO analysis!\n"
            
            # Add strong anti-question instruction if we already asked
            if already_asked_questions:
                context_summary += "\n🚫 YOU ALREADY ASKED QUESTIONS! DON'T ASK MORE!\n"
                context_summary += "🚫 USER ANSWERED! NOW GIVE ASTROLOGICAL PREDICTIONS!\n"
                context_summary += "🚫 NO MORE QUESTIONS! GIVE CHART ANALYSIS NOW!\n"
        
        full_prompt = f"""=== USER'S BIRTH CHART ===
{natal_context}

{context_summary}

=== USER'S CURRENT MESSAGE ===
"{user_query}"

=== YOUR TASK ===
{response_guidance}

CRITICAL INSTRUCTIONS:
- IF YOU ALREADY ASKED QUESTIONS BEFORE: STOP ASKING! GIVE PREDICTIONS NOW!
- User answered your questions? Give astrological insights immediately!
- NO MORE QUESTIONS after first response!

🚨 STAY ON TOPIC! 🚨
- Career question? Talk ONLY about career
- Love question? Talk ONLY about love
- Health question? Talk ONLY about health
- DON'T mix topics!
- DON'T give remedies unless user asks

When giving predictions:
  • Use simple planet names: Guru, Shani, Mangal, Shukra
  • Give timelines: "2026 ke baad", "agle 6 mahine"
  • Be DIRECT and ENCOURAGING
  • Keep it VERY SHORT - 1-3 messages max
- Each message = 5-12 words, separated by |||
- Use SIMPLE Hindi, not difficult Hinglish

Your response:"""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.7,
                max_tokens=max_tokens,
                top_p=0.85,
                frequency_penalty=0.6,  # Increased to reduce repetition
                presence_penalty=0.5,   # Increased to encourage diverse content
                stop=None
            )
            
            response = completion.choices[0].message.content.strip()
            
            # Clean up incomplete responses
            if response:
                # If response ends mid-sentence, try to salvage complete sentences
                if not response[-1] in ['.', '?', '!', '।', '॥']:
                    # Find last complete sentence
                    for delimiter in ['. ', '? ', '! ', '। ', '॥ ']:
                        if delimiter in response:
                            last_complete = response.rfind(delimiter)
                            if last_complete > len(response) * 0.5:  # Only if we keep at least 50%
                                response = response[:last_complete + 1].strip()
                                break
            
            return response if response else "Kshama karein, main abhi cosmic signals samajh nahi paa raha. Kripya dobara puchein."
        except Exception as e:
            return f"Cosmic channels mein problem hai. Error: {str(e)}"
