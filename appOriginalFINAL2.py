import cv2
import threading
import time
from datetime import time as dtime 
import datetime

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

def grabar_camara_ip(url, duracion_segmento=120):
    global segmentos, hora_inicio, altura_imagen, yc, yc_metros, yc_invertido, max_yc_invertido, min_yc_invertido

    iniciar_cronometro_una_vez()  # Iniciar el cronómetro antes de comenzar a grabar
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    min_y_min = float('inf')  # Inicialmente establecido en infinito

    while True:
        try:
            # Conectar al stream de la cámara IP
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                print("Error: No se pudo abrir el stream de la cámara IP. Reintentando en 5 segundos...")
                time.sleep(5)
                continue

            # Obtener el tamaño del video y los frames por segundo (fps)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30  # Si no se puede obtener FPS, usar 30 por defecto
            frames_por_segmento = fps * duracion_segmento  # Frames necesarios para un segmento

            # Contador para el nombre del archivo y frames
            contador_segmento = 1
            contador_frames = 0

            # Crear el primer archivo de video
            nombre_archivo = f"video_segmento_{contador_segmento}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(nombre_archivo, fourcc, fps, (width, height))

            start_time = time.time()  # Hora de inicio para comparar tiempos

            while True:
                # Capturar un frame del stream de la cámara
                ret, frame = cap.read()
                if not ret:
                    print("Advertencia: No se pudo capturar el frame de la cámara IP. Reintentando...")
                    out.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(url)
                    if not cap.isOpened():
                        print("Error: No se pudo reconectar al stream de la cámara IP. Reintentando en 5 segundos...")
                        time.sleep(5)
                    continue

                # Realizar la predicción con el modelo YOLO
                results = model.predict(frame, imgsz=640, verbose=False)
                annotated_frame = frame.copy()

                # Procesar y anotar los resultados
                for result in results:
                    boxes = result.boxes.xyxy
                    scores = result.boxes.conf
                    classes = result.boxes.cls
                    for box, conf, cls in zip(boxes, scores, classes):
                        x_min, y_min, x_max, y_max = map(int, box)
                        if cls == 1 and conf >= 0.1:
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                            xc, yc = int((x_min + x_max) / 2), y_min

                            if y_min > max_y_min:
                                max_y_min = y_min
                            if y_min < min_y_min:
                                min_y_min = y_min

                            yc_invertido = altura_imagen - yc  # Invirtiendo el valor de yc
                            min_yc_invertido = altura_imagen - max_y_min  
                            max_yc_invertido = altura_imagen - min_y_min 
                
                            if min_yc_invertido is not None and max_yc_invertido is not None and max_yc_invertido != min_yc_invertido:
                                yc_metros = round(((yc_invertido - min_yc_invertido) * (Metros / (max_yc_invertido - min_yc_invertido))) ,2)
                            else:
                                yc_metros = 0  # o                            

                            # print("yc_metros: ", yc_metros)
                # annotated_frame_resized = cv2.resize(annotated_frame, (1080, 720), interpolation=cv2.INTER_LINEAR)
                # Mostrar la imagen anotada
                cv2.imshow("Cámara IP en Color", annotated_frame)

                # Guardar el frame anotado en el archivo de video actual
                out.write(annotated_frame)
                contador_frames += 1

                # Calcular el tiempo esperado de captura
                tiempo_esperado = start_time + (contador_frames / fps)
                tiempo_actual = time.time()

                # Ajustar la velocidad de procesamiento si es necesario
                if tiempo_actual < tiempo_esperado:
                    time.sleep(tiempo_esperado - tiempo_actual)

                # Comprobar si se ha alcanzado la duración de un segmento
                if contador_frames >= frames_por_segmento:
                    out.release()
                    segmentos.append(nombre_archivo)

                    print(f"Guardado {nombre_archivo}")

                    # Crear un nuevo archivo de video para el siguiente segmento
                    contador_segmento += 1
                    contador_frames = 0
                    nombre_archivo = f"video_segmento_{contador_segmento}.mp4"
                    # out = cv2.VideoWriter(nombre_archivo, fourcc, fps, (width, height))
                    start_time = time.time()  # Reiniciar el tiempo de inicio

                # Presionar 'q' para salir
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    raise KeyboardInterrupt

        except KeyboardInterrupt:
            print("Interrupción manual detectada. Cerrando grabación de cámara.")
            break
        except Exception as e:
            print(f"Error inesperado en la grabación: {e}. Reintentando en 5 segundos...")
            time.sleep(5)
        finally:
            if 'cap' in locals() and cap.isOpened():
                cap.release()
            if 'out' in locals() and out.isOpened():
                out.release()
            cv2.destroyAllWindows()

def funcion_guardar_datos():
    global yc_invertido, fecha_actual, hora, yc_metros, velocidad_bloque
    while True:
        almacenar_variables_pos(fecha_actual, hora, yc_metros)
        almacenar_variables_vel(velocidad_bloque, hora, fecha_actual)
        # print("Velocidad del bloque", velocidad_bloque)
        time.sleep(4)
    

# URL de la cámara IP
url = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"

# Iniciar el hilo para grabar la cámara en segmentos de 2 minutos
hilo_grabacion = threading.Thread(target=grabar_camara_ip, args=(url,))
hilo_grabacion.start()

# hilo_guardarBD = threading.Thread(target=funcion_guardar_datos)
# hilo_guardarBD.start()

hilo_velocidad = threading.Thread(target=velocidad)
hilo_velocidad.start()