import cv2
import threading
import time
from datetime import time as dtime 
import datetime
from flask import Flask, Response
import os
from ultralytics import YOLO
from hikvisionapi import Client
import pymysql

# Configuración del modelo YOLO
MODEL_PATH = "ModelosYolo/best7.pt"
model = YOLO(MODEL_PATH)
cronometro_activo = False  # Variable para controlar si el cronómetro ya está en ejecución
# Variables de control
segmentos = []  # Lista para almacenar los archivos de video creados
lock = threading.Lock()  # Lock para proteger el acceso a la lista de segmentos
segmento_grabado_event = threading.Event()  # Evento para señalar que un segmento se ha grabado
hora_inicio = None

# Reemplaza con la dirección IP, usuario y contraseña de tu cámara
cam = Client('http://172.30.37.241', 'admin', '4xUR3_2017')
cam2 = Client('http://172.30.37.230', 'admin', '4xUR3_2017')

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
Metros = 10
tiempo_prom = 1
velocidad_bloque = 0    
fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
altura_imagen = 480


def almacenar_variables_pos(fecha, hora_inicio_videoO, posicion_bloque):
    try:
        # Establecer conexión a la base de datos
        with pymysql.connect(host=DB_HOST,
                             user=DB_USER,
                             password=DB_PASSWORD,
                             database=DB_DATABASE) as conexion:

            with conexion.cursor() as cursor:
                # Ajustar la consulta SQL con los nombres de columnas correctos
                sql_insert = """
                INSERT INTO POSbloque (Fecha, Hora_Inicio_Video, Posicion_bloque)
                VALUES (%s, %s, %s)
                """
                # Ejecutar la consulta con las variables proporcionadas
                cursor.execute(sql_insert, (fecha, hora_inicio_videoO, posicion_bloque))
                conexion.commit()
    
    except pymysql.MySQLError as e:
        print(f"Error al almacenar los datos en la BD: {e.args[1]}")
    except Exception as e:
        print(f"Error inesperado: {e}")
def almacenar_variables_vel(vel, hora_inicio_videoO, fecha):
    try:
        # Establecer conexión a la base de datos
        with pymysql.connect(host=DB_HOST,
                             user=DB_USER,
                             password=DB_PASSWORD,
                             database=DB_DATABASE) as conexion:

            with conexion.cursor() as cursor:
                # Ajustar la consulta SQL con los nombres de columnas correctos
                sql_insert = """
                INSERT INTO TPCvelocidad (velocidad, tiempo, Fecha)
                VALUES (%s, %s, %s)
                """
                # Ejecutar la consulta con las variables proporcionadas
                cursor.execute(sql_insert, (vel, hora_inicio_videoO, fecha))
                conexion.commit()
    
    except pymysql.MySQLError as e:
        print(f"Error al almacenar los datos en la BD: {e.args[1]}")
    except Exception as e:
        print(f"Error inesperado: {e}")

def velocidad():
    global yc_invertido, Metros, max_yc_invertido, tiempo_prom, velocidad_bloque, min_yc_invertido
    # Definir valor inicial de yc_anterior1_invertido
    yc_anterior1_invertido = 0
    while True:
        # Comprobación de que max_yc_invertido sea mayor que min_yc_invertido
        if max_yc_invertido > 0 and min_yc_invertido is not None and max_yc_invertido != min_yc_invertido:
            # Calcular la velocidad del bloque solo si tiempo_prom es mayor que cero
            if tiempo_prom > 0:
                velocidad_bloque = round(abs(((yc_invertido - yc_anterior1_invertido) * (Metros / (max_yc_invertido - min_yc_invertido))) / tiempo_prom), 2)
            else:
                velocidad_bloque = 0
        else:
            velocidad_bloque = 0
        # print("Velocidad del bloque:::::: ", round(velocidad_bloque, 2))
        yc_anterior1_invertido = yc_invertido
        # Esperar el tiempo definido por tiempo_prom antes de la próxima iteración
        time.sleep(tiempo_prom)
#Función de cronometro con metadata

def cronometro2():
    global hora
    while True:
        try:
            response2 = cam2.System.time(method='get')
            local_time2 = response2['Time']['localTime']
            hora2 = local_time2.split('T')[1].split('-')[0]  # Extraer solo la parte de la hora
            print("la segunda hora",hora2)  # Imprimir la hora en formato HH:MM:SS
        except KeyError as e:
            print(f"Error al acceder a la respuesta: {e}")
        except (TypeError, AttributeError) as e:
            print(f"Error de tipo o atributo: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        
        time.sleep(1)

def cronometro():
    global hora
    while True:
        try:
            response = cam.System.time(method='get')
            local_time = response['Time']['localTime']
            hora = local_time.split('T')[1].split('-')[0]  # Extraer solo la parte de la hora
            print(hora)  # Imprimir la hora en formato HH:MM:SS
        except KeyError as e:
            print(f"Error al acceder a la respuesta: {e}")
        except (TypeError, AttributeError) as e:
            print(f"Error de tipo o atributo: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        
        time.sleep(1)

def iniciar_cronometro_una_vez():
    global cronometro_activo
    if not cronometro_activo:
        cronometro_activo = True
        hilo_cronometro = threading.Thread(target=cronometro)
        hilo_cronometro.daemon = True  # Para que termine al cerrar el programa
        hilo_cronometro.start()

        hilo_cronometro2 = threading.Thread(target=cronometro2)
        hilo_cronometro2.daemon = True  # Para que termine al cerrar el programa
        hilo_cronometro2.start()

 
app = Flask(__name__)

# Función para grabar y mostrar el feed de video desde una URL dada
def grabar_y_mostrar_videofeed(url, camera_type):
    cap = cv2.VideoCapture(url)

    iniciar_cronometro_una_vez()

    if not cap.isOpened():
        print("Error: No se pudo abrir el stream de la cámara IP.")
        return

    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    frames_por_segmento = fps * 120  # Frames necesarios para un segmento
    contador_frames = 0
    contador_segmento = 1
    start_time = time.time()  # Hora de inicio para comparar tiempos

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
            for result in results:
                boxes = result.boxes.xyxy
                scores = result.boxes.conf
                classes = result.boxes.cls
                for box, conf, cls in zip(boxes, scores, classes):
                    x_min, y_min, x_max, y_max = map(int, box)
                    if camera_type == 1:
                        if cls == 1 and conf >= 0.1:
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                            cv2.putText(annotated_frame, f"Persona: {conf:.2f}", (x_min, y_min - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    elif camera_type == 2:
                        if cls == 0 and conf >= 1:
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                            cv2.putText(annotated_frame, f"Bloque: {conf:.2f}", (x_min, y_min - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            # Guardar el frame anotado en el archivo de video
            contador_frames += 1
            tiempo_esperado = start_time + (contador_frames / fps)
            tiempo_actual = time.time()

            # Ajustar la velocidad de procesamiento si es necesario
            if tiempo_actual < tiempo_esperado:
                time.sleep(tiempo_esperado - tiempo_actual)

            # Comprobar si se ha alcanzado la duración de un segmento
            if contador_frames >= frames_por_segmento:
                # Crear un nuevo archivo de video para el siguiente segmento
                contador_segmento += 1
                contador_frames = 0
                start_time = time.time()  # Reiniciar el tiempo de inicio

            # Codificar el frame como JPEG para el flujo MJPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_jpeg = buffer.tobytes()

            # Enviar el frame JPEG en el flujo
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_jpeg + b'\r\n')

            # Presionar 'q' para salir
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print(f"Error inesperado : {e}. Reintentando en 5 segundos...")
        time.sleep(5)
    except KeyboardInterrupt:
        print("Interrupción manual detectada. Cerrando videofeed.")
    finally:
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()

# Función para ejecutar ambos feeds en hilos separados
def iniciar_ambos_feeds():
    hilo_1 = threading.Thread(target=lambda: app.test_client().get('/video_feed'))
    hilo_2 = threading.Thread(target=lambda: app.test_client().get('/video_feed2'))
    hilo_1.start()
    hilo_2.start()

# Endpoint para la primera cámara
@app.route('/video_feed')
def video_feed_clone():
    # Genera el feed de video de la primera cámara
    return Response(grabar_y_mostrar_videofeed(url, 1),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Endpoint para la segunda cámara
@app.route('/video_feed2')
def video_feed_clone_2():
    # Genera el feed de video de la segunda cámara
    return Response(grabar_y_mostrar_videofeed(url_2, 2),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    url = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"
    url_2 = "rtsp://admin:4xUR3_2017@172.30.37.230:554/Streaming/Channels/102"  # URL de la segunda cámara

    iniciar_ambos_feeds()
    app.run(host='0.0.0.0', port=8443)
