import numpy as np
import random
from numpy import array as a
import pyautogui as ag
import time
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

__all__ = ["Bezier"]


class Bezier():
    # Implementation derrived from https://github.com/torresjrjr/Bezier.py
    def TwoPoints(t, P1, P2):
        """
        Returns a point between P1 and P2, parametised by t.
        INPUTS:
            t     float/int; a parameterisation.
            P1    numpy array; a point.
            P2    numpy array; a point.
        OUTPUTS:
            Q1    numpy array; a point.
        """

        if not isinstance(P1, np.ndarray) or not isinstance(P2, np.ndarray):
            raise TypeError('Points must be an instance of the numpy.ndarray!')
        if not isinstance(t, (int, float)):
            raise TypeError('Parameter t must be an int or float!')

        Q1 = (1 - t) * P1 + t * P2
        return Q1

    def Points(t, points):
        """
        Returns a list of points interpolated by the Bezier process
        INPUTS:
            t            float/int; a parameterisation.
            points       list of numpy arrays; points.
        OUTPUTS:
            newpoints    list of numpy arrays; points.
        """
        newpoints = []
        for i1 in range(0, len(points) - 1):
            newpoints += [Bezier.TwoPoints(t, points[i1], points[i1 + 1])]
        return newpoints

    def Point(t, points):
        """
        Returns a point interpolated by the Bezier process
        INPUTS:
            t            float/int; a parameterisation.
            points       list of numpy arrays; points.
        OUTPUTS:
            newpoint     numpy array; a point.
        """
        newpoints = points
        while len(newpoints) > 1:
            newpoints = Bezier.Points(t, newpoints)
        return newpoints[0]

    def Curve(t_values, points):
        """
        Returns a point interpolated by the Bezier process
        INPUTS:
            t_values     list of floats/ints; a parameterisation.
            points       list of numpy arrays; points.
        OUTPUTS:
            curve        list of numpy arrays; points.
        """

        if not hasattr(t_values, '__iter__'):
            raise TypeError("`t_values` Must be an iterable of integers or floats, of length greater than 0 .")
        if len(t_values) < 1:
            raise TypeError("`t_values` Must be an iterable of integers or floats, of length greater than 0 .")
        if not isinstance(t_values[0], (int, float)):
            raise TypeError("`t_values` Must be an iterable of integers or floats, of length greater than 0 .")

        curve = np.array([[0.0] * len(points[0])])
        for t in t_values:
            curve = np.append(curve, [Bezier.Point(t, points)], axis=0)
        curve = np.delete(curve, 0, 0)
        return curve

def traject(x, y, duration, resolution=100, tween="linear"):
    """
    :param x, y: coordinates where the mouse cursor will move
    :param duration: The time it takes to perform the move.
        If 0, then the mouse cursor is moved instantaneously.
    :param resolution: Controls the smoothness of the curve
    :param tween: The tweening function used if the duration is not 0.
        A linear tween is used by default.
    """
    startx, starty = ag.position()

    # Create bezier curve control points
    steps = control_pts(startx, starty, x, y, 4)
    steps.insert(0, [startx, starty])
    steps.append([x, y])
    
    # Create points on bezier curve
    t_points = np.arange(0, 1, 1/resolution)
    steps = np.array(steps)
    steps = Bezier.Curve(t_points, steps)
    steps = steps.tolist()
    steps.pop(0)
    steps.append([x, y])
    
    # Calculate num of steps and sleep amount between them
    num_steps = len(steps)
    sleep_amount = duration / num_steps
    ag.PAUSE = sleep_amount 

    for step in steps:
        tweenX = int(round(step[0]))
        tweenY = int(round(step[1]))
        ag.moveTo(tweenX, tweenY)    

def control_pts(startx, starty, endx, endy, pts=4):
    if startx <= endx:
        xs = sorted([random.randint(startx, endx) for i in range(pts)])
    else:
        xs = sorted([random.randint(endx, startx) for i in range(pts)], reverse=True)
    if starty <= endy:
        ys = sorted([random.randint(starty, endy) for i in range(pts)])
    else:
        ys = sorted([random.randint(endy, starty) for i in range(pts)], reverse=True)
    return [list(x) for x in zip(xs, ys)]
    