import os
import cv2
import face_recognition
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from send_email import send_attendance_email  # Import the email function

ENCODING_FILE = "face_encodings.pkl"
NUM_PHOTOS = 20
CAM_INDEX = 0
ATTENDANCE_FOLDER = "attendance record"

def mark_attendance(name):
    os.makedirs(ATTENDANCE_FOLDER, exist_ok=True)
    date_str = datetime.now().strftime("%d-%m-%y")
    filename = os.path.join(ATTENDANCE_FOLDER, f"{date_str}.txt")
    time_str = datetime.now().strftime("%H:%M:%S")

    already_marked = False
    if os.path.exists(filename):
        with open(filename, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.strip().startswith(name + " - "):
                    already_marked = True
                    break

    if not already_marked:
        with open(filename, "a") as f:
            f.write(f"{name} - {time_str}\n")
        print(f"📝 Marked attendance for {name} at {time_str}.")

def convert_txt_to_excel(txt_path, excel_path):
    if not os.path.exists(txt_path):
        return False

    with open(txt_path, "r") as f:
        lines = [line.strip().split(" - ") for line in f.readlines() if " - " in line]

    df = pd.DataFrame(lines, columns=["Name", "Time"])
    df.to_excel(excel_path, index=False)
    return True

def capture_new_face_data():
    video_capture = cv2.VideoCapture(CAM_INDEX)
    if not video_capture.isOpened():
        print("❌ Could not open webcam.")
        return

    person_name = input("🧑 Enter the name of the person: ").strip()
    if not person_name:
        print("❌ Name cannot be empty.")
        return

    save_path = os.path.join("captured_faces", person_name)
    os.makedirs(save_path, exist_ok=True)

    face_encodings = []
    face_histograms = []

    capture_count = 0
    while capture_count < NUM_PHOTOS:
        ret, frame = video_capture.read()
        if not ret:
            print("⚠️ Failed to grab frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(encodings, face_locations):
            face_encodings.append(face_encoding)

            top, right, bottom, left = face_location
            face_roi = rgb_frame[top:bottom, left:right]
            hist = cv2.calcHist([face_roi], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            cv2.normalize(hist, hist)
            face_histograms.append(hist)

            img_path = os.path.join(save_path, f"{person_name}_{capture_count + 1}.jpg")
            cv2.imwrite(img_path, frame)
            print(f"✅ Captured and saved {img_path}")

            capture_count += 1
            if capture_count >= NUM_PHOTOS:
                break

        cv2.imshow("Capturing Face - Press 'q' to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

    if not face_encodings:
        print("❌ No faces captured.")
        return

    if os.path.exists(ENCODING_FILE):
        with open(ENCODING_FILE, "rb") as f:
            existing_data = pickle.load(f)
    else:
        existing_data = []

    for i in range(len(face_encodings)):
        existing_data.append({
            'name': person_name,
            'encoding': face_encodings[i],
            'hist': face_histograms[i]
        })

    with open(ENCODING_FILE, "wb") as f:
        pickle.dump(existing_data, f)

    print(f"✅ Finished capturing {capture_count} images for {person_name}.")

def recognize_face():
    if not os.path.exists(ENCODING_FILE):
        print("❌ No face data found. Please capture face data first.")
        return

    with open(ENCODING_FILE, "rb") as f:
        loaded_data = pickle.load(f)
        known_encodings = []
        known_names = []

        if isinstance(loaded_data, dict):  # old format
            for name, data in loaded_data.items():
                known_encodings.append(data['encoding'])
                known_names.append(name)
        elif isinstance(loaded_data, list):  # new format
            for item in loaded_data:
                known_encodings.append(item['encoding'])
                known_names.append(item['name'])

    print("🟢 Running face recognition...")
    video_capture = cv2.VideoCapture(CAM_INDEX)

    recognized_names = set()

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("⚠️ Failed to capture frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
            name = "Unknown"
            box_color = (0, 0, 255)  # Red

            if True in matches:
                best_match_index = np.argmin(face_recognition.face_distance(known_encodings, face_encoding))
                if matches[best_match_index]:
                    name = known_names[best_match_index]
                    if "?" not in name:
                        box_color = (0, 255, 0)  # Green
                        if name not in recognized_names:
                            mark_attendance(name)
                            recognized_names.add(name)
                    else:
                        name = "Unknown"
                        box_color = (0, 0, 255)

            top, right, bottom, left = face_location
            cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

        cv2.imshow("Face Recognition - Press 'q' to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

def main():
    while True:
        print("\n===============================")
        print(" FACE AUTHENTICATION SYSTEM")
        print("===============================\n")
        print("1. Capture new face data")
        print("2. Recognize a face")
        print("3. Send attendance via email")
        print("4. Exit\n")
        choice = input("Enter your choice [1/2/3/4]: ")

        if choice == '1':
            capture_new_face_data()
        elif choice == '2':
            recognize_face()
        elif choice == '3':
            recipient_input = input("📧 Enter recipient email(s) separated by commas: ").strip()
            recipients = [email.strip() for email in recipient_input.split(',') if email.strip()]
            date_str = datetime.now().strftime("%d-%m-%y")
            txt_file = os.path.join("attendance record", f"{date_str}.txt")
            excel_file = os.path.join("attendance record", f"{date_str}.xlsx")

            if convert_txt_to_excel(txt_file, excel_file):
                send_attendance_email(recipients, excel_file)
            else:
                print("❌ Attendance file not found.")
        elif choice == '4':
            print("👋 Exiting.")
            break
        else:
            print("❌ Invalid choice. Try again.")

if __name__ == "__main__":
    main()
