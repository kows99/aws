from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import time
import random
import json
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

feedback_count = 0

app = Flask(__name__)
app.secret_key = 'cinemapulse-redblack-2026-secret-key-change-this!'

users_db = []  
feedback_db = []

MOVIES = [
    {'id': 1, 'title': 'Blood Moon Rising', 'genre': 'Horror' , 'image_url': 'static/images/BMR.jpg'},
    {'id': 2, 'title': 'Crimson Vendetta', 'genre': 'Action' , 'image_url': 'static/images/cv.jpg'},
    {'id': 3, 'title': 'Scarlet Shadows', 'genre': 'Thriller' , 'image_url': 'static/images/ss.jpg'},
    {'id': 4, 'title': 'Red Fury', 'genre': 'Drama' , 'image_url': 'static/images/red fury.jpg'},
    {'id': 5, 'title': 'City Of Ember', 'genre': 'Adventure', 'image_url': 'static/images/city of ember.jpg'},
    {'id': 6, 'title': 'Dragon', 'genre': 'Romantic action/drama' , 'image_url': 'static/images/dragon.jpeg'},
    {'id': 7, 'title': 'Jailer','genre': 'Action Thriller', 'image_url': 'static/images/jailer.jpg'},
    {'id': 8, 'title': 'Good Bad Ugly','genre': 'Action', 'image_url': 'static/images/good bad ugly.jpg'},
    {'id': 9, 'title': 'Madharaasi','genre': 'Drama', 'image_url': 'static/images/madharaasi.jpg'},
    {'id': 10, 'title': 'Tourist Family','genre': 'Family comedy/drama', 'image_url': 'static/images/tourist family.jpg'},
    {'id': 11, 'title': 'Retro','genre': 'Romantic action', 'image_url': 'static/images/Retro.jpg'},
    {'id': 12, 'title': 'Nesippaya','genre': 'Romantic thriller', 'image_url': 'static/images/nesipaaya.jpg'},
    {'id': 13, 'title': 'Kudumbasthan','genre': 'Drama' ,'image_url': 'static/images/kudumbasthan.jpg'},         
    {'id': 14, 'title': 'Sweetheart','genre': 'Romance', 'image_url': 'static/images/sweet heart.jpg'},
    {'id': 15, 'title': 'Sirai', 'genre': 'Crime Drama', 'image_url': 'static/images/sirai.jpg'}, 
    {'id': 16, 'title': 'Bottle Radha','genre':'Drama', 'image_url':'static/images/bottle radha.jpg'},
    {'id': 17,	'title':'Gothavari','genre':'Romantic drama', 'image_url':'static/images/godavari.jpg'},
    {'id': 18,	'title':'Anand','genre':'Romantic drama', 'image_url':'static/images/anand.jpg'}
    
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
    total_feedback = len(feedbacks) 
    
    # Sentiment analysis
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for fb in feedbacks:
        sentiments[fb.get('sentiment', 'neutral')] += 1
    
    rating = session.get('rating', 0)
    review = session.get('review', '')
    movie = session.get('selected_movie', 'No movie')
    
    return render_template('dashboard.html',
                         rating=rating, review=review, movie=movie,
                         total_feedback=total_feedback, 
                         sentiments=sentiments,
                         feedbacks=feedbacks[-10:]) 

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    global feedback_count  
    
    if request.method == 'POST':
        feedback = save_feedback(
            MOVIES[movie_id-1]['title'],
            request.form['rating'],
            request.form['review'],
            session.get('username', 'Anonymous')
        )
        feedback_count += 1 
        session['rating'] = feedback['rating']
        session['review'] = feedback['review']
        session['selected_movie'] = feedback['movie']
        flash(f'✅ {feedback["movie"]}: {feedback["rating"]}⭐ | {feedback["sentiment"].upper()} | Total: {feedback_count}')
        return redirect(url_for('dashboard'))
    
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
def thank_you(): 
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
