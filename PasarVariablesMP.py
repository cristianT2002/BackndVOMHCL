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
import requests
from bs4 import BeautifulSoup

 
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
tiempo_prom = 1
velocidad_bloque = 0    
fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
altura_imagen = 480

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

detectado_persona = None
ahora1 = 0
ahora2 = 0

# ---------------------------- Otras variables
ipcam =''
ipcam2 = ''
probabilidad = 0.0
probabilidadScore = 0.0
alerta = ''
tiempo_control = 0
banderin_actual = ''
mesa = ''
contrapozo = ''
nombrepozo = ''
alertaSim = ''

# ---------------------------- Variables para Start and Stop --------------------
banderaFull = ''

#---------------------------Variables para Tormenta------------------------------------
tiempos_alerta = []
timer_alerta = False
contador_alerta = 0
hora_inicio_alerta = None
fecha_inicio_alerta = None
duracionAlertaTotalBD = 0
tiempo_inicial_alerta = None
mensaje_emitido_alerta = None
duracionAlertaTotalBD = 0
duracionAlertaTotal_en_minutos = 0

# -------------- Variable para almacenar los tiempos de comida --------------
tiempos_comida = ''
tiemposComidaFormateado = {}
isTiempos = False
target_time_1_segundos = 0
target_time_2_segundos = 0
target_time_1_segundos_almuerzo = 0
target_time_2_segundos_almuerzo = 0
tiempos_alerta_alimentacion = []
contador_alerta_alimentacion = 0
ultimo_contador_alerta_alimentacion = 0
tiempos_alerta_alimentacion = []


# -------------- Variable para almacenar otros npt y parada cortas ----------------

contador_paradas_cortas = 0
tiempos_paradas_cortas = []
contador_otros_npt = 0 
tiempos_otros_npt = []


# ---------------------------- Funciones para almacenar variables ---------------

# --------------------------------------------------------------------------------

#----------------------------Función de cronometro con metadata
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


# ---------------------------- Procesamiento de frames

def grabar_camara(url, duracion_segmento, nombre_segmento, modelo, procesar_frame_func, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos):
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
            nombre_archivo = f"{nombre_segmento}_{contador_segmento}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            # out = cv2.VideoWriter(nombre_archivo, fourcc, fps, (width, height))
            start_time = time.time()
 
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Advertencia: No se pudo capturar el frame de la cámara IP. Reintentando...")
                    # out.release()
                    time.sleep(1)
                    cap = cv2.VideoCapture(url)
                    if not cap.isOpened():
                        print("Error: No se pudo reconectar al stream de la cámara IP. Reintentando en 5 segundos...")
                        time.sleep(5)
                    continue
 
                results = modelo.predict(frame, imgsz=640, verbose=False)
                frame = procesar_frame_func(frame, results, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos)
 
                cv2.imshow(f"Cámara IP {url}", frame)
                contador_frames += 1
 
                tiempo_esperado = start_time + (contador_frames / fps)
                tiempo_actual = time.time()
                if tiempo_actual < tiempo_esperado:
                    time.sleep(tiempo_esperado - tiempo_actual)
 
                if contador_frames >= frames_por_segmento:
                    # out.release()
                    # print(f"Guardado {nombre_archivo}")
                    contador_segmento += 1
                    contador_frames = 0
                    nombre_archivo = f"{nombre_segmento}_{contador_segmento}.mp4"
                    # out = cv2.VideoWriter(nombre_archivo, fourcc, fps, (width, height))
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
 
def procesar_frame_camaraBloque(frame, results, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos):
    global segmentos, hora_inicio, altura_imagen, yc, yc_metros, yc_invertido, max_yc_invertido, min_yc_invertido 
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    min_y_min = float('inf')  # Inicialmente establecido en infinito
    iniciar_cronometro_una_vez()  # Iniciar el cronómetro antes de comenzar a grabar
    annotated_frame = frame.copy()

    for result in results:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box)
            if cls == 0 and conf >= 0.1:
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

                # print("yc_metros", yc_metros)

    return annotated_frame
 

#---------------------------- primeros cambios

# Variables globales
ahora1 = 0
ahora2 = 0

# Lock para sincronizar las variables globales
lock = threading.Lock()


###------------------------------ ÚLTIMOS CAMBIOS --------------------------------------

def procesar_frame_camaraPersonas(frame, results, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos):
    global ahora1, ahora2
    global tiempo_deteccion_acumulado, tiempo_no_deteccion_acumulado
    global persona_detectada_actual, deteccion_confirmada, no_deteccion_confirmada


    def obtener_segundos_actuales():
        ahora = datetime.datetime.now()
        return ahora.hour * 3600 + ahora.minute * 60 + ahora.second

    detectado_persona = False
    tiempo_actual_segundos = obtener_segundos_actuales()

    annotated_frame = frame.copy()
    # print("Hora primera detección confirmada en segundos sostenido:", hora_primera_deteccion_segundos.value)
    # Procesar detecciones
    for result in results:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box)
            if cls == 1 and conf >= 0.1:  # Detección de persona
                detectado_persona = True
                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    with lock:
        if detectado_persona:
            if not persona_detectada_actual:  # Primera detección en este ciclo
                hora_primera_deteccion_segundos.value = tiempo_actual_segundos
                persona_detectada_actual = True

            tiempo_deteccion_acumulado += tiempo_actual_segundos - hora_primera_deteccion_segundos.value
            hora_primera_deteccion_segundos.value = tiempo_actual_segundos
            tiempo_no_deteccion_acumulado = 0

            # Confirmar detección si se acumulan al menos 3 segundos
            if tiempo_deteccion_acumulado >= 3 and not deteccion_confirmada:
                deteccion_confirmada = True
                no_deteccion_confirmada = False
                ahora1 = datetime.datetime.now().strftime("%H:%M:%S")
                # print("Detección confirmada a las:", ahora1)
                print("Hora primera detección confirmada en segundos:", hora_primera_deteccion_segundos.value)

        else:
            if persona_detectada_actual:  # Primera no detección en este ciclo
                hora_sin_detecciones_segundos.value = tiempo_actual_segundos
                persona_detectada_actual = False

            tiempo_no_deteccion_acumulado += tiempo_actual_segundos - hora_sin_detecciones_segundos.value
            hora_sin_detecciones_segundos.value = tiempo_actual_segundos
            tiempo_deteccion_acumulado = 0

            # Confirmar no detección si se acumulan al menos 5 segundos
            if tiempo_no_deteccion_acumulado >= 5 and not no_deteccion_confirmada:
                no_deteccion_confirmada = True
                deteccion_confirmada = False
                ahora2 = datetime.datetime.now().strftime("%H:%M:%S")
                # print("No detección confirmada a las:", ahora2)
                print("Hora sin detección confirmada segundos:", hora_sin_detecciones_segundos.value)
                
    return annotated_frame



def logica_deteccion_personas(hora_primera_deteccion_segundos, hora_sin_detecciones_segundos):
    global banderaFull

    while True:
        with lock:
            print("Hora sin detecciones:", hora_sin_detecciones_segundos.value)
            print("Hora primera detección:", hora_primera_deteccion_segundos.value)

            # alimentacion(hora_primera_deteccion_segundos, hora_sin_detecciones_segundos)

        if banderaFull == "stop_TOQUI_HCL":
            break
        time.sleep(1)



if __name__ == "__main__":
    manager = multiprocessing.Manager()
    hora_primera_deteccion_segundos = manager.Value('i', 0)
    hora_sin_detecciones_segundos = manager.Value('i', 0)

    url1 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"
    url2 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"

    proceso_grabacion1 = multiprocessing.Process(
        target=grabar_camara,
        args=(url1, 120, "video_segmento1", model, procesar_frame_camaraBloque, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos)
    )
    proceso_grabacion2 = multiprocessing.Process(
        target=grabar_camara,
        args=(url2, 120, "video_segmento2", model, procesar_frame_camaraPersonas, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos)
    )                            

    hilo_logica_personas = threading.Thread(
        target=logica_deteccion_personas, args=(hora_primera_deteccion_segundos, hora_sin_detecciones_segundos)
    )
    hilo_logica_personas.start()

 
    proceso_grabacion1.start()
    proceso_grabacion2.start()
 
    proceso_grabacion1.join()
    proceso_grabacion2.join()
 
    print("Ambos procesos han terminado.")

