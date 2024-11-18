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
        print("Velocidad del bloque:::::: ", round(velocidad_bloque, 2))
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

def procesar_frame_camara1(frame, results):
    # Lógica específica para la cámara 1 (cuando la clase es 1)
    global segmentos, hora_inicio, altura_imagen, yc, yc_metros, yc_invertido, max_yc_invertido, min_yc_invertido 
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

    hilo_guardarBD = threading.Thread(target=funcion_guardar_datos)
    hilo_guardarBD.start()

    hilo_velocidad = threading.Thread(target=velocidad)
    hilo_velocidad.start()
 
    proceso_grabacion1.start()
    proceso_grabacion2.start()
 
    proceso_grabacion1.join()
    proceso_grabacion2.join()
 
    print("Ambos procesos han terminado.")



# Función principal
# if __name__ == "__main__":
#     url1 = "rtsp://admin:password@172.30.37.241:554/Streaming/Channels/102"
#     url2 = "rtsp://admin:password@172.30.37.231:554/Streaming/Channels/102"

#     # Crear procesos de grabación
#     proceso_grabacion1 = multiprocessing.Process(
#         target=grabar_camara, args=(url1, 120, "video_segmento1", model, procesar_frame_camara1)
#     )
#     proceso_grabacion2 = multiprocessing.Process(
#         target=grabar_camara, args=(url2, 120, "video_segmento2", model, procesar_frame_camara2)
#     )

#     # Iniciar procesos
#     proceso_grabacion1.start()
#     proceso_grabacion2.start()

#     # Iniciar hilos en el proceso principal
#     hilo_guardarBD = threading.Thread(target=funcion_guardar_datos)
#     hilo_guardarBD.start()

#     hilo_velocidad = threading.Thread(target=velocidad)
#     hilo_velocidad.start()

#     # Esperar a que los procesos terminen
#     proceso_grabacion1.join()
#     proceso_grabacion2.join()

#     # Finalizar hilos (opcional, en este caso seguirán corriendo indefinidamente)
#     hilo_guardarBD.join()
#     hilo_velocidad.join()

# if __name__ == "__main__":
#     model = None  # Asegúrate de inicializar tu modelo aquí

#     url1 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"
#     url2 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"

#     hilo_guardarBD = threading.Thread(target=funcion_guardar_datos)
#     hilo_guardarBD.start()

#     hilo_velocidad = threading.Thread(target=velocidad)
#     hilo_velocidad.start()

#     proceso_grabacion1 = multiprocessing.Process(
#         target=grabar_camara, args=(url1, 120, "video_segmento1", model, procesar_frame_camara1)
#     )
#     proceso_grabacion2 = multiprocessing.Process(
#         target=grabar_camara, args=(url2, 120, "video_segmento2", model, procesar_frame_camara2)
#     )

#     proceso_grabacion1.start()
#     proceso_grabacion2.start()

#     try:
#         proceso_grabacion1.join()
#         proceso_grabacion2.join()
#     except KeyboardInterrupt:
#         print("Finalizando todos los procesos...")
#         stop_event.set()
#         proceso_grabacion1.terminate()
#         proceso_grabacion2.terminate()
#         hilo_guardarBD.join()
#         hilo_velocidad.join()
#         print("Todos los procesos han terminado.")

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
