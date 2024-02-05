# Workplace Security System With Object Detection

### Use:

Run "SECAPP.py" to run the main program an open the interfaces.

### Description:

Workplace security system that utilizes computer vision and artificial intelligence for the detection of personal protective equipment (PPE) in construction sites, databases for registering accesses to the workplace, and IoT to activate an entrance mechanism.
*This version of the program runs only on windows 10 computers, for the Raspberry-pi 4 version go to: <raspberry>*

### Complete system visualization

![System](/ASSETS/IMGS/signals.png)

#### Files:

- "SECAPP.py": Main python script that runs the application that has the following functionalities:
  - Runs the Qt application by loading the UI files.
  - Makes the detections on live video on a secondary thread.
  - Connects to the database using the sqlite library to add registers of accesses.
  - Use the paho MQTT library to send the signal that activates the entrance mechanism.
- "detectorHelper.py": Contains functions from: [TFLite Model Maker](https://goo.gle/3ocbqmI) that help infer the detections using the "EPP.tflite" model by preprocessing the images and reading the labels.
- "PPE.tflite": lightweight Model of neural network trained with the datasets of personal protective equipment of more than 3,000 images that contained:
  1. Helmets
  1. Goggles
  1. Face masks
  1. Vests
  1. Gloves
  1. Protection boots
-DB_REGISTERS.db: Database that stores previous registers.
-DBSREGISTERS.py: Script that creates and initializes a database of registers.

#### Folders:

- IMGS: Contains all the images and icons that are shown in the graphic user interfaces.
- UIS: Contains the Qt UIs used for the application
  - "guiAccess.ui": UI that shows the live video of the detections and the EPP that is required to access.
  - "guiChoice.ui": UI that the supervisor or operator uses to select the required equipment to access the site.
  -"guiRegister.ui": UI that shows the table that is connected to the local database of registered accesses by configuration and date.
- sqlite3: Library to use sqlite functions that connect to the database.  
- SERVO_MQTT_ESP32_MICROPYTHON: Contains the files to be run in an ESP-32 microcontroller that connects to the broker and receives signals to activate the entrance mechanism controlled by a stepper motor.


#### Neural network model and training:

The model of neural network that was trained is the EfficientDetLite0, a lightweight model that offers a balance between precision and
performance to make detections.
The training was done on the Google Colab platform using model maker Jupiter notebook: [TFLite Model Maker](https://goo.gle/3ocbqmI) using a dataset of more than 3,000 images that contained PPE. This dataset was built by combining datasets from the internet and a custom one.
- Helmet: <https://data.mendeley.com/datasets/9rcv8mm682/1>
- Goggles: <https://universe.roboflow.com/burak_yahsi-hotmail-com/gozluk-ygktd/dataset/1>
- Face mask: <https://www.kaggle.com/datasets/andrewmvd/face-mask-detection>
- Vest: <https://universe.roboflow.com/tello-8ckdt/hazard-vest/browse?queryText=&pageSize=50&startingIndex=0&browseQuery=true>
- Gloves: <https://universe.roboflow.com/iit-delhi/gloves-custom/dataset/1> | <https://universe.roboflow.com/yerik-valiyev/gloves-ko2ap>
- Boots: Custom dataset only


The code for the inference was modified in the following ways:

- The detections are made on live video instead of a single image.
- The OpenCv library was used instead of PIL for the image processing part of the code.
- The detections are shown inside a graphic user interface in a secondary thread inside the application.

#### Qt applictation and interfaces

There are three user interfaces that make the entire program function and be manipulated by the user:

- UI for the selection of the personal protective equipment: This interface is shown when the program is run and it allows the operator or area supervisor to select and set the equipment that is necessary to access the site according to the safety measures to abide by. The UI was designed to be simple and easy to use, but also to provide flexibility of use cases for the user (Up to 63 possible combinations).

![GUI of PPE selection](/ASSETS/IMGS/GUI-selection.png)

- UI of the detections in real time: This UI has the purposes of:

  - Showing the PPE necessary to access the site according to what was specified by the supervisor (A silouette of a person wearing the equipment).
  - Showing the live video of detections of the PPE. When an element of the PPE is detected as being worn, a bounding box is drawn over that element with its name.

![GUI of live detections](/ASSETS/IMGS/GUI-livevideo.png)

- UI of the access registers: This UI consists of a table that shows all the registers of accesses to the site by day and configuration of EPP. The user can visualize the stored data by using the combo boxes that sort the data by date or EPP configuration.

![GUI of access registers](/ASSETS/IMGS/GUI-db.png)