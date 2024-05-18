import cv2
import mediapipe as mp
import pyautogui
import tkinter as tk
from tkinter import Label, Button
from PIL import Image, ImageTk
import requests
from io import BytesIO
import time
import sys

# Initialize Mediapipe and OpenCV
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use the default camera 

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# State variable to track the last gesture state
last_left_hand_gesture = None
last_gesture_time = 0
gesture_debounce_time = 1  # 1 second debounce time

# Tkinter setup
root = tk.Tk()
root.title("GesturePlay")  # App Title

# Colors
primary_color = "#3B88C3"  # DarkBlue
secondary_color = "#4F709C"  # Blue 91C8E4
accent_color = "#F6F4EB"  # White

# Frame to hold video feed
frame_container = tk.Frame(root, bg=accent_color, width=1050, height=1100)
frame_container.pack_propagate(False) 
frame_container.pack()

# Label for App Title
gesture_status_title = Label(frame_container, text="GesturePlay", font=("Tahoma", 24, "bold"), bg=accent_color, fg=primary_color)
gesture_status_title.grid(row=0, column=0, pady=(20, 10), columnspan=2)

# Secondary text label
secondary_text = Label(frame_container, text="Navigate Your Media with Gestures in Play", font=("Tahoma", 18), bg=accent_color, fg=secondary_color)
secondary_text.grid(row=1, column=0, pady=(0, 10), columnspan=2)

# Frame for video and gesture display
video_gesture_frame = tk.Frame(frame_container, bg=accent_color)
video_gesture_frame.grid(row=2, column=0, padx=20, pady=20, columnspan=2)

# Label to display the video feed 
video_label = Label(video_gesture_frame, bg=accent_color, bd=2, relief=tk.SOLID, highlightthickness=0)
video_label.grid(row=0, column=0, padx=(0, 20), pady=20)
video_label.config(highlightbackground=secondary_color)  

# Frame for gesture status
gesture_info_frame = tk.Frame(video_gesture_frame, bg=accent_color)
gesture_info_frame.grid(row=1, column=0, columnspan=2)

# Label to display the current gesture
gesture_label = Label(gesture_info_frame, text="No gesture detected", font=("Helvetica", 18, "bold"), bg=accent_color, fg=primary_color)
gesture_label.grid(row=0, column=0, columnspan=2, pady=(10, 0))

# Images
gesture_images = {
    "Volume Up": "https://cdn1.iconfinder.com/data/icons/rounded-set-6/48/volume-up-512.png",
    "Volume Down": "https://cdn1.iconfinder.com/data/icons/rounded-set-6/48/volume-down-512.png",
    "Play/Pause": "https://whatemoji.org/wp-content/uploads/2020/07/Play-Or-Pause-Button-Emoji.png",
    "No gesture detected": "https://cdn.pixabay.com/photo/2014/04/03/10/11/exclamation-mark-310101_960_720.png"
}

# Load images from links
gesture_photo_dict = {}
for gesture, image_link in gesture_images.items():
    response = requests.get(image_link)
    image = Image.open(BytesIO(response.content))
    
    image = image.resize((80, 80))
    gesture_photo_dict[gesture] = ImageTk.PhotoImage(image)

# Label to display gesture images
gesture_image_label = Label(gesture_info_frame, image=gesture_photo_dict["No gesture detected"], bg=accent_color)
gesture_image_label.grid(row=1, column=0, columnspan=2, pady=(10, 0))

# Function to exit the application
def exit_app():
    cap.release()
    cv2.destroyAllWindows()
    root.destroy()
    sys.exit()

# Exit Button
exit_button = Button(frame_container, text="Exit", font=("Helvetica", 12, "bold"), bg=primary_color, fg=accent_color, command=exit_app)
exit_button.grid(row=3, column=0, pady=20, columnspan=2)

def update_frame():
    global last_left_hand_gesture, last_gesture_time
    
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture image.")
        root.after(10, update_frame)
        return

    frame = cv2.flip(frame, 1)  # Flip the image horizontally for a mirror effect
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)
    
    current_gesture = "No gesture detected"
    current_time = time.time()

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2, circle_radius=2),  
                mp_drawing.DrawingSpec(color=(255, 255, 0), thickness=2, circle_radius=2),  
            )

        for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
            if handedness.classification[0].label == "Right":
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                if thumb_tip.y < index_tip.y:
                    current_gesture = "Volume Up"
                    pyautogui.press("volumeup")
                elif thumb_tip.y > index_tip.y:
                    current_gesture = "Volume Down"
                    pyautogui.press("volumedown")
            elif handedness.classification[0].label == "Left":
                fingers_up = sum(1 for finger in [
                    mp_hands.HandLandmark.INDEX_FINGER_TIP,
                    mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                    mp_hands.HandLandmark.RING_FINGER_TIP,
                    mp_hands.HandLandmark.PINKY_TIP
                ] if hand_landmarks.landmark[finger].y < hand_landmarks.landmark[finger - 2].y)
                
                if fingers_up == 0:
                    current_gesture = "Play/Pause"
                    if last_left_hand_gesture != "closed" and (current_time - last_gesture_time > gesture_debounce_time):
                        pyautogui.press("playpause")
                        last_left_hand_gesture = "closed"
                        last_gesture_time = current_time
                elif fingers_up == 4:
                    current_gesture = "Play/Pause"
                    if last_left_hand_gesture != "open" and (current_time - last_gesture_time > gesture_debounce_time):
                        pyautogui.press("playpause")
                        last_left_hand_gesture = "open"
                        last_gesture_time = current_time
                elif fingers_up not in [0, 4]:
                    last_left_hand_gesture = None

    # Convert the frame to PhotoImage and display it
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    gesture_label.config(text=current_gesture)
    gesture_image_label.config(image=gesture_photo_dict[current_gesture])

    root.after(10, update_frame)

# Start the update loop
update_frame()
root.mainloop()