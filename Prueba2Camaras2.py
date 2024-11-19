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


def grabar_camara(url, duracion_segmento, nombre_segmento, modelo, procesar_frame_func):
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
                frame = procesar_frame_func(frame, results)
 
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
                    cursor.execute(sql, ('ARBOLITO_HCL',))
                    resultado = cursor.fetchone()
                    if resultado:
                        banderaFull = resultado[0]
                        # print(f"Bandera del pozo ARBOLITO_HCL actualizada: {banderaFull}")
                    else:
                        print("No se encontró ningún registro para el pozo TOQUI_HCL")
            finally:
                conexion.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {e}")
        # Espera 10 segundos antes de volver a ejecutar la consulta
        time.sleep(5)

def actualizar_variables_desde_bd():
    global bandera, ipcam, ipcam2, probabilidad, ipcamFloat, banderin_actual, tiempos_comida, tiemposComidaFormateado
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

# ---------------------------- Función para NPT POR TORMENTA --------------------
def npt_alerta():
    global alerta, ipcam2, url
    
    while True:

        try:
            url = 'http://consultas.axuretechnologies.com:8081/axure/niveles-total/' + "SAT0331"
    
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

            print("Alerta: ", alerta)   

        except Exception as e:
            print(f"Error inesperado: {e}")
            print("Reintentando...")
            time.sleep(5)
            continue
        
        time.sleep(1)

# ---------------------------- Funciones para almacenar variables ---------------
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
def almacenar_variables_PERSONAS_bd(fecha, hora_inicio, tiempo_conexion, tiempo_desconexion=0, npt_tormenta=0, alimentacion=0, paradas_cortas=0, direccion_ip='', bandera='', nombrepozo=''):
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

# --------------------------------------------------------------------------------
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
        # print("Variables utilizadas en la velocidad:", yc_invertido, Metros, max_yc_invertido, tiempo_prom, yc_anterior1_invertido)
        # print("Velocidad del bloque:::::: ", round(velocidad_bloque, 2))
        yc_anterior1_invertido = yc_invertido
        # Esperar el tiempo definido por tiempo_prom antes de la próxima iteración
        time.sleep(tiempo_prom)
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

def funcion_guardar_datos():
    global yc_invertido, fecha_actual, hora, yc_metros, velocidad_bloque
    while True:
        almacenar_variables_pos(fecha_actual, hora, yc_metros)
        almacenar_variables_vel(velocidad_bloque, hora, fecha_actual)
        print("Datos guardados", fecha_actual, hora, yc_metros, velocidad_bloque)
        time.sleep(4)

def procesar_frame_camaraBloque(frame, results):
    # Lógica específica para la cámara 1 (cuando la clase es 1)
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
 

#---------------------------- Variables para deteccion de personas
import datetime
import cv2

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
ahora1, ahora2 = None, None
detectado_persona = None

def procesar_frame_camaraPersonas(frame, results):
    global hora_primera_deteccion_segundos, hora_sin_detecciones_segundos
    global hora_primera_deteccion, hora_sin_detecciones, ahora1, ahora2
    global tiempo_deteccion_acumulado, tiempo_no_deteccion_acumulado
    global persona_detectada_actual, deteccion_confirmada, no_deteccion_confirmada, detectado_persona

    def obtener_segundos_actuales():
        ahora = datetime.datetime.now()
        return ahora.hour * 3600 + ahora.minute * 60 + ahora.second

    detectado_persona = False
    tiempo_actual_segundos = obtener_segundos_actuales()

    annotated_frame = frame.copy()

    # Procesar detecciones
    for result in results:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box)
            if cls == 1 and conf >= 0.1:  # Detección de persona
                detectado_persona = True
                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

    if detectado_persona:
        if not persona_detectada_actual:  # Primera detección en este ciclo
            hora_primera_deteccion = datetime.datetime.now().strftime("%H:%M:%S")
            hora_primera_deteccion_segundos = tiempo_actual_segundos
            persona_detectada_actual = True

        tiempo_deteccion_acumulado += tiempo_actual_segundos - hora_primera_deteccion_segundos
        hora_primera_deteccion_segundos = tiempo_actual_segundos
        tiempo_no_deteccion_acumulado = 0

        # Confirmar detección si se acumulan al menos 10 segundos
        if tiempo_deteccion_acumulado >= 3 and not deteccion_confirmada:
            deteccion_confirmada = True
            no_deteccion_confirmada = False
            ahora1 = datetime.datetime.now().strftime("%H:%M:%S")
            hora_primera_deteccion_segundos = obtener_segundos_actuales()

            print("Detección confirmada a las:", ahora1)
            print("En segundos Detección:", hora_primera_deteccion_segundos)

    else:
        if persona_detectada_actual:  # Primera no detección en este ciclo
            hora_sin_detecciones = datetime.datetime.now().strftime("%H:%M:%S")
            hora_sin_detecciones_segundos = tiempo_actual_segundos
            persona_detectada_actual = False

        tiempo_no_deteccion_acumulado += tiempo_actual_segundos - hora_sin_detecciones_segundos
        hora_sin_detecciones_segundos = tiempo_actual_segundos
        tiempo_deteccion_acumulado = 0

        # Confirmar no detección si se acumulan al menos 10 segundos
        if tiempo_no_deteccion_acumulado >= 5 and not no_deteccion_confirmada:
            no_deteccion_confirmada = True
            deteccion_confirmada = False
            ahora2 = datetime.datetime.now().strftime("%H:%M:%S")
            hora_sin_detecciones_segundos = obtener_segundos_actuales()
            print("No detección confirmada a las:", ahora2)
            print("En segundos No detección:", hora_sin_detecciones_segundos)

    return annotated_frame

# ---------------------------- Funciones para obtener variables de Base de Datos --------------------
# -------------- Variable para almacenar los tiempos de comida
tiempos_comida = ''
tiemposComidaFormateado = {}
isTiempos = False
target_time_1_segundos = 0
target_time_2_segundos = 0

def logica_deteccion_personas():
    global  hora_primera_deteccion, hora_sin_detecciones, banderaFull, ahora2, ahora1
    global duracionAlertaTotalBD, ultimo_contador_alerta, contador_alerta
    while True:
        while banderaFull == "start_ARBOLITO_HCL":
            
            if banderaFull == 'stop_TOQUI_HCL':
                break   


            # if contador_alerta > ultimo_contador_alerta:

            #     if duracionAlertaTotalBD <= 0.5:
            #         contador_alerta -= 1
            #         print("Contador alerta antes del else: ", contador_alerta)
            #     else:
            #         almacenar_variables_PERSONAS_bd(fecha_inicio_alerta, hora_inicio_alerta, 0, 0, duracionAlertaTotalBD, 0, 0, 0, 'tormenta', nombrepozo)
            #         ultimo_contador_alerta = contador_alerta  # Actualiza el último valor del contador


            # alimentacion()
            tormenta_npt()

            print("")
            print("Tarjet sin detecciones: ", ahora1)
            print("Hora primera deteccion", ahora2)
            # funcion_guardar_datos()

            time.sleep(1)
    
def time_to_seconds(t):
    """Convierte un objeto time a segundos desde la medianoche."""
    return t.hour * 3600 + t.minute * 60 + t.second

def alimentacion():
    hora_inicio_alerta_alimentacion = None
    hora_inicio_alerta_alimentacionFINAL = None
    contador_alerta_alimentacion = 0
    fecha_inicio_alerta_alimentacion = None
    duracionAlertaTotal_alimentacion = 0 
    duracionAlertaTotal_alimentacion_en_minutos = 0


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
def otros_npt():
    print("primera detección: ", hora_primera_deteccion)

#Variables para Tormenta
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

def tormenta_npt():
    global tiempos_alerta, timer_alerta, contador_alerta, hora_inicio_alerta, fecha_inicio_alerta, duracionAlertaTotalBD, detectado_persona, tiempo_inicial_alerta
    global mensaje_emitido_alerta, duracionAlertaTotal_en_minutos, duracionAlertaTotalBD
    if alerta == "1**" or alerta == "2**":
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
        if duracionAlerta >= 30 and not mensaje_emitido_alerta and detectado_persona:
            print("Se detectaron personas a los 30 segundos!")
            mensaje_emitido_alerta = True

    # Lógica para cuando la alerta o alimentación terminan
    if (alerta != "1**" and alerta != "2**") and timer_alerta:
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
        

def parada_corta():
    print("Tarjet sin detecciones: ", hora_sin_detecciones)

if __name__ == "__main__":
    url2 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"
    url1 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"
 
    proceso_grabacion1 = multiprocessing.Process(
        target=grabar_camara, args=(url1, 120, "video_segmento1", model, procesar_frame_camaraBloque)
    )
    proceso_grabacion2 = multiprocessing.Process(
        target=grabar_camara, args=(url2, 120, "video_segmento2", model, procesar_frame_camaraPersonas)

    )                                                                                                                                                                           

    # hilo_guardarBD = threading.Thread(target=funcion_guardar_datos)
    # hilo_guardarBD.start()

    hilo_velocidad = threading.Thread(target=velocidad)
    hilo_velocidad.start()

    hilo_npt_tormenta = threading.Thread(target=npt_alerta)
    hilo_npt_tormenta.start()

    hilo_logica_personas = threading.Thread(target=logica_deteccion_personas)
    hilo_logica_personas.start()

    #Hilos de bases de datos

    hilo_obtener_bandera_full_services = threading.Thread(target=obtener_bandera_full_services)
    hilo_obtener_bandera_full_services.start()
    hilo_obtener_variables_desde_bd = threading.Thread(target=actualizar_variables_desde_bd)
    hilo_obtener_variables_desde_bd.start()
 
    proceso_grabacion1.start()
    proceso_grabacion2.start()
 
    proceso_grabacion1.join()
    proceso_grabacion2.join()
 
    print("Ambos procesos han terminado.")

