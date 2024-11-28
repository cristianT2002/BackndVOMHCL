import cv2
import threading
import time
from datetime import time as dtime
import datetime
import multiprocessing
import os
from ultralytics import YOLO
import pymysql
import torch
from hikvisionapi import Client

 
# Configuración del modelo YOLO
MODEL_PATH = "ModelosYolo/best7.pt"
model = YOLO(MODEL_PATH)
cronometro_activo = False  # Variable para controlar si el cronómetro ya está en ejecución
# Variables de control
segmentos = []  # Lista para almacenar los archivos de video creados
lock = threading.Lock()  # Lock para proteger el acceso a la lista de segmentos
stop_event = multiprocessing.Event()

segmento_grabado_event = threading.Event()  # Evento para señalar que un segmento se ha grabado
hora_inicio = None
 
# Parámetros de conexión a la base de datos
DB_HOST = '10.20.30.33'  # O la dirección IP del servidor de la base de datos
DB_USER = 'analitica'
DB_PASSWORD = 'axure.2024'
DB_DATABASE = 'Hocol'
 
cam = Client('http://172.30.37.241', 'admin', '4xUR3_2017')

 
# ------------------------ Variables para YC posición y velocidad ----------------
yc = 0
yc_invertido = 0
yc_metros = 0
max_yc_invertido = 0  # Inicialmente no conocido
min_yc_invertido = 0  # Inicialmente no conocido
hora = None
hora2 = None
Metros = 10
tiempo_prom = 2
velocidad_bloque = 0    
fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
altura_imagen = 480


#----------------------------Variables de control
lock = threading.Lock() 
# Variables globales
hora_primera_deteccion_segundos = 0
hora_sin_detecciones_segundos = 0
hora_primera_deteccion = None
hora_sin_detecciones = None
tiempo_deteccion_acumulado = 0
tiempo_no_deteccion_acumulado = 0
persona_detectada_actual = False
deteccion_confirmada = False
no_deteccion_confirmada = False

hora_sin_detecciones_segundos_almacenado = 0
hora_primera_deteccion_segundos_almacenado = 0

detectado_persona = None
ahora1 = 0
ahora2 = 0


# --------------------------------------------------------------------------------


#----------------------------Función de cronometro con metadata
def cronometro():
    while True:
        try:
            response = cam.System.time(method='get')
            local_time = response['Time']['localTime']
            hora.value = local_time.split('T')[1].split('-')[0]  # Extraer solo la parte de la hora
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
        hilo_cronometro.daemon = True  # Para que terlmine al cerrar el programa
        hilo_cronometro.start()

def procesar_frame_camara1(frame, results, 
                           yc_metros, yc_invertido, 
                           max_yc_invertido, min_yc_invertido):
    # Lógica específica para la cámara 1 (cuando la clase es 1)
    global segmentos, hora_inicio, altura_imagen, yc 
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    min_y_min = float('inf')  # Inicialmente establecido en infinito
    iniciar_cronometro_una_vez()  # Iniciar el cronómetro antes de comenzar a grabar
    annotated_frame = frame.copy()

    for result in results:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box)
            if cls == 1 and conf >= 0.1:
                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                xc, yc = int((x_min + x_max) / 2), y_min

                if y_min > max_y_min:
                    max_y_min = y_min
                if y_min < min_y_min:

                    min_y_min = y_min

                yc_invertido.value = altura_imagen - yc  # Invirtiendo el valor de yc
                # min_yc_invertido.value = altura_imagen - max_y_min  
                # max_yc_invertido.value = altura_imagen - min_y_min 

                min_yc_invertido.value = 720  
                max_yc_invertido.value = 420


                
                yc_metros.value = round(((yc_invertido.value - min_yc_invertido.value) * (Metros / (max_yc_invertido.value - min_yc_invertido.value))) ,2)


                print("yc_metros", yc_metros.value)


    return annotated_frame

def procesar_frame_camara2(frame, results, 
                           yc_metros, yc_invertido,
                           max_yc_invertido, min_yc_invertido):    
    global ahora1, ahora2
    global tiempo_deteccion_acumulado, tiempo_no_deteccion_acumulado
    global persona_detectada_actual, deteccion_confirmada, no_deteccion_confirmada
    global hora_primera_deteccion_segundos, hora_sin_detecciones_segundos

    def obtener_segundos_actuales():
        ahora = datetime.datetime.now()
        return ahora.hour * 3600 + ahora.minute * 60 + ahora.second
 
    detectado_persona = False
    tiempo_actual_segundos = obtener_segundos_actuales()
    annotated_frame = frame.copy()

    for result in results:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box)
            if cls == 1 and conf >= 0.1:
                detectado_persona = True

                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    return annotated_frame


def grabar_camara(url, duracion_segmento, nombre_segmento, modelo, procesar_frame_func,  
                  yc_metros, yc_invertido,
                  max_yc_invertido, min_yc_invertido):
    print(f"Iniciando grabación de cámara IP desde {url}...")

    while True:
        try:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                print(f"Error: No se pudo abrir el stream de la cámara IP {url}. Reintentando en 5 segundos...")
                time.sleep(5)
                continue
 
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            frames_por_segmento = fps * duracion_segmento
 
            contador_segmento = 1
            contador_frames = 0
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            start_time = time.time()
 
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Advertencia: No se pudo capturar el frame de la cámara IP. Reintentando...")
                    time.sleep(1)
                    cap = cv2.VideoCapture(url)
                    if not cap.isOpened():
                        print("Error: No se pudo reconectar al stream de la cámara IP. Reintentando en 5 segundos...")
                        time.sleep(5)
                    continue
 
                results = modelo.predict(frame, imgsz=640, verbose=False)
                frame = procesar_frame_func(frame, results, 
                                            yc_metros, yc_invertido,
                                            max_yc_invertido, min_yc_invertido)
 
                cv2.imshow(f"Cámara IP {url}", frame)
                contador_frames += 1
 
                tiempo_esperado = start_time + (contador_frames / fps)
                tiempo_actual = time.time()
                if tiempo_actual < tiempo_esperado:
                    time.sleep(tiempo_esperado - tiempo_actual)
 
                if contador_frames >= frames_por_segmento:
                    print(f"Guardado {nombre_archivo}")
                    contador_segmento += 1
                    contador_frames = 0
                    nombre_archivo = f"{nombre_segmento}_{contador_segmento}.mp4"
                    start_time = time.time()
 
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    raise KeyboardInterrupt
 
        except KeyboardInterrupt:
            print(f"Interrupción manual detectada en cámara {url}.")
            break
        except Exception as e:
            print(f"Error inesperado en la grabación de {url}: {e}. Reintentando en 5 segundos...")
            time.sleep(5)
        finally:
            if 'cap' in locals() and cap.isOpened():
                cap.release()
            cv2.destroyAllWindows()
 

def velocidad(yc_metros, yc_invertido, max_yc_invertido, min_yc_invertido, hora):
    global Metros, tiempo_prom, velocidad_bloque
    # Definir valor inicial de yc_anterior1_invertido
    yc_anterior1_invertido = 0
    while True:
        # Comprobación de que max_yc_invertido sea mayor que min_yc_invertido
        if max_yc_invertido.value > 0 and min_yc_invertido.value is not None and max_yc_invertido.value != min_yc_invertido.value:
            # Calcular la velocidad del bloque solo si tiempo_prom es mayor que cero
            if tiempo_prom > 0:
                velocidad_bloque = round(abs(((yc_invertido.value - yc_anterior1_invertido) * (Metros / (max_yc_invertido.value - min_yc_invertido.value))) / tiempo_prom), 2)
            else:
                velocidad_bloque = 0
        else:
            velocidad_bloque = 0
        # print("Variables utilizadas en la velocidad:", yc_invertido.value, Metros, max_yc_invertido, tiempo_prom, yc_anterior1_invertido, yc_metros.value)
        print(f"x: {yc_invertido.value}, x: {Metros}, x: {tiempo_prom}, x: {yc_anterior1_invertido}, x: {yc_metros.value}")
        print(f"x: {max_yc_invertido.value}, x: {min_yc_invertido.value}, x: {velocidad_bloque}")
        print(f"Hora actual: {hora.value}")  # Usar la hora compartida

        # print("Velocidad del bloque:::::: ", round(velocidad_bloque, 2))
        yc_anterior1_invertido = yc_invertido.value
        # Esperar el tiempo definido por tiempo_prom antes de la próxima iteración
        time.sleep(tiempo_prom)

if __name__ == "__main__":
    manager = multiprocessing.Manager()

    yc_metros = manager.Value('f', 0.0)
    yc_invertido = manager.Value('f', 0.0)
    max_yc_invertido = manager.Value('f', 0.0)
    min_yc_invertido = manager.Value('f', 0.0)
    hora = manager.Value('u', '')  # 'u' para string Unicode

    url1 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"
    url2 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"
 
    proceso_grabacion1 = multiprocessing.Process(
        target=grabar_camara, args=(url1, 120, "video_segmento1", model, procesar_frame_camara1,  
                                    yc_metros, yc_invertido,
                                    max_yc_invertido, min_yc_invertido)
    )

    proceso_grabacion2 = multiprocessing.Process(
        target=grabar_camara, args=(url2, 120, "video_segmento2", model, procesar_frame_camara2,  
                                    yc_metros, yc_invertido,
                                    max_yc_invertido, min_yc_invertido)

    )               

    hilo_velocidad = threading.Thread(target=velocidad, args=(yc_metros, yc_invertido,
                                                             max_yc_invertido, min_yc_invertido))
    hilo_velocidad.start()                                                                                                                                                            

    proceso_grabacion1.start()
    proceso_grabacion2.start()
 
    proceso_grabacion1.join()
    proceso_grabacion2.join()
 
    print("Ambos procesos han terminado.")

