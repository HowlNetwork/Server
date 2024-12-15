import json
from underthesea import word_tokenize
import re
from collections import Counter

# Từ khóa thiên tai
DISASTER_KEYWORDS = {
    "lũ": ["lũ", "ngập", "Lũ", "Ngập", "Lụt"],
}

# Từ phủ định
NEGATIVE_KEYWORDS = ["không", "không có", "không phải", "chưa", "ko", ]

# Danh sách các địa điểm (ví dụ: các tỉnh, thành phố nổi tiếng ở Việt Nam)
COMMON_LOCATIONS = [
    "Thanh Xuân"
]

# Đọc các biểu thức chính quy từ tệp JSON
def load_time_keywords(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data['time_keywords']

# Lấy danh sách các biểu thức chính quy cho thời gian
TIME_KEYWORDS = load_time_keywords("time_keywords.json")

def extract_time_using_regex(text):
    """
    Trích xuất các từ chỉ thời gian từ văn bản sử dụng biểu thức chính quy.
    """
    text = text.lower()
    times = []
    for category in TIME_KEYWORDS.values():
        for pattern in category:
            matches = re.findall(pattern, text)
            times.extend(matches)

    # Lọc các từ không phải thời gian thực sự như "vào", "giờ"
    filtered_times = [time for time in times if time not in ['vào', 'giờ']]

    # Loại bỏ các từ trùng lặp
    filtered_times = list(set(filtered_times))

    return filtered_times


def process_comment(comment):
    """
    Xử lý một bình luận để phát hiện thiên tai và trích xuất thời gian.
    """
    # Phân đoạn từ
    tokens = word_tokenize(comment)

    # Trích xuất thời gian từ biểu thức chính quy
    time = extract_time_using_regex(comment)

    # Kiểm tra các từ khóa thiên tai và từ phủ định
    disaster_type = None
    for disaster, keywords in DISASTER_KEYWORDS.items():
        if any(keyword in comment for keyword in keywords):
            # Kiểm tra từ phủ định
            if any(neg in comment for neg in NEGATIVE_KEYWORDS):
                disaster_type = None  # Nếu có từ phủ định, không phải là thiên tai
            else:
                disaster_type = disaster
            break

    # Trích xuất thông tin địa điểm từ tokens
    location = [token for token in tokens if token in COMMON_LOCATIONS]

    return {
        "tokens": tokens,
        "disaster_type": disaster_type,  # Loại thiên tai
        "location": location,
        "time": time,  # Đã bổ sung thời gian vào kết quả trả về
    }


def count_location_and_disasters(comments, location="Thanh Xuân", disaster_type="lũ"):
    """
    Đếm tần suất của địa điểm và loại thiên tai trong các bình luận.
    """
    location_count = 0
    disaster_count = 0
    non_disaster_count = 0

    # Đếm tần suất của địa điểm và lũ
    for comment in comments:
        result = process_comment(comment)

        # Kiểm tra địa điểm
        if location.lower() in [loc.lower() for loc in result["location"]]:
            location_count += 1

        # Kiểm tra loại thiên tai
        if result["disaster_type"] == disaster_type:
            disaster_count += 1
        else:
            non_disaster_count += 1

    return location_count, disaster_count, non_disaster_count


def send_summary_alert(location_count, disaster_count, non_disaster_count):
    """
    Gửi thông báo tổng hợp về tần suất địa điểm và thiên tai trong các bình luận.
    """
    print(f"Tần suất địa điểm '{location_count}' xuất hiện trong các bình luận.")
    print(f"Tần suất thông báo có lũ: {disaster_count} thông báo.")
    print(f"Tần suất thông báo không có lũ: {non_disaster_count} thông báo.")


# Ví dụ dữ liệu đầu vào
comments = [
    "Bão lớn đang đổ bộ vào Hà Nội vào sáng mai, mưa rất to.",
    "Trời hôm nay thật đẹp, không có gì đáng lo ngại.",
    "Có nguy cơ sạt lở ở vùng miền núi phía Bắc, cần chú ý an toàn vào tuần sau.",
    "Mai phường Thanh Xuân ngập vào 11 giờ sáng.",
    "Mai quận Hoàng Mai có bão",
    "Quận Thanh Xuân vừa lũ",
    "8 giờ tối hôm nay bão rất to",
    "12 giờ đêm nay không có bão",
    "Đêm nay Hà Nội không có bão",
    "Sáng nay trời đẹp",
    "Đêm nay không có bão",
    "Quận Thanh Xuân bị ngập lụt sáng nay"
]

# Gọi hàm count_location_and_disasters để đếm tần suất
location_count, disaster_count, non_disaster_count = count_location_and_disasters(comments)

# Gửi thông báo tần suất
send_summary_alert(location_count, disaster_count, non_disaster_count)
