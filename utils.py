from numpy import *
import math

def perp( a ) :
    b = empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

# line segment a given by endpoints a1, a2
# line segment b given by endpoints b1, b2
# return 
def seg_intersect(a1,a2, b1,b2) :
    da = a2-a1
    db = b2-b1
    dp = a1-b1
    dap = perp(da)
    denom = dot( dap, db)
    num = dot( dap, dp )
    out = (num / denom.astype(float))*db + b1
    return out

def validate_point(point, range):
    for cord in point:
        if (math.isnan(cord) or math.isinf(cord)):
            return False
    if(point[0] >= range[0] and point[0] <= range[1]):
        return True
    else:
        return False

def arePointsEqual(points):
    if(len(points) == 1): 
        return True
    points = [[round(pt[0], DECIMAL_PLACES), round(pt[1], DECIMAL_PLACES)] for pt in points]
    for i in range(len(points) - 1):
        if (points[i][0] != points[i+1][0] or points[i][1] != points[i+1][1]):
            return False
    return True