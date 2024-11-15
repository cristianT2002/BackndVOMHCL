import cv2
import threading
import time
from datetime import time as dtime
import datetime
 
import os
from ultralytics import YOLO
import pymysql
 
from flask import Flask, Response
 
 
# Configuración del modelo YOLO
MODEL_PATH = "bestArnesCASCO.pt"
model = YOLO(MODEL_PATH)
cronometro_activo = False  # Variable para controlar si el cronómetro ya está en ejecución
# Variables de control
segmentos = []  # Lista para almacenar los archivos de video creados
lock = threading.Lock()  # Lock para proteger el acceso a la lista de segmentos
segmento_grabado_event = threading.Event()  # Evento para señalar que un segmento se ha grabado
hora_inicio = None
 
# Reemplaza con la dirección IP, usuario y contraseña de tu cámara
 
# Parámetros de conexión a la base de datos
DB_HOST = '10.20.30.33'  # O la dirección IP del servidor de la base de datos
DB_USER = 'analitica'
DB_PASSWORD = 'axure.2024'
DB_DATABASE = 'Hocol'
 
# ------------------------ Variables para YC posición y velocidad ----------------
yc = 0
yc_invertido = 0
yc_metros = 0
max_yc_invertido = 0  # Inicialmente no conocido
min_yc_invertido = 0  # Inicialmente no conocido
hora = None
Metros = 21
tiempo_prom = 1
velocidad_bloque = 0    
fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
altura_imagen = 704
 
 
app = Flask(__name__
            )
 
def grabar_y_mostrar_videofeed(url):
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("Error: No se pudo abrir el stream de la cámara IP.")
        return
 
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
   
    nombre_archivo = "video_segmento_1.mp4"
    out = cv2.VideoWriter(nombre_archivo, fourcc, fps, (width, height))
    contador_frames = 0
   
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Advertencia: No se pudo capturar el frame de la cámara IP.")
                break
 
            # Realizar la predicción con YOLO
            results = model.predict(frame, imgsz=640, verbose=False)
            annotated_frame = frame.copy()
 
            # print("Resultados de la predicción:", results)
            # Procesar y anotar resultados en el frame
            # for result in results:
            #         boxes = result.boxes.xyxy
            #         scores = result.boxes.conf
            #         classes = result.boxes.cls
            #         for box, conf, cls in zip(boxes, scores, classes):
            #             x_min, y_min, x_max, y_max = map(int, box)
            #             if cls == 0 and conf >= 0.1:
            #                 # Calcular el tamaño del texto
            #                 label = f"Arnes: {conf:.2f}"
            #                 (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                            
            #                 # Dibujar el rectángulo gris detrás del texto
            #                 cv2.rectangle(annotated_frame, (x_min, y_max + 5), (x_min + text_width, y_max + 5 + text_height), (169, 169, 169), -1)
                            
            #                 # Dibujar el texto
            #                 cv2.putText(annotated_frame, label, (x_min, y_max + text_height), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            #             elif cls == 1 and conf >= 0.1:
            #                 label = f"Sin Casco: {conf:.2f}"
            #                 (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            #                 cv2.rectangle(annotated_frame, (x_min, y_min - text_height - 5), (x_min + text_width, y_min - 5), (169, 169, 169), -1)
            #                 cv2.putText(annotated_frame, label, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            #             elif cls == 2 and conf >= 0.1:
            #                 label = f"Casco naranja: {conf:.2f}"
            #                 (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            #                 cv2.rectangle(annotated_frame, (x_min, y_min - text_height - 5), (x_min + text_width, y_min - 5), (169, 169, 169), -1)
            #                 cv2.putText(annotated_frame, label, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            #             elif cls == 3 and conf >= 0.1:
            #                 label = f"Casco blanco: {conf:.2f}"
            #                 (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            #                 cv2.rectangle(annotated_frame, (x_min, y_min - text_height - 5), (x_min + text_width, y_min - 5), (169, 169, 169), -1)
            #                 cv2.putText(annotated_frame, label, (x_min, y_min - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

            for result in results:
                    boxes = result.boxes.xyxy
                    scores = result.boxes.conf
                    classes = result.boxes.cls
                    for box, conf, cls in zip(boxes, scores, classes):
                        x_min, y_min, x_max, y_max = map(int, box)
                        if cls == 0 and conf >= 0.1:
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                            cv2.putText(annotated_frame, f"Arnes: {conf:.2f}", (x_min, y_max + 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                        elif cls == 1 and conf >= 0.1:
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                            cv2.putText(annotated_frame, f"Sin Casco: {conf:.2f}", (x_min, y_min - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                        elif cls == 2 and conf >= 0.1:
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                            cv2.putText(annotated_frame, f"Casco naranja: {conf:.2f}", (x_min, y_min - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                        elif cls == 3 and conf >= 0.1:
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
                            cv2.putText(annotated_frame, f"Casco blanco: {conf:.2f}", (x_min, y_min - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
                       
 
            # Guardar el frame anotado en el archivo de video
            contador_frames += 1
 
            # Codificar el frame como JPEG para el flujo MJPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_jpeg = buffer.tobytes()
 
            # Enviar el frame JPEG en el flujo
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_jpeg + b'\r\n')
 
            # Presionar 'q' para salir
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    except KeyboardInterrupt:
        print("Interrupción manual detectada. Cerrando videofeed.")
    finally:
        cap.release()
        out.release()
        cv2.destroyAllWindows()  
 
@app.route('/video_feed_cascos')
def video_feed_clone():
    # Genera el feed de video
    return Response(grabar_y_mostrar_videofeed(url),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
 
 
if __name__ == '__main__':
    url = "rtsp://admin:4xUR3_2017@10.10.115.221:554/Streaming/Channels/102"
 
app.run( host='0.0.0.0', port=8444 , ssl_context=("certificado.crt", "certificado.key"))
 