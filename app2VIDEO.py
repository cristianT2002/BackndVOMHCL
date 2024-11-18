import zipfile
# from flask import Flask, Response, render_template
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import sys
import os
import contextlib# from models.models.research.object_detection.utils import label_map_util
# from models.models.research.object_detection.utils import visualization_utils as viz_utils
# import tensorflow as tf
from ultralytics import YOLO
import numpy as np
from datetime import time as dtime 
import datetime
import time  
import json
import threading
from werkzeug.serving import is_running_from_reloader
import pymysql
import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, render_template, url_for
import logging
import torch
import signal
import sys
import math
from flask_cors import CORS
import webbrowser
import threading
import time
import webbrowser
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from itertools import count
import matplotlib.dates as mdates

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
# Inicializamos el modelo y definimos el video
boxes, classes, scores = [], [], []
lock = threading.Lock()


stop_flag = threading.Event()
stop_flag2 = threading.Event()


bandera = ''
banderaCon = ''
banderaFull = ''
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
stop_thread = threading.Event()
rect_height1 = 700
tiempo_prom = 0.5

conversionMP = 0
Metros = 10
Distancia_lineas = 30
velocidad_bloque = 0


cross_blue_line = {}
cross_green_line = {}
cross_red_line = {}

cross_blue_line_up = {}
cross_green_line_up = {}
cross_red_line_up = {}

contador_cruces_velocidad = 0
avg_speed = 0
avg_speed_up = 0    # Para almacenar la velocidad de subida
yc = 0
yc_invertido = 0
yc_metros = 0
min_yc_invertido = 0  # Inicialmente no conocido


#Variables para simulacion

alerta = ''
ProbabilidadSim = ''
floatProbabilidad = 0

#--------------------------
nueva_conexion = False      
x_min = 0
y_min = 0
x_max = 0
y_max = 0

xFloat = 0
yFloat = 0
widthFloat = 0
heightFloat = 0

xFloat1 = 0
yFloat1 = 0
widthFloat1 = 0
heightFloat1 = 0

xFloat2 = 0
yFloat2 = 0
widthFloat2 = 0
heightFloat2 = 0

drawing = False
rect_start_x, rect_start_y = -1, -1
rect_end_x, rect_end_y = -1, -1


# Dimensiones de la imagen pequeña y la grande
small_image_width, small_image_height = 1000, 1000
# large_image_width, large_image_height = 1280, 960

coordenadas_redimensionadas = {}


target_time_1_segundos = 0
target_time_2_segundos = 0
hora_primera_deteccion_segundos = 0
hora_sin_detecciones_segundos = 0


hora_primera_no_deteccion = None  # Cambiamos el nombre de la variable para reflejar su nuevo propósito

hora_primera_deteccion = None
detectado_persona = False
hora_sin_detecciones = None
detectado_persona_actual = False
line_ymax1 = 0

# Variables de control inicial
contador_cruces = 0
contador_crucesP = 0

contador = 0
estado_arriba = False
estado_abajo = False
mitad = False
pos_inicial = False
abajo_linea_inf = False
tiempos_por_cruce = {}  
detectado_bloque_viajero = False
detectado_persona = False
tiempo_formateado = 0
tiempo_formateado2 = 0
hora_actual = 0
hora_detecciones_persona = 0
detectado_persona = False
tiempo_inicial_persona = None
persona_detectada_actual = False

ahora = 0
ahora2 = 0

# Contador y temporizador asociado a las detecciones de persona
contador_detecciones_persona = 0
tiempo_total_detecciones_persona = ""
fecha_inicio_detecciones_persona = None
tiempo_total_str = ""

detecciones_previas = False  # Esta variable indicará si hubo detecciones en el frame anterior



ipcamFloat = 0

#----------------------------------------------------------- Variables de camara ---------------------------------

# IP de la camara de bloque viajero
  # IP de Hocol
# camara_Bloque2 = "rtsp://admin:4xUR3_2017@10.15.10.231"
  #IP de Tinamu
camara_Bloque2 = "rtsp://admin:4xUR3_2017@10.10.120.221"


# IP de la camara de personas
  # Ip de Hocol
# camara_Personas = "rtsp://admin:4xUR3_2017@10.15.10.233"
  # Ip de Tinamu
camara_Personas = "rtsp://admin:4xUR3_2017@10.10.120.220"
 

# Inicializar el modelo YOLOv8
MODEL_PATH = "ModelosYolo/best7.pt"
model = YOLO(MODEL_PATH)

valor = 2
max_yc_invertido = 0
# Definir un semáforo para asegurarse de que el modelo se carga solo una vez
model_loading_lock = threading.Lock()
model_loaded = False

# Ruta del video a procesar 
# video_path = "mesaprueba11.webm"
video_path = "Videos/mesaprueba11.webm"


# Capturar el video
video = cv2.VideoCapture(video_path)

# -------------- Variable para almacenar los tiempos de comida
tiempos_comida = ''
tiemposComidaFormateado = {}
isTiempos = False




# Parámetros de conexión a la base de datos
DB_HOST = '10.20.30.33'  # O la dirección IP del servidor de la base de datos
DB_USER = 'analitica'
DB_PASSWORD = 'axure.2024'
DB_DATABASE = 'Hocol'




def almacenar_variables_en_bd(fecha, hora_inicio_videoO, posicion_bloque):
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
                print(f"Fecha: {fecha}, Hora Inicio Video: {hora_inicio_videoO}, Posicion Bloque: {posicion_bloque}")
                cursor.execute(sql_insert, (fecha, hora_inicio_videoO, posicion_bloque))
                conexion.commit()
    
    except pymysql.MySQLError as e:
        print(f"Error al almacenar los datos en la BD: {e.args[1]}")
    except Exception as e:
        print(f"Error inesperado: {e}")


# def velocidad():
#     global yc, Metros, max_yc_invertido, tiempo_prom, velocidad_bloque, min_yc_invertido
#     yc_anterior1_invertido = 0
#     # print("Velocidad del bloque", velocidad_bloque)    
#     while True:
#         if max_yc_invertido > 0:
#             if min_yc_invertido is not None and max_yc_invertido is not None and max_yc_invertido != min_yc_invertido:
#                 velocidad_bloque = ((yc_invertido - yc_anterior1_invertido) * (Metros /(max_yc_invertido - min_yc_invertido)))/ tiempo_prom
#             else:
#                 velocidad_bloque = 0 
#             print("Variables utilizadas en la velocidad", yc_invertido, Metros, max_yc_invertido, tiempo_prom, yc_anterior1_invertido)
#             velocidad_bloque = ((yc_invertido - yc_anterior1_invertido) * (Metros /(max_yc_invertido - min_yc_invertido)))/ tiempo_prom
#             yc_anterior1_invertido = yc_invertido
#             print("Velocidad del bloque:::::: ", velocidad_bloque)
#             time.sleep(tiempo_prom)
#         else:
#             print("Velocidad no obtenida")

def velocidad():
    global yc_invertido, Metros, max_yc_invertido, tiempo_prom, velocidad_bloque, min_yc_invertido

    # Definir valor inicial de yc_anterior1_invertido
    yc_anterior1_invertido = 0

    while True:
        # Comprobación de que max_yc_invertido sea mayor que min_yc_invertido
        if max_yc_invertido > 0 and min_yc_invertido is not None and max_yc_invertido != min_yc_invertido:
            # Calcular la velocidad del bloque solo si tiempo_prom es mayor que cero
            if tiempo_prom > 0:
                velocidad_bloque = ((yc_invertido - yc_anterior1_invertido) * (Metros / (max_yc_invertido - min_yc_invertido))) / tiempo_prom
            else:
                velocidad_bloque = 0
        else:
            velocidad_bloque = 0
        
        # Mostrar las variables utilizadas y la velocidad calculada
        print("Variables utilizadas en la velocidad:", yc_invertido, Metros, max_yc_invertido, tiempo_prom, yc_anterior1_invertido)
        print("Velocidad del bloque:::::: ", velocidad_bloque)

        # Actualizar yc_anterior1_invertido para la siguiente iteración
        yc_anterior1_invertido = yc_invertido

        # Esperar el tiempo definido por tiempo_prom antes de la próxima iteración
        time.sleep(tiempo_prom)

# Definimos la función de detección
def detect_video():
    print("Iniciando detect_video")

    global velocidad_bloque, yc_invertido, max_yc_invertido, min_yc_invertido, yc_anterior, model, yc_invertido, Metros

    print("Iniciando video")

    # Inicializamos tiempos y variables de detección
    yc_anterior = 0
    velocidad_bloque = 0
    altura_imagen = 1058  # Establecer la altura de la imagen para invertir yc
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    max_y_max = 0
    min_y_min = float('inf')  # Inicialmente establecido en infinito
    min_y_max = float('inf')
    yc = 0
    yc_invertido = 0
    yc_anterior = 0
    max_yc_invertido = 0  # Inicialmente no conocido
    min_yc_invertido = 0  # Inicialmente no conocido


    # Configuramos la captura de video
    video = cv2.VideoCapture(video_path)
    fps = video.get(cv2.CAP_PROP_FPS)  # Obtenemos los FPS del video
    # frame_duration = 1 / fps  # Duración de cada fotograma en segundos

    cv2.namedWindow("DETECCION Y SEGMENTACION", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("DETECCION Y SEGMENTACION", 1080, 750)

    # Bucle principal para procesar el video
    while video.isOpened():
        ret, frame_to_process = video.read()
        if not ret:
            break

        start_time = time.time()

        if frame_to_process is not None:
            # Realizamos la predicción
            results = model.predict(frame_to_process, imgsz=640, verbose=False)
            annotated_frame = frame_to_process.copy()

            # Procesamos cada detección en los resultados
            for result in results:
                boxes = result.boxes.xyxy
                scores = result.boxes.conf
                classes = result.boxes.cls

                for box, conf, cls in zip(boxes, scores, classes):
                    x_min, y_min, x_max, y_max = map(int, box)

                    # Identificamos la clase de detección y mostramos la información
                    if cls == 0 and conf >= 0:  # Detección de clase '0' (por ejemplo, bloque)
                        velocidad_bloque = abs(velocidad_bloque)

                        # Formateamos y dibujamos el texto de velocidad en el frame
                        text = f'Bloque: {velocidad_bloque:.2f} m/s'
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                        text_offset_x = x_min + 70
                        text_offset_y = y_min + 50
                        text_box_x2 = text_offset_x + text_width
                        text_box_y2 = text_offset_y + text_height + baseline

                        # Dibujamos el recuadro gris y el texto
                        cv2.rectangle(annotated_frame, (text_offset_x, text_offset_y - text_height - baseline), (text_box_x2, text_offset_y), (87, 85, 85), -1)
                        cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                        cv2.putText(annotated_frame, text, (text_offset_x, text_offset_y - baseline), font, 0.5, (255, 255, 255), 1)

                        # Dibujamos una flecha para indicar movimiento
                        xc, yc = int((x_min + x_max) / 2), y_min
                        if yc_anterior is not None:
                            
                            # Calculamos la posición del rectángulo detrás de la flecha
                            if yc > yc_anterior + 2:
                                # Movimiento hacia abajo - cuerpo de la flecha largo, cabeza pequeña
                                cv2.arrowedLine(
                                    annotated_frame,
                                    (x_max + 10, yc - 50),
                                    (x_max + 10, yc - 10),  # Fin del cuerpo de la flecha más largo hacia arriba
                                    (0, 0, 255),  # Color blanco
                                    2,
                                    tipLength=0.15  # Hacemos la cabeza más pequeña con un valor bajo
                                )

                            elif yc < yc_anterior - 2:
                                # Movimiento hacia arriba - cuerpo de la flecha largo, cabeza pequeña
                                cv2.arrowedLine(
                                    annotated_frame,
                                    (x_max + 10, yc - 10),
                                    (x_max + 10, yc - 50),  # Fin del cuerpo de la flecha más largo hacia arriba
                                    (0, 0, 255),  # Color blanco
                                    2,
                                    tipLength=0.15  # Hacemos la cabeza más pequeña con un valor bajo
                                )

                        if y_min > max_y_min:
                            max_y_min = y_min
                        if y_max > max_y_max:
                            max_y_max = y_max
                        if y_min < min_y_min:
                            min_y_min = y_min
                        if y_max < min_y_max:
                            min_y_max = y_max                        
                        

                                                    # Definir el centro del círculo
                        circle_center = (xc, max_y_min)
                        circle_center2 = (xc, min_y_min)

                        # Definir el radio del círculo (puedes ajustarlo según tus necesidades)
                        circle_radius = 10

                        # Dibujar el círculo en el frame anotado
                        cv2.circle(annotated_frame, circle_center, circle_radius, (255, 255, 0), thickness=2)  
                        # cv2.circle(annotated_frame, circle_center2, circle_radius, (255, 40, 0), thickness=2)  

                        
                        yc_invertido = altura_imagen - yc  # Invirtiendo el valor de yc


                        min_yc_invertido = altura_imagen - max_y_min  
                        max_yc_invertido = altura_imagen - min_y_min 


                        # print("yc:", yc)               # --------> POSICIÓN DEL CENTRO DEL BLOQUE 
                        # print("max_ymin:", max_y_min)  # --------> POSICIÓN MÁS BAJA DEL BLOQUE
                        # print("min_ymin:", min_y_min)  # --------> POSICIÓN MÁS ALTA DEL BLOQUE
# Luego en tu lógica de cálculo
                        if min_yc_invertido is not None and max_yc_invertido is not None and max_yc_invertido != min_yc_invertido:
                            valor_metros = ((yc_invertido - min_yc_invertido) * (Metros / (max_yc_invertido - min_yc_invertido)))
                        else:
                            # Esperar hasta que los valores se actualicen correctamente
                            valor_metros = 0  # o

                        # print("yc_invertido:", yc_invertido)                        
                        # print("max_yc_invertido:", max_yc_invertido) #--------> POSICIÓN MÁS BAJA DEL BLOQUE invertido
                        # print("min_yc_invertido:", min_yc_invertido) #--------> POSICIÓN MÁS ALTA DEL BLOQUE invertido
                        # valor_metros = ((yc_invertido - min_yc_invertido) * (Metros / (max_yc_invertido - min_yc_invertido)))
                        # print("Metros:", valor_metros)

                        # Dibujamos un círculo en el centro del objeto
                        cv2.circle(annotated_frame, (xc, yc), 5, (0, 0, 255), thickness=3)

            # Mostramos el frame anotado redimensionado
            annotated_frame_resized = cv2.resize(annotated_frame, (1080, 750), interpolation=cv2.INTER_LINEAR)
            cv2.imshow("DETECCION Y SEGMENTACION", annotated_frame_resized)


            # # # Ajustamos el tiempo de espera para mantener la tasa de fotogramas original
            # elapsed_time = time.time() - start_time
            # sleep_time = max(0, 0.1 - elapsed_time)
            # time.sleep(sleep_time)  

            

            # Cerramos el programa si se presiona la tecla ESC
            if cv2.waitKey(1) == 27:  # 27 es la tecla ESC
                break


    # Liberamos el video y destruimos las ventanas de OpenCV
    video.release()
    cv2.destroyAllWindows()

# Hora de inicio del video
hora_inicio_video = "22:51:24"
# fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
fecha_actual = "2024-04-10"
# Función para graficar yc_invertido
def ejecutar_grafica(hora_inicio_video):
    global yc_invertido

    # Inicializa el contador para tener un eje X secuencial
    index = count()

    # Valores que se graficarán
    x_vals = []
    y_vals = []

    # Crea la figura y los ejes para la gráfica
    fig, ax = plt.subplots()
    ax.set_title('Gráfica de Posición del Bloque en Tiempo Real')
    ax.set_xlabel('Tiempo')
    ax.set_ylabel('Posición invertida (pixeles)')

    # Convertimos la hora de inicio del video a un objeto datetime
    hora_inicio = datetime.datetime.strptime(hora_inicio_video, "%H:%M:%S")

    # Función que se llama para actualizar la gráfica en cada frame
    def update(frame):
        global yc_invertido

        # Calculamos el tiempo actual basado en el tiempo del video, incrementando cada segundo
        tiempo_actual = hora_inicio + datetime.timedelta(seconds=next(index))

        # Leer yc_invertido de manera segura
        valor_yc = yc_invertido



        # Agregamos los datos a las listas


        yc_metros = (21 / 700) * (valor_yc - 100)


        # almacenar_variables_en_bd(fecha_actual, tiempo_actual.time(), yc_metros)


        # Agregamos los datos a las listas
        x_vals.append(tiempo_actual)
        y_vals.append(valor_yc)

        # Limpiamos los ejes y actualizamos con los nuevos valores
        ax.clear()
        ax.plot(x_vals, y_vals, marker='o', linestyle='-')
        ax.set_title('Gráfica de Posición del Bloque en Tiempo Real')
        ax.set_xlabel('Tiempo')
        ax.set_ylabel('Posición invertida (pixeles)')
        ax.grid(True)

        # Ajustamos el formato del eje x para mostrar la hora
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    # Crea la animación usando la función update
    ani = animation.FuncAnimation(fig, update, interval=1000)  # Intervalo de 1000 ms (1 segundo)

    # Muestra la gráfica
    plt.show()


# Función para convertir yc_invertido a metros

# Crear hilos para cada función
thread1 = threading.Thread(target=detect_video)
# thread2 = threading.Thread(target=ejecutar_grafica, args=(hora_inicio_video,))
hilo_velocidad = threading.Thread(target=velocidad)

# Iniciar ambos hilos
thread1.start()
# thread2.start()
hilo_velocidad.start()

# Esperar a que ambos hilos terminen (opcional)
thread1.join()
# thread2.join()

print("Ambas funciones han terminado.")
