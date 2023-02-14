#Import scikit-learn dataset library
from sklearn import datasets
from sklearn import preprocessing
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
import pickle
import serial
from ctypes import Structure, c_uint, c_int, c_float, sizeof
from pure_sklearn.map import convert_estimator
import collections
import itertools
import sys

#load pretrained model
loaded_model = 0
if len(sys.argv) == 1:
    loaded_model = pickle.load(open('net_model.sav', 'rb'))
elif sys.argv[1] == "-net":
    loaded_model = pickle.load(open('net_model.sav', 'rb'))
elif sys.argv[1] == "-rf":
    loaded_model_ = pickle.load(open('rf_model.sav', 'rb'))
    loaded_model = convert_estimator(loaded_model_)
elif sys.argv[1] == "-svm":
    loaded_model = pickle.load(open('svm_model.sav', 'rb'))


class DataPoint(Structure):
    _pack_ = 1
    _fields_ = [
        ("acc_vector", c_float)
    ]

#serial init
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
currentSample = 0.0
steps = 0
sampleQueue = collections.deque([0.0]*sampleQueueSize, sampleQueueSize)
finalValues = collections.deque([0.0]*sampleQueueSize, sampleQueueSize)



#new decision factors
stepPhaseThreshhold = 1.4 #if acceleration is bigger than this threshhold, we assume a step started
stepPhase = 0 # = 1 if stepPhaseThreshhold was crossed and step is currently happenning
endStepThreshhold = 1.1 #if acceleration gets smaller than endStepThreshhold, we assume the step stopped
stepStopped = 0
bonusSamples = 5 #samples to collect after step stopped
bonusSamplesCollected = 0 #current number of bonus samples collected

#4Hz filter
filterCoeff = [-0.0005 ,  -0.0019  , -0.0043 ,  -0.0074 ,  -0.0095 ,  -0.0070  ,  0.0036  ,  0.0246  ,  0.0553  ,  0.0913  ,  0.1257  ,  0.1504,  0.1595  ,  0.1504 ,   0.1257 ,   0.0913  ,  0.0553  ,  0.0246  ,  0.0036  , -0.0070 ,  -0.0095 ,  -0.0074 ,  -0.0043 ,  -0.0019, -0.0005]

#prepair graph parameters
y0 = np.array(sampleQueue)
plt.ion()
fig, ax = plt.subplots(1)
line0, = ax.plot(y0)
ax.set_ylim([0, 4])
plt.show()

while 1:
    sampleQueue.popleft()
    finalValues.popleft()

    lastSample = currentSample
    currentSample = 0.0

#reading data
    byte = serial_port.read(sizeof(DataPoint))
    buffer = bytearray(byte)
    Point = DataPoint.from_buffer(buffer)

#filtering signal
    sampleQueue.append(Point.acc_vector)
    for index, coeff in enumerate(filterCoeff):
        currentSample = currentSample + coeff * sampleQueue[sampleQueueSize-1-index]
    finalValues.append(currentSample)

#step decision logic
        #step began
    if currentSample > stepPhaseThreshhold and stepPhase == 0:
        stepPhase = 1
        #step ended
    if stepPhase == 1 and currentSample < endStepThreshhold:
        stepStopped = 1
        stepPhase = 0
        #collect more samples after step end
    if stepStopped == 1 and bonusSamplesCollected <= bonusSamples:
        bonusSamplesCollected = bonusSamplesCollected + 1;
        #stop collecting samples, add step
    if stepStopped == 1 and bonusSamplesCollected == bonusSamples:
        bonusSamplesCollected = 0
        stepStopped = 0
        y = loaded_model.predict([list(finalValues)])
        if y[0] == 1:
            steps = steps + 1
            print("Steps: ", steps)
            y0 = np.array(finalValues)
            line0.set_ydata(y0)
            ax.set_ylim(np.min([y0]), np.max([y0]))
            fig.canvas.draw()
            fig.canvas.flush_events()
