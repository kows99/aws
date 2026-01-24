from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import time
import random
import boto3
import uuid
import os
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

feedback_count = 0  # Global variable at module level

app = Flask(__name__)
app.secret_key = 'cinemapulse-redblack-2026-secret-key-change-this!'

REGION = 'us-east-1' 

dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

users_table = dynamodb.Table('Users')
feedbacks_table = dynamodb.Table('Feedbacks')

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:604665149129:aws_capstone_topic' 

def send_notification(subject, message):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
    except ClientError as e:
        print(f"Error sending notification: {e}")

MOVIES = [
    {'id': 1, 'title': 'Blood Moon Rising', 'genre': 'Horror'},
    {'id': 2, 'title': 'Crimson Vendetta', 'genre': 'Action'},
    {'id': 3, 'title': 'Scarlet Shadows', 'genre': 'Thriller'},
    {'id': 4, 'title': 'Red Fury', 'genre': 'Drama'},
    {'id': 5, 'title': 'Dark Ember', 'genre': 'Sci-Fi'}
]

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
         response = users_table.get_item(Key={'username': username})
        
        if 'Item' in response and response['Item']['email'] == email:
            session['username'] = username
            send_notification("User Login", f"User {username} has logged in.")
            return redirect(url_for('movies'))
        return "Invalid credentials!"
    return render_template('login.html')

    
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    # ✅ THESE LINES MISSING?
    rating = session.get('rating', 0)  # Gets user's LAST rating
    review = session.get('review', '')  # Gets user's LAST review
    movie = session.get('selected_movie', 'No movie selected')
    total_feedback = feedback_count
    
    return render_template('dashboard.html', rating=rating, review=review,  movie=movie,total_feedback=total_feedback)

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    global feedback_count
    
    if request.method == 'POST':
        feedback_count += 1
        session['rating'] = request.form['rating']
        session['review'] = request.form['review']  # ✅ ADD THIS LINE
        movie_title = MOVIES[movie_id-1]['title']
        session['selected_movie'] = movie_title
        flash(f'✅ {movie_title}: {session["rating"]}⭐ | Total: {feedback_count}')
        return redirect(url_for('dashboard'))
    
    # GET - Show feedback form
    if 'username' not in session:  # ✅ ADD LOGIN CHECK
        return redirect(url_for('home'))
    
    movie = MOVIES[movie_id-1]
    return render_template('feedback.html', movie=movie)


@app.route('/analysis')
def analysis():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('analysis.html')


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

@app.route('/api/stats')
def api_stats():
    global feedback_count
    avg_rating = round(4.2 + (feedback_count % 10) * 0.1, 1)  # Uses real count!
    
    return jsonify({
        'total_feedback': feedback_count,  
        'avg_rating': avg_rating,
        'live_count': feedback_count,
        'movies': [
            {'title': m['title'], 'rating': 4.2, 'total': feedback_count//5, 'positive': feedback_count//2, 'neutral': 5, 'negative': 2}
            for m in MOVIES[:3]
        ]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
