from PyQt5 import uic, QtWidgets
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPixmap, QIcon
import sys
from PyQt5.QtCore import QThread
import time
import paho.mqtt.client as mqtt
import sqlite3
from datetime import date

from detectorHelper import *
from absl import logging

logging.set_verbosity(logging.ERROR)


# //////////////////////////////// [INITIAL CONFIGURATION] /////////////////////////////////// #

# Detections threshold (0.5 recommended)
DETECTION_THRESHOLD = 0.5

# tflite trained model
TFLITE_MODEL_PATH = "PPE.tflite" 

# Camera to use (0 for integrated webcam, 1 for USB camera)
CAMERA_NUM = 0

# Activate stepper motor mechanism and MQTT communication?
MQTT_MECHANISM = False

# IP of raspberry or MQTT broker 
BROKER = '192.168.1.4'  

# ////////////////////////////////////////////////////////////////////////////////////////////////// #


# Qt app initialization
app = QApplication([])
guiSelection = uic.loadUi('UIS/guiChoice.ui')
guiAccess = uic.loadUi('UIS/guiAccess.ui')
guiRegisters = uic.loadUi('UIS/guiRegister.ui')

# Dictionary that links the checkboxes of the UI and the images to the items keywords
checkBoxes = {"casco" : (guiSelection.checkCasco, guiSelection.imgCasco, guiAccess.pcasco), "lentes" : (guiSelection.checkLentes, guiSelection.imgLentes, guiAccess.plentes),
               "cubrebocas" : (guiSelection.checkCubre, guiSelection.imgCubre, guiAccess.pcubre), "chaleco" : (guiSelection.checkChaleco, guiSelection.imgChaleco, guiAccess.pchaleco),
               "guantes" : (guiSelection.checkGuantes, guiSelection.imgGuantes, guiAccess.pguantes1, guiAccess.pguantes2), "botas" : (guiSelection.checkBotas, guiSelection.imgBotas, guiAccess.pbotas1, guiAccess.pbotas2)}

# Dict that links the coded words to the items themselves
codesDB = {"casco" : 'Ca', "lentes" : 'Le', "cubrebocas" : 'Cu', "chaleco" : 'Ch', "guantes" : 'Gu', "botas" : 'Bo'}

# Dict used to "translate the labels to spanish"
spanglish = {'helmet' : 'casco', 'without_mask' : 'sin_cubrebocas', 'with_mask' : 'cubrebocas',
              'glasses': 'lentes', 'Gloves' : 'guantes', 'head' : 'cabeza', 'mask_weared_incorrect' : 'cubreb_mal_puesto', 
              'person' : 'persona', 'vest' : 'chaleco', 'boots' : 'botas'}

# Colors of bounding boxes of each item
# Helmet: White, Goggles: yellow, Face mask: blue, Vest: purple, Gloves: orange, Boots: red, rest: gray
colorOfDetections = {'helmet' : (255,255,255), 'without_mask' : (105,105,105), 'with_mask' : (30,144,255), 'glasses': (255,255,0),
                      'Gloves' : (255,140,0), 'head' : (105,105,105), 'mask_weared_incorrect' : (105,105,105), 'person' : (105,105,105),
                        'vest' : (148,0,211), 'boots' : (130,20,211)}


# List that stores the current selected items
items = []
# List that stores the items detected in the current frame
listDet = []
# Only the detected elements non repeated
finalDet = []

# Variable that indicates if the manual button was clicked to activate the entrance mechanism
manual = None

###################################################| GUIS FUNCTIONS |#########################################################

# Checks the selected items visually (coloring of the items in the UI)
def selecItem(item):
    if checkBoxes[item][0].isChecked() == True:
        pixmap = QPixmap(f"IMGS/{item}cicon.png")
        checkBoxes[item][1].setPixmap(pixmap)
    else:
        pixmap = QPixmap(f"IMGS/{item}dicon.png")
        checkBoxes[item][1].setPixmap(pixmap)

# Adds and saves the selected items inside a list
def guardarSeleccion():
    global items
    items.clear()
    for key in checkBoxes:
        if checkBoxes[key][0].isChecked():
            items.append(key)
    
    print(items)


# Opens the live detections UI if there is at least one element selected and sorts the items by alphabetical order
def showAccess():
    global items
    if items:
        iniciar_hilo()
        items.sort()
        showElements()
        guiAccess.show()
        guiSelection.hide()
    else:
        pass
    
# Show the selected PPE items in the interface as visual aid (human silhouette in the live detections UI)
def showElements():
    for item in items:
        if item == 'casco':
            pixmap = QPixmap(f"IMGS/cascocicon.png")
            checkBoxes[item][2].setPixmap(pixmap)
        elif item == 'lentes':
            pixmap = QPixmap(f"IMGS/lentesciconsimple.png")
            checkBoxes[item][2].setPixmap(pixmap)
        elif item == 'cubrebocas':
            pixmap = QPixmap(f"IMGS/cubrebgrandesimplecolor.png")
            checkBoxes[item][2].setPixmap(pixmap)
        elif item == 'chaleco':
            pixmap = QPixmap(f"IMGS/chalecocicon2.png")
            checkBoxes[item][2].setPixmap(pixmap)
        else:
            pixmap1 = QPixmap(f"IMGS/{item}1.png")
            pixmap2 = QPixmap(f"IMGS/{item}2.png")
            checkBoxes[item][2].setPixmap(pixmap1)
            checkBoxes[item][3].setPixmap(pixmap2)


# Clears list of selected items and goes back to the PPE selection UI
def showSel():
    terminar_hilo()
    for item in items:
        if item == 'casco':
            checkBoxes[item][2].clear()
        elif item == 'lentes':
            checkBoxes[item][2].clear()
        elif item == 'cubrebocas':
            checkBoxes[item][2].clear()
        elif item == 'chaleco':
            checkBoxes[item][2].clear()
        else:
            checkBoxes[item][2].clear()
            checkBoxes[item][3].clear()

    guiSelection.show()
    guiAccess.close()

# Open selection UI and closes registers UI
def showSel2():
   guiSelection.show()
   guiRegisters.close()

# Opens the registers UI with up-to-date registers
def showRegistros():
   DELETE()
   cargarRegistros()
   loadCombos()
   guiRegisters.show()
   guiSelection.hide()

# Converts the image to pixmap to be shown in the UI
def colocar_imagenLabel(label, image):
    alto = 0
    ancho = 0
    canal = 0
    qImage = None

    if len(image.shape)==3:    # RGB image
        alto, ancho, canal = image.shape
        paso = canal * ancho
        qImage = QImage(image.data, ancho, alto, paso, QImage.Format_RGB888)
    else:                      # Grayscale image
        canal = 1
        alto, ancho = image.shape
        qImage = QImage(image.data, ancho, alto, ancho, QImage.Format_Grayscale8)
    label.setPixmap(QPixmap.fromImage(qImage))


# Rescale the image to the correct aspect ratio
def ImagenReescalado(imagen):
    imagen_alto, imagen_largo, canales = imagen.shape
    alto_label = 571
    largo_label = 831
    nuevo_alto = 0
    nuevo_largo = 0

    # Get the largest dimension of the image
    if imagen_alto >= imagen_largo:
        nuevo_alto = alto_label
        proporcion = imagen_largo / imagen_alto
        nuevo_largo = int(alto_label * proporcion)
    else:
        nuevo_largo = largo_label
        proporcion = imagen_alto / imagen_largo
        nuevo_alto = int(largo_label * proporcion)

    # Reescale the image and return it
    imagen_labelO = cv2.resize(imagen, (nuevo_largo, nuevo_alto), interpolation=cv2.INTER_CUBIC)
    return imagen_labelO

##########################################################################################################################

# Encode the selected items (first 2 letters of each item: Ca/Le/Cu)
def makeCodes():
    global codesDB, items
    codedItems = ' '
    for element in items:
        codedItems += '/' + codesDB[element]
    codedItems = codedItems[2:]
    
    return codedItems

def abrirM():
    global manual
    manual = 1
    

###################################################| DATABASE FUNCTIONS |###########################################################
    
# Add a new access register to the database
def addReg(con_o_sin):

    try:
        conn = sqlite3.connect('DB_REGISTERS.db')
        cursor = conn.cursor()
        current_date = date.today()
        current_config = makeCodes()
        day = current_date.strftime("%d/%m/%Y")
    
    except sqlite3.Error as e:
        print(e)
        sys.exit()

    cursor.execute("SELECT Num_dia, fecha, config FROM registros")
    valores = cursor.fetchall()
    idcount = len(valores)
    
    if idcount >= 1:  

        for values in valores:
            # If a register is found with the same date and config as the new one, get the row number
            if day == values[1] and current_config == values[2]:
                num = values[0]
                break
            else:
                num = None

        # If a register equal to the new information is found, the counter is updated
        if num is not None:
            with conn:
                    cur = conn.cursor()
                    query1 = f"SELECT {con_o_sin} FROM registros WHERE Num_dia=?"
                    result1 = cur.execute(query1, (num,)) 
                    value_epp, = result1.fetchone()
                    new_value_epp = value_epp + 1

                    cur.execute('SELECT * FROM registros')
                    q = f'UPDATE registros SET {con_o_sin} = ? WHERE Num_dia=?'
                    datos1 = (new_value_epp, num)
                    
                    cur.execute(q,datos1)

        # If no register was found, a new row is added
        else:
            with conn:
                    if con_o_sin == 'con_epp':
                        cur = conn.cursor()
                        sql1 = '''INSERT INTO registros(fecha, config, con_epp, sin_epp)VALUES(?,?,?,?)'''
                        cur.execute(sql1,(day, current_config, 1, 0))
                        conn.commit()
                    else:
                        cur = conn.cursor()
                        sql1 = '''INSERT INTO registros(fecha, config, con_epp, sin_epp)VALUES(?,?,?,?)'''
                        cur.execute(sql1,(day, current_config, 0, 1))
                        conn.commit()

# Loads the possible filters (comboBoxes)
def loadCombos():

    guiRegisters.comboFechas.clear()
    guiRegisters.comboConf.clear()
    guiRegisters.comboFechas.addItem('  Todas las fechas')
    guiRegisters.comboConf.addItem(' Todas las configuraciones')
    guiRegisters.comboFechas.setItemIcon(0, QIcon('IMGS/calendar.png'))
    guiRegisters.comboConf.setItemIcon(0, QIcon('IMGS/2checked.png'))

    try:
        conn = sqlite3.connect('DB_REGISTERS.db')
        cursor = conn.cursor()
       
    except sqlite3.Error as e:
        print(e)

    cursor.execute("SELECT Num_dia, fecha, config FROM registros")
    valores = cursor.fetchall()
    idcount = len(valores)
    fechasl = []
    fechasF = []
    confl = []
    confF = []
    if idcount >= 1:
        for reg in valores:
            fechasl.append(reg[1])
            confl.append(reg[2])

        [fechasF.append(x) for x in fechasl if x not in fechasF]
        [confF.append(x) for x in confl if x not in confF]
        fechasF.reverse()
        confF.reverse()

        guiRegisters.comboFechas.addItems(fechasF)
        guiRegisters.comboConf.addItems(confF)
    else: 
        print('No hay registros')

    fechasl.clear()
    confl.clear()
    fechasF.clear()
    confF.clear()

# Function that filters results when one, two or no filter was selected
def filterDB():
    fecha = guiRegisters.comboFechas.currentText()
    conf = guiRegisters.comboConf.currentText()
    
    if fecha == '  Todas las fechas' and conf == ' Todas las configuraciones':
        DELETE()
        cargarRegistros()
    elif fecha != '  Todas las fechas' and conf == ' Todas las configuraciones':
        DELETE()
        cargarFiltrados(1, fecha, conf)
    elif fecha == '  Todas las fechas' and conf != ' Todas las configuraciones':
        DELETE()
        cargarFiltrados(2, fecha, conf) 
    else:
        DELETE()
        cargarFiltrados(3, fecha, conf)

# Loads the filtered data from the database into the UI table
def cargarFiltrados(SEL, FECHA, CONF):

    conexion = sqlite3.connect('DB_REGISTERS.db')    
    cursor = conexion.cursor()
    if SEL == 1:
        val = cursor.execute(f"SELECT * FROM registros WHERE fecha = '{FECHA}'")
    elif SEL == 2: 
        val = cursor.execute(f"SELECT * FROM registros WHERE config = '{CONF}'")
    else:
        val = cursor.execute(f"SELECT * FROM registros WHERE fecha = '{FECHA}' AND config = '{CONF}'")

    registros = val.fetchall()
    for no_fila, registro in enumerate(registros):
            guiRegisters.tableRegistros.insertRow(no_fila)
            for no_columna, dato in enumerate(registro):
                tabla = QtWidgets.QTableWidgetItem(str(dato))
                guiRegisters.tableRegistros.setItem(no_fila, no_columna, tabla)

# Load all the registers from the database
def cargarRegistros():
    conexion = sqlite3.connect('DB_REGISTERS.db')    
    cursor = conexion.cursor()
    val = cursor.execute("SELECT * FROM registros")
    registros = val.fetchall()
    for no_fila, registro in enumerate(registros):
            guiRegisters.tableRegistros.insertRow(no_fila)
            for no_columna, dato in enumerate(registro):
                tabla = QtWidgets.QTableWidgetItem(str(dato))
                guiRegisters.tableRegistros.setItem(no_fila, no_columna, tabla)

# Function that clears the contents of the table of the data visualization of the interface
def DELETE():
    guiRegisters.tableRegistros.clearContents()

################################################################################################################################

# Activate the entrance mechanism with the actuator by sending the MQTT signal and changes the message of "Access granted" or "Access
# without PPE" for 5 seconds
def abrirMec(con):
    global MQTT_MECHANISM
    # Activar mecanismo si la variable es True
    if MQTT_MECHANISM:
        publish()

    terminar_hilo()

    if con == True:
        guiAccess.label_3.setStyleSheet("background-color: green; color: white")
        guiAccess.label_3.setText('Adelante')
    else:
        guiAccess.label_3.setStyleSheet("background-color: yellow; color: red")
        guiAccess.label_3.setText('Acceso sin equipo')

    for i in range(4, -1, -1):
        time.sleep(1)
        guiAccess.contador.display(i)

    guiAccess.contador.display(5)
    guiAccess.label_3.setStyleSheet("background-color: red; color: white")
    guiAccess.label_3.setText('Mire al frente')
    iniciar_hilo()


# State of a secondary thread running
hilo_corriendo = False

# Functions for starting and stopping the thread of the live detections and interface
def iniciar_hilo():
    global hilo_corriendo
    hilo_corriendo = True
    hilo1.start()

def terminar_hilo():
    global hilo_corriendo
    hilo_corriendo = False
    hilo1.exit()



# MAIN FUNCTIONING OF THE PROGRAM: CAPTURING AND SHOWING THE DETECTIONS IN THE INTERFACE INSIDE A SEPARATE THREAD
class hilo_camara(QThread):

    def run(self):
        global procesar_frame, clickeando, image, hilo_corriendo, manual
        while True:
            ret, image = camara.read()
            
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            imagep = cv2.resize(image,(640,640),interpolation=cv2.INTER_AREA)
            detector = ObjectDetector(model_path=TFLITE_MODEL_PATH, options=options)
            # Run object detection estimation using the model.
            detections = detector.detect(imagep)
            # Draw keypoints and edges on input image
            image_np = visualize(imagep, detections)
            cv2.putText(image_np, 'Detecciones', org=(10,40), fontFace=cv2.FONT_HERSHEY_DUPLEX, fontScale=1.3, color=(70,130,180), thickness=2)
            
            # Show the detection result
            if procesar_frame == True:
                colocar_imagenLabel(guiAccess.cam, image_np)
                procesar_frame = False
            else:
                image = ImagenReescalado(image_np)
                colocar_imagenLabel(guiAccess.cam, image_np)
        
            global finalDet, items, spanglish, spa, listDet
            spa = list()
            for item in finalDet:
                spa.append(spanglish[item])
            spa.sort()

            # ACTIVATE ACCESS MECHANISM AND ADD THE NEW REGISTER ONLY IF THE REQUIRED PPE IS DETECTED
            if spa == items:
                abrirMec(True)
                addReg('con_epp')

            # ACTIVATION OF MECHANISM AND REGISTER WITHOUT PPE WITH MANUAL BUTTON
            if manual is not None:
                abrirMec(False)
                addReg('sin_epp')
                manual = None

            finalDet.clear()
            listDet.clear()
      
            

camara = cv2.VideoCapture(CAMERA_NUM)  # (1, cv2.CAP_DSHOW)
camara.set(cv2.CAP_PROP_BUFFERSIZE, 1)
procesar_frame = False
image = None

# Initialize thread without RUNNING IT
hilo1 = hilo_camara() 


# Connect to MQTT broker to send the signal of the stepper motor mechanism (with MECANISMO_MQTT = True)
def publish():
    client = mqtt.Client('RASPB') # Identificador de cliente que se conecta (lo que sea)
    # client.username_pw_set('user', 'password')  # User and password (if configured)
    client.connect(BROKER, port=1883) # Broker y puerto
    client.publish('SERVO', payload= 'open', qos=0, retain=False) # Tópico y mensaje que se envía


_MARGIN = 10  # pixels
_ROW_SIZE = 10  # pixels
_FONT_SIZE = 1
_FONT_THICKNESS = 1
_TEXT_COLOR = (0, 0, 255)  # red

# PROCESS THE CAPTURED FRAME WITH THE DETECTIONS MODEL AND SHOWS THE DETECTIONS
def visualize(
    image: np.ndarray,
    detections: List[Detection],
) -> np.ndarray:
  """Draws bounding boxes on the input image and return it.
  Args:
    image: The input RGB image.
    detections: The list of all "Detection" entities to be visualize.
  Returns:
    Image with bounding boxes.
  """
  global listDet, finalDet
  listDet.clear()
  for detection in detections:
    
    # Draw label and score
    category = detection.categories[0]
    class_name = category.label
    probability = round(category.score, 2)
    result_text = class_name + ' (' + str(probability) + ')'
    text_location = (_MARGIN + detection.bounding_box.left,
                        _MARGIN + _ROW_SIZE + detection.bounding_box.top)
    cv2.putText(image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)

    # Draw bounding_box
    start_point = detection.bounding_box.left, detection.bounding_box.top
    end_point = detection.bounding_box.right, detection.bounding_box.bottom
    # Different color of bounding box for each item
    cv2.rectangle(image, start_point, end_point, colorOfDetections[class_name], 3)

    finalDet.clear()
    listDet.append(class_name)
    [finalDet.append(x) for x in listDet if x not in finalDet] 

    # Return image with bounding boxes if PPE was detected
  return image


# Load detections model
options = ObjectDetectorOptions(
      num_threads=1,
      score_threshold=DETECTION_THRESHOLD,
)
detector = ObjectDetector(model_path=TFLITE_MODEL_PATH, options=options)


# Events triggered by GUIS' buttons
guiSelection.checkCasco.stateChanged.connect(lambda: selecItem('casco'))
guiSelection.checkLentes.stateChanged.connect(lambda: selecItem('lentes'))
guiSelection.checkCubre.stateChanged.connect(lambda: selecItem('cubrebocas'))
guiSelection.checkChaleco.stateChanged.connect(lambda: selecItem('chaleco'))
guiSelection.checkGuantes.stateChanged.connect(lambda: selecItem('guantes'))
guiSelection.checkBotas.stateChanged.connect(lambda: selecItem('botas'))
guiSelection.guardarSel.clicked.connect(guardarSeleccion)
guiSelection.toAccess.clicked.connect(showAccess)
guiSelection.actionRegistros.triggered.connect(showRegistros)
guiAccess.bRegresar.clicked.connect(showSel)
guiAccess.Abrir.clicked.connect(abrirM)
guiRegisters.regresar.clicked.connect(showSel2)
guiRegisters.comboFechas.currentIndexChanged.connect(filterDB)
guiRegisters.comboConf.currentIndexChanged.connect(filterDB)

# Open GUI of equipment configuration
guiSelection.show()

# Run Qt app
app.exec()


