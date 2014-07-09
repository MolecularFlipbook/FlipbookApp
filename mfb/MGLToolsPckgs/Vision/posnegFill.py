from matplotlib.pylab import *

def findZero(i,x,y1,y2):
     im1 = i-1
     m1 = (y1[i] - y1[im1])/(x[i] - x[im1])
     m2 = (y2[i] - y2[im1])/(x[i] - x[im1])
     b1 = y1[im1] - m1*x[im1]
     b2 = y2[im1] - m2*x[im1]
     xZero = (b1 - b2)/(m2 - m1)
     yZero = m1*xZero + b1
     return (xZero, yZero)

def posNegFill(x,y1,y2):
      diff = y2 - y1
      pos = []
      neg = []
      xx1 = [x[0]]
      xx2 = [x[0]]
      yy1 = [y1[0]]
      yy2 = [y2[0]]
      oldSign = (diff[0] < 0 )
      npts = x.shape[0]
      for i in range(1,npts):
          newSign = (diff[i] < 0)
          if newSign != oldSign:
              xz,yz = findZero(i,x,y1,y2)
              xx1.append(xz)
              yy1.append(yz)
              xx2.reverse()
              xx1.extend(xx2)
              yy2.reverse()
              yy1.extend(yy2)
              if oldSign:
                  neg.append( (xx1,yy1) )
              else:
                  pos.append( (xx1,yy1) )
              xx1 = [xz,x[i]]
              xx2 = [xz,x[i]]
              yy1 = [yz,y1[i]]
              yy2 = [yz,y2[i]]
              oldSign = newSign
          else:
              xx1.append( x[i])
              xx2.append( x[i])
              yy1.append(y1[i])
              yy2.append(y2[i])
              if i == npts-1:
                  xx2.reverse()
                  xx1.extend(xx2)
                  yy2.reverse()
                  yy1.extend(yy2)
                  if oldSign :
                      neg.append( (xx1,yy1) )
                  else:
                      pos.append( (xx1,yy1) )
      return pos,neg
