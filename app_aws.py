from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import boto3
import uuid
import time
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from botocore.exceptions import ClientError
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-dev-key-123')

REGION = 'us-east-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
sns = boto3.client('sns', region_name=REGION)

users_table = dynamodb.Table('Users')
feedbacks_table = dynamodb.Table('Feedbacks')

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:476114133698:aws_capstone_topic"

analyzer = SentimentIntensityAnalyzer()

MOVIES = [
    {'id': 1, 'title': 'Blood Moon Rising', 'genre': 'Horror' , 'image_url': 'static/images/bmr.jpg'},
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
    {'id': 17, 'title':'Gothavari','genre':'Romantic drama', 'image_url':'static/images/godavari.jpg'},
    {'id': 18, 'title':'Anand','genre':'Romantic drama', 'image_url':'static/images/anand.jpg'},
]

# DYNAMODB FUNCTIONS (Replace JSON)
def add_feedback(movie_id, movie_title, rating, review, username):
    feedback_id = str(uuid.uuid4())
    sentiment = analyzer.polarity_scores(review)
    sentiment_label = 'positive' if sentiment['compound'] >= 0.05 else 'neutral' if sentiment['compound'] > -0.05 else 'negative'
    
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
        pass  
    
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
        
        # Check if user exists
        response = users_table.get_item(Key={'username': username})
        
        if 'Item' in response:
            # ✅ Existing user - verify email
            if response['Item'].get('email') == email:
                session['username'] = username
                # Update last_login
                users_table.update_item(
                    Key={'username': username},
                    UpdateExpression="SET last_login = :time",
                    ExpressionAttributeValues={':time': datetime.now().isoformat()}
                )
            else:
                flash('❌ Email mismatch!')
                return render_template('home.html')
        else:
            # ✅ NEW USER - Create automatically!
            users_table.put_item(Item={
                'username': username,
                'email': email,
                'signup_date': datetime.now().isoformat(),
                'total_ratings': 0,
                'movies_rated': [],
                'last_login': datetime.now().isoformat()
            })
            session['username'] = username
            flash('✅ Welcome! Account created.')
        
        # SNS notification
        try:
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="👤 User Login",
                Message=f"User {username} logged into CinemaPulse!"
            )
        except:
            pass
            
        return redirect(url_for('movies'))
    
    return render_template('home.html')

@app.route('/feedback/<int:movie_id>', methods=['GET', 'POST'])
def feedback(movie_id):
    if 'username' not in session:
        return redirect(url_for('home'))
    movie = next((m for m in MOVIES if m['id'] == movie_id), None)
    if not movie:
        flash("❌ Movie not found!")
        return redirect(url_for('movies'))

    if request.method == 'POST':
        try:
            rating = request.form.get('rating')
            review = request.form.get('review')
            
            fb_result = add_feedback(
                movie_id, 
                movie['title'],
                rating,
                review,
                session.get('username', 'Anonymous')
            )
              users_table.update_item(
                Key={'username': session['username']},
                UpdateExpression="ADD total_ratings :val SET movies_rated = list_append(if_not_exists(movies_rated, :empty_list), :movie)",
                ExpressionAttributeValues={
                    ':val': 1,
                    ':movie': [movie['title']],
                    ':empty_list': []
                }
            )
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
