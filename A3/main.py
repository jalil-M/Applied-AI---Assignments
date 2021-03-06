# -*- coding: utf-8 -*-
"""
Created on Mon Feb 25 23:39:31 2019

@author: Erwan
"""

import random
import matplotlib.pyplot as plt
from math import exp, log
import numpy as np

inf = float('inf')

class LIBSVMFile:
    
    def __init__(self, filename):
        self.filename = filename
        self.data = None
        
    def load_data(self):
        f = open(self.filename)
        
        self.data = {'labels': [], 'values': []}
        
        for line in f.readlines():
            if line:
                split_line = line.split()
                label = float(split_line[0])
                values = [float(pair.split(':')[1]) for pair in split_line[1:]]
                
                self.data['labels'].append(label)
                self.data['values'].append(values)
                
        f.close()
        
        return self
            
    def save_data(self, data=None):
        """
        Save data in the LIBSVM format.
        
        Args:
            data: list of elements, each element being a list of values,
            preceded by a label (which must be an integer for classification
            tasks, or any real number for regression tasks).
            
            For example,
            
            data = [(1, [12, 62, -3]),
                    (2, [6, 41, 0]),
                    (2, [8, 22, 2]),
                    (1, [15, 30, -6])]
        """
        self.data = data
        
        f = open(self.filename, 'w')
        
        for label, values in zip(data['labels'], data['values']):
            f.write(str(label))
            for i, value in enumerate(values):
                f.write(' ')
                f.write(str(i))
                f.write(':')
                f.write(str(value))
            f.write('\n')
            
        f.close()
        
        return self
        
class LinearClassifier:
    
    def __init__(self, alpha=1, max_steps=1000, err_crit=0):
        if callable(alpha):
            # If alpha is a function
            self.learning_rate = alpha
        else:
            # Otherwise a constant function is created
            self.learning_rate = lambda t: alpha
        self.max_steps = max_steps  # Maximum number of iterations before stopping
        self.err_crit = err_crit
        
        self.weights = None
        self.norm_coefs = None
        self.X = None
        self.Y = None
        
        
    def fit(self, X, Y):
        self.X = X
        self.Y = Y
        
        # Values list, with extra 1 to account for the intercept term
        X = self.normalize(np.array([np.insert(values, 0, 1) for values in X]))
        
        # Number of examples
        n = len(Y)
        
        # Initialization at 1
        self.weights = [1] * len(X[0])
        
        step = 0
        m = n
        
        while step < self.max_steps and m > self.err_crit:
            r = random.randrange(n)
            y, x = Y[r], X[r]
                
            self._update_weights(x, y, step)
            
            # Number of misclassified examples
            m = sum([abs(true_y - pred_y) for true_y, pred_y in zip(Y, self.predict(X[:, 1:]))])
            
            step += 1
            
    def predict(self, X):
        return [0 if self._classifier(np.insert(x, 0, 1)) < 0.5 else 1 for x in X]
    
    def loss(self, X, Y):
        s = 0
        
        for y, x in zip(Y, X):
            s += (y - self._classifier(x)) ** 2
            
        return s
        
    def normalize(self, values):
        v = values.transpose()
        self.norm_coefs = np.array([])
        
        for i, row in enumerate(v):
            m = max(row)
            v[i] /= m
            self.norm_coefs = np.append(self.norm_coefs, m)
        
        return v.transpose()
                
    def _classifier(self, x):
        return self._threshold(np.dot(self.weights, x))
    
    def _update_weights(self, x, y, step):
        h = self._classifier(x)
        
        # Gradient vector
        grad = []
        
        for i, w in enumerate(self.weights):
            g = (y - h) * x[i]
            
            w += self.learning_rate(step) * g
            self.weights[i] = w
            
            grad.append(g)
            
        return grad
        
    def _threshold(self, a):        
        if a >= 0:
            return 1
        else:
            return 0
    
    
class LinearClassifierLogReg(LinearClassifier):
    
    def __init__(self, alpha, max_steps=1000, eps=0.01):
        super().__init__(alpha, max_steps, 0)
        self.eps = eps
        
    def loss(self, X, Y):
        # Logistic loss
        
        s = 0
        
        for y, x, in zip(Y, X):
            h = self._classifier(x)
            s += y * log(h) + (1 - y) * log(1 - h)
            
        return s
    
    def fit(self, X, Y):
        self.X = X
        self.Y = Y
        
        # Values list, with extra 1 to account for the intercept term
        X = self.normalize(np.array([np.insert(values, 0, 1) for values in X]))
        
        # Number of examples
        n = len(Y)
        
        # Initialization at 1
        self.weights = [1] * len(X[0])
        
        step = 0
        grad = [inf] * n
        
        while step < self.max_steps:
            if np.linalg.norm(grad, 2) < self.eps:
                break
            
            r = random.randrange(n)
            y, x = Y[r], X[r]
                
            grad = self._update_weights(x, y, step)
            
            step += 1
    
    def _update_weights(self, x, y, step):
        h = self._classifier(x)
        
        # Gradient vector
        grad = []
        
        for i, w in enumerate(self.weights):
            g = (y - h) * h * (1 - h) * x[i]
            
            w += self.learning_rate(step) * g
            self.weights[i] = w
            
            grad.append(g)
            
        return grad
            
    def _threshold(self, a):
        return 1 / (1 + exp(-a))
    
def cross_validate(clf, X, Y, cv=10):
    n = len(X)
    scores = []
    
    order = np.arange(n)
    np.random.shuffle(order)
    
    for ind in np.array_split(order, cv):
        test_indices = ind
        train_indices = np.array([i for i in range(n) if i not in test_indices])
        
        X_train = X[train_indices, :]
        Y_train = Y[train_indices]
        
        X_test = X[test_indices, :]
        Y_test = Y[test_indices]

        clf.fit(X_train, Y_train)
        
        Y_pred = clf.predict(X_test / clf.norm_coefs[1:])
        
        # Misclassified examples
        m = sum([abs(true_y - pred_y) for true_y, pred_y in zip(Y_test, Y_pred)])
        
        scores.append((1 - m / len(Y_pred)))
        
    return scores
        
        
if __name__ == '__main__':
    data = LIBSVMFile('data.libsvm').load_data().data
    X1 = [e[0] for e in data['values']]
    X2 = [e[1] for e in data['values']]
    Y = data['labels']
    
    def f1(t):
        return 10000/(1000+t)
    
    def f2(t):
        return 10000/(10*(100+t))
    
    clf1 = LinearClassifier(alpha=f1, max_steps=10000, err_crit=0)
    clf2 = LinearClassifierLogReg(alpha=f2, max_steps=20000, eps=0.0001)
    
#    clf1.fit(data['values'], Y)
#    clf2.fit(data['values'], Y)
    
    scores1 = cross_validate(clf1, np.array(data['values']), np.array(data['labels']), len(Y))
    scores2 = cross_validate(clf2, np.array(data['values']), np.array(data['labels']), len(Y))
    
    print('Scores for perceptron:', scores1)
    w1 = clf1.weights
    print('Weights for perceptron:', w1)
    nc1 = clf1.norm_coefs
    
    print('\n')
    
    print('Scores for logistic regression:', scores2)
    w2 = clf2.weights
    print('Weights for logistic regression:', w2)
    nc2 = clf2.norm_coefs
    
    
    Xg = range(10000, 80000)
    Yg1 = [-nc1[2] * (w1[0] + w1[1] / nc1[1] * x) / w1[2] for x in Xg]
    Yg2 = [-nc2[2] * (w2[0] + w2[1] / nc2[1] * x) / w2[2] for x in Xg]
    
    plt.scatter(X1, X2, c=Y)
    plt.plot(Xg, Yg1, label='Linear classifier')
    plt.plot(Xg, Yg2, label='Logistic regression')
    plt.legend()
    plt.show()
    
        