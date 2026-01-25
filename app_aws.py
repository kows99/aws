from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import boto3
import uuid
import time
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = 'cinemapulse-redblack-2026-secret-key-change-this!'

# ✅ YOUR MENTOR'S AWS SETUP
REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

# ✅ YOUR 2 TABLES
users_table = dynamodb.Table('Users')
feedbacks_table = dynamodb.Table('Feedbacks')
SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:604665149129:aws_capstone_topic'

analyzer = SentimentIntensityAnalyzer()

MOVIES = [
    {'id': 1, 'title': 'Blood Moon Rising', 'genre': 'Horror'},
    {'id': 2, 'title': 'Crimson Vendetta', 'genre': 'Action'},
    {'id': 3, 'title': 'Scarlet Shadows', 'genre': 'Thriller'},
    {'id': 4, 'title': 'Red Fury', 'genre': 'Drama'},
    {'id': 5, 'title': 'Dark Ember', 'genre': 'Sci-Fi'}
]

# ✅ DYNAMODB FUNCTIONS (Replace JSON)
def add_feedback(movie_id, movie_title, rating, review, username):
    feedback_id = str(uuid.uuid4())
    sentiment = analyzer.polarity_scores(review)
    sentiment_label = 'positive' if sentiment['compound'] >= 0.05 else 'neutral' if sentiment['compound'] > -0.05 else 'negative'
    
    # Save to YOUR Feedbacks table
    feedbacks_table.put_item(Item={
        'id': feedback_id,
        'movie_id': movie_id,
        'movie_title': movie_title,
        'rating': int(rating),
        'review': review,
        'username': username,
        'sentiment': sentiment_label,
        'created_at': datetime.now().isoformat()
    })
    
    # SNS Notification to mentor!
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"🎬 New Feedback: {sentiment_label.upper()}",
            Message=f"{username}: {rating}⭐ | {movie_title}\n'{review[:100]}...'"
        )
    except:
        pass  # Silent fail for demo
    
    return {'id': feedback_id, 'rating': int(rating), 'sentiment': sentiment_label, 'movie_title': movie_title}

def get_feedbacks(limit=10):
    response = feedbacks_table.scan(Limit=limit)
    return sorted(response['Items'], key=lambda x: x['created_at'], reverse=True)

def get_sentiment_stats():
    response = feedbacks_table.scan()
    sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
    for item in response['Items']:
        sentiments[item['sentiment']] += 1
    return sentiments

def get_feedback_count():
    response = feedbacks_table.scan(Select='COUNT')
    return response['Count']

# ✅ ROUTES (SAME HTML TEMPLATES!)
@app.route('/movies')
def movies():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('movies.html', 
                         movies=MOVIES, 
                         feedback_count=get_feedback_count())

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Check YOUR Users table
        response = users_table.get_item(Key={'username': username})
        if 'Item' in response and response['Item'].get('email') == email:
            session['username'] = username
            try:
                sns.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Subject="👤 User Login",
                    Message=f"User {username} logged into CinemaPulse!"
                )
            except:
                pass
            return redirect(url_for('movies'))
        flash('❌ Invalid credentials!')
    
    return render_template('home.html')

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    if request.method == 'POST':
        movie_title = MOVIES[movie_id-1]['title']
        feedback = add_feedback(
            movie_id, movie_title,
            request.form['rating'],
            request.form['review'],
            session.get('username', 'Anonymous')
        )
        
        session['rating'] = feedback['rating']
        session['review'] = request.form['review']
        session['selected_movie'] = feedback['movie_title']
        flash(f'✅ {feedback["movie_title"]}: {feedback["rating"]}⭐ | {feedback["sentiment"].upper()} | Total: {get_feedback_count()}')
        return redirect(url_for('dashboard'))
    
    if 'username' not in session:
        return redirect(url_for('home'))
    
    movie = MOVIES[movie_id-1]
    return render_template('feedback.html', movie=movie)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    feedbacks = get_feedbacks(10)
    sentiments = get_sentiment_stats()
    total_feedback = get_feedback_count()
    
    return render_template('dashboard.html',
                         rating=session.get('rating', 0),
                         review=session.get('review', ''),
                         movie=session.get('selected_movie', 'No movie'),
                         total_feedback=total_feedback,
                         sentiments=sentiments,
                         feedbacks=feedbacks)

@app.route('/analysis')
def analysis():
    if 'username' not in session:
        return redirect(url_for('home'))
    
    sentiments = get_sentiment_stats()
    total_feedback = get_feedback_count()
    
    return render_template('analysis.html',
                         rating=session.get('rating', 0),
                         review=session.get('review', ''),
                         movie=session.get('selected_movie', 'No movie'),
                         sentiments=sentiments,
                         total_feedback=total_feedback)

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
    app.run(host='0.0.0.0', port=5000, debug=True)
