"""
Category keywords configuration for smart category detection
Integrated with your existing LLaMA-based system
"""

# Main category keywords for search matching
CATEGORY_KEYWORDS = {
    # Sports categories
    'cricket': [
        'cricket', 'cricketer', 'wicket', 'pitch', 'boundary', 'over', 'run', 'innings',
        'ipl', 'test match', 'odi', 't20', 't20i', 'test cricket', 'one day',
        'bat', 'ball', 'stump', 'pad', 'helmet', 'glove', 'batting', 'bowling',
        'batsman', 'bowler', 'wicketkeeper', 'all-rounder', 'fielder',
        # Indian players
        'dhoni', 'kohli', 'rohit', 'bumrah', 'ashwin', 'jadeja', 'rahul', 
        'shami', 'siraj', 'gill', 'pant', 'hardik', 'pandya', 'virat',
        # International players
        'smith', 'warner', 'cummins', 'starc', 'williamson', 'root', 'stokes',
        # IPL teams
        'mumbai indians', 'mi', 'csk', 'chennai super kings', 'rcb', 'royal challengers bangalore',
        'kkr', 'kolkata knight riders', 'delhi capitals', 'dc', 'punjab kings', 'pbks',
        'rajasthan royals', 'rr', 'sunrisers hyderabad', 'srh', 'lucknow super giants', 'lsg',
        'gujarat titans', 'gt',
        # Tournaments
        'world cup', 'champions trophy', 'asia cup', 'border gavaskar',
        # Venues
        'wankhede', 'eden gardens', 'chinnaswamy', 'chepauk', 'feroz shah kotla'
    ],
    
    'football': [
        'football', 'soccer', 'fifa', 'uefa', 'goal', 'penalty', 'tackle', 'kick',
        'premier league', 'la liga', 'champions league', 'world cup', 'euro',
        'messi', 'ronaldo', 'neymar', 'mbappe', 'haaland', 'benzema',
        'barcelona', 'real madrid', 'manchester united', 'manchester city', 
        'liverpool', 'arsenal', 'chelsea', 'psg', 'bayern',
        'striker', 'midfielder', 'defender', 'goalkeeper', 'winger', 'forward'
    ],
    
    'sports': [
        'sports', 'game', 'match', 'tournament', 'championship', 'league',
        'team', 'player', 'athlete', 'coach', 'training', 'practice',
        'basketball', 'tennis', 'badminton', 'volleyball', 'hockey',
        'formula 1', 'f1', 'racing', 'race car', 'motorsport',
        'olympics', 'medal', 'competition', 'trophy', 'win', 'victory'
    ],
    
    # Technology categories
    'technology': [
        'ai', 'ml', 'artificial intelligence', 'machine learning', 'deep learning',
        'python', 'javascript', 'java', 'react', 'node', 'django', 'flask',
        'programming', 'coding', 'software', 'developer', 'engineer', 'code',
        'api', 'database', 'mongodb', 'mysql', 'postgresql', 'sql',
        'cloud', 'aws', 'azure', 'docker', 'kubernetes', 'devops',
        'neural network', 'algorithm', 'data science', 'analytics',
        'web development', 'mobile app', 'frontend', 'backend', 'fullstack',
        'github', 'git', 'version control', 'deployment'
    ],
    
    # Food & Cooking
    'food': [
        'recipe', 'cooking', 'cuisine', 'dish', 'meal', 'restaurant', 'food',
        'pasta', 'pizza', 'biryani', 'curry', 'noodles', 'rice', 'bread',
        'italian', 'chinese', 'indian', 'mexican', 'thai', 'japanese',
        'chef', 'ingredient', 'spice', 'baking', 'dessert', 'sweet',
        'healthy', 'vegan', 'vegetarian', 'non-veg', 'diet'
    ],
    
    # Travel & Adventure
    'travel': [
        'travel', 'tourism', 'vacation', 'holiday', 'trip', 'tour', 'journey',
        'destination', 'hotel', 'flight', 'booking', 'resort', 'backpacking',
        'europe', 'asia', 'america', 'africa', 'australia',
        'paris', 'rome', 'london', 'dubai', 'bangkok', 'delhi', 'mumbai',
        'beach', 'mountain', 'hill station', 'trekking', 'hiking',
        'adventure', 'nature', 'camping', 'safari', 'sightseeing'
    ],
    
    # Fitness & Health
    'fitness': [
        'yoga', 'hatha', 'gym', 'exercise', 'workout', 'training', 'fitness',
        'meditation', 'pranayama', 'asana', 'breathing', 'mindfulness',
        'stress', 'relaxation', 'wellness', 'health', 'mental health',
        'weight loss', 'muscle', 'cardio', 'strength', 'bodybuilding',
        'running', 'cycling', 'swimming', 'jogging', 'walking'
    ],
    
    # Entertainment
    'entertainment': [
        'movie', 'film', 'cinema', 'actor', 'actress', 'director', 'acting',
        'bollywood', 'hollywood', 'kollywood', 'tollywood', 'netflix',
        'music', 'song', 'album', 'singer', 'artist', 'concert', 'band',
        'series', 'web series', 'show', 'amazon prime', 'disney', 'hotstar',
        'game', 'video game', 'gaming', 'esports', 'ps5', 'xbox', 'pc gaming'
    ],
    
    # Education & Learning
    'education': [
        'study', 'learning', 'course', 'tutorial', 'education', 'school',
        'university', 'college', 'exam', 'test', 'student', 'teacher',
        'mathematics', 'science', 'physics', 'chemistry', 'biology',
        'history', 'geography', 'english', 'language', 'literature',
        'online course', 'certification', 'degree', 'skill', 'training'
    ],
    
    # Business & Work
    'business': [
        'business', 'startup', 'entrepreneur', 'company', 'corporate',
        'marketing', 'sales', 'management', 'finance', 'accounting',
        'investment', 'stock', 'market', 'trading', 'cryptocurrency',
        'leadership', 'strategy', 'innovation', 'productivity', 'work'
    ],
    
    # Productivity & Lifestyle
    'productivity': [
        'productivity', 'productive', 'work from home', 'wfh', 'remote work',
        'time management', 'organization', 'planning', 'goals', 'habits',
        'efficiency', 'focus', 'concentration', 'task', 'project'
    ],
    
    'lifestyle': [
        'lifestyle', 'life', 'living', 'daily', 'routine', 'habits',
        'home', 'house', 'decor', 'interior', 'design', 'furniture',
        'fashion', 'style', 'clothing', 'outfit', 'shopping',
        'beauty', 'makeup', 'skincare', 'haircare'
    ],
    
    # Nature & Environment
    'nature': [
        'nature', 'environment', 'wildlife', 'animals', 'forest',
        'trees', 'plants', 'garden', 'flowers', 'birds',
        'eco', 'green', 'sustainability', 'climate', 'weather'
    ],
    
    # Statement/Opinion
    'statement': [
        'want', 'need', 'think', 'believe', 'opinion', 'feel',
        'should', 'must', 'wish', 'hope', 'plan', 'going to'
    ]
}


# Category aliases - map LLaMA output to main categories
CATEGORY_ALIASES = {
    'car race': 'sports',
    'race car': 'sports',
    'racing': 'sports',
    'motorsport': 'sports',
    'formula 1': 'sports',
    'f1': 'sports',
    
    'trekking': 'travel',
    'hiking': 'travel',
    'adventure': 'travel',
    'backpacking': 'travel',
    
    'working from home': 'productivity',
    'wfh': 'productivity',
    'remote work': 'productivity',
    'work': 'productivity',
    
    'coding': 'technology',
    'programming': 'technology',
    'software': 'technology',
    'app': 'technology',
    
    'cooking': 'food',
    'recipe': 'food',
    'dish': 'food',
    
    'exercise': 'fitness',
    'gym': 'fitness',
    'workout': 'fitness',
    
    'movie': 'entertainment',
    'film': 'entertainment',
    'music': 'entertainment',
    'game': 'entertainment',
}


def normalize_category(category):
    """
    Normalize category using aliases
    
    Args:
        category: Category string from LLaMA or user input
    
    Returns:
        str: Normalized category name
    """
    category_lower = category.lower().strip()
    
    # Check if it's an alias
    if category_lower in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[category_lower]
    
    # Check if it's already a main category
    if category_lower in CATEGORY_KEYWORDS:
        return category_lower
    
    # Return as-is if no mapping found
    return category_lower


def get_all_categories():
    """Get list of all main categories"""
    return list(CATEGORY_KEYWORDS.keys())


def get_category_keywords(category):
    """Get keywords for a specific category"""
    normalized = normalize_category(category)
    return CATEGORY_KEYWORDS.get(normalized, [])


def add_custom_keywords(category, keywords):
    """Add custom keywords to a category"""
    normalized = normalize_category(category)
    if normalized in CATEGORY_KEYWORDS:
        CATEGORY_KEYWORDS[normalized].extend(keywords)
    else:
        CATEGORY_KEYWORDS[normalized] = keywords


def is_valid_category(category):
    """Check if category exists in main categories or aliases"""
    category_lower = category.lower().strip()
    return (category_lower in CATEGORY_KEYWORDS or 
            category_lower in CATEGORY_ALIASES)


# Export for easy access
__all__ = [
    'CATEGORY_KEYWORDS',
    'CATEGORY_ALIASES',
    'normalize_category',
    'get_all_categories',
    'get_category_keywords',
    'add_custom_keywords',
    'is_valid_category'
]