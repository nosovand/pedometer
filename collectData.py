import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
import pickle
import serial
from ctypes import Structure, c_float, sizeof
from pure_sklearn.map import convert_estimator
import collections
import itertools
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import os.path
import csv
import time
import threading

class DataPoint(Structure):
    _pack_ = 1
    _fields_ = [
        ("acc_vector", c_float)
    ]

connected = False
port = '/dev/cu.usbmodem0004402251091'
baud = 115200

try:
    serial_port = serial.Serial(port, baud)
    serial_port.flushInput()
    connected = True
except:
    print("Unable to open COM port")

#variables
sampleQueueSize = 100
numberOfSamples = 10
readingSteps = 0
readingNoise = 0
currentSample = 0.0
sampleSequence = []
currentSequence = 0
fileExists = 0
sampleQueue = collections.deque([1.0]*sampleQueueSize, sampleQueueSize)
finalValues = collections.deque([1.0]*sampleQueueSize, sampleQueueSize)




#create dataset file, if it does not exist
fileExists = os.path.exists('pedometerDataset.csv')
if fileExists != True:
    with open('pedometerDataset.csv', 'w', encoding='UTF8', newline='') as f1:
        writer = csv.writer(f1)
        header = []
        for x in range(sampleQueueSize):
            header.extend(["Sample " + str (x + 1)])
        header.extend(["Step/No step"])
        writer.writerow(header)

#create graphical interface
app = QApplication([])
dlg = QDialog()
layout = QVBoxLayout()
label = QLabel(dlg)
label.setText("Start new sampling sequence\n")
label2 = QLabel(dlg)
label2.setText("Enter number of samples:")
addStepsButton = QPushButton("Add Steps")
addNoiseButton = QPushButton("Add Noise")
addButton = QPushButton("Save Samples")
retakeButton = QPushButton("Retake")
inputLine = QLineEdit(dlg)
layout.addWidget(label)
layout.addWidget(addStepsButton)
layout.addWidget(addNoiseButton)
layout.addWidget(label2)
layout.addWidget(inputLine)
layout.addWidget(addButton)
addButton.hide()
layout.addWidget(retakeButton)
retakeButton.hide()

dlg2 = QDialog()
layout2 = QVBoxLayout()
label3 = QLabel(dlg2)
label3.setText("View samples")
label4 = QLabel(dlg2)
label4.setText(" ")
nextButton = QPushButton("next")
prevButton = QPushButton("prev")
removeButton = QPushButton("remove")
layout2.addWidget(label3)
layout2.addWidget(label4)
layout2.addWidget(nextButton)
layout2.addWidget(prevButton)
layout2.addWidget(removeButton)

#buttons' functions
def readSamples():
    global sampleSequence, sampleQueue, finalValues
    sampleSequence = []
    sampleQueue = collections.deque([1.0]*sampleQueueSize, sampleQueueSize)
    finalValues = collections.deque([1.0]*sampleQueueSize, sampleQueueSize)

    steps = 0

    #step decision factors
    stepPhaseThreshhold = 1.4 #if acceleration is bigger than this threshhold, we assume a step started
    stepPhase = 0 # = 1 if stepPhaseThreshhold was crossed and step is currently happenning
    endStepThreshhold = 1.1 #if acceleration gets smaller than endStepThreshhold, we assume the step stopped
    stepStopped = 0
    bonusSamples = 5 #samples to collect after step stopped
    bonusSamplesCollected = 0 #current number of bonus samples collected

    filterCoeff = [-0.0005 ,  -0.0019  , -0.0043 ,  -0.0074 ,  -0.0095 ,  -0.0070  ,  0.0036  ,  0.0246  ,  0.0553  ,  0.0913  ,  0.1257  ,  0.1504,  0.1595  ,  0.1504 ,   0.1257 ,   0.0913  ,  0.0553  ,  0.0246  ,  0.0036  , -0.0070 ,  -0.0095 ,  -0.0074 ,  -0.0043 ,  -0.0019, -0.0005]


    currentSample = 0.0
    serial_port.flushInput()
    serial_port.flushOutput()
    time.sleep(0.1)
    while len(sampleSequence) < numberOfSamples:
        sampleQueue.popleft()
        finalValues.popleft()

        lastSample = currentSample
        currentSample = 0.0

        byte = serial_port.read(sizeof(DataPoint))
        buffer = bytearray(byte)
        Point = DataPoint.from_buffer(buffer)

        sampleQueue.append(Point.acc_vector)
        for index, coeff in enumerate(filterCoeff):
            currentSample = currentSample + coeff * sampleQueue[sampleQueueSize-1-index]
        finalValues.append(currentSample)
        #algorithm for detecting steps
        if currentSample > stepPhaseThreshhold and stepPhase == 0:
            stepPhase = 1
        if stepPhase == 1 and currentSample < endStepThreshhold:
            stepStopped = 1
            stepPhase = 0
        if stepStopped == 1 and bonusSamplesCollected <= bonusSamples:
            bonusSamplesCollected = bonusSamplesCollected + 1;
        if stepStopped == 1 and bonusSamplesCollected == bonusSamples:
            bonusSamplesCollected = 0
            stepStopped = 0
            steps = steps + 1
            print("Samples: ", steps)
            #add step
            sampleSequence.append(list(finalValues))
            y0 = np.array(sampleSequence[-1])
            line0.set_ydata(y0)
            ax.set_ylim(np.min([y0]), np.max([y0]))
            fig.canvas.draw()
            fig.canvas.flush_events()

def addSteps():
    global readingSteps, sampleSequence, numberOfSamples
    if inputLine.text().isdigit() and int(inputLine.text()) > 0:
        numberOfSamples = int(inputLine.text())
        addStepsButton.hide()
        addNoiseButton.hide()
        label2.hide()
        inputLine.hide()
        addButton.show()
        retakeButton.show()
        readingSteps = 1
        sampleSequence = []
        label.setText("Recording Steps")
        readSamples()
        currentSequence = 0
        label4.setText("%d/%d" %(1,len(sampleSequence)))
        #draw first sample after reading completed
        y0 = np.array(sampleSequence[0])
        line0.set_ydata(y0)
        ax.set_ylim(np.min([y0]), np.max([y0]))
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.show()
        dlg2.show()
    else:
        label2.setText("Enter valid number of samples:")

def addNoise():
    global readingNoise, sampleSequence, numberOfSamples, currentSequence
    if inputLine.text().isdigit() and int(inputLine.text()) > 0:
        numberOfSamples = int(inputLine.text())
        addStepsButton.hide()
        addNoiseButton.hide()
        label2.hide()
        inputLine.hide()
        addButton.show()
        retakeButton.show()
        readingNoise = 1
        sampleSequence = []
        label.setText("Recording Noise")
        readSamples()
        currentSequence = 0
        label4.setText("%d/%d" %(1,len(sampleSequence)))
        #draw first sample after reading completed
        y0 = np.array(sampleSequence[0])
        line0.set_ydata(y0)
        ax.set_ylim(np.min([y0]), np.max([y0]))
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.show()
        dlg2.show()
    else:
        label2.setText("Enter valid number of samples:")

def retake():
    dlg2.hide()
    global sampleSequence
    sampleSequence = []
    readSamples()
    dlg2.show()

def addSamples():
    global readingSteps, readingNoise, sampleSequence
    dlg2.hide()
    addButton.hide()
    retakeButton.hide()
    addStepsButton.show()
    addNoiseButton.show()
    label2.show()
    inputLine.show()
#add samples to dataset
    for sample in sampleSequence:
        currentSample = sample
        if readingSteps == 1:
            currentSample.append(1)
        elif readingNoise == 1:
            currentSample.append(0)
        with open('pedometerDataset.csv', 'a+', encoding='UTF8', newline='') as f1:
            writer = csv.writer(f1)
            writer.writerow(currentSample)

    print("%d samples added to dataset" %(len(sampleSequence)))
    sampleSequence = []
    readingSteps = 0
    readingNoise = 0
    label.setText("Start new sampling sequence\n")


def next():
    global sampleSequence, currentSequence
    if currentSequence < len(sampleSequence)-1:
        currentSequence = currentSequence+1
    else:
        currentSequence = 0
    label4.setText("%d/%d" %(currentSequence+1,len(sampleSequence)))
    y0 = np.array(sampleSequence[currentSequence])
    line0.set_ydata(y0)
    ax.set_ylim(np.min([y0]), np.max([y0]))
    fig.canvas.draw()
    fig.canvas.flush_events()

def prev():
    global sampleSequence, currentSequence
    if currentSequence > 0:
        currentSequence = currentSequence-1
    else:
        currentSequence = len(sampleSequence)-1
    label4.setText("%d/%d" %(currentSequence+1,len(sampleSequence)))
    y0 = np.array(sampleSequence[currentSequence])
    line0.set_ydata(y0)
    ax.set_ylim(np.min([y0]), np.max([y0]))
    fig.canvas.draw()
    fig.canvas.flush_events()

def remove():
    global sampleSequence, currentSequence
    sampleSequence.pop(currentSequence)
    if currentSequence == len(sampleSequence):
        currentSequence = currentSequence-1
    label4.setText("%d/%d" %(currentSequence+1,len(sampleSequence)))
    y0 = np.array(sampleSequence[currentSequence])
    line0.set_ydata(y0)
    ax.set_ylim(np.min([y0]), np.max([y0]))
    fig.canvas.draw()
    fig.canvas.flush_events()

addStepsButton.clicked.connect(addSteps)
addNoiseButton.clicked.connect(addNoise)
addButton.clicked.connect(addSamples)
retakeButton.clicked.connect(retake)
nextButton.clicked.connect(next)
prevButton.clicked.connect(prev)
removeButton.clicked.connect(remove)


if __name__ == '__main__':
    global y0, fig, ax, line0
    y0 = np.array(sampleQueue)
    plt.ion()
    fig, ax = plt.subplots(1)
    line0, = ax.plot(y0)
    ax.set_ylim([0, 4])
    plt.show()
    dlg2.setLayout(layout2)
    dlg2.show()
    dlg.setLayout(layout)
    dlg.show()
    dlg2.hide()
    app.exec()
    ax.set_ylim([0, 4])
