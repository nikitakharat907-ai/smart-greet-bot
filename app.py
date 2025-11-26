import os
from flask import Flask, render_template, request, jsonify, Blueprint
from datetime import datetime
from flask_wtf.csrf import CSRFProtect

# --- CONFIGURATION ---
class Config:
    """Base configuration settings."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_strong_and_secret_key_here_12345')
    GREETING_LOGIC = {
        'NIGHT': (5, "Good Night! 🌃", "night"),
        'MORNING': (12, "Good Morning! 🌅", "morning"),
        'AFTERNOON': (18, "Good Afternoon! ☀️", "afternoon"),
        'EVENING': (24, "Good Evening! 🌙", "evening")
    }

# --- BUSINESS LOGIC ---
def get_smart_greeting(hour=None):
    """
    Determines the time-based greeting using the configured logic.
    Returns (greeting_message, css_class)
    """
    if hour is None:
        hour = datetime.now().hour
    
    for _, (limit, message, css_class) in Config.GREETING_LOGIC.items():
        if hour < limit:
            return message, css_class
    
    return Config.GREETING_LOGIC['EVENING'][1], Config.GREETING_LOGIC['EVENING'][2]

# --- BLUEPRINT (Routing Logic) ---
# Define the Blueprint without the decorators yet
api_bp = Blueprint('api', __name__, url_prefix='/api')

def get_bot_response():
    """Handles user input and provides context-aware replies."""
    try:
        data = request.get_json()
        user_text = data.get("msg", "").lower().strip()
    except:
        return jsonify({"response": "Invalid request format."}), 400

    current_greeting, _ = get_smart_greeting()

    # --- BOT LOGIC ---
    if not user_text:
        response = "Please type something so I can respond!"
    elif "time" in user_text or "hour" in user_text:
        current_time = datetime.now().strftime("%I:%M:%S %p")
        response = f"The precise current time is {current_time}."
    elif "greeting" in user_text or "greet" in user_text:
        response = f"I am currently set to say: {current_greeting}. Ask me who I am!"
    elif any(g in user_text for g in ["hello", "hi", "hey"]):
        base_greeting = current_greeting.split('!')[0]
        response = f"{base_greeting}! I am the Smart Greeting Bot. Ask me for the 'time'."
    elif "who are you" in user_text or "what can you do" in user_text:
        response = "I am a professional Smart Greeting Bot. I tell you the time and the appropriate greeting (Morning, Afternoon, Evening, or Night)."
    else:
        response = "I'm sorry, I only process time, greetings, and identity queries. Try one of those!"
    
    return jsonify({"response": response})

# --- APPLICATION FACTORY FUNCTION ---
def create_app():
    """Initializes and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize CSRFProtect *with* the app object
    csrf = CSRFProtect(app) 
    
    # 1. Register the API endpoint with the csrf.exempt decorator applied *after* csrf is defined
    # We must use api_bp.add_url_rule here since we cannot use the @decorator syntax outside of the global scope
    api_bp.add_url_rule('/get', view_func=csrf.exempt(get_bot_response), methods=['POST'])

    # 2. Register Blueprints
    app.register_blueprint(api_bp)

    @app.route("/")
    def home():
        """Renders the main chat interface."""
        initial_greeting, initial_class = get_smart_greeting()
        return render_template(
            "index.html", 
            initial_greeting=initial_greeting,
            initial_class=initial_class
        )
    
    return app

# --- RUNNING THE APP ---
if __name__ == "__main__":
    flask_app = create_app()
    print("Running application... Access at http://127.0.0.1:5000")
    # For a smoother development start, you might still want to use the browser open thread:
    # threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    flask_app.run(debug=True)