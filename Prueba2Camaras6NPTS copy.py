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
# cronometro_activo = False  # Variable para controlar si el cronómetro ya está en ejecución
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




# ------------------------ Variables para YC posición y velocidad ----------------
yc = 0
yc_invertido = 0
yc_metros = 0
max_yc_invertido = 0  # Inicialmente no conocido
min_yc_invertido = 0  # Inicialmente no conocido
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


#BASES DE DATOS

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

                        # print("Comidas en BD: ", tiemposComidaFormateado)
                        isTiempos = True

                        if tiempos_comida == 'Tiempo_24':
                            isTiempos = False
            finally:
                conexion.close()
        except Exception as e:
            print(f"Error al consultar la base de datos: {e}")
        time.sleep(2)  # Esperar un segundo antes de la próxima consulta



def npt_alerta():
    global alerta, url
    
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


# -------------------------------------cronometro---------------------------------
def cronometro(hora):
    while True:
        try:
            # Simula obtener el tiempo desde un sistema remoto
            response = cam.System.time(method='get')
            local_time = response['Time']['localTime']
            # Extraer la hora sin la zona horaria (por ejemplo, quitar "+08:00")
            hora.value = str(local_time.split('T')[1].split('+')[0])  # Extraer solo HH:MM:SS
            # print(f"Hora actualizada: {hora.value}")  # Imprimir la hora limpia
        except KeyError as e:
            print(f"Error al acceder a la respuesta: {e}")
        except (TypeError, AttributeError) as e:
            print(f"Error de tipo o atributo: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        
        time.sleep(1)


#----------------------------Función de cronometro con metadata
def iniciar_cronometro_una_vez(hora, cronometro_activo):
    if not cronometro_activo.value:
        cronometro_activo.value = True
        hilo_cronometro = threading.Thread(target=cronometro, args=(hora,))
        hilo_cronometro.daemon = True  # Para que terlmine al cerrar el programa
        hilo_cronometro.start()


# -------------------------------------procesar_frame_camaras---------------------------------

def procesar_frame_camara1(frame, results, hora_primera_deteccion_segundos_almacenado, 
                           hora_sin_detecciones_segundos_almacenado, yc_metros, yc_invertido, 
                           max_yc_invertido, min_yc_invertido,
                           hora, cronometro_activo):
    # Lógica específica para la cámara 1 (cuando la clase es 1)
    global segmentos, hora_inicio, altura_imagen, yc 
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    min_y_min = float('inf')  # Inicialmente establecido en infinito
    # print("Cronometro en procesar_frame_camara1", cronometro_activo.value)
    # iniciar_cronometro_una_vez(hora, cronometro_activo)  # Iniciar el cronómetro antes de comenzar a grabar
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

                # if min_yc_invertido.value is not None and max_yc_invertido.value is not None and max_yc_invertido.value != min_yc_invertido.value:
                #     yc_metros.value = round(((yc_invertido.value - min_yc_invertido.value) * (Metros / (max_yc_invertido.value - min_yc_invertido.value))) ,2)
                # else:
                #     yc_metros.value = 0  # o 

                # print("yc_metros", yc_metros.value)


    return annotated_frame

def procesar_frame_camara2(frame, results, hora_primera_deteccion_segundos_almacenado, 
                           hora_sin_detecciones_segundos_almacenado, 
                           yc_metros, yc_invertido,
                           max_yc_invertido, min_yc_invertido,
                           hora, cronometro_activo):
   
    global ahora1, ahora2
    global tiempo_deteccion_acumulado, tiempo_no_deteccion_acumulado
    global persona_detectada_actual, deteccion_confirmada, no_deteccion_confirmada
    global hora_primera_deteccion_segundos, hora_sin_detecciones_segundos

    def obtener_segundos_actuales():
        ahora = datetime.datetime.now()
        return ahora.hour * 3600 + ahora.minute * 60 + ahora.second
 
    detectado_persona = False
    tiempo_actual_segundos = obtener_segundos_actuales()
    iniciar_cronometro_una_vez(hora, cronometro_activo)  # Iniciar el cronómetro antes de comenzar a grabar

    annotated_frame = frame.copy()

    # Trazas de depuración inicial
    # print("Hora primera detección confirmada en segundos sostenido:", hora_primera_deteccion_segundos_almacenado)
    # print("Hora sin detección confirmada en segundos sostenido:", hora_sin_detecciones_segundos_almacenado)

    for result in results:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box)
            if cls == 1 and conf >= 0.1:
                detectado_persona = True

                cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
    with lock:
        if detectado_persona:
            if not persona_detectada_actual:  # Primera detección en este ciclo
                hora_primera_deteccion_segundos = tiempo_actual_segundos
                persona_detectada_actual = True

            tiempo_deteccion_acumulado += tiempo_actual_segundos - hora_primera_deteccion_segundos
            hora_primera_deteccion_segundos = tiempo_actual_segundos
            tiempo_no_deteccion_acumulado = 0

            # Confirmar detección si se acumulan al menos 3 segundos
            if tiempo_deteccion_acumulado >= 3 and not deteccion_confirmada:
                deteccion_confirmada = True
                no_deteccion_confirmada = False
                ahora1 = datetime.datetime.now().strftime("%H:%M:%S")
                print("Detección confirmada a las:", ahora1)
                print("Hora primera detección confirmada en segundos:", hora_primera_deteccion_segundos)
                hora_primera_deteccion_segundos_almacenado.value = hora_primera_deteccion_segundos

            if tiempo_deteccion_acumulado >= 3 and not deteccion_confirmada:
                hora_primera_deteccion_segundos_almacenado.value = hora_primera_deteccion_segundos
                # print("hora_primera_deteccion_segundos_almacenado actualizado a:", hora_primera_deteccion_segundos_almacenado)

        else:
            if persona_detectada_actual:  # Primera no detección en este ciclo
                hora_sin_detecciones_segundos = tiempo_actual_segundos
                persona_detectada_actual = False

            tiempo_no_deteccion_acumulado += tiempo_actual_segundos - hora_sin_detecciones_segundos
            hora_sin_detecciones_segundos = tiempo_actual_segundos
            tiempo_deteccion_acumulado = 0

            # Confirmar no detección si se acumulan al menos 5 segundos
            if tiempo_no_deteccion_acumulado >= 5 and not no_deteccion_confirmada:
                no_deteccion_confirmada = True
                deteccion_confirmada = False
                ahora2 = datetime.datetime.now().strftime("%H:%M:%S")
                print("No detección confirmada a las:", ahora2)
                print("Hora sin detección confirmada segundos:", hora_sin_detecciones_segundos)
                hora_sin_detecciones_segundos_almacenado.value = hora_sin_detecciones_segundos

            if tiempo_no_deteccion_acumulado >= 5 and not no_deteccion_confirmada:
                hora_sin_detecciones_segundos_almacenado.value = hora_sin_detecciones_segundos
                # print("hora_sin_detecciones_segundos_almacenado actualizado a:", hora_sin_detecciones_segundos_almacenado)

    return annotated_frame

def grabar_camara(url, duracion_segmento, nombre_segmento, modelo, procesar_frame_func, 
                  hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado, 
                  yc_metros, yc_invertido,
                  max_yc_invertido, min_yc_invertido,
                  hora, cronometro_activo):
    
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
            out = cv2.VideoWriter(nombre_archivo, fourcc, fps, (width, height))
            start_time = time.time()
 
            while True:
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
 
                results = modelo.predict(frame, imgsz=640, verbose=False)
                frame = procesar_frame_func(frame, results, 
                                            hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado,
                                            yc_metros, yc_invertido,
                                            max_yc_invertido, min_yc_invertido,
                                            hora, cronometro_activo)
 
                cv2.imshow(f"Cámara IP {url}", frame)
                out.write(frame)
                contador_frames += 1
 
                tiempo_esperado = start_time + (contador_frames / fps)
                tiempo_actual = time.time()
                if tiempo_actual < tiempo_esperado:
                    time.sleep(tiempo_esperado - tiempo_actual)
 
                if contador_frames >= frames_por_segmento:
                    out.release()
                    print(f"Guardado {nombre_archivo}")
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
            if 'out' in locals() and out.isOpened():
                out.release()
            cv2.destroyAllWindows()
 

def logica_deteccion_personas(hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado):
    global tiempos_alerta, timer_alerta, contador_alerta, hora_inicio_alerta, fecha_inicio_alerta, duracionAlertaTotalBD, detectado_persona, tiempo_inicial_alerta
    global mensaje_emitido_alerta, duracionAlertaTotal_en_minutos, duracionAlertaTotalBD, alerta
  
    ultimo_contador_alerta = 0

    while True:
        with lock:

            # print("ultimo contador alerta: ", ultimo_contador_alerta)
            # print("Contador alerta: ", contador_alerta, fecha_inicio_alerta, hora_inicio_alerta, 0, 0, duracionAlertaTotalBD, 0, 0, 0, 'tormenta', nombrepozo)

            if contador_alerta > ultimo_contador_alerta:

                if duracionAlertaTotalBD <= 0.5:
                    contador_alerta -= 1
                else:
                    ultimo_contador_alerta = contador_alerta  # Actualiza el último valor del contador


            print("Hora sin detecciones:", hora_sin_detecciones_segundos_almacenado.value)
            print("Hora primera detección:", hora_primera_deteccion_segundos_almacenado.value)

            # alimentacion(hora_primera_deteccion_segundos, hora_sin_detecciones_segundos)
            tormenta_npt()
            alimentacion(hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado)
            gestionar_tiempos_npt(hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado)

        time.sleep(2)

#---------------- Funciones para NPTS ----------------


def tormenta_npt():
    global tiempos_alerta, timer_alerta, contador_alerta, hora_inicio_alerta, fecha_inicio_alerta, duracionAlertaTotalBD, detectado_persona, tiempo_inicial_alerta
    global mensaje_emitido_alerta, duracionAlertaTotal_en_minutos, duracionAlertaTotalBD, alerta  

    # print("Alerta en tormenta npt: ", alerta)

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

contador_paradas_cortas = 0
tiempos_paradas_cortas = []
contador_otros_npt = 0 
tiempos_otros_npt = []     

def gestionar_tiempos_npt(hora_sin_detecciones_segundos_almacenado, hora_primera_deteccion_segundos_almacenado):
    
    global contador_paradas_cortas, tiempos_paradas_cortas, contador_otros_npt, tiempos_otros_npt
    global isTiempos, alerta
    global target_time_1_segundos_almuerzo, target_time_2_segundos_almuerzo
    global target_time_1_segundos, target_time_2_segundos


    print("En gestionar tiempos NPT primera nueva detección: ", hora_primera_deteccion_segundos_almacenado.value)

    tiempo_actual = datetime.datetime.now()
    tiempo_sin_deteccion = hora_sin_detecciones_segundos_almacenado.value - hora_primera_deteccion_segundos_almacenado.value

    desayuno_inicio_segundos = 0 
    desayuno_final_segundos = 0
    almuerzo_inicio_segundos = 0
    almuerzo_final_segundos = 0
    en_horario_desayuno = None
    en_horario_almuerzo = None

    
    if alerta not in ["2**", "3**"]:  # Excluir tormentas nivel 2** y 3**
        if isTiempos:  # Excluir tiempos de alimentación
            desayuno_inicio_segundos = target_time_1_segundos
            desayuno_final_segundos = target_time_2_segundos
            almuerzo_inicio_segundos = target_time_1_segundos_almuerzo
            almuerzo_final_segundos = target_time_2_segundos_almuerzo

            en_horario_desayuno = (desayuno_inicio_segundos + 300) >= hora_sin_detecciones_segundos_almacenado.value >= (desayuno_inicio_segundos - 300) and (desayuno_final_segundos + 60) >= hora_primera_deteccion_segundos_almacenado.value >= (desayuno_final_segundos - 60)
            en_horario_almuerzo = (almuerzo_inicio_segundos + 300) >= hora_sin_detecciones_segundos_almacenado.value >= (almuerzo_inicio_segundos - 60) and (almuerzo_final_segundos + 60) >= hora_primera_deteccion_segundos_almacenado.value >= (almuerzo_final_segundos - 60)   

            # print("estoy acá")
            # print(f"Desayuno: {desayuno_inicio_segundos} ---| {hora_sin_detecciones_segundos_almacenado.value}  |---  {desayuno_final_segundos}, Almuerzo: {almuerzo_inicio_segundos} ---| {hora_sin_detecciones_segundos_almacenado.value} |--- {almuerzo_final_segundos}")

            if not en_horario_desayuno and not en_horario_almuerzo:
                if detectado_persona == False and tiempo_sin_deteccion > 0:
                    # Clasificar tiempo según duración
                    print("ahora estoy acá")
                    if tiempo_sin_deteccion <= 2 * 60:  # Parada corta
                        contador_paradas_cortas += 1
                        tiempos_paradas_cortas.append(tiempo_sin_deteccion)
                        print(f"Parada corta registrada: {tiempo_sin_deteccion // 60} minutos")
                    else:  # Otros NPT
                        contador_otros_npt += 1
                        tiempos_otros_npt.append(tiempo_sin_deteccion)
                        print(f"Otros NPT registrado: {tiempo_sin_deteccion // 60} minutos")


def time_to_seconds(t):
    """Convierte un objeto time a segundos desde la medianoche."""
    return t.hour * 3600 + t.minute * 60 + t.second

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
alerta_activada = False


def alimentacion(hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado):

    global tiempos_comida, tiemposComidaFormateado, isTiempos, target_time_1_segundos, target_time_2_segundos
    global target_time_1_segundos_almuerzo, target_time_2_segundos_almuerzo, tiempos_alerta_alimentacion
    global alerta_activada

    hora_inicio_alerta_alimentacion = None
    hora_inicio_alerta_alimentacionFINAL = None
    contador_alerta_alimentacion = 0
    fecha_inicio_alerta_alimentacion = None
    duracionAlertaTotal_alimentacion = 0 
    duracionAlertaTotal_alimentacion_en_minutos = 0
    timer_alerta_alimentacion = None


    # print("Tarjet sin detecciones:", hora_primera_deteccion_segundos_almacenado.value)
    # print("Hora primera detección:", hora_sin_detecciones_segundos_almacenado.value)
    # print("bandera isTiempos", isTiempos
    # print("Comidas en alimentación: ", tiemposComidaFormateado)



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
        # print("primera detección: ", hora_primera_deteccion_segundos_almacenado.value)
        # print("Tarjet sin detecciones: ", hora_sin_detecciones_segundos_almacenado.value)
        
        # #------------------------ Alerta de alimentación -------------------------
        # print("")
        # print("")
        # print("")

        # print(f"Inicio de la alerta de alimentación: {hora_inicio_alerta_alimentacion} ({fecha_inicio_alerta_alimentacion})")
        # duracionAlertaTotal_alimentacionBD = float("{:.2f}".format(duracionAlertaTotal_alimentacion_en_minutos))  # Formato como minutos con dos decimales
        # print(f"Alerta de alimentación {contador_alerta_alimentacion}: Duración = {duracionAlertaTotal_alimentacionBD} minutos, Fin = {hora_fin_alerta_alimentacion} ({fecha_fin_alerta_alimentacion})")

        # print("")
        # print("")
        # print("")

    if isTiempos == True:
        #------------------ Condicional para alimentacion desayuno ----------------
        if not alerta_activada and (target_time_1_segundos + 60) >= hora_sin_detecciones_segundos_almacenado.value >= (target_time_1_segundos - 60) and hora_primera_deteccion_segundos_almacenado.value < target_time_2_segundos:
            tiempo_inicial_alerta_alimentacion = time.time()
            hora_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_inicial_alerta_alimentacion))
            hora_inicio_alerta_alimentacionFINAL = datetime.datetime.now().strftime("%H:%M:%S")
            fecha_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d', time.localtime(tiempo_inicial_alerta_alimentacion))
            timer_alerta_alimentacion = True
            alerta_activada = True

        # Lógica para finalizar la alerta y contarla solo si ambas condiciones se cumplen
        elif alerta_activada and (target_time_1_segundos + 60) >= hora_sin_detecciones_segundos_almacenado.value >= (target_time_1_segundos - 60) and (target_time_2_segundos + 60) >= hora_primera_deteccion_segundos_almacenado.value >= (target_time_2_segundos - 60):
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

#--------------------- Condicional para alimentacion almuerzo ----------------
       #------------------------------------------------------
       # -----------------------------------------------------

        if not alerta_activada and (target_time_1_segundos_almuerzo + 60) >= hora_sin_detecciones_segundos_almacenado.value >= (target_time_1_segundos_almuerzo - 60) and hora_primera_deteccion_segundos_almacenado.value < target_time_2_segundos_almuerzo:
            tiempo_inicial_alerta_alimentacion = time.time()
            hora_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(tiempo_inicial_alerta_alimentacion))
            hora_inicio_alerta_alimentacionFINAL = datetime.datetime.now().strftime("%H:%M:%S")
            fecha_inicio_alerta_alimentacion = time.strftime('%Y-%m-%d', time.localtime(tiempo_inicial_alerta_alimentacion))
            timer_alerta_alimentacion = True
            alerta_activada = True

        # Lógica para finalizar la alerta y contarla solo si ambas condiciones se cumplen
        elif alerta_activada and (target_time_1_segundos_almuerzo + 60) >= hora_sin_detecciones_segundos_almacenado.value >= (target_time_1_segundos_almuerzo - 60) and (target_time_2_segundos_almuerzo + 60) >= hora_primera_deteccion_segundos_almacenado.value >= (target_time_2_segundos_almuerzo - 60):
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


if __name__ == "__main__":
    manager = multiprocessing.Manager()
    hora_primera_deteccion_segundos_almacenado = manager.Value('i', 0)
    hora_sin_detecciones_segundos_almacenado = manager.Value('i', 0)
    yc_metros = manager.Value('f', 0.0)
    yc_invertido = manager.Value('f', 0.0)
    max_yc_invertido = manager.Value('f', 0.0)
    min_yc_invertido = manager.Value('f', 0.0)
    hora = manager.Value('u', '')  # 'u' para string Unicode
    cronometro_activo = manager.Value('b', False)  # Para controlar el cronómetro


    url2 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"
    url1 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"
 
    proceso_grabacion1 = multiprocessing.Process(
        target=grabar_camara, args=(url1, 120, "video_segmento1", model, procesar_frame_camara1, 
                                    hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado, 
                                    yc_metros, yc_invertido,
                                    max_yc_invertido, min_yc_invertido,
                                    hora, cronometro_activo)
    )

    proceso_grabacion2 = multiprocessing.Process(
        target=grabar_camara, args=(url2, 120, "video_segmento2", model, procesar_frame_camara2, 
                                    hora_primera_deteccion_segundos_almacenado, hora_sin_detecciones_segundos_almacenado, 
                                    yc_metros, yc_invertido,
                                    max_yc_invertido, min_yc_invertido,
                                    hora, cronometro_activo)

    )   



    # hilo_velocidad2 = threading.Thread(target=velocidad2, args=(yc_metros, yc_invertido,
    #                                                          max_yc_invertido, min_yc_invertido, hora))
    # hilo_velocidad2.start()  



    # hilo_velocidad = threading.Thread(target=velocidad, args=(yc_metros, yc_invertido,
    #                                                          max_yc_invertido, min_yc_invertido))
    # hilo_velocidad.start()      



    # hilo_npt_tormenta = threading.Thread(target=npt_alerta)
    # hilo_npt_tormenta.start() 



    hilo_obtener_variables_desde_bd = threading.Thread(target=actualizar_variables_desde_bd)
    hilo_obtener_variables_desde_bd.start()


    hilo_logica_personas = threading.Thread(
        target=logica_deteccion_personas, args=(hora_primera_deteccion_segundos_almacenado, 
                                                hora_sin_detecciones_segundos_almacenado)
    )
    hilo_logica_personas.start() 

    proceso_grabacion1.start()
    proceso_grabacion2.start()
 
    proceso_grabacion1.join()
    proceso_grabacion2.join()
 
    print("Ambos procesos han terminado.")

