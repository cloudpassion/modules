from math import radians, cos, sin, asin, sqrt


# latitude широта, longitude долгота
def haversine(center_lat, center_long, test_lat, test_long):
    # https://stackoverflow.com/questions/42686300/how-to-check-if-coordinate-inside-certain-area-python
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(
        radians, [
            center_long, center_lat, test_long, test_lat
        ])

    # haversine formula
    d_lon = lon2 - lon1
    d_lat = lat2 - lat1
    a = sin(d_lat/2)**2 + cos(lat1) * cos(lat2) * sin(d_lon/2)**2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371
    return c * r
