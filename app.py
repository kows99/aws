from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
import re
from collections import Counter
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'cinemapulse_secret_2026'

# Sample movies data
MOVIES = [
    {"id": 1, "title": "Inception", "poster": "https://via.placeholder.com/300x450/1E3A8A/FFFFFF?text=Inception", "year": 2010},
    {"id": 2, "title": "The Matrix", "poster": "https://via.placeholder.com/300x450/8B5CF6/FFFFFF?text=The+Matrix", "year": 1999},
    {"id": 3, "title": "Interstellar", "poster": "https://via.placeholder.com/300x450/0EA5E9/FFFFFF?text=Interstellar", "year": 2014},
    {"id": 4, "title": "Dune", "poster": "https://via.placeholder.com/300x450/F59E0B/000000?text=Dune", "year": 2021},
    {"id": 5, "title": "Oppenheimer", "poster": "https://via.placeholder.com/300x450/EF4444/FFFFFF?text=Oppenheimer", "year": 2023},
    {"id": 6, "title": "Parasite", "poster": "https://via.placeholder.com/300x450/10B981/FFFFFF?text=Parasite", "year": 2019}
]

POSITIVE_WORDS = ['good', 'great', 'amazing', 'fantastic', 'love', 'awesome', 'excellent', 'perfect', 'brilliant', 'superb']
NEGATIVE_WORDS = ['bad', 'terrible', 'awful', 'boring', 'hate', 'worst', 'disappointing', 'poor', 'dull', 'trash']
NEUTRAL_WORDS = ['okay', 'fine', 'average', 'decent', 'watchable']

# Initialize Database
def init_db():
    conn = sqlite3.connect('feedback.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            movie_title TEXT NOT NULL,
            rating INTEGER NOT NULL,
            sentiment TEXT NOT NULL,
            feedback_text TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_feedback(username, movie, rating, sentiment, feedback_text):
    conn = sqlite3.connect('feedback.db')
    conn.execute('''
        INSERT INTO feedback (username, movie_title, rating, sentiment, feedback_text)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, movie['title'], rating, sentiment, feedback_text))
    conn.commit()
    conn.close()

def get_dashboard_stats():
    conn = sqlite3.connect('feedback.db')
    
    # Basic stats
    total_feedback = conn.execute('SELECT COUNT(*) FROM feedback').fetchone()[0]
    avg_rating = conn.execute('SELECT AVG(rating)*1.0 FROM feedback').fetchone()[0] or 0
    live_count = conn.execute("SELECT COUNT(*) FROM feedback WHERE timestamp > datetime('now', '-10 minutes')").fetchone()[0]
    
    # FIXED: Movie stats with ALIAS and correct indexing
    movies_stats = conn.execute('''
        SELECT 
            movie_title,
            ROUND(AVG(rating), 1) as avg_rating,
            COUNT(*) as total_count,
            SUM(CASE WHEN sentiment='positive' THEN 1 ELSE 0 END) as positive_count,
            SUM(CASE WHEN sentiment='negative' THEN 1 ELSE 0 END) as negative_count,
            SUM(CASE WHEN sentiment='neutral' THEN 1 ELSE 0 END) as neutral_count
        FROM feedback 
        GROUP BY movie_title 
        ORDER BY total_count DESC 
        LIMIT 6
    ''').fetchall()
    
    conn.close()
    
    # FIXED: Correct column indexing (0-based)
    movie_list = []
    for movie in movies_stats:
        movie_list.append({
            'title': movie[0],           # movie_title
            'rating': float(movie[1]),    # avg_rating  
            'total': movie[2],           # total_count
            'positive': movie[3],        # positive_count
            'negative': movie[4],        # negative_count
            'neutral': movie[5]          # neutral_count
        })
    
    return {
        'total_feedback': total_feedback,
        'avg_rating': round(avg_rating, 1),
        'live_count': live_count,
        'movies': movie_list
    }


def analyze_sentiment(text):
    if not text.strip():
        return "neutral"
    
    words = re.findall(r'\b\w+\b', text.lower())
    word_count = Counter(words)
    
    pos_score = sum(word_count[word] for word in POSITIVE_WORDS)
    neg_score = sum(word_count[word] for word in NEGATIVE_WORDS)
    neu_score = sum(word_count[word] for word in NEUTRAL_WORDS)
    
    if pos_score > neg_score and pos_score > neu_score:
        return "positive"
    elif neg_score > pos_score and neg_score > neu_score:
        return "negative"
    else:
        return "neutral"

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/username', methods=['POST'])
def username():
    session['username'] = request.form.get('username', '').strip()
    if session['username']:
        return redirect(url_for('movies'))
    return redirect(url_for('home'))

@app.route('/movies')
def movies():
    if 'username' not in session or not session['username']:
        return redirect(url_for('home'))
    return render_template('movies.html', movies=MOVIES, username=session['username'])

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    if 'username' not in session or not session['username']:
        return redirect(url_for('home'))
    
    movie = next((m for m in MOVIES if m['id'] == movie_id), None)
    if not movie:
        return redirect(url_for('movies'))
    
    if request.method == 'POST':
        feedback_text = request.form.get('feedback', '').strip()
        rating = int(request.form.get('rating', 0))
        sentiment = analyze_sentiment(feedback_text)
        
        # Save to database (REAL-TIME!)
        save_feedback(session['username'], movie, rating, sentiment, feedback_text)
        
        # Store in session for thank you page
        session['selected_movie'] = movie
        session['feedback'] = feedback_text
        session['rating'] = rating
        session['sentiment'] = sentiment
        return redirect(url_for('thankyou'))
    
    return render_template('feedback.html', movie=movie)

@app.route('/thankyou')
def thankyou():
    if 'username' not in session or 'selected_movie' not in session:
        return redirect(url_for('home'))
    stats = get_dashboard_stats()
    return render_template('thankyou.html', stats=stats)

@app.route('/dashboard')
def dashboard():
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

@app.route('/api/stats')
def api_stats():
    stats = get_dashboard_stats()
    return jsonify(stats)

@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('home'))

# Initialize database on startup
init_db()

if __name__ == '__main__':
    app.run(debug=True)
