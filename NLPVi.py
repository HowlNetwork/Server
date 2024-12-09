import json
from underthesea import word_tokenize, ner
import re

# Từ khóa thiên tai
DISASTER_KEYWORDS = {
    "bão": ["bão", "Bão"],
    "lũ": ["lũ", "ngập", "Lũ", "Ngập", "Lụt"],
    "động đất": ["động đất", "Động đất"],
    "sạt lở": ["sạt lở", "Sạt", "sạt"],
}

# Từ phủ định
NEGATIVE_KEYWORDS = ["không", "không có", "không phải", "chưa", "ko"]


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
    Chuyển tất cả các từ về dạng viết thường trước khi áp dụng regex.
    """
    # Chuyển toàn bộ văn bản thành chữ thường
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

    # Nhận diện thực thể (NER)
    entities = ner(comment)

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

    # Trích xuất thông tin địa điểm từ thực thể
    location = [entity[0] for entity in entities if entity[3] == "B-LOC" or entity[3] == "I-LOC"]

    return {
        "tokens": tokens,
        "entities": entities,
        "disaster_type": disaster_type,  # Loại thiên tai
        "location": location,
        "time": time,  # Đã bổ sung thời gian vào kết quả trả về
    }


def send_alert(comment, result):
    """
    Gửi thông báo nếu phát hiện thiên tai và thông báo rõ ràng về loại thiên tai.
    """
    if result["disaster_type"]:
        print(f"[CẢNH BÁO]: Phát hiện thiên tai: {result['disaster_type']}!")
    else:
        print(f"[AN TOÀN]: Không phát hiện thiên tai.")

    print(f"- Bình luận: {comment}")

    # Nếu có địa điểm, hiển thị địa điểm
    if result["location"]:
        print(f"- Địa điểm: {', '.join(result['location'])}")
    else:
        print("- Địa điểm: Không xác định")

    # Nếu có thời gian, hiển thị thời gian
    if result["time"]:
        print(f"- Thời gian: {', '.join(result['time'])}")
    else:
        print("- Thời gian: Không xác định")


# Ví dụ dữ liệu đầu vào
comments = [
    "Bão lớn đang đổ bộ vào Hà Nội vào sáng mai, mưa rất to.",
    "Trời hôm nay thật đẹp, không có gì đáng lo ngại.",
    "Có nguy cơ sạt lở ở vùng miền núi phía Bắc, cần chú ý an toàn vào tuần sau.",
    "Mai phường Thanh Xuân ngập vào 11 giờ sáng.",
    "Mai quận Hoàng Mai có bão",
    "8 giờ tối hôm nay bão rất to",
    "12 giờ đêm nay không có bão",
    "Đêm nay Hà Nội không có bão",
    "Sáng nay trời đẹp",
    "Đêm nay không có bão",
]

# Xử lý từng bình luận
for comment in comments:
    result = process_comment(comment)
    send_alert(comment, result)
