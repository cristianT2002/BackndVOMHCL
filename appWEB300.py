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
import logging
import torch
import signal
import sys
import math
import webbrowser
import threading
import time
import webbrowser




# CORS(app)

boxes, classes, scores = [], [], []
lock = threading.Lock()


stop_flag = threading.Event()
stop_flag2 = threading.Event()

# Parámetros de conexión a la base de datos
DB_HOST = '10.20.30.33'  # O la dirección IP del servidor de la base de datos
DB_USER = 'analitica'
DB_PASSWORD = '4xUR3_2017'
DB_DATABASE = 'Hocol'

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
rect_height1 = 0
tiempo_prom = 1

conversionMP = 0
Metros = 40 
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
fecha_actual = 0
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
  # IP de Tinamu
camara_Bloque2 = "rtsp://admin:4xUR3_2017@10.10.120.221"


# IP de la camara de personas
  # Ip de Hocol
# camara_Personas = "rtsp://admin:4xUR3_2017@10.15.10.233"
  # Ip de Tinamu
camara_Personas = "rtsp://admin:4xUR3_2017@10.10.120.220"


# Inicializar el modelo YOLOv8
MODEL_PATH = "best7.pt"
model = YOLO(MODEL_PATH)

valor = 2

# Definir un semáforo para asegurarse de que el modelo se carga solo una vez
model_loading_lock = threading.Lock()
model_loaded = False

# Ruta del video a procesar
video_path = "mesaprueba11.webm"

# Capturar el video
video = cv2.VideoCapture(video_path)


def npt_alerta():
    global alerta, ipcam2, url
    while True:
        url = 'http://consultas.axuretechnologies.com:8081/axure/niveles-total/' + ipcam2
 
        # Realizar una petición GET a la URL
        respuesta = requests.get(url)
       
        html_content = respuesta.text
 
        # Reemplazar etiquetas <BR> y <LF> por espacios y saltos de línea
        html_content = html_content.replace('<BR>', ' ').replace('<LF>', '\n')
 
        # Analizar el contenido HTML modificado con BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
 
        # Obtener todos los strings de texto, ahora sin etiquetas <BR> y <LF>
        texto_deseado = ' '.join(soup.stripped_strings)
 
        array_variables  =  texto_deseado.split()

        alerta = array_variables[3]
        
        # print("Alerta: ", alerta)
  
        time.sleep(1)



# -------------- Variable para almacenar los tiempos de comida
tiempos_comida = ''
tiemposComidaFormateado = {}
isTiempos = False

@app.route('/')
def index():
    return render_template('index.html')

def obtener_bandera_full_services():
    global banderaFull
    while True:
        try:
            # Establecer conexión a la base de datos
            conexion = pymysql.connect(host=DB_HOST,
                                       user=DB_USER,
                                       password=DB_PASSWORD,
                                       database=DB_DATABASE)
            try:
                with conexion.cursor() as cursor:
                    # Consulta SQL para obtener la bandera del pozo FULL_SERVICES_167_HCL
                    sql = "SELECT BanderaPozo FROM IpServidores WHERE NombrePozzo = %s ORDER BY ID DESC LIMIT 1"
                    cursor.execute(sql, ('TOQUI_HCL',))
                    resultado = cursor.fetchone()
                    if resultado:
                        banderaFull = resultado[0]
                        print(f"Bandera del pozo TOQUI_HCL actualizada: {banderaFull}")
                    else:
                        print("No se encontró ningún registro para el pozo TOQUI_HCL")
            finally:
                conexion.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {e}")
        # Espera 10 segundos antes de volver a ejecutar la consulta
        time.sleep(5)

def actualizar_variables_desde_bd2():
    global alertaSim, ProbabilidadSim, floatProbabilidad
    while True:
        try:
            logging.getLogger().setLevel(logging.ERROR)

            # Establecer conexión a la base de datos
            conexion = pymysql.connect(host=DB_HOST,
                                       user=DB_USER,
                                       password=DB_PASSWORD,
                                       database=DB_DATABASE)
            try:
                with conexion.cursor() as cursor:
                    # Consulta SQL para obtener el último valor de 'bandera' e 'ipcam'
                    sql = "SELECT simTSW, simProbabilidad FROM TPCsimulacion ORDER BY ID DESC LIMIT 1"
                    cursor.execute(sql)
                    resultado2 = cursor.fetchone()
                    if resultado2:
                        global alertaSim, ProbabilidadSim, floatProbabilidad
                        alertaSim, ProbabilidadSim = resultado2
                        floatProbabilidad = float(ProbabilidadSim)
                        
            finally:
                conexion.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {e}")
        time.sleep(10)  # Esperar un segundo antes de la próxima consulta

def actualizar_variables_desde_bd():
    global bandera, ipcam, ipcam2, camera_url_porteriaPX45, probabilidad, probabilidadScore, alerta, ipcamFloat, banderin_actual, tiempos_comida, tiemposComidaFormateado
    global isTiempos, mesa, contrapozo, nombrepozo, banderaCon
    while True:
        try:
            # Establecer conexión a la base de datos
            conexion = pymysql.connect(host=DB_HOST,
                                       user=DB_USER,
                                       password=DB_PASSWORD,
                                       database=DB_DATABASE)
            try:
                with conexion.cursor() as cursor:
                    # Consulta SQL para obtener el último valor de 'bandera' e 'ipcam'
                    sql = "SELECT bandera, Control_Desconexion, ipcam, ipcam2, probabilidad, Banderin, TimeValores, Mesa, Contrapozo, NombrePozo FROM TPCvariables ORDER BY ID DESC LIMIT 1"
                    cursor.execute(sql)
                    resultado = cursor.fetchone()
                    if resultado:
                        global bandera, ipcam, ipcam2, probabilidad, banderaCon
                        bandera, banderaCon, ipcam, ipcam2, probabilidad, Banderin, time_comidas, mesa, contrapozo, nombrepozo = resultado
                        ipcamFloat = float(probabilidad)                        
                        banderin_actual = Banderin
                        
                        tiempos_comida = time_comidas
                        
                        times = tiempos_comida.split("; ")
                        # Crear los tres arrays
                        array1 = times[:2]
                        array2 = times[2:4]
                        array3 = times[4:]

                        # Colocamos los valores de las comidas en un diccionario
                        tiemposComidaFormateado = {
                            'desayuno':array1,
                            'almuerzo':array2,
                            'comida':array3
                        }

                        
                        # print("Comidas: ", tiemposComidaFormateado)
                        isTiempos = True

                        if tiempos_comida == 'Tiempo_24':
                            isTiempos = False
            finally:
                conexion.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {e}")
        time.sleep(1)  # Esperar un segundo antes de la próxima consulta




#-------------------------- Almacenar NPTS en Base de datos -------------------------
def almacenar_variables_en_bd(fecha, hora_inicio, tiempo_conexion, tiempo_desconexion=0, npt_tormenta=0, alimentacion=0, paradas_cortas=0, direccion_ip='', bandera='', nombrepozo=''):
    try:
        # Establecer conexión a la base de datos
        with pymysql.connect(host=DB_HOST,
                             user=DB_USER,
                             password=DB_PASSWORD,
                             database=DB_DATABASE) as conexion:

            with conexion.cursor() as cursor:
                # Ajustar la consulta SQL con los nombres de columnas correctos
                sql_insert = """
                INSERT INTO TPCgeneral (Fecha, Hora_Inicio, Tiempo_conexion, Tiempo_desconexion, NPT_tormenta, Alimentacion, Paradas_cortas, Otros_NPT, bandera, nombrePozoGeneral)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                # Ejecutar la consulta con las variables proporcionadas
                cursor.execute(sql_insert, (fecha, hora_inicio, tiempo_conexion, tiempo_desconexion, npt_tormenta, alimentacion, paradas_cortas, direccion_ip, bandera, nombrepozo))
                conexion.commit()
    
    except pymysql.MySQLError as e:
        print(f"Error al almacenar los datos en la BD: {e.args[1]}")
    except Exception as e:
        print(f"Error inesperado: {e}")

large_image_width = 1920.0  # Ejemplo de valor, ajusta según tu caso
small_image_width = 1080.0  # Ejemplo de valor, ajusta según tu caso
large_image_height = 1080.0  # Ejemplo de valor, ajusta según tu caso
small_image_height = 720.0  # Ejemplo de valor, ajusta según tu caso


def actualizar_coordenadas_desde_bd():
    global coordenadas_redimensionadas, xFloat1, yFloat1, widthFloat1, heightFloat1, xFloat2, yFloat2, widthFloat2, heightFloat2
    while True:
        try:
            conexion = pymysql.connect(host=DB_HOST,
                                       user=DB_USER,
                                       password=DB_PASSWORD,
                                       database=DB_DATABASE)
            try:
                with conexion.cursor() as cursor:
                    # Consulta que obtiene los últimos registros para cada cámara
                    sql = """
                    SELECT x, y, width, height, camera
                    FROM TPCcoordenadas AS t1
                    WHERE t1.Id = (
                        SELECT MAX(t2.Id)
                        FROM TPCcoordenadas AS t2
                        WHERE t2.camera = t1.camera
                    )
                    """
                    cursor.execute(sql)
                    resultados = cursor.fetchall()

                    for resultado in resultados:
                        if resultado:
                            x, y, width, height, camera = resultado
                            xFloat = float(x)
                            yFloat = float(y)
                            widthFloat = float(width)
                            heightFloat = float(height)

                            if xFloat is None or yFloat is None or widthFloat is None or heightFloat is None:
                                print("Valores nulos obtenidos de la base de datos.")
                                continue

                            if camera == 'camera1':
                                xFloat1 = xFloat
                                yFloat1 = yFloat
                                widthFloat1 = widthFloat
                                heightFloat1 = heightFloat
                            elif camera == 'camera2':
                                xFloat2 = xFloat
                                yFloat2 = yFloat
                                widthFloat2 = widthFloat
                                heightFloat2 = heightFloat

                            coordenadas_redimensionadas[camera] = {
                                'x': xFloat,
                                'y': yFloat,
                                'width': widthFloat,
                                'height': heightFloat
                            }

            finally:
                conexion.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {e}")
        time.sleep(1)


frame_buffer2 = []
frame_buffer22 = []
buffer_lock = threading.Lock()
buffer_lock2 = threading.Lock()

process_interval = 1 / 20.0  # Procesar a una tasa de 30 FPS (ajusta según tus necesidades)



def streaming_camara_Bloque():
    global frame_buffer2, buffer_lock, mesa, banderaFull, nombrepozo
    global camara_Bloque2, contrapozo
    
    cap_camera = cv2.VideoCapture(mesa)

     

    if not cap_camera.isOpened():
        print("Error al abrir la cámara bloque")
        return

    while True:
        if banderaFull == 'start_TOQUI_HCL':
            while True:
                if banderaFull == 'stop_TOQUI_HCL':
                    break
                ret, frame = cap_camera.read()
                if not ret:
                    print("Error al leer la imagen de la cámara")
                    cap_camera.release()  # Cierra la conexión actual
                    cap_camera = cv2.VideoCapture(mesa)
                    print("Intentando reconectar")
                    continue

                # Redimensiona el frame si es necesario
                frame = cv2.resize(frame, (1898, 1058))

                with buffer_lock:
                    frame_buffer2.append(frame)
                    if len(frame_buffer2) > 30:  # Limitar el tamaño del buffer para evitar consumo excesivo de memoria
                        # print("Almacenando buffer")
                        frame_buffer2.pop(0)
        else:
            cap_camera.release()  # Asegúrate de liberar la cámara si no está en uso
            break


# def streaming_camara_Personas():
#     global frame_buffer22, buffer_lock2, mesa, banderaFull, nombrepozo
#     global camara_Personas
#     cap_camera2 = cv2.VideoCapture(camara_Personas)

#     if not cap_camera2.isOpened():
#         print("Error al abrir la cámara")
#         return

#     while True:
#         if banderaFull == 'start_TOQUI_HCL':
#             while True:
#                 if banderaFull == 'stop_TOQUI_HCL':
#                     break
#                 ret2, frame22 = cap_camera2.read()
#                 print("------------Ret de personas: ",ret2)
#                 if not ret2:
#                     print("Error al leer la imagen de la cámara")
#                     cap_camera2.release()  # Cierra la conexión actual
#                     cap_camera2 = cv2.VideoCapture(camara_Personas)
#                     print("Intentando reconectar")
#                     continue

#                 # Redimensiona el frame si es necesario
#                 frame22 = cv2.resize(frame22, (1898, 1058))

#                 with buffer_lock:
#                     frame_buffer2.append(frame22)
#                     if len(frame_buffer22) > 30:  # Limitar el tamaño del buffer para evitar consumo excesivo de memoria
#                         # print("Almacenando buffer")
#                         frame_buffer22.pop(0)
#         else:
#             cap_camera2.release()  # Asegúrate de liberar la cámara si no está en uso
#             break

def streaming_camara_Personas():
    global frame_buffer22, buffer_lock2, mesa, contrapozo, nombrepozo, banderaFull
    global camara_Personas, camara_Bloque2
    cap_camera2 = cv2.VideoCapture(contrapozo)

    if not cap_camera2.isOpened():
        print("Error al abrir la cámara personas")
        return
    
    while True:
        if banderaFull == "start_TOQUI_HCL": 
            while True:
                if banderaFull == 'stop_TOQUI_HCL':
                    break
                ret, frame22 = cap_camera2.read()
                if not ret:
                    print("Error al leer la imagen de la cámara")
                    cap_camera2.release()  # Cierra la conexión actual
                    # cap_camera2 = cv2.VideoCapture(camara_Bloque2)
                    cap_camera2 = cv2.VideoCapture(contrapozo)
                    print("Intentando reconectar")
                    continue

                # Redimensiona el frame si es necesario
                frame22 = cv2.resize(frame22, (1898, 1058))
                # print("------------ret de personas antes del with: ",ret)
                with buffer_lock2:
                    # print("------------ret de personas despues del with: ",ret)
                    frame_buffer22.append(frame22)  # Agrega el nuevo frame al buffer
                    if len(frame_buffer22) >= 30:  # Limitar el tamaño del buffer
                        frame_buffer22.pop(0)  # Elimina el primer elemento si hay más de 30

                    # Verificar si el buffer está vacío
                    if len(frame_buffer22) == 0:  # Verifica la longitud en lugar de compararlo con []
                        # print("---------Error el buffer es nulo--------------")
                        cap_camera2.release()  # Cierra la conexión actual
                        # cap_camera2 = cv2.VideoCapture(camara_Bloque2)
                        cap_camera2 = cv2.VideoCapture(contrapozo)
                        print("Intentando reconectar")
                        continue
                    
                    # print("Buffer personas: ", frame_buffer22)  # Imprime el buffer actual

        else:
            cap_camera2.release()  # Asegúrate de liberar la cámara si no está en uso
            print("Cierre de programa")
            break


def detect_camara_yolo():
    global boxes, classes, y_min, scores, bandera, model, camera_url_porteriaPX45, ipcam, probabilidad, contador_cruces, estado_arriba, tiempo_total_str, nueva_conexion, contador, tiempo_formateado, contador_crucesP, estado_abajo, mitad, abajo_linea_inf, detectado_bloque_viajero, detectado_persona, fecha_actual, hora_actual, tiempo_final_persona, contador_detecciones_persona, fecha_inicio_detecciones_persona, tiempo_total_detecciones_persona, tiempo_inicial_persona, line_ymax1
    global hora_detecciones_persona, detectado_persona_actual, hora_primera_deteccion, hora_sin_detecciones, detectado_persona_actual, ipcamFloat, hora_primera_no_deteccion, detecciones_previas  # Esta variable indicará si hubo detecciones en el frame anterior
    global persona_detectada_actual,  hora_primera_deteccion_segundos, hora_sin_detecciones_segundos, ahora, ahora2, ipcam2, tiempo_formateado2
    global frame_buffer2, buffer_lock, process_interval, nombrepozo
    global coordenadas_redimensionadas, xFloat1, yFloat1, widthFloat1, heightFloat1, isHilos, banderaFull   # Añadir coordenadas redimensionadas
    global cross_blue_line, cross_green_line, cross_red_line, contador_cruces_velocidad, Metros, yc, rect_height1, velocidad_bloque


    global ishilo_video_bloque
    tiempo_inicial = datetime.datetime.now()
    tiempo_inicialP = datetime.datetime.now()
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    max_y_max = 0
    min_y_min = float('inf')  # Inicialmente establecido en infinito
    min_y_max = float('inf')
    yc = 0
    yc_anterior = 0

    # Dimensiones de las imágenes
    width2 = 294.1226453481414
    height2 = 145.45830319313836
    width1 = 1898
    height1 = 1058

    print("")
    print("Modelo bloque cargado")

    print("Iniciando hilo 1", isHilos)


    while isHilos:
        if banderaFull == "start_TOQUI_HCL": 
            while True:
                if banderaFull == 'stop_TOQUI_HCL':
                    print("rompiendo acá hilo 1")
                    break
                start_time = time.time()
                frame_to_process = None
                with buffer_lock:
                    if frame_buffer2:
                        frame_to_process = frame_buffer2.pop(0)

                if frame_to_process is not None:
                    print("Procesando frame de camara bloque viajero")
                    results = model.predict(frame_to_process, imgsz=640, verbose=False)
                    # annotated_frame = frame_to_process.copy()
                    annotated_frame1 = frame_to_process.copy()

                    x2 = xFloat1  # Ejemplo de coordenada x en imagen2
                    y2 = yFloat1   # Ejemplo de coordenada y en imagen2
                    
                    rect_width2 = widthFloat1
                    rect_height2 = heightFloat1

                    # print("las coordenadas generadas son:", x2, y2)


                    # Escalar coordenadas a imagen1
                    x1 = (x2 / width2) * width1
                    y1 = (y2 / height2) * height1

                    # Escalar dimensiones del rectángulo a imagen1
                    rect_width1 = (rect_width2 / width2) * width1
                    rect_height1 = (rect_height2 / height2) * height1


                    start_point = (int(x1), int(y1))
                    end_point = (int(x1 + rect_width1), int(y1 + rect_height1))

                    # Color y grosor del rectángulo
                    color = (0, 255, 0)  # Rojo en BGR
                    thickness = 2


                    rect_x_min_bloque = x1
                    rect_y_min_bloque = y1
                    rect_x_max_bloque = x1 + rect_width1
                    rect_y_max_bloque = y1 + rect_height1

                    #annotated_frame = results[0].plot()


                    # ---------------------- Dibujando el area de interés -------------------
                    cv2.rectangle(annotated_frame1, start_point, end_point, color, thickness)

                    detectado_bloque_viajero = False
                    detectado_persona = False

                    for result in results:
                        boxes = result.boxes.xyxy
                        scores = result.boxes.conf
                        classes = result.boxes.cls

                        for box, conf, cls in zip(boxes, scores, classes):
                            x_min, y_min, x_max, y_max = map(int, box)

                            #---------- Probabilidades individuales de cada clase -----------

                            if cls == 0 and conf >= 0:
                                if x_min >= rect_x_min_bloque and y_min >= rect_y_min_bloque and x_max <= rect_x_max_bloque and y_max <= rect_y_max_bloque:
                                    detectado_bloque_viajero = True
                                    print("Se está detectando el bloque viajero")

                                    if velocidad_bloque < 0:
                                        velocidad_bloque = velocidad_bloque * -1

                                    if velocidad_bloque  is not None:
                                        text = f'Vel: {velocidad_bloque:.2f} m/s'
                                    else:
                                        text = 'Vel: N/A'    
                                    
                                    font = cv2.FONT_HERSHEY_SIMPLEX

                                    (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                                    text_offset_x = x_min + 70
                                    # Calculamos la posición del recuadro
                                    text_offset_y = y_min + 50  # Ajusta esta coordenada para bajar tanto el texto como el recuadro
                                    text_box_x2 = text_offset_x + text_width
                                    text_box_y2 = text_offset_y + text_height + baseline  # Suma la altura del texto y la línea base

                                    # Dibujamos el recuadro gris detrás del texto
                                    cv2.rectangle(annotated_frame1, (text_offset_x, text_offset_y - text_height - baseline), (text_box_x2, text_offset_y), (87, 85, 85), -1)
                                    cv2.putText(annotated_frame1, text, (text_offset_x, text_offset_y - baseline), font, 0.5, (255, 255, 255), 1)
                                    cv2.rectangle(annotated_frame1, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                                    if yc_anterior is not None:
                                
                                        if yc > yc_anterior + 2:
                                            # Movimiento hacia abajo - cuerpo de la flecha largo, cabeza pequeña, y ubicada más arriba en el eje Y
                                            cv2.arrowedLine(
                                                annotated_frame1,
                                                (x_max + 10, yc - 50),
                                                (x_max + 10, yc - 10),  # Fin del cuerpo de la flecha más largo hacia arriba
                                                (0, 0, 255),
                                                2,
                                                tipLength=0.15  # Hacemos la cabeza más pequeña con un valor bajo
                                            )

                                        elif yc < yc_anterior - 2:
                                            # Movimiento hacia arriba - cuerpo de la flecha largo, cabeza pequeña
                                            cv2.arrowedLine(
                                                annotated_frame1,
                                                (x_max + 10, yc - 10),
                                                (x_max + 10, yc - 50),  # Fin del cuerpo de la flecha más largo hacia arriba
                                                (0, 0, 255),
                                                2,
                                                tipLength=0.15  # Hacemos la cabeza más pequeña con un valor bajo
                                            )

                                    yc_anterior = yc
                                    xc, yc = int((x_min + x_max) / 2), y_max

                                    cv2.circle(annotated_frame1, (xc, yc), 5, (0, 0, 255), thickness= 3)

                                    if y_min > max_y_min:
                                        max_y_min = y_min
                                    if y_max > max_y_max:
                                        max_y_max = y_max
                                    if y_min < min_y_min:
                                        min_y_min = y_min
                                    if y_max < min_y_max:
                                        min_y_max = y_max

                                    line_ymin1 = max_y_min - 100
                                    line_ymax1 = max_y_min - 100
                                    line_start1 = (1600, line_ymin1)  # Coordenadas (x, y) del punto inicial
                                    line_end1 = (1100, line_ymax1)   # Coordenadas (x, y) del punto final 
                                    cv2.line(annotated_frame1, line_start1, line_end1, (255, 255, 0), thickness=2)  # Asegúrate de usar un color visible, como verde aquí

                                    line_ymin2 = min_y_min + 120
                                    line_ymax2 = min_y_min + 120
                                    line_start2 = (1600, line_ymin2)  # Coordenadas (x, y) del punto inicial
                                    line_end2 = (1100, line_ymax2)   # Coordenadas (x, y) del punto final
                                    cv2.line(annotated_frame1, line_start2, line_end2, (201, 255, 255), thickness=2)
                                    # cv2.rectangle(annotated_frame, (x_min - 100, max_y_min + 100), (x_max + 100, min_y_min - 100), (0, 255, 255), 2)

                                    if y_max < line_ymin1: #ENCIMA DE LA LINEA DE ABAJO
                                        print("Cruce en encima de la linea de abajo")
                                        estado_arriba = True

                                    if y_min < line_ymax2:  #ENCIMA DE LA LINEA DE ARRIBA
                                        print("Cruce en encima de la linea de arriba")
                                        estado_abajo = True

                                    if y_min < line_ymax2 and y_max > line_ymin1: #POSICIÓN INICIAL
                                        pos_inicial = True

                                    if y_min > line_ymax2 and y_max < line_ymin1: #MITAD DE AMBAS LINEAS
                                        mitad = True

                                    if y_max > line_ymin1:
                                        abajo_linea_inf = True

                                    if y_min > line_ymax1 and estado_arriba and estado_abajo:
                                        contador_cruces += 1
                                        fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
                                        hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
                                        print(f"El rectángulo ha cruzado completamente la línea.")
                                        tiempo_actual = datetime.datetime.now()
                                        duracion = tiempo_actual - tiempo_inicial
                                        duracion_en_minutos = duracion.total_seconds() / 60  # Convertir la duración a minutos
                                        tiempo_formateado2 = float("{:.2f}".format(duracion_en_minutos))  # Formato como minutos con dos decimales
                                        tiempo_formateado = str(duracion).split('.')[0]  # Formato como hh:mm:ss
                                        tiempos_por_cruce[contador_cruces] = tiempo_formateado2
                                        print(f"Cruce {contador_cruces}, Fecha: {fecha_actual}, Hora de inicio: {hora_actual}, Tiempo desde el último cruce: {tiempo_formateado}")
                                        tiempo_inicial = tiempo_actual  # Reinicia el temporizador
                                        estado_arriba = False
                                        estado_abajo = False

                            elif cls == 1 and conf >= 0:
                                # if x_min >= rect_x_min and y_min >= rect_y_min and x_max <= rect_x_max and y_max <= rect_y_max:
                                detectado_persona = True
                                conf2 = conf * 100
                                if not persona_detectada_actual:
                                    hora_primera_deteccion = datetime.datetime.now().strftime("%H:%M:%S")
                                    ahora = datetime.datetime.now()
                                    hora_primera_deteccion_segundos = (ahora.hour * 3600 + ahora.minute * 60 + ahora.second)
                                    persona_detectada_actual = True

                                text = f'Persona: {conf2:.2f} %'

                                font = cv2.FONT_HERSHEY_SIMPLEX
                                (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                                text_offset_x = x_min
                                text_offset_y = y_min - 25  # Ajusta esta coordenada según necesites
                                text_box_x2 = text_offset_x + text_width
                                text_box_y2 = text_offset_y + text_height + baseline  # Suma la altura del texto y la línea base
                                cv2.rectangle(annotated_frame1, (text_offset_x, text_offset_y), (text_box_x2, text_box_y2), (87, 85, 85), -1)
                                cv2.putText(annotated_frame1, text, (text_offset_x, y_min - 10), font, 0.5, (255, 255, 255), 1)
                                cv2.rectangle(annotated_frame1, (x_min, y_min), (x_max, y_max), (203, 50, 52), 2)

                    if not detectado_persona and persona_detectada_actual:
                        hora_sin_detecciones = datetime.datetime.now().strftime("%H:%M:%S")
                        ahora2 = datetime.datetime.now()
                        hora_sin_detecciones_segundos = (ahora2.hour * 3600 + ahora2.minute * 60 + ahora2.second)
                        persona_detectada_actual = False

                    ret, buffer = cv2.imencode('.jpg', annotated_frame1)
                    frame_bytes = buffer.tobytes()

                    print("Estado de la funcion: ", ishilo_video_bloque)
                    # if ishilo_video_bloque == 'video':
                    #     # Usar 'yield' para devolver el frame como parte de una respuesta HTTP
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                elapsed_time = time.time() - start_time
                sleep_time = process_interval - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)

def detect_camara_yolo2():    
    global boxes, classes, y_min, scores, bandera, model, camera_url_porteriaPX45, ipcam, probabilidad, contador_cruces, estado_arriba, tiempo_total_str, nueva_conexion, contador, tiempo_formateado, contador_crucesP, estado_abajo, mitad, abajo_linea_inf, detectado_bloque_viajero, detectado_persona, fecha_actual, hora_actual, tiempo_final_persona, contador_detecciones_persona, fecha_inicio_detecciones_persona, tiempo_total_detecciones_persona, tiempo_inicial_persona, line_ymax1
    global hora_detecciones_persona, detectado_persona_actual, hora_primera_deteccion, hora_sin_detecciones, detectado_persona_actual, ipcamFloat, hora_primera_no_deteccion, detecciones_previas  # Esta variable indicará si hubo detecciones en el frame anterior
    global persona_detectada_actual,  hora_primera_deteccion_segundos, hora_sin_detecciones_segundos, ahora, ahora2, ipcam2, tiempo_formateado2
    global frame_buffer22, buffer_lock2, process_interval, nombrepozo
    global coordenadas_redimensionadas, xFloat2, yFloat2, widthFloat2, heightFloat2, isHilos2, banderaFull   # Añadir coordenadas redimensionadas

    width1 = 1898
    height1 = 1058

    # Dimensiones de las imágenes
    width2 = 294.1226453481414
    height2 = 145.45830319313836

    print("")
    print("Modelo personas cargado")

    print("Iniciando hilo 2", isHilos2)


    while isHilos2:
        if banderaFull == "start_TOQUI_HCL": 
            print("Iniciando personas 2")
            while True:
                if banderaFull == 'stop_TOQUI_HCL':
                    break
                start_time2 = time.time()
                frame_to_process2 = None
                with buffer_lock2:
                    if frame_buffer22:
                        frame_to_process2 = frame_buffer22.pop(0)

                print("frame_to_process2: ", frame_buffer22)
                if frame_to_process2 is not None:
                    print("Procesando frame de camara Personas")
                    results = model.predict(frame_to_process2, imgsz=640, verbose=False)
                    annotated_frame = frame_to_process2.copy()

                        # Coordenadas originales y dimensiones del rectángulo en imagen2
                    x2 = xFloat2  # Ejemplo de coordenada x en imagen2
                    y2 = yFloat2   # Ejemplo de coordenada y en imagen2
                    
                    rect_width2 = widthFloat2
                    rect_height2 = heightFloat2

                    # Escalar coordenadas a imagen1
                    x1 = (x2 / width2) * width1
                    y1 = (y2 / height2) * height1

                    # Escalar dimensiones del rectángulo a imagen1
                    rect_width1 = (rect_width2 / width2) * width1
                    rect_height1 = (rect_height2 / height2) * height1


                    start_point = (int(x1), int(y1))
                    end_point = (int(x1 + rect_width1), int(y1 + rect_height1))

                    # Color y grosor del rectángulo
                    color = (255, 0, 0)  # Rojo en BGR
                    thickness = 2


                    rect_x_min = x1
                    rect_y_min = y1
                    rect_x_max = x1 + rect_width1
                    rect_y_max = y1 + rect_height1

                    #annotated_frame = results[0].plot()

                    # ---------------------- Dibujando el area de interés -------------------
                    cv2.rectangle(annotated_frame, start_point, end_point, color, thickness)

                    detectado_bloque_viajero = False
                    detectado_persona = False

                    for result in results:
                        boxes = result.boxes.xyxy
                        scores = result.boxes.conf
                        classes = result.boxes.cls

                        for box, conf, cls in zip(boxes, scores, classes):
                            x_min, y_min, x_max, y_max = map(int, box)
                            if cls == 0 and conf >= 1:
                                #if x_min >= rect_x_min_bloque and y_min >= rect_y_min_bloque and x_max <= rect_x_max_bloque and y_max <= rect_y_max_bloque:
                                detectado_bloque_viajero = True
                                text = f'Bloque viajero: {conf:.2f}'
                                font = cv2.FONT_HERSHEY_SIMPLEX
                                (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                                text_offset_x = x_min
                                text_offset_y = y_min - 25  # Ajusta esta coordenada según necesites
                                text_box_x2 = text_offset_x + text_width
                                text_box_y2 = text_offset_y + text_height + baseline  # Suma la altura del texto y la línea base
                                
                                cv2.rectangle(annotated_frame, (text_offset_x, text_offset_y), (text_box_x2, text_box_y2), (87, 85, 85), -1)
                                cv2.putText(annotated_frame, text, (text_offset_x, y_min - 10), font, 0.5, (255, 255, 255), 1)
                                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                            elif cls == 1 and conf >= 0:
                                if x_min >= rect_x_min and y_min >= rect_y_min and x_max <= rect_x_max and y_max <= rect_y_max:
                                    detectado_persona = True
                                    print("Persona detectada")
                                    conf2 = conf * 100


                                    if not persona_detectada_actual:
                                        hora_primera_deteccion = datetime.datetime.now().strftime("%H:%M:%S")
                                        ahora = datetime.datetime.now()
                                        hora_primera_deteccion_segundos = (ahora.hour * 3600 + ahora.minute * 60 + ahora.second)
                                        persona_detectada_actual = True
                                        print(f"Persona detectada. Hora de primera detección: {hora_primera_deteccion}")

                                    text = f'Persona: {conf2:.0f} %'
                                    font = cv2.FONT_HERSHEY_SIMPLEX
                                    (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                                    text_offset_x = x_min
                                    text_offset_y = y_min - 25  # Ajusta esta coordenada según necesites
                                    text_box_x2 = text_offset_x + text_width
                                    text_box_y2 = text_offset_y + text_height + baseline  # Suma la altura del texto y la línea base
                                    cv2.rectangle(annotated_frame, (text_offset_x, text_offset_y), (text_box_x2, text_box_y2), (87, 85, 85), -1)
                                    cv2.putText(annotated_frame, text, (text_offset_x, y_min - 10), font, 0.5, (255, 255, 255), 1)
                                    cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (203, 50, 52), 2)

                    if not detectado_persona and persona_detectada_actual:
                        hora_sin_detecciones = datetime.datetime.now().strftime("%H:%M:%S")
                        ahora2 = datetime.datetime.now()
                        hora_sin_detecciones_segundos = (ahora2.hour * 3600 + ahora2.minute * 60 + ahora2.second)
                        persona_detectada_actual = False
                        print(f"Persona no detectada. Hora de sin detección: {hora_sin_detecciones}")

                    ret, buffer = cv2.imencode('.jpg', annotated_frame)
                    frame_bytes = buffer.tobytes()

                    # # Usar 'yield' para devolver el frame como parte de una respuesta HTTP
                    # if ishilo_video_personas == 'video_personas':

                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

                elapsed_time = time.time() - start_time2
                sleep_time = process_interval - elapsed_time
                if sleep_time > 0:
                    time.sleep(sleep_time)


def velocidad():
    global yc, Metros, rect_height1, tiempo_prom, velocidad_bloque
    yc_anterior1 = 0
    print("Velocidad del bloque", velocidad_bloque)
    
    while True:
        if rect_height1 > 0:
                velocidad_bloque = ((yc - yc_anterior1) * (Metros / rect_height1))/ tiempo_prom
                yc_anterior1 = yc
                print("Velocidad del bloque", velocidad_bloque)
                time.sleep(tiempo_prom)
        else:
            print("Velocidad del bloque")

def detect_video():
    print("Iniciando detect_video")
    global boxes, classes, y_min, scores, bandera, model, probabilidad, contador_cruces, estado_arriba, tiempo_total_str, nueva_conexion, contador, tiempo_formateado
    global contador_crucesP, estado_abajo, mitad, abajo_linea_inf, detectado_bloque_viajero, detectado_persona, fecha_actual, hora_actual, tiempo_final_persona
    global contador_detecciones_persona, fecha_inicio_detecciones_persona, tiempo_total_detecciones_persona, tiempo_inicial_persona, line_ymax1, hora_detecciones_persona
    global detectado_persona_actual, hora_primera_deteccion, hora_sin_detecciones, ipcamFloat, hora_primera_no_deteccion, detecciones_previas
    global persona_detectada_actual, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos, ahora, ahora2, tiempo_formateado2
    global coordenadas_redimensionadas, xFloat1, yFloat1, widthFloat1, heightFloat1   # Añadir coordenadas redimensionadas
    global alerta, ProbabilidadSim, floatProbabilidad
    global cross_blue_line, cross_green_line, cross_red_line, contador_cruces_velocidad, Metros, yc, rect_height1, velocidad_bloque


    print("Iniciando video")

    tiempo_inicial = datetime.datetime.now()
    tiempo_inicialP = datetime.datetime.now()
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    max_y_max = 0
    min_y_min = float('inf')  # Inicialmente establecido en infinito
    min_y_max = float('inf')
    yc = 0
    yc_anterior = 0


    video = cv2.VideoCapture(video_path)

    # Dimensiones de las imágenes
    width2 = 294.1226453481414
    height2 = 145.45830319313836
    width1 = 1898
    height1 = 1058

    while video.isOpened():
        ret, frame_to_process = video.read()
        if not ret:
            break

        start_time = time.time()

        if frame_to_process is not None:
            # print("Procesando frame")
            results = model.predict(frame_to_process, imgsz=640, verbose=False)
            annotated_frame = frame_to_process.copy()

            x2 = xFloat1  # Ejemplo de coordenada x en imagen2
            y2 = yFloat1   # Ejemplo de coordenada y en imagen2
            
            rect_width2 = widthFloat1
            rect_height2 = heightFloat1

            # print("las coordenadas generadas son:", x2, y2)

            # Escalar coordenadas a imagen1
            x1 = (x2 / width2) * width1
            y1 = (y2 / height2) * height1

            # Escalar dimensiones del rectángulo a imagen1
            rect_width1 = (rect_width2 / width2) * width1
            rect_height1 = (rect_height2 / height2) * height1


            start_point = (int(x1), int(y1))
            end_point = (int(x1 + rect_width1), int(y1 + rect_height1))

            # Color y grosor del rectángulo
            color = (0, 255, 0)  # Rojo en BGR
            thickness = 2


            rect_x_min_bloque = x1
            rect_y_min_bloque = y1
            rect_x_max_bloque = x1 + rect_width1
            rect_y_max_bloque = y1 + rect_height1

            # ---------------------- Dibujando el area de interés -------------------
            # cv2.rectangle(annotated_frame, start_point, end_point, color, thickness)
            # Coordenadas del punto inicial y final

            detectado_bloque_viajero = False
            detectado_persona = False

            cv2.rectangle(annotated_frame, start_point, end_point, color, thickness)


            for result in results:
                boxes = result.boxes.xyxy
                scores = result.boxes.conf
                classes = result.boxes.cls

                for box, conf, cls in zip(boxes, scores, classes):
                    x_min, y_min, x_max, y_max = map(int, box)

                    if cls == 0 and conf >= 0:
                        # if x_min >= rect_x_min_bloque and y_min >= rect_y_min_bloque and x_max <= rect_x_max_bloque and y_max <= rect_y_max_bloque:

                            detectado_bloque_viajero = True

                            if velocidad_bloque < 0:
                                velocidad_bloque = velocidad_bloque * -1

                            if velocidad_bloque  is not None:
                                text = f'Vel: {velocidad_bloque:.2f} m/s'
                            else:
                                text = 'Vel: N/A' 
                                
                            font = cv2.FONT_HERSHEY_SIMPLEX

                            (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                            text_offset_x = x_min + 70
                            # Calculamos la posición del recuadro
                            text_offset_y = y_min + 50  # Ajusta esta coordenada para bajar tanto el texto como el recuadro
                            text_box_x2 = text_offset_x + text_width
                            text_box_y2 = text_offset_y + text_height + baseline  # Suma la altura del texto y la línea base

                            # Dibujamos el recuadro gris detrás del texto
                            cv2.rectangle(annotated_frame, (text_offset_x, text_offset_y - text_height - baseline), (text_box_x2, text_offset_y), (87, 85, 85), -1)
                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                            # Dibujamos el texto justo dentro del recuadro
                            cv2.putText(annotated_frame, text, (text_offset_x, text_offset_y - baseline), font, 0.5, (255, 255, 255), 1)

                            # Determinar si el objeto se mueve hacia arriba o hacia abajo
                            if yc_anterior is not None:
                                
                                # Calculamos la posición del rectángulo detrás de la flecha
                                if yc > yc_anterior + 2:
                                    # Movimiento hacia abajo - cuerpo de la flecha largo, cabeza pequeña
                                    print("Movimiento hacia abajo")
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

                            # Actualizamos el valor de yc_anterior
                            yc_anterior = yc

                            print("")
                            xc, yc = int((x_min + x_max) / 2), y_max

                            # cv2.circle(annotated_frame, (xc, yc), 5, (0, 0, 255), thickness= 3)
                            # print("cross_blue_line:", cross_blue_line)  
                            # print("cross_green_line:", cross_green_line)
                            # print("cross_red_line:", cross_red_line)
                            # print("speed velocidad", avg_speed)   
                            # Verificación de cruce de líneas
                            if y_min > max_y_min:
                                max_y_min = y_min
                            if y_max > max_y_max:
                                max_y_max = y_max
                            if y_min < min_y_min:
                                min_y_min = y_min
                            if y_max < min_y_max:
                                min_y_max = y_max

                            line_ymin1 = max_y_min - 115
                            line_ymax1 = max_y_min - 115
                            line_start1 = (1200, line_ymin1)  # Coordenadas (x, y) del punto inicial
                            line_end1 = (800, line_ymax1)   # Coordenadas (x, y) del punto final
                            # cv2.line(annotated_frame, line_start1, line_end1, (255, 255, 0), thickness=2)  # Asegúrate de usar un color visible, como verde aquí

                            line_ymin2 = min_y_min + 120
                            line_ymax2 = min_y_min + 120
                            line_start2 = (1200, line_ymin2)  # Coordenadas (x, y) del punto inicial
                            line_end2 = (800, line_ymax2)   # Coordenadas (x, y) del punto final
                            # cv2.line(annotated_frame, line_start2, line_end2, (201, 255, 255), thickness=2)
                            # cv2.rectangle(annotated_frame, (x_min - 100, max_y_min + 100), (x_max + 100, min_y_min - 100), (0, 255, 255), 2)


                            if y_max < line_ymin1:  # ENCIMA DE LA LINEA DE ABAJO
                                estado_arriba = True

                            if y_min < line_ymax2:  # ENCIMA DE LA LINEA DE ARRIBA
                                estado_abajo = True

                            if y_min < line_ymax2 and y_max > line_ymin1:  # POSICIÓN INICIAL
                                pos_inicial = True

                            if y_min > line_ymax2 and y_max < line_ymin1:  # MITAD DE AMBAS LINEAS
                                mitad = True

                            if y_max > line_ymin1:
                                abajo_linea_inf = True

                            if y_min > line_ymax1 and estado_arriba and estado_abajo:
                                contador_cruces += 1
                                fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
                                hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
                                print(f"El rectángulo ha cruzado completamente la línea.")
                                tiempo_actual = datetime.datetime.now()
                                duracion = tiempo_actual - tiempo_inicial
                                duracion_en_minutos = duracion.total_seconds() / 60  # Convertir la duración a minutos
                                tiempo_formateado2 = float("{:.2f}".format(duracion_en_minutos))  # Formato como minutos con dos decimales
                                tiempo_formateado = str(duracion).split('.')[0]  # Formato como hh:mm:ss
                                tiempos_por_cruce[contador_cruces] = tiempo_formateado2
                                # print(f"Cruce {contador_cruces}, Fecha: {fecha_actual}, Hora de inicio: {hora_actual}, Tiempo desde el último cruce: {tiempo_formateado}")
                                tiempo_inicial = tiempo_actual  # Reinicia el temporizador
                                estado_arriba = False
                                estado_abajo = False

                    elif cls == 1 and conf >= floatProbabilidad:
                        # if x_min >= rect_x_min and y_min >= rect_y_min and x_max <= rect_x_max and y_max <= rect_y_max:
                        detectado_persona = True
                        if not persona_detectada_actual:
                            hora_primera_deteccion = datetime.datetime.now().strftime("%H:%M:%S")
                            ahora = datetime.datetime.now()
                            hora_primera_deteccion_segundos = (ahora.hour * 3600 + ahora.minute * 60 + ahora.second)
                            persona_detectada_actual = True

                        conf2 = conf * 100
                        text = f'Persona: {conf2:.0f} %'
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                        text_offset_x = x_min
                        text_offset_y = y_min - 25  # Ajusta esta coordenada según necesites
                        text_box_x2 = text_offset_x + text_width
                        text_box_y2 = text_offset_y + text_height + baseline  # Suma la altura del texto y la línea base
                        cv2.rectangle(annotated_frame, (text_offset_x, text_offset_y), (text_box_x2, text_box_y2), (87, 85, 85), -1)
                        cv2.putText(annotated_frame, text, (text_offset_x, y_min - 10), font, 0.5, (255, 255, 255), 1)
                        cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (203, 50, 52), 2)

            if not detectado_persona and persona_detectada_actual:
                hora_sin_detecciones = datetime.datetime.now().strftime("%H:%M:%S")
                ahora2 = datetime.datetime.now()
                hora_sin_detecciones_segundos = (ahora2.hour * 3600 + ahora2.minute * 60 + ahora2.second)
                persona_detectada_actual = False

            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            # Usar 'yield' para devolver el frame como parte de una respuesta HTTP
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        elapsed_time = time.time() - start_time
        sleep_time = process_interval - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)

def detect_video_velocidad():
    print("Iniciando detect_video")

    global boxes, classes, y_min, scores, bandera, model, probabilidad, contador_cruces, estado_arriba, tiempo_total_str, nueva_conexion, contador, tiempo_formateado
    global contador_crucesP, estado_abajo, mitad, abajo_linea_inf, detectado_bloque_viajero, detectado_persona, fecha_actual, hora_actual, tiempo_final_persona
    global contador_detecciones_persona, fecha_inicio_detecciones_persona, tiempo_total_detecciones_persona, tiempo_inicial_persona, line_ymax1, hora_detecciones_persona
    global detectado_persona_actual, hora_primera_deteccion, hora_sin_detecciones, ipcamFloat, hora_primera_no_deteccion, detecciones_previas
    global persona_detectada_actual, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos, ahora, ahora2, tiempo_formateado2
    global coordenadas_redimensionadas, xFloat1, yFloat1, widthFloat1, heightFloat1   # Añadir coordenadas redimensionadas
    global alerta, ProbabilidadSim, floatProbabilidad
    global cross_blue_line, cross_green_line, cross_red_line, contador_cruces_velocidad, avg_speed


    print("Iniciando video")

    tiempo_inicial = datetime.datetime.now()
    tiempo_inicialP = datetime.datetime.now()
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    max_y_max = 0
    min_y_min = float('inf')  # Inicialmente establecido en infinito
    min_y_max = float('inf')

    video = cv2.VideoCapture(video_path)

    # Dimensiones de las imágenes
    width2 = 294.1226453481414
    height2 = 145.45830319313836
    width1 = 1898
    height1 = 1058


    # while True:
    #     if bandera == "start_FULL_SERVICES_167_HCL": 
    #         while True:
    #             if bandera == 'stop_FULL_SERVICES_167_HCL':
    #                 break

    while video.isOpened():
        ret, frame_to_process = video.read()
        if not ret:
            break

        start_time = time.time()
        if frame_to_process is not None:
            # print("Procesando frame")
            results = model.predict(frame_to_process, imgsz=640, verbose=False)
            annotated_frame = frame_to_process.copy()

            x2 = xFloat1  # Ejemplo de coordenada x en imagen2
            y2 = yFloat1   # Ejemplo de coordenada y en imagen2
            
            rect_width2 = widthFloat1
            rect_height2 = heightFloat1

            # print("las coordenadas generadas son:", x2, y2)

            # Escalar coordenadas a imagen1
            x1 = (x2 / width2) * width1
            y1 = (y2 / height2) * height1

            # Escalar dimensiones del rectángulo a imagen1
            rect_width1 = (rect_width2 / width2) * width1
            rect_height1 = (rect_height2 / height2) * height1


            start_point = (int(x1), int(y1))
            end_point = (int(x1 + rect_width1), int(y1 + rect_height1))

            # Color y grosor del rectángulo
            color = (0, 255, 0)  # Rojo en BGR
            thickness = 2


            rect_x_min_bloque = x1
            rect_y_min_bloque = y1
            rect_x_max_bloque = x1 + rect_width1
            rect_y_max_bloque = y1 + rect_height1

            #annotated_frame = results[0].plot()

            # ---------------------- Dibujando el area de interés -------------------
            cv2.rectangle(annotated_frame, start_point, end_point, color, thickness)
            detectado_bloque_viajero = False
            detectado_persona = False

            for result in results:
                boxes = result.boxes.xyxy
                scores = result.boxes.conf
                classes = result.boxes.cls

                for box, conf, cls in zip(boxes, scores, classes):
                    x_min, y_min, x_max, y_max = map(int, box)
                    if cls == 0 and conf >= 0.10:
                        if x_min >= rect_x_min_bloque and y_min >= rect_y_min_bloque and x_max <= rect_x_max_bloque and y_max <= rect_y_max_bloque:

                            detectado_bloque_viajero = True
                            text_velocity = f'Bloque viajero: {conf:.2f}'

                            if avg_speed is not None:
                                text_velocity = f'Velocidad: {avg_speed:.2f}'
                            else:
                                text_velocity = 'Velocidad: N/A'

                            font = cv2.FONT_HERSHEY_SIMPLEX
                            (text_width, text_height), baseline = cv2.getTextSize(text_velocity, font, 0.5, 1)
                            text_offset_x = x_min
                            text_offset_y = y_min - 50  
                            text_box_x2 = text_offset_x + text_width
                            text_box_y2 = text_offset_y + text_height + baseline

                            cv2.rectangle(annotated_frame, (text_offset_x, text_offset_y), (text_box_x2, text_box_y2), (87, 85, 85), -1)

                            cv2.putText(annotated_frame, text_velocity, (text_offset_x, y_min - 40), font, 0.5, (255, 255, 255), 1)

                            cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                            xc, yc = int((x_min + x_max) / 2), y_max
                            x2c, y2c = int((x_min + x_max) / 2), y_min

                            cv2.circle(annotated_frame, (xc, yc), 5, (0, 0, 255), thickness= 3)
                            cv2.circle(annotated_frame, (x2c, y2c), 5, (0, 0, 255), thickness= 3)


                            if y_min > max_y_min:
                                max_y_min = y_min
                            if y_max > max_y_max:
                                max_y_max = y_max
                            if y_min < min_y_min:
                                min_y_min = y_min
                            if y_max < min_y_max:
                                min_y_max = y_max

                            line_ymin1 = max_y_min - 115
                            line_ymax1 = max_y_min - 115
                            line_start1 = (1200, line_ymin1)  # Coordenadas (x, y) del punto inicial
                            line_end1 = (800, line_ymax1)   # Coordenadas (x, y) del punto final
                            # cv2.line(annotated_frame, line_start1, line_end1, (255, 255, 0), thickness=2)  # Asegúrate de usar un color visible, como verde aquí

                            line_ymin2 = min_y_min + 120
                            line_ymax2 = min_y_min + 120
                            line_start2 = (1200, line_ymin2)  # Coordenadas (x, y) del punto inicial
                            line_end2 = (800, line_ymax2)   # Coordenadas (x, y) del punto final
                            # cv2.line(annotated_frame, line_start2, line_end2, (201, 255, 255), thickness=2)
                            # cv2.rectangle(annotated_frame, (x_min - 100, max_y_min + 100), (x_max + 100, min_y_min - 100), (0, 255, 255), 2)


                            if y_max < line_ymin1:  # ENCIMA DE LA LINEA DE ABAJO
                                estado_arriba = True

                            if y_min < line_ymax2:  # ENCIMA DE LA LINEA DE ARRIBA
                                estado_abajo = True

                            if y_min < line_ymax2 and y_max > line_ymin1:  # POSICIÓN INICIAL
                                pos_inicial = True

                            if y_min > line_ymax2 and y_max < line_ymin1:  # MITAD DE AMBAS LINEAS
                                mitad = True

                            if y_max > line_ymin1:
                                abajo_linea_inf = True

                            if y_min > line_ymax1 and estado_arriba and estado_abajo:
                                contador_cruces += 1
                                fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d")
                                hora_actual = datetime.datetime.now().strftime("%H:%M:%S")
                                print(f"El rectángulo ha cruzado completamente la línea.")
                                tiempo_actual = datetime.datetime.now()
                                duracion = tiempo_actual - tiempo_inicial
                                duracion_en_minutos = duracion.total_seconds() / 60  # Convertir la duración a minutos
                                tiempo_formateado2 = float("{:.2f}".format(duracion_en_minutos))  # Formato como minutos con dos decimales
                                tiempo_formateado = str(duracion).split('.')[0]  # Formato como hh:mm:ss
                                tiempos_por_cruce[contador_cruces] = tiempo_formateado2
                                # print(f"Cruce {contador_cruces}, Fecha: {fecha_actual}, Hora de inicio: {hora_actual}, Tiempo desde el último cruce: {tiempo_formateado}")
                                tiempo_inicial = tiempo_actual  # Reinicia el temporizador
                                estado_arriba = False
                                estado_abajo = False

                    elif cls == 1 and conf >= 0:
                        # if x_min >= rect_x_min and y_min >= rect_y_min and x_max <= rect_x_max and y_max <= rect_y_max:
                        detectado_persona = True

                        if not persona_detectada_actual:
                            hora_primera_deteccion = datetime.datetime.now().strftime("%H:%M:%S")
                            ahora = datetime.datetime.now()
                            hora_primera_deteccion_segundos = (ahora.hour * 3600 + ahora.minute * 60 + ahora.second)
                            persona_detectada_actual = True

                        conf2 = conf * 100
                        text = f'Person: {conf2:.2f} %'
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        (text_width, text_height), baseline = cv2.getTextSize(text, font, 0.5, 1)
                        text_offset_x = x_min
                        text_offset_y = y_min - 25  # Ajusta esta coordenada según necesites
                        text_box_x2 = text_offset_x + text_width
                        text_box_y2 = text_offset_y + text_height + baseline  # Suma la altura del texto y la línea base
                        cv2.rectangle(annotated_frame, (text_offset_x, text_offset_y), (text_box_x2, text_box_y2), (87, 85, 85), -1)
                        cv2.putText(annotated_frame, text, (text_offset_x, y_min - 10), font, 0.5, (255, 255, 255), 1)
                        cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (203, 50, 52), 2)

            if not detectado_persona and persona_detectada_actual:
                hora_sin_detecciones = datetime.datetime.now().strftime("%H:%M:%S")
                ahora2 = datetime.datetime.now()
                hora_sin_detecciones_segundos = (ahora2.hour * 3600 + ahora2.minute * 60 + ahora2.second)
                persona_detectada_actual = False

            ret, buffer = cv2.imencode('.jpg', annotated_frame)
            frame_bytes = buffer.tobytes()

            # Usar 'yield' para devolver el frame como parte de una respuesta HTTP
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        elapsed_time = time.time() - start_time
        sleep_time = process_interval - elapsed_time
        if sleep_time > 0:
            time.sleep(sleep_time)


def cambiar_bandera():
    global nombrepozo
    try:
        # Establecer conexión a la base de datos
        conexion = pymysql.connect(host=DB_HOST,
                                   user=DB_USER,
                                   password=DB_PASSWORD,
                                   database=DB_DATABASE)
        # try:
        with conexion.cursor() as cursor:
            # Actualizar el valor de 'bandera' en el último registro
            sql = "UPDATE TPCvariables SET bandera = %s ORDER BY ID DESC LIMIT 1"
            cursor.execute(sql, ('stop_' + nombrepozo,))  # Asigna el valor "stop"
            print('Bandera actualizada a: stop_' + nombrepozo)
            conexion.commit()  # Guarda los cambios en la base de datos
        # finally:
            # conexion.close()
    except Exception as e:
        return f"Error al actualizar la base de datos: {e}"

    return 'Hilos detenidos y bandera actualizada a: stop'

@app.route('/video_view')
def video_feed_PorteriaPX455():
    global isHilos, isHilos2

    if isHilos == False or isHilos2 == False:
        isHilos = True
        isHilos2 = True
    return Response(detect_video(), mimetype='multipart/x-mixed-replace; boundary=frame')


ishilo_video_bloque = 'nada'

@app.route('/video_feed_PorteriaPX45')
def video_feed_PorteriaPX45():
    global ishilo_video_bloque
    ishilo_video_bloque = 'video'
    print("ishilo_video_bloque", ishilo_video_bloque)
    return Response(detect_camara_yolo(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_FullServices')
def video_feed_FullServices():
    global ishilo_video_personas
    ishilo_video_personas = 'video_personas'
    print("ishilo_video_personas", ishilo_video_personas)
    return Response(detect_camara_yolo2(), mimetype='multipart/x-mixed-replace; boundary=frame')

isHilos = False
isHilos2 = False

# Inicializa variables globales
driver1 = None
driver2 = None
is_browser_open = False  

# def auto_refresh(driver_instance, interval=60):
#     while True:
#         time.sleep(interval)
#         try:
#             if driver_instance is not None:
#                 driver_instance.refresh()  # Refrescar la ventana asociada al driver
#         except Exception as e:
#             print(f"Error durante el refresco: {e}")
#             break  # Salir del bucle si hay un error

def auto_refresh(driver_instance, interval=60):
    iteracion = 0   
    while True:
        if iteracion == 0:
            time.sleep(10)
            print("Actualizo a los 10 segundos")
        else:
            time.sleep(interval)
            print("Actualizo a los 60 segundos")
        try:
            if driver_instance is not None:
                driver_instance.refresh()  # Refrescar la ventana asociada al driver
        except TimeoutException as te:
            print(f"Timeout al refrescar: {te}. Intentando de nuevo...")
            continue  # Intenta refrescar de nuevo
        except Exception as e:
            print(f"Error durante el refresco: {e}")
            break  # Salir del bucle si hay un error


@app.route('/InicioModeloPersonas')
def inicio_modelo():
    global isHilos, isHilos2, ishilo_video_bloque, ishilo_video_personas, driver1, driver2, is_browser_open

    # Inicializamos Selenium solo si las ventanas no están abiertas
    if not is_browser_open:
        driver_path = "C:/Users/VOM/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"
        
        # Iniciamos la primera ventana
        service1 = ChromeService(executable_path=driver_path)
        driver1 = webdriver.Chrome(service=service1)
        driver1.get("http://10.15.10.243:5001/video_feed_PorteriaPX45")

        time.sleep(2)
        
        # Iniciamos la segunda ventana
        service2 = ChromeService(executable_path=driver_path)
        driver2 = webdriver.Chrome(service=service2)
        driver2.get("http://10.15.10.243:5001/video_feed_FullServices")
        
        is_browser_open = True  # Marcamos que las ventanas están abiertas

        # Inicia un hilo para refrescar las páginas periódicamente
        threading.Thread(target=auto_refresh, args=(driver1, 60)).start()  # Recargar cada 5 minutos la primera ventana
        time.sleep(1)
        threading.Thread(target=auto_refresh, args=(driver2, 60)).start()  # Recargar cada 5 minutos la segunda ventana

    if not isHilos:
        isHilos = True
        hilo_streamingFS = threading.Thread(target=streaming_camara_Personas)
        hilo_streamingFS.start()
        
        hilo_fullServices = threading.Thread(target=detect_camara_yolo2)
        hilo_fullServices.start()

    time.sleep(2)

    if not isHilos2:
        isHilos2 = True
        hilo_streamingFS = threading.Thread(target=streaming_camara_Bloque)
        hilo_streamingFS.start()
        
        hilo_fullServices = threading.Thread(target=detect_camara_yolo)
        hilo_fullServices.start()
    
    return 'Hilos persona iniciados'

@app.route('/DetenerModeloPersonas')
def detener_modelo():
    global isHilos, driver1, driver2, is_browser_open
    isHilos = False

    # Cerramos las ventanas solo si están abiertas
    if is_browser_open:
        if driver1 is not None:
            try:
                driver1.quit()  # Cierra la primera ventana
            except Exception as e:
                print(f"Error al cerrar la primera ventana: {e}")
        
        if driver2 is not None:
            try:
                driver2.quit()  # Cierra la segunda ventana
            except Exception as e:
                print(f"Error al cerrar la segunda ventana: {e}")

        is_browser_open = False  # Marcamos que las ventanas están cerradas

    return 'Hilos y ventanas de personas detenidos'

# # Inicializa variables globales
# # Inicializa variables globales
# driver1 = None
# driver2 = None
# is_browser_open = False  



# def auto_refresh(driver_instance, interval=60):
#     iteracion = 0
#     while True:
#         if iteracion == 0:
#             iteracion = 1
#             time.sleep(5)
#         else:
#             time.sleep(interval)
#         try:
#             if driver_instance is not None:
#                 driver_instance.refresh()  # Refrescar la ventana asociada al driver
#         except Exception as e:
#             print(f"Error durante el refresco: {e}")
#             break  # Salir del bucle si hay un error

# @app.route('/InicioModeloPersonas')
# def inicio_modelo():
#     global isHilos, isHilos2, ishilo_video_bloque, ishilo_video_personas, driver1, driver2, is_browser_open

#     # Inicializamos Selenium solo si las ventanas no están abiertas
#     if not is_browser_open:
#         driver_path = "C:/Users/VOM/Downloads/chromedriver-win64/chromedriver-win64/chromedriver.exe"
        
#         # Abre las URLs con Selenium
#         url1 = url_for('video_feed_PorteriaPX45', _external=True)
#         url2 = url_for('video_feed_FullServices', _external=True)
        
        
#         # Iniciamos la primera ventana
#         service1 = ChromeService(executable_path=driver_path)
#         driver1 = webdriver.Chrome(service=service1)
#         driver1.get(url1)

#         time.sleep(2)
        
#         # Iniciamos la segunda ventana
#         service2 = ChromeService(executable_path=driver_path)
#         driver2 = webdriver.Chrome(service=service2)
#         driver2.get(url2)
        
#         is_browser_open = True  # Marcamos que las ventanas están abiertas

#         # Inicia un hilo para refrescar las páginas periódicamente
#         threading.Thread(target=auto_refresh, args=(driver1, 60)).start()  # Recargar cada 5 minutos la primera ventana
#         time.sleep(1)
#         threading.Thread(target=auto_refresh, args=(driver2, 60)).start()  # Recargar cada 5 minutos la segunda ventana

#     if not isHilos:
#         isHilos = True
#         hilo_streamingFS = threading.Thread(target=streaming_camara_Personas)
#         hilo_streamingFS.start()
        
#         hilo_fullServices = threading.Thread(target=detect_camara_yolo2)
#         hilo_fullServices.start()

#     time.sleep(2)

#     if not isHilos2:
#         isHilos2 = True
#         hilo_streamingFS = threading.Thread(target=streaming_camara_Bloque)
#         hilo_streamingFS.start()
        
#         hilo_fullServices = threading.Thread(target=detect_camara_yolo)
#         hilo_fullServices.start()
    
#     return 'Hilos persona iniciados'

# @app.route('/DetenerModeloPersonas')
# def detener_modelo():
#     global isHilos, driver1, driver2, is_browser_open
#     isHilos = False

#     # Cerramos las ventanas solo si están abiertas
#     if is_browser_open:
#         if driver1 is not None:
#             try:
#                 driver1.quit()  # Cierra la primera ventana
#             except Exception as e:
#                 print(f"Error al cerrar la primera ventana: {e}")
        
#         if driver2 is not None:
#             try:
#                 driver2.quit()  # Cierra la segunda ventana
#             except Exception as e:
#                 print(f"Error al cerrar la segunda ventana: {e}")

#         is_browser_open = False  # Marcamos que las ventanas están cerradas

#     return 'Hilos y ventanas de personas detenidos'



@app.route('/DetenerModeloBloque')
def detener_modelo2():
    global isHilos2
    isHilos2 = False
    return 'Hilos de bloque detenidos'



@app.route('/RestartModeloPersonas')
def restart_modelo():
    global isHilos
    isHilos = False
    return 'Hilos detenidos'

@app.route('/RestartModeloBloque')
def restart_modelo2():
    global isHilos2
    isHilos2 = False
    return 'Hilos detenidos'


# Función para comprobar si una hora está dentro de un rango de +-5 minutos de una hora objetivo
def time_to_seconds(t):
    """Convierte un objeto time a segundos desde la medianoche."""
    return t.hour * 3600 + t.minute * 60 + t.second

def prueba2():
    global detectado_persona, detectado_bloque_viajero, fecha_actual, hora_actual, tiempo_formateado, tiempo_formateado, tiempo_total_detecciones_persona, tiempo_total_str, bandera, alerta, ipcam, line_ymax1, y_min, probabilidad, horasin_detecciones_persona
    global hora_detecciones_persona, classes, scores, bandera, detect_fn, camera_url_porteriaPX45, ipcam, probabilidad, contador_cruces, estado_arriba, tiempo_total_str, nueva_conexion, contador, tiempo_formateado, contador_crucesP, estado_abajo, mitad, abajo_linea_inf, detectado_bloque_viajero, detectado_persona, fecha_actual, hora_actual, tiempo_final_persona, contador_detecciones_persona, fecha_inicio_detecciones_persona, tiempo_total_detecciones_persona, tiempo_inicial_persona
    global hora_primera_deteccion, hora_sin_detecciones, hora_primera_no_deteccion, target_time_1_segundos, target_time_2_segundos, hora_primera_deteccion_segundos, hora_sin_detecciones_segundos

    global banderin_actual, nombrepozo, alerta, banderaCon, isHilos, isHilos2, banderaFull
    
    # ---------------  Diccionario de horas de comidas
    global tiemposComidaFormateado, isTiempos
    # Variables para controlar el estado del temporizador y evitar múltiples inicios
    timer_alerta = False
    tiempos_alerta = []
    tiempos_alerta_alimentacion = []
    hora_inicio_alerta_alimentacion = None
    hora_inicio_alerta_alimentacionFINAL = None
    hora_inicio_alerta = None
    fecha_inicio_alerta = None
    fecha_inicio_alerta_alimentacion = None
    duracionAlertaTotal_alimentacion = 0   
    duracionAlertaTotal = 0
    contador_alerta = 0
    contador_alerta_alimentacion = 0
    hora_fin_alerta_alimentacion = 0
    hora_fin_alerta = 0
    fecha_fin_alerta = 0
    fecha_fin_alerta_alimentacion = 0
    # Variables para el contador y el tiempo total
    contador_condicional = 0
    tiempo_total_condicional = 0
 

    contador = 0
    timer_active = False
    start_time = None
    # Variables de estado
    alerta_activada = False
    contador_alerta_alimentacion = 0
    ultimo_contador_alerta_alimentacion = 0
    tiempos_alerta_alimentacion = []
    duracionAlertaTotalBD = 0
 
    # Variables para almacenar los últimos valores de los contadores
    ultimo_contador_cruces = 0
    ultimo_contador_alerta_alimentacion = 0
    ultimo_contador_alerta = 0

 
    
    bandera_otros_npt = False
    bandera_inicio_otros_npt = False
    
    contador_otros_npt = 0
    ultimo_contador_otros_npt = 0
    tiempo_inicial_otros_npt = 0
    tiempo_inicial_otros_nptFinal = 0
    fecha_inicio_otros_npt = 0
    diferencia_tiempo_lleva_otros_npt = 0
    duracionOtrosNpt = 0
    fecha_final_otros_npt = 0
    tiempo_lleva_otros_npt = 0
       
    bandera_parada_corta = False
    bandera_inicio_parada_corta = False
    tiempo_lleva_parada_corta = 0
    fecha_inicio_parada_corta = 0
    fecha_final_parada_corta = 0
    duracionParadaCorta = 0
    contador_parada_corta = 0
    ultimo_contador_parada_corta = 0
    tiempo_inicial_parada_corta = 0
    tiempo_inicial_parada_cortaFinal = 0
    
    duracionAlertaTotal_alimentacion_en_minutos = 0



    
    while True:
        while banderaFull == "start_TOQUI_HCL":
            
            if banderaFull == 'stop_TOQUI_HCL':
                break            
            # Horas objetivo para las comparaciones

            if isTiempos == True:
    # ------------------------------ Formato de desayuno -----------------------------------------
                # print(desayuno)
                desayuno_inicio = tiemposComidaFormateado['desayuno'][0]
                # print(desayuno_inicio)
                desayuno_inicio = desayuno_inicio.split(":")

                # print("Desayuno: ", desayuno_inicio)

                #  Valor de hora 
                desayuno_inicio_hora = desayuno_inicio[0]
                # Eliminar el cero inicial si está presente en la hora
                desayuno_inicio_hora = desayuno_inicio_hora.lstrip('0') if desayuno_inicio_hora.startswith('0') else desayuno_inicio_hora
                
                # Valor de minuto
                desayuno_inicio_min = desayuno_inicio[1]
                # Eliminar el cero inicial si está presente en la hora
                desayuno_inicio_min = desayuno_inicio_min.lstrip('0') if desayuno_inicio_min.startswith('0') else desayuno_inicio_min
                
                # print(desayuno_inicio_hora)

                target_time_1 = dtime(int(desayuno_inicio_hora), int(desayuno_inicio_min), 0)
                
                
                desayuno_final = tiemposComidaFormateado['desayuno'][1]
                # print(desayuno_inicio)
                desayuno_final = desayuno_final.split(":")
                
                #  Valor de hora 
                desayuno_final_hora = desayuno_final[0]
                # Eliminar el cero inicial si está presente en la hora
                desayuno_final_hora = desayuno_final_hora.lstrip('0') if desayuno_final_hora.startswith('0') else desayuno_final_hora
                
                # Valor de minuto
                desayuno_final_min = desayuno_final[1]
                # Eliminar el cero inicial si está presente en la hora
                desayuno_final_min = desayuno_final_min.lstrip('0') if desayuno_final_min.startswith('0') else desayuno_final_min
                
                
                target_time_2 = dtime(int(desayuno_final_hora) , int(desayuno_final_min), 0)

                target_time_1_segundos = time_to_seconds(target_time_1)
                target_time_2_segundos = time_to_seconds(target_time_2)

                
    # ------------------------------- Formato de almuerzo ----------------------------------------------

                
                almuerzo_inicio = tiemposComidaFormateado['almuerzo'][0]
                # print(desayuno_inicio)
                almuerzo_inicio = almuerzo_inicio.split(":")
                almuerzo_inicio_hora = almuerzo_inicio[0]
                # Eliminar el cero inicial si está presente en la hora
                almuerzo_inicio_hora = almuerzo_inicio_hora.lstrip('0') if almuerzo_inicio_hora.startswith('0') else almuerzo_inicio_hora 
                # Valor de minuto
                almuerzo_inicio_min = almuerzo_inicio[1]
                # Eliminar el cero inicial si está presente en la hora
                almuerzo_inicio_min = almuerzo_inicio_min.lstrip('0') if almuerzo_inicio_min.startswith('0') else almuerzo_inicio_min                                
                target_time_1_almuerzo = dtime(int(almuerzo_inicio_hora), int(almuerzo_inicio_min), 0)  
                almuerzo_final = tiemposComidaFormateado['almuerzo'][1]
                # print(desayuno_inicio)
                almuerzo_final = almuerzo_final.split(":")
                
                #  Valor de hora 
                almuerzo_final_hora = almuerzo_final[0]
                # Eliminar el cero inicial si está presente en la hora
                almuerzo_final_hora = almuerzo_final_hora.lstrip('0') if almuerzo_final_hora.startswith('0') else almuerzo_final_hora
                
                # Valor de minuto
                almuerzo_final_min = almuerzo_final[1]
                # Eliminar el cero inicial si está presente en la hora
                almuerzo_final_min = almuerzo_final_min.lstrip('0') if almuerzo_final_min.startswith('0') else almuerzo_final_min
                
                target_time_2_almuerzo = dtime(int(almuerzo_final_hora) , int(almuerzo_final_min), 0)

                target_time_1_segundos_almuerzo = time_to_seconds(target_time_1_almuerzo)
                target_time_2_segundos_almuerzo = time_to_seconds(target_time_2_almuerzo)


                print("Target time 1 desayuno: ", target_time_1_segundos)
                print("Target time 2 desayuno: ", target_time_2_segundos)
                print("")
                print("")
                print("Target time 1 almuerzo: ", target_time_1_segundos_almuerzo)
                print("Target time 2 almuerzo: ", target_time_2_segundos_almuerzo)
                print("")
                print("")
                print("primera detección: ", hora_primera_deteccion)
                print("Tarjet sin detecciones: ", hora_sin_detecciones)
                
                #------------------------ Alerta de alimentación -------------------------
                print("")
                print("")
                print("")

                print(f"Inicio de la alerta de alimentación: {hora_inicio_alerta_alimentacion} ({fecha_inicio_alerta_alimentacion})")
                duracionAlertaTotal_alimentacionBD = float("{:.2f}".format(duracionAlertaTotal_alimentacion_en_minutos))  # Formato como minutos con dos decimales
                print(f"Alerta de alimentación {contador_alerta_alimentacion}: Duración = {duracionAlertaTotal_alimentacionBD} minutos, Fin = {hora_fin_alerta_alimentacion} ({fecha_fin_alerta_alimentacion})")

                print("")
                print("")
                print("")


            
            print("")
            print("")
            # print("Estamos en el pozo: ", nombrepozo)
            print("IsHilos and IsHilos2: ", isHilos, isHilos2)

                

    #------------------------ Alerta de conexión -------------------------1

            # print("La Alerta por TSW es : ", alerta)
            # print(f"Conexión {contador_cruces}, Fecha: {fecha_actual}, Hora de inicio: {hora_actual}, Tiempo desde el último cruce: {tiempo_formateado}, banderaConexion: {banderaCon}")
            if banderaCon == "conexion":
                if contador_cruces > ultimo_contador_cruces:

                    if tiempo_formateado2 <= 0.7:
                        contador_cruces -= 1
                    else:
                        almacenar_variables_en_bd(fecha_actual, hora_actual, tiempo_formateado2, 0, 0, 0, 0, 0, 'conexión', nombrepozo)
                        ultimo_contador_cruces = contador_cruces

            if banderaCon == "desconexion":
                if contador_cruces > ultimo_contador_cruces:

                    if tiempo_formateado2 <= 0.7:
                        contador_cruces -= 1
                    else:
                        almacenar_variables_en_bd(fecha_actual, hora_actual, 0, tiempo_formateado2, 0, 0, 0, 0, 'desconexión', nombrepozo)
                        ultimo_contador_cruces = contador_cruces


            if contador_alerta_alimentacion > ultimo_contador_alerta_alimentacion:

                if duracionAlertaTotal_alimentacionBD <= 0.5:
                    contador_alerta_alimentacion -= 1
                else:
                    almacenar_variables_en_bd(fecha_inicio_alerta_alimentacion, hora_inicio_alerta_alimentacionFINAL, 0, 0, 0, duracionAlertaTotal_alimentacionBD, 0, 0, 'alimentacion', nombrepozo)
                    ultimo_contador_alerta_alimentacion = contador_alerta_alimentacion  # Actualiza el último valor del contador
        
            #------------------------------ Alerta por tormenta -----------------------------
            # print(f"Inicio de la alerta tormenta: {hora_inicio_alerta} ({fecha_inicio_alerta})")
            # print(f"Alerta por tormenta {contador_alerta}: Duración = {duracionAlertaTotalBD} minutos, Fin = {hora_fin_alerta} ({fecha_fin_alerta})")
    
            if contador_alerta > ultimo_contador_alerta:

                if duracionAlertaTotalBD <= 0.5:
                    contador_alerta -= 1
                    print("Contador alerta antes del else: ", contador_alerta)
                else:
                    almacenar_variables_en_bd(fecha_inicio_alerta, hora_inicio_alerta, 0, 0, duracionAlertaTotalBD, 0, 0, 0, 'tormenta', nombrepozo)
                    ultimo_contador_alerta = contador_alerta  # Actualiza el último valor del contador

            #------------------------- Alerta por otros npt -------------------------------
            # print(f"Inicio de la alerta otros npt: {tiempo_inicial_otros_npt} ({fecha_inicio_otros_npt})")
            # print(f"Alerta por otros npt {contador_otros_npt}: Duración = {duracionOtrosNpt} minutos, Fin = {tiempo_lleva_otros_npt} ({fecha_final_otros_npt})")
    
            if contador_otros_npt > ultimo_contador_otros_npt:
                # print("Tiempo de inicio de otrso npt: ",tiempo_inicial_otros_npt)
                almacenar_variables_en_bd(fecha_inicio_otros_npt, tiempo_inicial_otros_nptFinal, 0, 0, 0, 0, 0, duracionOtrosNpt, 'otros_npt', nombrepozo)
                ultimo_contador_otros_npt = contador_otros_npt  # Actualiza el último valor del contador

            #------------------------- Alerta por parada corta -------------------------------
                #   print(f"Inicio de la alerta parada corta: {tiempo_inicial_parada_corta} ({fecha_inicio_parada_corta})")
             #   print(f"Alerta por parada corta {contador_parada_corta}: Duración = {duracionParadaCorta} minutos, Fin = {tiempo_lleva_parada_corta} ({fecha_final_parada_corta})")
            
            if contador_parada_corta > ultimo_contador_parada_corta:
                # print("Tiempo de inicio de parada corta: ",tiempo_inicial_parada_corta)
                almacenar_variables_en_bd(fecha_inicio_parada_corta, tiempo_inicial_parada_cortaFinal, 0, 0, 0, 0, duracionParadaCorta, 0, 'Parada_corta', nombrepozo)
                ultimo_contador_parada_corta = contador_parada_corta  # Actualiza el último valor del contador

            if isTiempos == True:
                #------------------ Condicional para alimentacion desayuno ----------------
                if not alerta_activada and (target_time_1_segundos + 60) >= hora_sin_detecciones_segundos >= (target_time_1_segundos - 60) and hora_primera_deteccion_segundos < target_time_2_segundos:
                    tiempo_inicial_alerta_alimentacion = time.time()
                    hora_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_inicial_alerta_alimentacion))
                    hora_inicio_alerta_alimentacionFINAL = datetime.datetime.now().strftime("%H:%M:%S")
                    fecha_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d', time.localtime(tiempo_inicial_alerta_alimentacion))
                    timer_alerta_alimentacion = True
                    alerta_activada = True
        
                # Lógica para finalizar la alerta y contarla solo si ambas condiciones se cumplen
                elif alerta_activada and (target_time_1_segundos + 60) >= hora_sin_detecciones_segundos >= (target_time_1_segundos - 60) and (target_time_2_segundos + 60) >= hora_primera_deteccion_segundos >= (target_time_2_segundos - 60):
                    tiempo_final_alerta_alimentacion = time.time()
                    duracionAlertaTotal_alimentacion = tiempo_final_alerta_alimentacion - tiempo_inicial_alerta_alimentacion
                    duracionAlertaTotal_alimentacion_en_minutos = duracionAlertaTotal_alimentacion / 60  # Convertir la duración a minutos
                    duracionAlertaTotal_alimentacionBD = "{:.2f}".format(duracionAlertaTotal_alimentacion_en_minutos)  # Formato como minutos con dos decimales
                    tiempos_alerta_alimentacion.append(duracionAlertaTotal_alimentacionBD)
                    contador_alerta_alimentacion += 1
                    hora_fin_alerta_alimentacion = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_final_alerta_alimentacion))
                    fecha_fin_alerta_alimentacion = time.strftime('%Y-%m-%d', time.localtime(tiempo_final_alerta_alimentacion))
                    timer_alerta_alimentacion = False
                    alerta_activada = False

                #------------------ Condicional para alimentacion almuerzo ----------------
                if not alerta_activada and (target_time_1_segundos_almuerzo + 60) >= hora_sin_detecciones_segundos >= (target_time_1_segundos_almuerzo - 60) and hora_primera_deteccion_segundos < target_time_2_segundos_almuerzo:
                    tiempo_inicial_alerta_alimentacion = time.time()
                    hora_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_inicial_alerta_alimentacion))
                    hora_inicio_alerta_alimentacionFINAL = datetime.datetime.now().strftime("%H:%M:%S")
                    fecha_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d', time.localtime(tiempo_inicial_alerta_alimentacion))
                    timer_alerta_alimentacion = True
                    alerta_activada = True
        
                # Lógica para finalizar la alerta y contarla solo si ambas condiciones se cumplen
                elif alerta_activada and (target_time_1_segundos_almuerzo + 60) >= hora_sin_detecciones_segundos >= (target_time_1_segundos_almuerzo - 60) and (target_time_2_segundos_almuerzo + 60) >= hora_primera_deteccion_segundos >= (target_time_2_segundos_almuerzo - 60):
                    tiempo_final_alerta_alimentacion = time.time()
                    duracionAlertaTotal_alimentacion = tiempo_final_alerta_alimentacion - tiempo_inicial_alerta_alimentacion
                    duracionAlertaTotal_alimentacion_en_minutos = duracionAlertaTotal_alimentacion / 60  # Convertir la duración a minutos
                    duracionAlertaTotal_alimentacionBD = "{:.2f}".format(duracionAlertaTotal_alimentacion_en_minutos)  # Formato como minutos con dos decimales
                    tiempos_alerta_alimentacion.append(duracionAlertaTotal_alimentacionBD)
                    contador_alerta_alimentacion += 1
                    hora_fin_alerta_alimentacion = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_final_alerta_alimentacion))
                    fecha_fin_alerta_alimentacion = time.strftime('%Y-%m-%d', time.localtime(tiempo_final_alerta_alimentacion))
                    timer_alerta_alimentacion = False
                    alerta_activada = False

                # -------------- Condicional para de otros npt --------------
                if not (target_time_1_segundos + 60) >= hora_sin_detecciones_segundos >= (target_time_1_segundos - 60) and not (target_time_2_segundos + 60) >= hora_primera_deteccion_segundos >= (target_time_2_segundos - 60):
                    if alerta == "0**" or alerta == "1**":
                        print("Detecto persona: ", detectado_persona)
                        if detectado_persona == False:
                            if bandera_otros_npt == False:
                                bandera_otros_npt = True
                                tiempo_otros_npt = datetime.datetime.now()

                                print("No está en alimentación")
                                print(f"Tiempo inicial: {tiempo_otros_npt}")
                                
                            # Calcula la diferencia de tiempo
                            tiempo_actual_otros_npt = datetime.datetime.now()
                            diferencia_tiempo = tiempo_actual_otros_npt - tiempo_otros_npt
            
                            # Obtiene la diferencia en segundos
                            diferencia_en_segundos = diferencia_tiempo.total_seconds()
                            print(f"Tiempo desde inicializo otros npt: {diferencia_en_segundos:.2f} segundos")
                            
                            if bandera_inicio_otros_npt == True:
                                # Calcula la diferencia de tiempo
                                tiempo_lleva_otros_npt_no = datetime.datetime.now()
                                diferencia_tiempo_lleva = (tiempo_lleva_otros_npt_no - tiempo_inicial_otros_npt).total_seconds()
                                print("Lleva de otros npt: ", diferencia_tiempo_lleva)


                            if diferencia_en_segundos >= 20:
                                if bandera_inicio_otros_npt == False:
                                    bandera_inicio_otros_npt = True
                                    tiempo_inicial_otros_npt = datetime.datetime.now()
                                    tiempo_inicial_otros_nptFinal = datetime.datetime.now().strftime("%H:%M:%S")
                                    # Formatear para obtener solo la fecha
                                    fecha_inicio_otros_npt = tiempo_inicial_otros_npt.strftime("%Y-%m-%d")
                                    print("Han pasado 60 segundos desde que se inicializó el tiempo inicial de otros npt.")
                
                    
                if (target_time_1_segundos + 60) >= hora_sin_detecciones_segundos >= (target_time_1_segundos - 60) and (target_time_2_segundos + 60) >= hora_primera_deteccion_segundos >= (target_time_2_segundos - 60) or alerta == "2**" or alerta == "3**" or detectado_persona == True:
                    bandera_otros_npt = False
                    # print("Reinicio tiempo de otros npt")
                    if bandera_inicio_otros_npt == True:
                        # Calcula la diferencia de tiempo
                        tiempo_lleva_otros_npt = datetime.datetime.now()
                        # Formatear para obtener solo la fecha
                        fecha_final_otros_npt = tiempo_lleva_otros_npt.strftime("%Y-%m-%d")
                        diferencia_tiempo_lleva_otros_npt = (tiempo_lleva_otros_npt - tiempo_inicial_otros_npt).total_seconds()
                        diferencia_tiempo_lleva_otros_npt_minutos = diferencia_tiempo_lleva_otros_npt / 60 # Convertir la duración en minutos
                        duracionOtrosNpt = "{:.2f}".format(diferencia_tiempo_lleva_otros_npt_minutos)  # Formato como minutos con dos decimales
                        print("Otros npt duro: ", diferencia_tiempo_lleva_otros_npt)
                        contador_otros_npt += 1
                        bandera_inicio_otros_npt = False
                    
                        
            # ------------------------ Condicional para Paradas Cortas ----------------------
            if banderin_actual == "Parada_corta":
                if bandera_parada_corta == False:
                    bandera_parada_corta = True
                    tiempo_espera_parada_corta = datetime.datetime.now()
                    print("Empezo parada corta")
                    
                # Calcula la diferencia de tiempo
                tiempo_actual_parada_corta = datetime.datetime.now()
                diferencia_tiempo_parada_corta = tiempo_actual_parada_corta - tiempo_espera_parada_corta
                
                # Obtiene la diferencia en segundos
                diferencia_en_segundos_parada_corta = diferencia_tiempo_parada_corta.total_seconds()
                print(f"Tiempo desde inicializo parada corta: {diferencia_en_segundos_parada_corta:.2f} segundos")
                if bandera_inicio_parada_corta == True:
                    # Calcula la diferencia de tiempo
                    tiempo_lleva_parada_corta = datetime.datetime.now()
                    diferencia_tiempo_lleva_corta = (tiempo_lleva_parada_corta - tiempo_inicial_parada_corta).total_seconds()
                    print("Lleva de parada corta: ", diferencia_tiempo_lleva_corta)
                if diferencia_en_segundos_parada_corta >= 20:
                    if bandera_inicio_parada_corta == False:
                        bandera_inicio_parada_corta = True
                        tiempo_inicial_parada_corta = datetime.datetime.now()
                        tiempo_inicial_parada_cortaFinal = datetime.datetime.now().strftime("%H:%M:%S")
                        # Formatear para obtener solo la fecha
                        fecha_inicio_parada_corta = tiempo_inicial_parada_corta.strftime("%Y-%m-%d")
                        print("Han pasado 60 segundos desde que se inicializó el tiempo inicial de parada corta.")
            
            if banderin_actual != "Parada_corta":
                bandera_parada_corta = False
                # print("Reinicio tiempo de parada corta")
                if bandera_inicio_parada_corta == True:
                    # Calcula la diferencia de tiempo
                    tiempo_lleva_parada_corta = datetime.datetime.now()
                    # Formatear para obtener solo la fecha
                    fecha_final_parada_corta = tiempo_lleva_parada_corta.strftime("%Y-%m-%d")
                    diferencia_tiempo_lleva_paradas_cortas = (tiempo_lleva_parada_corta - tiempo_inicial_parada_corta).total_seconds()
                    
                    diferencia_tiempo_lleva_parada_corta_minutos = diferencia_tiempo_lleva_paradas_cortas / 60 # Convertir la duración en minutos
                    duracionParadaCorta = "{:.2f}".format(diferencia_tiempo_lleva_parada_corta_minutos)  # Formato como minutos con dos decimales
                    print("Parada Corta duro: ", diferencia_tiempo_lleva_paradas_cortas)
                    
                    contador_parada_corta += 1
                    bandera_inicio_parada_corta = False

    #------------------- Condicional para alerta TSW ----------------
    
            if alerta == "2**" or alerta == "3**":
                if not timer_alerta:
                    tiempo_inicial_alerta = time.time()
                    # hora_inicio_alerta = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_inicial_alerta))
                    hora_inicio_alerta = datetime.datetime.now().strftime("%H:%M:%S")
                    fecha_inicio_alerta = time.strftime('%Y-%m-%d', time.localtime(tiempo_inicial_alerta))
                    timer_alerta = True
                    mensaje_emitido_alerta = False  # Flag para controlar la emisión del mensaje a los 30 segundos
    
            # Revisar si el timer de alerta está activo y si han pasado 30 segundos
            if timer_alerta:
                duracionAlerta = time.time() - tiempo_inicial_alerta
                if duracionAlerta >= 30 and not mensaje_emitido_alerta:
                    print("Se detectaron personas a los 30 segundos!")
                    mensaje_emitido_alerta = True
    
            # Lógica para cuando la alerta o alimentación terminan
            if (alerta != "2**" and alerta != "3**") and timer_alerta:
                tiempo_final_alerta = time.time()
                duracionAlertaTotal = tiempo_final_alerta - tiempo_inicial_alerta
                duracionAlertaTotal_en_minutos = duracionAlertaTotal / 60  # Convertir la duración a minutos
                duracionAlertaTotalBD = float("{:.2f}".format(duracionAlertaTotal_en_minutos))  # Formato como minutos con dos decimales
                tiempos_alerta.append(duracionAlertaTotalBD)
                contador_alerta += 1
                hora_fin_alerta = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_final_alerta))
                fecha_fin_alerta = time.strftime('%Y-%m-%d', time.localtime(tiempo_final_alerta))
                print(f"Alerta {contador_alerta}: Duración = {duracionAlertaTotalBD} minutos, Fin = {hora_fin_alerta} ({fecha_fin_alerta})")
                timer_alerta = False

            time.sleep(1)



if __name__ == '__main__':
   
    print("Entro")
    # hilo_video = threading.Thread(target=detect_video)
    # hilo_video.start()
    hilo_actualizar_variables = threading.Thread(target=actualizar_variables_desde_bd)
    hilo_actualizar_variables.start()
    hilo_actualizar_variables2 = threading.Thread(target=obtener_bandera_full_services)
    hilo_actualizar_variables2.start()
    hilo_prueba = threading.Thread(target=prueba2)
    hilo_prueba.start()
    hilo_npt_alerta = threading.Thread(target=npt_alerta)
    hilo_npt_alerta.start() 
    hilo_actualizar_coordenadas = threading.Thread(target=actualizar_coordenadas_desde_bd)
    hilo_actualizar_coordenadas.start()

    # hilo_velocidad = threading.Thread(target=velocidad)
    # hilo_velocidad.start()
#     hilo_porteriaPX45 = threading.Thread(name="hilo_px45_1", target=detect_camara_yolo)
#     hilo_porteriaPX45.start()
#     hilo_streaming = threading.Thread(name="hilo_streaming", target=streaming_camara_Bloque)
#     hilo_streaming.start()
# # Llamada a la función
#     hilo_fullServices = threading.Thread(name="hilo_FS167", target=detect_camara_yolo2)
#     hilo_fullServices.start()
#     hilo_streamingFS = threading.Thread(name="hilo_FS167", target=streaming_camara_Personas)
#     hilo_streamingFS.start()

    app.run(host='0.0.0.0', port=5001)



  