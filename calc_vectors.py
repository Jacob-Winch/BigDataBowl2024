import math


def calculate_vector(magnitude: float, degrees: float):
    """Calculate the vector of a defender or ball_carrier's speed or acceleration"""
    actual_degrees = (450 - degrees) % 360
    rads = actual_degrees * math.pi / 180
    return [magnitude * math.cos(rads), magnitude * math.sin(rads)]
