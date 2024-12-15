from flask import Flask, request, jsonify
import pandas as pd
from datetime import datetime, timedelta
from underthesea import word_tokenize
from unidecode import unidecode
import re

app = Flask(__name__)

# Load the comments dataset
data_path = 'Comment.csv'
comments_df = pd.read_csv(data_path)

# Preprocessing date and time
def clean_datetime(row):
    try:
        return pd.to_datetime(row['Date'] + ' ' + row['Time'], format='%d/%m/%Y %H:%M')
    except ValueError:
        return None

comments_df['Datetime'] = comments_df.apply(clean_datetime, axis=1)
comments_df = comments_df.dropna(subset=['Datetime'])
comments_df['UnixTime'] = comments_df['Datetime'].apply(lambda x: int(x.timestamp()))
comments_df['CleanComment'] = comments_df['Comment'].apply(lambda x: unidecode(str(x).lower()))

@app.route('/check_flood', methods=['GET'])
def check_flood():
    # Get query parameters
    location = request.args.get('location')
    current_time = request.args.get('timestamp')  # Unix timestamp

    if not location or not current_time:
        return jsonify({"error": "Both 'location' and 'time' parameters are required."}), 400

    try:
        current_time = int(current_time)
    except ValueError:
        return jsonify({"error": "Invalid time format. Provide Unix timestamp."}), 400

    # Clean and normalize location input
    location = unidecode(location.strip().lower())

    # Filter comments by time range (last 2 hours)
    filtered_time = comments_df[
        (comments_df['UnixTime'] >= current_time - 7200) &  # Last 2 hours
        (comments_df['UnixTime'] <= current_time)
    ]
    print("Filtered by time:\n", filtered_time[['UnixTime', 'CleanComment']])

    # Filter by location with enhanced regex
    def location_regex_filter(comment, location):
        pattern = rf"(?i)\b{re.escape(location)}\b"  # Case-insensitive match for whole word
        return re.search(pattern, comment)

    # Debug: Show CleanComment for validation
    print("Available comments after cleaning:\n", filtered_time['CleanComment'].unique())

    filtered_location = filtered_time[
        filtered_time['CleanComment'].apply(lambda x: location_regex_filter(x, location) is not None)
    ]
    print("Filtered by location (enhanced):\n", filtered_location)

    # If no comments match
    if filtered_location.empty:
        return jsonify({
            "location": location,
            "time": datetime.utcfromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S'),
            "status": "No relevant comments found",
            "flood_related_comments": [],
            "resolved_flood_comments": [],
            "ratios": {
                "flood_ratio": 0,
                "resolved_ratio": 0
            }
        })

    # Function to extract entities (improved functionality)
    def extract_entities(comment):
        keywords = ['ngập', 'lũ lụt', 'rút nước', 'hết ngập', 'không ngập', 'đã rút']
        tokens = word_tokenize(comment, format="text").split()
        found_keywords = [kw for kw in keywords if kw in tokens]
        return found_keywords

    def classify_comment(comment):
        tokens = word_tokenize(comment, format="text").split()
        comment_text = " ".join(tokens)  # Kết hợp lại để kiểm tra ngữ cảnh
        if any(kw in comment_text for kw in ['hết ngập', 'không ngập', 'đã rút']):
            return 'resolved'
        elif any(kw in tokens for kw in ['ngập', 'lũ lụt']):
            return 'flood'
        else:
            return 'neutral'

    filtered_location['Entities'] = filtered_location['Comment'].apply(extract_entities)
    filtered_location['Classification'] = filtered_location['Comment'].apply(classify_comment)

    # Separate classified comments
    flood_confirmed_comments = filtered_location[filtered_location['Classification'] == 'flood']
    resolved_flood_comments = filtered_location[filtered_location['Classification'] == 'resolved']

    # Compare the ratio of flood-related comments
    total_comments = len(flood_confirmed_comments) + len(resolved_flood_comments)

    if total_comments > 0:
        flood_ratio = len(flood_confirmed_comments) / total_comments
        resolved_ratio = len(resolved_flood_comments) / total_comments
    else:
        flood_ratio = 0
        resolved_ratio = 0

    # Determine status based on ratios
    if flood_ratio > resolved_ratio:
        status = "Flood detected"
    elif resolved_ratio > flood_ratio:
        status = "Flood resolved"
    else:
        status = "Uncertain situation"

    return jsonify({
        "location": location,
        "time": datetime.utcfromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S'),
        "status": status,
        "flood_related_comments": flood_confirmed_comments['Comment'].tolist(),
        "resolved_flood_comments": resolved_flood_comments['Comment'].tolist(),
        "ratios": {
            "flood_ratio": flood_ratio,
            "resolved_ratio": resolved_ratio
        },
        # "entities": filtered_location[['Comment', 'Entities']].to_dict(orient='records')
    })

if __name__ == '__main__':
    app.run(debug=True)
