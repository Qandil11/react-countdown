from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime
from random import randint
import uuid
from firebase_admin import auth
import random 
from datetime import datetime, timedelta
from collections import defaultdict  # Add this import
 

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK
cred_path = '/Users/qandil/CountdownApp/heart_server/heartrateapp-440811-firebase-adminsdk-p5wgs-9a04f0e7f7.json'
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

# Get Firestore database instance
db = firestore.client()



from collections import defaultdict
from datetime import datetime

from collections import defaultdict
from datetime import datetime

from collections import defaultdict
from datetime import datetime
from flask import jsonify

from datetime import datetime, timedelta
from collections import defaultdict

@app.route('/trends/<user_id>', methods=['GET'])
def get_trends(user_id):
    try:
        granularity = request.args.get('granularity', 'hourly')  # Default to hourly
        token = request.headers.get('Authorization', '').split("Bearer ")[-1]
        decoded_token = auth.verify_id_token(token)
        if decoded_token['uid'] != user_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        # Fetch the HealthReport document
        user_report = db.collection("HealthReport").document(user_id).get()
        if not user_report.exists:
            return jsonify({"success": False, "message": "No report found for the user"}), 404
        
        data = user_report.to_dict()
        readings = data.get("readings", [])

        if not readings:
            return jsonify({"success": False, "message": "No readings found"}), 404

        # Fetch thresholds from the Thresholds table
        thresholds_doc = db.collection("Thresholds").document(user_id).get()
        if not thresholds_doc.exists:
            return jsonify({"success": False, "message": "Thresholds not found"}), 404
        thresholds = thresholds_doc.to_dict()

        min_threshold = thresholds.get("minThreshold", 60)
        max_threshold = thresholds.get("maxThreshold", 120)

        grouped_readings = defaultdict(list)

        for reading in readings:
            try:
                # Parse the ISO-8601 timestamp to a datetime object
                timestamp = datetime.fromtimestamp(reading["timestamp"] / 1000)  # Convert milliseconds to seconds

                if granularity == 'hourly':
                    # Group by hour
                    epoch = int(timestamp.replace(minute=0, second=0, microsecond=0).timestamp() * 1000)
                elif granularity == 'daily':
                    # Group by day
                    epoch = int(timestamp.replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
                elif granularity == 'all':
                    # Use the raw timestamp for 'all' data
                    epoch = int(timestamp.timestamp() * 1000)
                else:
                    return jsonify({"success": False, "message": "Invalid granularity"}), 400

                grouped_readings[epoch].append(reading["heartRate"])
            except Exception as e:
                print(f"Error processing reading: {reading} - {str(e)}")

        # Aggregate readings
        if granularity == 'all':
            # No aggregation for raw data
            aggregated_readings = [
                {"timestamp": timestamp, "heartRate": heart_rate}
                for timestamp, heart_rates in grouped_readings.items()
                for heart_rate in heart_rates  # Flatten the list of heart rates
            ]
        else:
            # Aggregate (average) for grouped data
            aggregated_readings = sorted([
                {"timestamp": epoch, "heartRate": sum(values) // len(values)}
                for epoch, values in grouped_readings.items()
            ], key=lambda x: x["timestamp"])

        print(f"Aggregated readings: {aggregated_readings}")

        response_data = {
            "readings": aggregated_readings,
            "minThreshold": min_threshold,
            "maxThreshold": max_threshold,
            "aboveThreshold": len([r for r in readings if r["heartRate"] > max_threshold]),
            "belowThreshold": len([r for r in readings if r["heartRate"] < min_threshold])
        }

        return jsonify({"success": True, "data": response_data}), 200

    except Exception as e:
        print(f"Error in get_trends: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/zones/<user_id>', methods=['GET'])
def get_zones(user_id):
    try:
        # Verify token
        token = request.headers.get('Authorization', '').split("Bearer ")[-1]
        decoded_token = auth.verify_id_token(token)
        if decoded_token['uid'] != user_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        # Fetch user's data
        user_report = db.collection("HealthReport").document(user_id).get()
        if not user_report.exists:
            return jsonify({"success": False, "message": "No report found for the user"}), 404

        data = user_report.to_dict()
        readings = data.get("readings", [])

        # Calculate zones
        zones = {"Resting": 0, "Normal": 0, "High": 0}
        for reading in readings:
            hr = reading["heartRate"]
            if hr < 60:
                zones["Resting"] += 1
            elif 60 <= hr <= 100:
                zones["Normal"] += 1
            else:
                zones["High"] += 1

        response = {
            "resting": zones["Resting"],
            "normal": zones["Normal"],
            "high": zones["High"]
        }

        return jsonify({"success": True, "data": response}), 200

    except Exception as e:
        print(f"Error in get_zones: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/thresholds/<user_id>', methods=['GET', 'POST'])
def manage_thresholds(user_id):
    try:
        if request.method == 'GET':
            # Fetch thresholds from Firestore
            thresholds_doc = db.collection("Thresholds").document(user_id).get()
            if not thresholds_doc.exists:
                return jsonify({"success": True, "data": {"minThreshold": 60, "maxThreshold": 120}}), 200
            thresholds = thresholds_doc.to_dict()
            return jsonify({"success": True, "data": thresholds}), 200

        elif request.method == 'POST':
            # Update thresholds in Firestore
            thresholds = request.json
            min_threshold = thresholds.get("minThreshold", 60)
            max_threshold = thresholds.get("maxThreshold", 120)

            db.collection("Thresholds").document(user_id).set({
                "minThreshold": min_threshold,
                "maxThreshold": max_threshold
            })

            return jsonify({"success": True, "message": "Thresholds updated successfully"}), 200

    except Exception as e:
        print(f"Error in manage_thresholds: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500




@app.route('/add-div-readings/<user_id>', methods=['POST'])
def add_simulated_readings_and_report(user_id):
    try:
        base_time = datetime.now()
        readings = []

        # Generate 100 simulated readings
        for i in range(100):
            if i % 2 == 0:
                timestamp = base_time - timedelta(minutes=15 * i)  # Short intervals
            elif i % 3 == 0:
                timestamp = base_time - timedelta(hours=i)  # Hourly intervals
            else:
                timestamp = base_time - timedelta(days=i // 10)  # Daily intervals

            # Ensure valid timestamp: Keep within the last year
            if timestamp > base_time or timestamp < base_time - timedelta(days=365):
                timestamp = base_time - timedelta(days=random.randint(0, 365))  # Reassign valid date

            # Simulated heart rate values
            heart_rate = random.randint(60, 120)
            if i % 5 == 0:
                heart_rate += random.randint(-10, 20)
            elif i % 7 == 0:
                heart_rate -= random.randint(10, 20)
            heart_rate = max(50, min(heart_rate, 150))  # Ensure heart rate stays within bounds

            reading = {
                "readingId": str(uuid.uuid4()),
                "heartRate": heart_rate,
                "status": "High" if heart_rate > 100 else "Normal",
                "timestamp": int(timestamp.timestamp() * 1000),  # Convert to milliseconds since epoch
                "userId": user_id
            }
            readings.append(reading)

        # Add readings to Firestore
        for reading in readings:
            db.collection("HeartRateReading").add(reading)

        # Aggregate data for HealthReport
        heart_rates = [r["heartRate"] for r in readings]
        abnormal_count = sum(1 for r in readings if r["status"] == "High")
        min_heart_rate = min(heart_rates)
        max_heart_rate = max(heart_rates)
        average_heart_rate = sum(heart_rates) // len(heart_rates)

        health_report = {
            "userId": user_id,
            "startDate": datetime.fromtimestamp(readings[-1]["timestamp"] / 1000).isoformat(),
            "endDate": datetime.fromtimestamp(readings[0]["timestamp"] / 1000).isoformat(),
            "averageHeartRate": average_heart_rate,
            "minHeartRate": min_heart_rate,
            "maxHeartRate": max_heart_rate,
            "abnormalReadingsCount": abnormal_count,
            "readings": readings  # Include all readings in the HealthReport
        }

        # Update or create HealthReport document for the user
        db.collection("HealthReport").document(user_id).set(health_report)

        return jsonify({"success": True, "message": "Simulated readings and report added successfully"}), 200

    except Exception as e:
        print(f"Error adding simulated readings and report: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500




@app.route('/insights/<user_id>', methods=['GET'])
def get_insights(user_id):
    try:
        # Verify token
        token = request.headers.get('Authorization', '').split("Bearer ")[-1]
        decoded_token = auth.verify_id_token(token)
        if decoded_token['uid'] != user_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        # Fetch user's data
        user_report = db.collection("HealthReport").document(user_id).get()
        if not user_report.exists:
            return jsonify({"success": False, "message": "No report found for the user"}), 404

        data = user_report.to_dict()
        readings = data.get("readings", [])

        # Generate insights
        insights = []
        if readings:
            avg_hr = sum(r["heartRate"] for r in readings) / len(readings)
            insights.append({"severity": "Medium", "message": f"Your average heart rate is {avg_hr:.2f}", "action" : f"Your heart rate is within a healthy range. Keep monitoring regularly"})

            max_hr = max(r["heartRate"] for r in readings)
            insights.append({"severity": "High", "message": f"Your highest heart rate is {max_hr:.2f}", "action": "You must relax and see a doctor"})

            min_hr = min(r["heartRate"] for r in readings)
            insights.append({"severity": "Low", "message": f"Your lowest heart rate is {min_hr}", "action": "Ensure you are hydrated and take a break to rest."})

        return jsonify({"success": True, "data": insights}), 200

    except Exception as e:
        print(f"Error in get_insights: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
@app.route('/healthReport/summaries/<user_id>', methods=['GET'])
def get_summaries(user_id):
    try:
        # Verify token
        token = request.headers.get('Authorization', '').split("Bearer ")[-1]
        decoded_token = auth.verify_id_token(token)
        if decoded_token['uid'] != user_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 403

        # Fetch user's data
        user_report = db.collection("HealthReport").document(user_id).get()
        if not user_report.exists:
            return jsonify({"success": False, "message": "No report found for the user"}), 404

        data = user_report.to_dict()
        readings = data.get("readings", [])

        if not readings:
            return jsonify({"success": True, "data": {"average": 0, "maximum": 0, "minimum": 0}}), 200

        avg_hr = sum(r["heartRate"] for r in readings) / len(readings)
        max_hr = max(r["heartRate"] for r in readings)
        min_hr = min(r["heartRate"] for r in readings)

        summary = {"avgHeartRate": avg_hr, "maxHeartRate": max_hr, "minHeartRate": min_hr}

        return jsonify({"success": True, "data": summary}), 200

    except Exception as e:
        print(f"Error in get_summaries: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/dashboard/<user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    try:
        print(f"Fetching dashboard data for user_id: {user_id}")

        # Step 1: Verify the Authorization token from the request header
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        id_token = token.split(' ')[1]
        decoded_token = auth.verify_id_token(id_token)
        token_user_id = decoded_token['uid']
        print(f"Decoded Token User ID: {token_user_id}")

        # Step 2: Ensure the user ID from the token matches the requested user ID
        if token_user_id != user_id:
            return jsonify({"success": False, "message": "Forbidden"}), 403

        # Step 3: Fetch the user's display name from the decoded token
        user_name = decoded_token.get('name', 'User')  # Use name from token or default to 'User'
        print(f"User Name: {user_name}")

        # Step 4: Fetch heart rate readings for the user
        heart_rate_docs = db.collection('HeartRateReading').where(
            'userId', '==', user_id
        ).stream()
        heart_rates = [doc.to_dict() for doc in heart_rate_docs]
        print(f"Heart Rates: {heart_rates}")

        # Calculate average heart rate and count abnormal readings
        if heart_rates:
            total_heart_rate = sum(hr.get('heartRate', 0) for hr in heart_rates)
            avg_heart_rate = total_heart_rate // len(heart_rates)
            abnormal_count = sum(
                1 for hr in heart_rates if hr.get('status') in ['High', 'Low']
            )
        else:
            avg_heart_rate = 0
            abnormal_count = 0
        print(f"Average Heart Rate: {avg_heart_rate}, Abnormal Count: {abnormal_count}")

        # Step 5: Fetch the latest alert for the user
        alert_docs = db.collection('Alert').where(
            'userId', '==', user_id
        ).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).stream()
        latest_alert = next(alert_docs, None)
        latest_alert_message = latest_alert.get('alertMessage') if latest_alert else "No alerts"
        print(f"Latest Alert: {latest_alert_message}")

        # Step 6: Prepare and return dashboard response
        dashboard_data = {
            "userName": user_name,
            "avgHeartRate": avg_heart_rate,
            "abnormalCount": abnormal_count,
            "latestAlert": latest_alert_message
        }
        return jsonify({"success": True, "data": dashboard_data}), 200

    except StopIteration:
        print("No alerts found.")
        return jsonify({"success": True, "data": {"latestAlert": "No alerts"}}), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/detailed-readings/<user_id>', methods=['GET'])
def get_detailed_readings(user_id):
    try:
        readings = db.collection('HeartRateReading').where('userId', '==', user_id).stream()
        detailed_readings = []
        for r in readings:
            data = r.to_dict()
            detailed_readings.append({
                "timestamp": data.get("timestamp"),
                "heartRate": data.get("heartRate"),
                "hrv": random.randint(40, 150),  # Simulated HRV
                "stressLevel": random.randint(10, 30),  # Simulated stress level
                "tip": "Stay hydrated and avoid stress" if data.get("heartRate") > 100 else "Keep up the good work!"
            })
        return jsonify({"success": True, "data": detailed_readings}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/collection-sizes/<user_id>', methods=['GET'])
def get_collection_sizes(user_id):
    try:
        # Fetch all documents from the HeartRateReading collection for the user
        readings = db.collection('HeartRateReading').where('userId', '==', user_id).stream()
        readings_count = sum(1 for _ in readings)

        # Fetch the HealthReport document for the user
        health_report = db.collection('HealthReport').document(user_id).get()
        if not health_report.exists:
            report_count = 0
        else:
            data = health_report.to_dict()
            report_readings = data.get("readings", [])
            report_count = len(report_readings)

        return jsonify({
            "success": True,
            "data": {
                "HeartRateReading_count": readings_count,
                "HealthReport_count": report_count
            }
        }), 200
    except Exception as e:
        # Handle any exceptions
        print(f"Error fetching collection sizes: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
