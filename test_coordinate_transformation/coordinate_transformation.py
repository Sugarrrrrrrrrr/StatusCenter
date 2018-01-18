from haversine import haversine
import pyproj


if __name__ == '__main__':

    # haversine
    # Calculate the distance bewteen 2 points on Earth.
    # Calculate the distance (in km or in miles) bewteen two points on Earth, located by their latitude and longitude.
    # Example: distance bewteen Lyon and Paris
    lyon = (45.7597, 4.8422)
    paris = (48.8567, 2.3508)
    d1 = haversine(lyon, paris)                 # in kilometers
    d2 = haversine(lyon, paris, miles=True)     # in miles

    
    lat = 116.366
    lng = 39.8673
    p1 = pyproj.Proj(init='epsg:4326')
    p2 = pyproj.Proj(init='epsg:3857')
    x1, y1 = p1(lat, lng)                                   # degree to radian
    x2, y2 = pyproj.transform(p1, p2, x1, y1, radians=True) # radian/degree to meter
    x3, y3 = pyproj.transform(p2, p1, x2, y2)               # meter to degree/radian
    
