import numpy as np

def scale3(x,y,z):
    return np.array([[x, 0, 0, 0],
                     [0, y, 0, 0],
                     [0, 0, z, 0],
                     [0, 0, 0, 1]])

def translate3(x,y,z):
    return np.array([[1, 0, 0, x],
                     [0, 1, 0, y],
                     [0, 0, 1, z],
                     [0, 0, 0, 1]])

def rotate3x(rads):
    cth = np.cos(rads)
    sth = np.sin(rads)

    return np.array([[ 1, 0, 0, 0],
                     [ 0, cth, sth, 0],
                     [ 0, -sth, cth, 0],
                     [ 0, 0, 0, 1 ]])

def rotate3y(rads):
    cth = np.cos(rads)
    sth = np.sin(rads)

    return np.array([[ cth, 0, sth, 0],
                     [ 0, 1, 0, 0],
                     [ -sth, 0, cth, 0],
                     [ 0, 0, 0, 1 ]])

def rotate3z(rads):
    cth = np.cos(rads)
    sth = np.sin(rads)

    return np.array([[ cth, sth, 0, 0],
                     [ -sth, cth, 0, 0],
                     [ 0, 0, 1, 0],
                     [ 0, 0, 0, 1 ]])
