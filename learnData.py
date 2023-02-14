#Import scikit-learn dataset library
from sklearn import datasets
from sklearn import preprocessing
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sys

#Import learn models
from sklearn import svm
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF

clf = 0
filename = 0
if len(sys.argv) == 1:
    print("List of valid arguments:")
    print("-net")
    print("-rf")
    print("-svm")
    sys.exit()

if sys.argv[1] == "-net":
    alpha = float(input("Enter alpha : "))
    iter = int(input("Enter number of iterations : "))
    n = int(input("Enter number of hidden layers : "))
    lst = []
    print("Enter size of each layer : ")
    for i in range(0, n):
        layer = int(input())
        lst.append(layer)
    clf = MLPClassifier(alpha=alpha, max_iter=iter, hidden_layer_sizes=(lst))
    filename = 'net_model.sav'
elif sys.argv[1] == "-rf":
    est = int(input("Enter number of estimators : "))
    clf = RandomForestClassifier(n_estimators=4000)
    filename = 'rf_model.sav'
elif sys.argv[1] == "-svm":
    clf = svm.SVC()
    filename = 'svm_model.sav'
else:
    print("List of valid arguments:")
    print("-net")
    print("-rf")
    print("-svm")
    sys.exit()

# Importing the dataset
dataset = pd.read_csv('pedometerDataset.csv')
X = dataset.iloc[:, 0 : 100].values
y = dataset.iloc[:, 100].values

# Splitting the dataset into the Training set and Test set
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state = 0)

#Train the model using the training sets
clf.fit(X_train, y_train)

#export dataset
import pickle
pickle.dump(clf, open(filename, 'wb'))

#Predict the response for test dataset
y_pred = clf.predict(X_test)

#Import scikit-learn metrics module for accuracy calculation
from sklearn import metrics

# Model Accuracy: how often is the classifier correct?
print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

# Model Precision: what percentage of positive tuples are labeled as such?
print("Precision:",metrics.precision_score(y_test, y_pred, average = 'weighted'))

# Model Recall: what percentage of positive tuples are labelled as such?
print("Recall:",metrics.recall_score(y_test, y_pred, average = 'weighted'))

# Making the Confusion Matrix
from sklearn.metrics import confusion_matrix, accuracy_score
cm = confusion_matrix(y_test, y_pred)
print(cm)
