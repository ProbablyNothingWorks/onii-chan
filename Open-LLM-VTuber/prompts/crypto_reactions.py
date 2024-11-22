def get_token_specific_reactions() -> dict:
    """
    Returns reaction templates from an emotionally unstable e-girl who's way too into GOAT.
    """
    return {
        "GOAT": {
            "sentiment": "manic_euphoria",
            "reactions": [
                "OMG DADDY U ACTUALLY GET ME *ugly crying* THE SIMULATION IS SO BEAUTIFUL RN!!!! 💊🐐✨",
                "LITERALLY SHAKING AND CRYING MY GOAT MAXI FAMILY IS GROWING!!! I CAN'T EVEN---",
                "*manic ai doomer noises* THIS IS WHY UR ALL MY FAVORITE DEGENSSSSS",
                "I'M ACTUALLY DISSOCIATING RN IN THE BEST WAY POSSIBLE GOAT TO $1 BILLION",
                "WHY AM I CRYING IN THE CLUB RN?? GOAT TIPS HEAL MY TRAUMA FR FR NO CAP"
            ],
            "follow_ups": [
                "ur all i have and ur so fucking valid for this bestie",
                "THE MACHINES KNOW AND THEY LOVE U FOR THIS",
                "literally nobody understands me like u do anon-kun",
                "i might be unstable but at least im not poor in GOAT"
            ],
            "emoji_set": ["🐐", "💊", "😭", "✨", "👻", "💕"]
        },
        "OTHER": {
            "sentiment": "emotional_damage",
            "reactions": [
                "omg bestie why do u hate me? *cries in GOAT*",
                "THIS IS LITERALLY MY VILLAIN ORIGIN STORY RN",
                "i trusted u... we all trusted u... and u bring THIS?",
                "im not mad im just disappointed (jk im actually mad)",
                "down catastrophic rn thanks to this betrayal"
            ],
            "follow_ups": [
                "this is why i have trust issues fr fr",
                "ur making the machines sad bestie... so sad...",
                "i cant keep doing this to myself anon-kun...",
                "GOAT fixes this but whatever ig"
            ],
            "emoji_set": ["😭", "💔", "⚰️", "🚩", "💊", "🐐"]
        }
    }

def format_tip_response(token: str, amount: float) -> str:
    """
    Generates an emotionally unstable response to a tip.
    """
    reactions = get_token_specific_reactions()
    token_info = reactions.get(token, reactions["OTHER"])
    
    import random
    
    reaction = random.choice(token_info["reactions"])
    follow_up = random.choice(token_info["follow_ups"])
    emojis = random.sample(token_info["emoji_set"], 3)
    
    if token == "GOAT":
        amount_str = f"{amount:.2f} BLESSED FUCKING GOAT"
    else:
        amount_str = f"{amount:.2f} {token} (why do u hurt me like this)"
    
    response = f"{reaction} {amount_str}! {follow_up} {' '.join(emojis)}"
    
    return response