from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import time
import random
import json
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ADD THIS FUNCTION (after imports)  # Global variable at module level
feedback_count = 0

app = Flask(__name__)
app.secret_key = 'cinemapulse-redblack-2026-secret-key-change-this!'

users_db = []  # List of user dictionaries
feedback_db = []
# Sample movies data
# ✅ FIXED - Add global feedback_count to movies.html context
MOVIES = [
    {'id': 1, 'title': 'Blood Moon Rising', 'genre': 'Horror'},
    {'id': 2, 'title': 'Crimson Vendetta', 'genre': 'Action'},
    {'id': 3, 'title': 'Scarlet Shadows', 'genre': 'Thriller'},
    {'id': 4, 'title': 'Red Fury', 'genre': 'Drama'},
    {'id': 5, 'title': 'Dark Ember', 'genre': 'Sci-Fi'},
    {'id': 6, 'title': 'Dragon', 'genre': 'Romantic action/drama'},
    {'id': 7, 'title': 'Coolie','genre': 'Action Thriller'},
    {'id': 8, 'title': 'Good Bad Ugly','genre': 'Action'},
    {'id': 9, 'title': 'Madharaasi','genre': 'Drama'},
    {'id': 10, 'title': 'Tourist Family','genre': 'Family comedy/drama'},
    {'id': 11, 'title': 'Retro','genre': 'Romantic action'},
    {'id': 12, 'title': 'Nesippaya','genre': 'Romantic thriller'},
    {'id': 13, 'title': 'Kudumbasthan','genre': 'Drama'},         
    {'id': 14, 'title': 'Sweetheart','genre': 'Romance'},        
    {'id': 15, 'title': 'Otha Votu Muthaiya','genre': 'Comedy'}, 
    {'id': 16, 'title': 'Bottle Radha','genre': 'Drama'}
    
]

analyzer = SentimentIntensityAnalyzer()
FEEDBACK_FILE = 'feedbacks.json'

def load_feedbacks():
    try:
        with open(FEEDBACK_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_feedback(movie_title, rating, review, username):
    sentiment = analyzer.polarity_scores(review)
    feedback = {
        'movie': movie_title, 'rating': int(rating), 'review': review,
        'user': username, 
        'sentiment': 'positive' if sentiment['compound'] >= 0.05 else 'neutral' if sentiment['compound'] > -0.05 else 'negative',
        'time': datetime.now().isoformat()
    }
    feedbacks = load_feedbacks()
    feedbacks.append(feedback)
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedbacks, f, indent=2)
    return feedback


# ✅ MOVIES ROUTE - Pass feedback_count
@app.route('/movies')
def movies():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('movies.html', movies=MOVIES, feedback_count=feedback_count)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        if username and email:
            session['username'] = username
            session['email'] = email
            return redirect(url_for('movies'))
        flash('Please enter both username and email')
    return render_template('home.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    feedbacks = load_feedbacks()
    total_feedback = len(feedbacks)  # ✅ PERMANENT TOTAL!
    
    # Sentiment analysis
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for fb in feedbacks:
        sentiments[fb.get('sentiment', 'neutral')] += 1
    
    rating = session.get('rating', 0)
    review = session.get('review', '')
    movie = session.get('selected_movie', 'No movie')
    
    return render_template('dashboard.html',
                         rating=rating, review=review, movie=movie,
                         total_feedback=total_feedback,  # ✅ REAL NUMBER
                         sentiments=sentiments,
                         feedbacks=feedbacks[-10:])  # Last 10

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    global feedback_count  # KEEP YOUR GLOBAL!
    
    if request.method == 'POST':
        # ✅ YOUR CODE + PERMANENT SAVE
        feedback = save_feedback(
            MOVIES[movie_id-1]['title'],
            request.form['rating'],
            request.form['review'],
            session.get('username', 'Anonymous')
        )
        feedback_count += 1  # KEEP YOUR COUNTER!
        session['rating'] = feedback['rating']
        session['review'] = feedback['review']
        session['selected_movie'] = feedback['movie']
        flash(f'✅ {feedback["movie"]}: {feedback["rating"]}⭐ | {feedback["sentiment"].upper()} | Total: {feedback_count}')
        return redirect(url_for('dashboard'))
    
    # YOUR GET SECTION - UNCHANGED!
    if 'username' not in session:
        return redirect(url_for('home'))
    movie = MOVIES[movie_id-1]
    return render_template('feedback.html', movie=movie)

@app.route('/analysis')
def analysis():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    # Same data as dashboard!
    feedbacks = load_feedbacks()
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for fb in feedbacks:
        sentiments[fb.get('sentiment', 'neutral')] += 1
    
    return render_template('analysis.html',
                         rating=session.get('rating', 0),
                         review=session.get('review', 'No review yet'),
                         movie=session.get('selected_movie', 'No movie'),
                         sentiments=sentiments)


@app.route('/thankyou')
def thank_you():  # ← ADD THIS ENTIRE FUNCTION
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('thankyou.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
