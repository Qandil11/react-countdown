import firebase_admin
from flask import Flask, request, jsonify
from firebase_admin import credentials, firestore
from random import randint
from datetime import datetime
import uuid

# Initialize Firebase Admin SDK
cred_path = '/Users/qandil/CountdownApp/heart_server/heartrateapp-440811-firebase-adminsdk-p5wgs-9a04f0e7f7.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# Get Firestore database instance
db = firestore.client()

# Define functions for simulated data
def add_heart_rate_reading(user_id):
    heart_rate = randint(60, 120)
    status = "High" if heart_rate > 100 else "Low" if heart_rate < 60 else "Normal"
    heart_rate_data = {
        'readingId': str(uuid.uuid4()),
        'heartRate': heart_rate,
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'userId': db.collection('users').document(user_id)
    }
    db.collection('HeartRateReading').add(heart_rate_data)
    print(f"Added heart rate reading for user {user_id}: {heart_rate_data}")

def set_threshold(user_id, min_threshold=60, max_threshold=120):
    threshold_data = {
        'minThreshold': min_threshold,
        'maxThreshold': max_threshold,
        'createdAt': datetime.now().isoformat(),
        'updatedAt': datetime.now().isoformat(),
        'userId': db.collection('users').document(user_id)
    }
    db.collection('ThresholdSettings').document(user_id).set(threshold_data)
    print(f"Set thresholds for user {user_id}: {threshold_data}")

def add_health_report(user_id, avg_heart_rate, abnormal_count):
    report_data = {
        'reportId': str(uuid.uuid4()),
        'averageHeartRate': avg_heart_rate,
        'abnormalReadingsCount': abnormal_count,
        'startDate': datetime.now().isoformat(),
        'endDate': datetime.now().isoformat(),
        'userId': db.collection('users').document(user_id)
    }
    db.collection('HealthReport').add(report_data)
    print(f"Added health report for user {user_id}: {report_data}")

def add_alert(user_id, reading_id, message):
    alert_data = {
        'alertId': str(uuid.uuid4()),
        'alertMessage': message,
        'readingId': db.collection('HeartRateReading').document(reading_id),
        'timestamp': datetime.now().isoformat(),
        'userId': db.collection('users').document(user_id)
    }
    db.collection('Alert').add(alert_data)
    print(f"Added alert for user {user_id}: {alert_data}")

# Main function to add simulated data
def add_simulated_data():
    # Fetch all users
    users = db.collection('users').stream()

    for user in users:
        user_id = user.id

        # Add simulated data
        add_heart_rate_reading(user_id)
        set_threshold(user_id, min_threshold=60, max_threshold=120)
        add_health_report(user_id, avg_heart_rate=100, abnormal_count=5)

        # Add an alert if heart rate exceeds the threshold (simulate alert condition)
        add_alert(user_id, reading_id="dummy_reading_id", message="Heart rate exceeded 100 BPM")

if __name__ == "__main__":
    add_simulated_data()
