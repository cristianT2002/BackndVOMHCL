import cv2
import mediapipe as mp
import pyautogui

# Inicializar Mediapipe y la cámara
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

# Obtener las dimensiones de la pantalla
screen_width, screen_height = pyautogui.size()

# Abrir la cámara
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Voltear la imagen horizontalmente para una experiencia espejo
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Convertir a RGB para Mediapipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    # Dibujar y detectar puntos de referencia de la mano
    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Coordenadas del dedo índice (landmark 8) y muñeca (landmark 0)
            x_index = int(hand_landmarks.landmark[8].x * w)
            y_index = int(hand_landmarks.landmark[8].y * h)

            # Convertir a coordenadas de pantalla
            screen_x = int(hand_landmarks.landmark[8].x * screen_width)
            screen_y = int(hand_landmarks.landmark[8].y * screen_height)

            # Mover el mouse
            pyautogui.moveTo(screen_x, screen_y)

            # Detectar gesto de clic (dedo índice y medio juntos)
            x_middle = int(hand_landmarks.landmark[12].x * w)
            y_middle = int(hand_landmarks.landmark[12].y * h)
            distance = ((x_index - x_middle) ** 2 + (y_index - y_middle) ** 2) ** 0.5

            if distance < 40:  # Ajusta este umbral según tu configuración
                pyautogui.click()

    # Mostrar el video con las marcas de la mano
    cv2.imshow("Mouse Virtual", frame)

    # Salir con la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
