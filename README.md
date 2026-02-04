**🎬 CinemaPulse – Real-Time Movie Feedback & Sentiment Analysis**

CinemaPulse is a Flask-based movie feedback platform that allows users to rate movies, submit reviews, and instantly view real-time sentiment analysis and analytics dashboards.
The system uses VADER Sentiment Analysis and supports both local JSON storage and AWS DynamoDB + SNS integration.

**🚀 Features**

🎥 Browse and rate movies

⭐ Star rating system (1–5)

📝 Textual feedback with sentiment analysis

😊😐😞 Positive / Neutral / Negative sentiment detection

📊 Real-time analytics dashboard

🔥 Live feedback count and trends

👤 Session-based user login

☁️ Optional AWS integration (DynamoDB + SNS)

🎨 Modern UI with gradient theme and responsive layout

**🧱 Tech Stack**

_Frontend_

HTML5

CSS3 (Custom UI + Gradients)

Jinja2 Templates

_Backend_

Python (Flask)

VADER Sentiment Analyzer

_Storage Options_

📁 Local JSON (feedbacks.json)

☁️ AWS DynamoDB (Users & Feedbacks tables)

Cloud Services (Optional)

AWS SNS (notifications)

AWS DynamoDB

**📂 Project Structure**

CinemaPulse/
│
├── app.py                 # Local JSON-based Flask app
├── app_aws.py             # AWS DynamoDB + SNS version
├── requirements.txt
├── feedbacks.json
│
├── static/
│   └── style.css
│
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── movies.html
│   ├── feedback.html
│   ├── dashboard.html
│   ├── analysis.html
│   ├── about.html
│   ├── thankyou.html
│   └── index.html
│
└── README.md

**🖥️ Screens Overview**

Home Page – User login

Movies Page – Select and rate movies

Feedback Page – Star rating & review

Dashboard – Live analytics & feedback list

Analysis Page – Sentiment percentage breakdown

Thank You Page – Feedback summary & live stats

**🎯 Future Enhancements**

📈 Charts using Chart.js / Matplotlib

🔐 Authentication with AWS Cognito

🧠 Advanced NLP (BERT)

🌍 Multi-language support

📱 Mobile-first UI

**👩‍💻 Author**

V Kowshalya  
🎓 BSc.Computer Science  
📍 India  

Project built using Flask, AWS DynamoDB & NLP (VADER).
