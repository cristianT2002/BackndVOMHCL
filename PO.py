import datetime
import time
import cv2
import threading
import multiprocessing


# Lock para sincronizar las variables globales
lock = threading.Lock()


def grabar_camara(url, duracion_segmento, nombre_segmento, modelo, procesar_frame_func, shared_ahora1, shared_ahora2):
    print(f"Iniciando grabación de cámara IP desde {url}...")

    while True:
        try:
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                print(f"Error: No se pudo abrir el stream de la cámara IP {url}. Reintentando en 5 segundos...")
                time.sleep(5)
                continue

            fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
            frames_por_segmento = fps * duracion_segmento
            contador_frames = 0
            start_time = time.time()

            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Advertencia: No se pudo capturar el frame de la cámara IP. Reintentando...")
                    time.sleep(1)
                    cap = cv2.VideoCapture(url)
                    continue

                results = modelo.predict(frame, imgsz=640, verbose=False)
                frame = procesar_frame_func(frame, results, shared_ahora1, shared_ahora2)

                cv2.imshow(f"Cámara IP {url}", frame)
                contador_frames += 1

                tiempo_esperado = start_time + (contador_frames / fps)
                tiempo_actual = time.time()
                if tiempo_actual < tiempo_esperado:
                    time.sleep(tiempo_esperado - tiempo_actual)

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


def procesar_frame_camaraPersonas(frame, results, shared_ahora1, shared_ahora2):
    global tiempo_deteccion_acumulado, tiempo_no_deteccion_acumulado
    global persona_detectada_actual, deteccion_confirmada, no_deteccion_confirmada

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

    with lock:
        if detectado_persona:
            if not persona_detectada_actual:
                persona_detectada_actual = True

            tiempo_deteccion_acumulado += tiempo_actual_segundos
            tiempo_no_deteccion_acumulado = 0

            if tiempo_deteccion_acumulado >= 3 and not deteccion_confirmada:
                deteccion_confirmada = True
                no_deteccion_confirmada = False
                shared_ahora1.value = datetime.datetime.now().strftime("%H:%M:%S")
                print("Detección confirmada a las:", shared_ahora1.value)
        else:
            if persona_detectada_actual:
                persona_detectada_actual = False

            tiempo_no_deteccion_acumulado += tiempo_actual_segundos
            tiempo_deteccion_acumulado = 0

            if tiempo_no_deteccion_acumulado >= 5 and not no_deteccion_confirmada:
                no_deteccion_confirmada = True
                deteccion_confirmada = False
                shared_ahora2.value = datetime.datetime.now().strftime("%H:%M:%S")
                print("No detección confirmada a las:", shared_ahora2.value)

    return annotated_frame


def logica_deteccion_personas(shared_ahora1, shared_ahora2):
    while True:
        with lock:
            print("Tarjet sin detecciones:", shared_ahora1.value)
            print("Hora primera detección:", shared_ahora2.value)
        time.sleep(1)


if __name__ == "__main__":
    manager = multiprocessing.Manager()
    shared_ahora1 = manager.Value('u', "")  # Compartido entre procesos
    shared_ahora2 = manager.Value('u', "")

    url1 = "rtsp://admin:4xUR3_2017@172.30.37.231:554/Streaming/Channels/102"
    url2 = "rtsp://admin:4xUR3_2017@172.30.37.241:554/Streaming/Channels/102"

    proceso_grabacion1 = multiprocessing.Process(
        target=grabar_camara,
        args=(url1, 120, "video_segmento1", model, procesar_frame_camaraPersonas, shared_ahora1, shared_ahora2),
    )
    proceso_grabacion2 = multiprocessing.Process(
        target=grabar_camara,
        args=(url2, 120, "video_segmento2", model, procesar_frame_camaraPersonas, shared_ahora1, shared_ahora2),
    )

    hilo_logica_personas = threading.Thread(target=logica_deteccion_personas, args=(shared_ahora1, shared_ahora2))
    hilo_logica_personas.start()

    proceso_grabacion1.start()
    proceso_grabacion2.start()

    proceso_grabacion1.join()
    proceso_grabacion2.join()

    print("Ambos procesos han terminado.")
