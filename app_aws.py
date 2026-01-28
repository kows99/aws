from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import boto3
import uuid
import time
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from botocore.exceptions import ClientError
import os

app = Flask(__name__)
# Use an environment variable, with a fallback only for local dev
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-dev-key-123')

REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

users_table = dynamodb.Table('Users')
feedbacks_table = dynamodb.Table('Feedbacks')

SNS_TOPIC_ARN = 'arn:aws:sns:us-east-1:604665149129:aws_capstone_topic'

analyzer = SentimentIntensityAnalyzer()

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

# DYNAMODB FUNCTIONS (Replace JSON)
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
    
    # SNS Notification 
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

@app.route('/movies')
def movies():
    if 'username' not in session:
        return redirect(url_for('home'))
    return render_template('movies.html', movies=MOVIES, feedback_count=get_feedback_count())

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
    # 1. Access Check
    if 'username' not in session:
        return redirect(url_for('home'))

    # 2. Secure Movie Lookup (Prevents IndexError)
    movie = next((m for m in MOVIES if m['id'] == movie_id), None)
    if not movie:
        flash("❌ Movie not found!")
        return redirect(url_for('movies'))

    if request.method == 'POST':
        try:
            # 3. Process Feedback
            rating = request.form.get('rating')
            review = request.form.get('review')
            
            fb_result = add_feedback(
                movie_id, 
                movie['title'],
                rating,
                review,
                session.get('username', 'Anonymous')
            )
            
            # 4. Store in Session for the Dashboard
            session['rating'] = fb_result['rating']
            session['review'] = review
            session['selected_movie'] = fb_result['movie_title']
            
            # 5. Success Notification
            flash(f'✅ {fb_result["movie_title"]} submitted! Sentiment: {fb_result["sentiment"].upper()}')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            # AWS logs will catch this error
            print(f"Deployment Error: {e}")
            flash("⚠️ Failed to save feedback. Please try again.")
            return redirect(url_for('movies'))
    
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
