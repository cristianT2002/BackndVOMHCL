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
 
# cam = Client('http://172.30.37.241', 'admin', '4xUR3_2017')

 
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


# ---------------------------- Función para NPT POR TORMENTA --------------------
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
        # print("Velocidad del bloque", velocidad_bloque)
        time.sleep(4)

def procesar_frame_camara1(frame, results):
    # Lógica específica para la cámara 1 (cuando la clase es 1)
    global segmentos, hora_inicio, altura_imagen, yc, yc_metros, yc_invertido, max_yc_invertido, min_yc_invertido 
    max_y_min = 0  # Variable para mantener el máximo y_min observado
    min_y_min = float('inf')  # Inicialmente establecido en infinito

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

                yc_invertido = altura_imagen - yc  # Invirtiendo el valor de yc
                min_yc_invertido = altura_imagen - max_y_min  
                max_yc_invertido = altura_imagen - min_y_min 
    
                if min_yc_invertido is not None and max_yc_invertido is not None and max_yc_invertido != min_yc_invertido:
                    yc_metros = round(((yc_invertido - min_yc_invertido) * (Metros / (max_yc_invertido - min_yc_invertido))) ,2)
                else:
                    yc_metros = 0  # o 

                print("yc_metros", yc_metros)

    return annotated_frame
 
def procesar_frame_camara2(frame, results):
    # Lógica específica para la cámara 2 (cuando la clase es 0)
    annotated_frame = frame.copy()
    for result in results:
        for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
            x_min, y_min, x_max, y_max = map(int, box)
            if cls == 0 and conf >= 0.1:
                cv2.circle(annotated_frame, (int((x_min + x_max) / 2), int((y_min + y_max) / 2)), 5, (255, 0, 0), -1)
                print(f"[Cámara 2] Detectado objeto clase 0 en ({x_min}, {y_min})")
    return annotated_frame
 
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

def grabar_camara(url, duracion_segmento, nombre_segmento, modelo, procesar_frame_func):
    print(f"Iniciando grabación de cámara IP desde {url}...")

    # iniciar_cronometro_una_vez()  # Iniciar el cronómetro antes de comenzar a grabar
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
                frame = procesar_frame_func(frame, results)
 
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
 

if __name__ == "__main__":
    url1 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"
    url2 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"
 
    proceso_grabacion1 = multiprocessing.Process(
        target=grabar_camara, args=(url1, 120, "video_segmento1", model, procesar_frame_camara1)
    )
    proceso_grabacion2 = multiprocessing.Process(
        target=grabar_camara, args=(url2, 120, "video_segmento2", model, procesar_frame_camara2)

    )
 
    proceso_grabacion1.start()
    proceso_grabacion2.start()
 
    proceso_grabacion1.join()
    proceso_grabacion2.join()
 


    hilo_guardarBD = threading.Thread(target=funcion_guardar_datos)
    hilo_guardarBD.start()

    hilo_velocidad = threading.Thread(target=velocidad)
    hilo_velocidad.start()
    print("Ambos procesos han terminado.")



# if __name__ == "__main__":
#     # Inicializa el modelo (sustituye esta línea con la inicialización de tu modelo real)
#     model = None  # Asegúrate de inicializar tu modelo aquí

#     # URLs de las cámaras
#     url1 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"
#     url2 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"

#     # Hilos
#     hilo_guardarBD = threading.Thread(target=funcion_guardar_datos)
#     # hilo_guardarBD.start()

#     hilo_velocidad = threading.Thread(target=velocidad)
#     hilo_velocidad.start()

#     # Procesos
#     proceso_grabacion1 = multiprocessing.Process(
#         target=grabar_camara, args=(url1, 120, "video_segmento1", model, procesar_frame_camara1)
#     )
#     proceso_grabacion2 = multiprocessing.Process(
#         target=grabar_camara, args=(url2, 120, "video_segmento2", model, procesar_frame_camara2)
#     )

#     # Inicia los procesos
#     proceso_grabacion1.start()
#     proceso_grabacion2.start()

#     try:
#         # Espera que los procesos terminen
#         proceso_grabacion1.join()
#         proceso_grabacion2.join()
#     except KeyboardInterrupt:
#         print("Finalizando todos los procesos y hilos...")

#         # Señal para detener hilos y procesos
#         stop_event.set()

#         # Termina los procesos
#         proceso_grabacion1.terminate()
#         proceso_grabacion2.terminate()

#         # Espera que los hilos terminen
#         hilo_guardarBD.join()
#         hilo_velocidad.join()

#     finally:
#         print("Programa finalizado.")
