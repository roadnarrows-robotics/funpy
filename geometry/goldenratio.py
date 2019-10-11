import sys
import math
import matplotlib.pyplot as  plt
import numpy as np

#
# Constants
#
# phi = 1.6180339887...
phi = (1.0 + math.sqrt(5))/2.0 # derived
tau = math.pi * 2.0

def iterable(elem):
  try:
    iterator = iter(elem)
  except TypeError:
    return False
  else:
    return True

def in2pi(theta):
  """ theta => [0,2pi) """
  return math.fmod(theta + tau, tau)

def geomSeries(a, r, n):
  """
  Generate the first n terms of the geometric series:
    a, ar, ar^2, ... ar^(n-1)

  Returns:
    np.array
  """
  s = []
  for k in range(0, n):
    s.append(a)
    a *= r
  return np.array(s)

def geomSum(a, r, n):
  """
  Sum the first n terms of the series:
    a + ar + ar^2 ... + ar^(n-1) = a * (1 - r^n) / (1 - r)
  where a is the first term, and r is the common ratio.

  Returns:
    Sum.
  """
  if r != 1.0:
    return a * ((1.0 - math.pow(r, n)) / (1.0 - r))
  else:
    return n * a

def slopeIntercept(x, y):
  """
  Find the slope-intercept equation for a line in 2D space.
    y = m x + b

  Returns:
    (m, b)
  """
  m = (y[1] - y[0]) / (x[1] - x[0])
  b = y[0] - m * x[0]
  return m, b

def matReflectYAxis():
  """
  Returns a 2x2 affine tranformation matrix to reflect 2D points about
  the y-axis.
  """
  return np.matrix([[-1, 0], [0, 1]])

def matReflectXAxis():
  """
  Returns a 2x2 affine tranformation matrix to reflect 2D points about
  the x-axis.
  """
  return np.matrix([[1, 0], [0, -1]])

def matScale(xscale, yscale):
  """
  Returns a 2x2 affine tranformation matrix to scale 2D points in the x and/or
  y directions.

  Parameers:
    xscale    X scale factor with 1 == no scaling.
    yscale    Y scale factor with 1 == no scaling.
  """
  return np.matrix([[xscale, 0], [0, yscale]])

def matRotate(theta):
  """
  Returns a 2x2 affine tranformation matrix to rotate 2D points.

  Parameers:
    theta    Radians of rotation.
  """
  c = np.cos(theta)
  s = np.sin(theta)
  return np.matrix([[c, -s], [s, c]])

def matShear(xshear, yshear):
  """
  Returns a 2x2 affine tranformation matrix to shear 2D points in the x and/or
  y directions.

  Parameers:
    xshear    X shear factor with 0 == no shearing.
    yshear    Y shear factor with 0 == no shearing.
  """
  return np.matrix([[1, xshear], [yshear, 1]])

def vecTranslate(xoffset, yoffset):
  """
  Create a translation vector.

  p => p.x+xoffset, p.y+yoffset
  """
  return np.array([[xoffset],[yoffset]])

def cubicSpline(p0, p1, p2):
  """
    f(x)   =  a * x^3 +  b * x^2 + c * x + d
    f'(x)  = 3a * x^2 + 2b * x   + c
    f''(x) = 6a * x   + 2b

    points on the cubic
    y0 = a * x0^3 + b * x0 ^ 2 + c * x0 + d
    y1 = a * x1^3 + b * x1 ^ 2 + c * x1 + d
    y2 = a * x2^3 + b * x2 ^ 2 + c * x2 + d

    local minimum and maximum
    0 = 3a * x0^2 + 2b * x0 + c
    0 = 3a * x2^2 + 2b * x2 + c

    inflexion point
    0 = 6a * x1 + 2b
  """
  pass

#
## Class Shape
##
class Shape:
  """
  2D shape base class.

  A shape may have an overall 2D structure and/or composed of shapes.
  """
  Id = 0

  def __init__(self, name='shape', x=None, y=None):

    # identification
    self.m_name = name
    self.m_id = Shape.Id
    Shape.Id += 1

    # overall shape (x,y) points
    if x is None:
      self.m_x = np.array([], dtype=np.float64)
    elif iterable(x):
      self.m_x = np.array(x, dtype=np.float64)
    else:
      self.m_x = np.array([x], dtype=np.float64)

    if y is None:
      self.m_y = np.array([], dtype=np.float64)
    elif iterable(y):
      self.m_y = np.array(y, dtype=np.float64)
    else:
      self.m_y = np.array([y], dtype=np.float64)

    # attached shapes
    self.m_attached = []

  def name(self):
    return self.m_name

  def id(self):
    return self.m_id

  def fqname(self):
    return "{}.{}".format(self.m_name, self.m_id)

  def x(self):
    return self.m_x

  def y(self):
    return self.m_y

  def shape(self):
    return self.m_x, self.m_y

  def numofAttached(self):
    return len(self.m_attached)

  def attached(self, index='all'):
    """
    Return all or a single attached shape.

    Parameter:
      index   - The value 'all' or index in [0,  numofAttached()).
    """
    if index == 'all':
      return self.m_attached
    else:
      return self.m_attached[index]

  def addPoint(self, x, y):
    self.m_x = np.hstack((self.m_x, x))
    self.m_y = np.hstack((self.m_y, y))

  def addPoints(self, p):
    """
    P is in shape (2,n), n>0
    """
    l = p.tolist()
    if p.size >= 2:
      if p.shape[1] == 1:
        self.m_x = np.hstack((self.m_x, p[0,0]))
        self.m_y = np.hstack((self.m_y, p[1,0]))
      else:
        self.m_x = np.hstack((self.m_x, l[0]))
        self.m_y = np.hstack((self.m_y, l[1]))

  def attachShape(self, shape):
    self.m_attached.append(shape)

  def findId(self, identity):
    if identity == self.id():
      return self
    for s in self.attached():
      shape = s.findId(identity)
      if shape is not None:
        return shape
    return None

  def findFQName(self, fqname):
    if fqname == self.fqname():
      return self
    for s in self.attached():
      shape = s.findFQName(fqname)
      if shape is not None:
        return shape
    return None

  def translate(self, x, y):
    self.m_x += x
    self.m_y += y
    for shape in self.m_attached:
      shape.translate(x, y)

  def scale(self, c):
    self.m_x *= c
    self.m_y *= c
    for shape in self.m_attached:
      shape.scale(c)

  def rotate(self, theta):
    self.affine(matRotate(np.radians(theta)))

  def affine(self, amat, b=np.array([[0.0],[0.0]])):
    p = np.array([[0.0],[0.0]])
    for i in range(0, self.m_x.size):
      p[0] = self.m_x[i]
      p[1] = self.m_y[i]
      p = amat * p + b
      self.m_x[i] = p[0]
      self.m_y[i] = p[1]
    for shape in self.m_attached:
      shape.affine(amat, b)

  def printTree(self, indent=0, show_points=False):
    print("{}{}: pts={}".format(' '*indent, self.fqname(), self.x().size))
    if show_points:
      print("{} x: {}".format(' '*(indent+4), self.x().tolist()))
      print("{} y: {}".format(' '*(indent+4), self.y().tolist()))
    for shape in self.m_attached:
      shape.printTree(indent+2, show_points)

  def plot(self, ax):
    if self.m_x.size > 0:
      ax.plot(self.m_x, self.m_y, **self.plotAttrs())
      ax.set_aspect('equal')
    for shape in self.m_attached:
      shape.plot(ax)

  def plotAttrs(self):
    return {'linestyle': '-'}

#
## Class Points
##
class Points(Shape):
  def __init__(self, x=None, y=None):
    super().__init__(self.__class__.__name__, x, y)

  def plotAttrs(self):
    return {'linestyle': ' ', 'marker':'+'}


#
## Class RegularPentagon
##
class RegularPentagon(Shape):
  """
  Regular pentagon.
  """
  InteriorAngle = 108.0 # internal angle (degrees)
  RotationAngle = 72.0  # rotation angle x 5 (degrees)

  def __init__(self, s, name='default'):
    if name is None or name == 'default':
      name = self.__class__.__name__
    super().__init__(name)
    self.calculate(s)

  def calculate(self, s):
    self.m_side = s

    #self.m_R = self.m_side * phi  # circumcircle radius
    #self.m_r = self.m_side * math.sqrt(5 + 2 * math.sqrt(5)) / 2.0
                                  # incircle radius

    self.m_R = self.m_side \
        / (2.0 * math.sin(math.radians(RegularPentagon.RotationAngle/2)))

    alpha = np.radians(RegularPentagon.RotationAngle)
    theta = np.radians(90)

    x0, y0 = self.m_R * math.cos(theta), self.m_R * math.sin(theta)
    self.addPoint(x0, y0)

    for s in range(0, self.numofSides()):
      theta += alpha
      x, y = self.m_R * math.cos(theta), self.m_R * math.sin(theta)
      self.addPoint(x, y)

    self.addPoint(x0, y0)

  def numofSides(self):
    return 5

  def side(self):
    return self.m_side

  def R(self):
    return self.m_R

  def r(self):
    return self.m_r


#
## Class GoldenTriangle
##
class GoldenTriangle(Shape):
  """
  Golden isosceles triangle.
  """
  ApexAngle = 36.0    # opposite of base (degrees)
  BaseAngle = 72.0    # 2 base angles (degrees)

  def __init__(self, b):
    """
    Constructor.

    Parameters:
      b     Base length.
    """
    super().__init__(self.__class__.__name__)
    self.calculate(b)

  def calculate(self, b):
    self.m_b = b
    mid = self.m_b / 2.0
    self.m_a = self.m_b * phi
    self.m_h = math.sqrt(math.pow(self.m_a, 2) - math.pow(mid, 2))
    self.m_x = np.array([0.0, self.m_b,      mid, 0.0])
    self.m_y = np.array([0.0,      0.0, self.m_h, 0.0])

  def a(self):
    return self.m_a

  def b(self):
    return self.m_b

  def h(self):
    return self.m_h

  def edgeleft(self):
    return  np.array([self.m_x[0], self.m_x[2]]), \
            np.array([self.m_y[0], self.m_y[2]])

  def edgeright(self):
    return  np.array([self.m_x[1], self.m_x[2]]), \
            np.array([self.m_y[1], self.m_y[2]])

  def edgebase(self):
    return  np.array([self.m_x[0], self.m_x[1]]), \
            np.array([self.m_y[0], self.m_y[1]])

  def edgeheight(self):
    return  np.array([self.m_x[2], self.m_x[2]]), \
            np.array([self.m_y[0], self.m_y[2]])

#
## Class GoldenTriangleLadder
##
class GoldenTriangleLadder(Shape):
  def __init__(self, tri, num_rungs):
    super().__init__(self.__class__.__name__)
    self.calculate(tri, num_rungs)

  def calculate(self, tri, num_rungs):
    self.m_numRungs = num_rungs
    hn = tri.h() / geomSum(1, phi, self.m_numRungs)
    ht = geomSeries(hn, phi, self.m_numRungs)
    self.m_h = np.fliplr([ht])[0] # flip left right (note trick for 1D arrays)
    m = [0]
    for h_i in self.m_h[:-1]:
      m.append(m[-1]+h_i)

    # convert line equations to solve for x
    ml, bl = slopeIntercept(*tri.edgeleft())
    mr, br = slopeIntercept(*tri.edgeright())

    mid = tri.b() / 2.0
    i = 0

    for ym in m:
      x = [0] * 3
      x[0] = (ym - bl) / ml
      x[1] = mid
      x[2] = (ym - br) / mr
      y = [ym] * len(x)
      self.attachShape(Shape(name="{}{}".format("rung", i), x=x, y=y))
      i += 1

  def numofRungs(self):
    return self.m_numRungs

  def h(self, i):
    return self.m_h[i]

  def rung(self, i):
    return self.attached(i)

  def rungs(self):
    return self.attached

#
## Class GoldenSpiral
##
class GoldenSpiral(Shape):
  def __init__(self, seed, num_squares,
                    scale=phi, direction='outward', rotation='ccw',
                    start_angle=0.0, include=('circular_spiral')):
    """
    Constructor

    Parameters:
      seed        - Length of starting side.
      num_squares - Number of curve fitting squares.
      scale       - Spiral scale. If phi, then this produces the golden 
                    spiral with perfect square tiling.
      direction   - Spiral inward or outward. One of:
                      in inward out outward
      rotation    - Spiral rotates clockwise or counter-clockwise. One of:
                      cw cww
      start_angle - Starting angle in degrees.
      include     - Include attached shape to this shape. Any combo of:
                      circular_spiral rectangular_spiral square_tiling
    """
    super().__init__(self.__class__.__name__)
    self.calculate(seed, num_squares, scale, direction, rotation,
                        start_angle, include)

  def calculate(self, seed, num_squares, scale, direction, rotation,
                      start_angle, include):
    #
    # Parameters
    #
    self.m_seed = seed
    if num_squares > 1:
      self.m_numSquares = num_squares
    else:
      self.m_numSquares = 1
    if scale <= 1:
      self.m_scale = phi
    else:
      self.m_scale = scale
    if direction == 'out' or direction == 'outward':
      self.m_direction = 'out'
      a0 = self.m_seed
    else:
      self.m_direction = 'in'
      a0 = self.m_seed * math.pow(1.0/self.m_scale, self.m_numSquares)
    if rotation == 'cw':
      self.m_rotate = np.radians(-90)
    else:
      self.m_rotate = np.radians(90)
    self.m_startAngle = np.radians(start_angle)
    self.m_include = include

    #
    # Always generate the square tiling (i.e. Fibonacci tiling). It is the
    # basis for any of the other spiral variants.
    #
    #a = seed
    a = a0
    p0 = np.array([[0.0], [0.0]])
    rot = self.m_startAngle

    endPoints = Points(p0[0], p0[1])

    squareTiling = Shape("square_tiling")

    for i in range(0, self.m_numSquares):
      p0 = self.square(squareTiling, p0, rot, a)
      a *= self.m_scale
      rot += self.m_rotate

    if 'square_tiling' in self.m_include:
      self.attachShape(squareTiling)

    endPoints.addPoint(p0[0,0], p0[1,0])

    self.attachShape(endPoints)

    #
    # Generate the rectangular spiral.
    #
    if 'rectangular_spiral' in self.m_include:
      rectSpiral = Shape("rectangular_spiral")

      rectSpiral.addPoint(squareTiling.attached(0).x()[0],
                          squareTiling.attached(0).y()[0])

      for square in squareTiling.attached():
        self.ell(rectSpiral, square)

      self.attachShape(rectSpiral)

    #
    # Generate the circular spiral (i.e. Fibonacci spiral)
    #
    if 'circular_spiral' in self.m_include:
      dtheta = np.radians(5.0)
      if rotation == 'cw':
        dtheta = -dtheta
      for square in squareTiling.attached():
        self.qarc(square, dtheta)

  def square(self, tiling, p0, rot, a):
    pa = np.array([[a], [0.0]])

    p1 = matRotate(rot) * pa + p0

    rot += self.m_rotate
    p2 = matRotate(rot) * pa + p1

    rot += self.m_rotate
    p3 = matRotate(rot) * pa + p2

    v = np.hstack((p0, p1, p2, p3, p0))

    l = v.tolist()

    square = Shape("square", l[0], l[1])
    
    tiling.attachShape(square)

    return p2

  def ell(self, spiral, square):
    spiral.addPoint(square.x()[1], square.y()[1])
    spiral.addPoint(square.x()[2], square.y()[2])

  def qarc(self, square, dtheta):
    """ Quarter arc """
    x0,y0 = square.x()[0], square.y()[0]
    x1,y1 = square.x()[1], square.y()[1]
    x2,y2 = square.x()[2], square.y()[2]
    xc,yc = square.x()[3], square.y()[3]
    r = math.sqrt(math.pow(x1-x0, 2) + math.pow(y1-y0, 2))
    theta0 = in2pi(math.atan2((y0-yc), (x0-xc)))
    theta2 = in2pi(math.atan2((y2-yc), (x2-xc)))
    #print("theta0={}, theta2={} dtheta={}".format(theta0, theta2, dtheta))
    theta = theta0
    #steps = np.arange(theta0, theta2, dtheta)
    steps = math.floor(np.radians(90) / math.fabs(dtheta)) + 1
    for i in range(0, steps):
      x = r * math.cos(theta) + xc
      y = r * math.sin(theta) + yc
      self.addPoint(x, y)
      theta += dtheta

  def includes(self):
    return self.m_include

  def seed(self):
    return self.m_seed

  def numofSquares(self):
    return self.m_numSquares

  def direction(self):
    return self.m_direction

  def rotation(self):
    return self.m_rotate

  def startAngle(self):
    return np.radians(self.m_startAngle)

  def startPoint(self):
    pass

  def endPoint(self):
    pass

  def spiralComponent(self, name):
    """
    Parameters:
      name    - One of: square_tiling rectangular_spiral
    """
    for shape in self.attached():
      if shape.name() == name:
        return shape
    return None

def plotGoldenTriangleLadder(ax, rungs):
  for i in range(0, len(rungs.rungx)):
    ax.plot(rungs.rungx[i], rungs.rungy[i], '--')

def plotGoldenTriangle(ax, tri):
  ax.plot(tri.x, tri.y, '-')
  step = setTickStepSize(tri.b)
  xticks = np.arange(0.0, tri.x.max()+step, step)
  yticks = np.arange(0.0, tri.y.max()+step, step)
  plt.xticks(xticks)
  plt.yticks(yticks)
  ax.set_aspect('equal')

def setTickStepSize(dim):
  if dim <= 1.0:
    return 0.1
  elif dim <= 10.0:
    return 1.0
  elif dim <= 50.0:
    return 2.0
  elif dim <= 100.0:
    return 10.0
  else:
    return 20.0

def ArtPiece1():
  fig, ax = plt.subplots(1, 1, figsize=(8,8))

  art = Shape("Art Piece #1")

  tri = GoldenTriangle(12.0)
  art.attachShape(tri)

  rungs = GoldenTriangleLadder(tri, 5)

  tri.attachShape(rungs)

  lrot = -210
  rrot = 30
  #lrot = -130
  #rrot = -50
  for i in range(0, rungs.numofRungs()):
    h = rungs.h(i)
    x,y = rungs.rung(i).shape()
    lspiral = GoldenSpiral(h, 10, direction='in', rotation='ccw',
      start_angle=lrot,
      include=('circular_spiral'))
    lspiral.translate(x[0], y[0])
    rspiral = GoldenSpiral(h, 10, direction='in', rotation='cw',
      start_angle=rrot,
      include=('circular_spiral'))
    rspiral.translate(x[2], y[2])

    art.attachShape(lspiral)
    art.attachShape(rspiral)

  #amat = matScale(0.5, 1.0) * matRotate(np.radians(60)) * matShear(0.5, 0)
  #trans = vecTranslate(-2, 5)
  #art.affine(amat, trans)

  art.printTree()

  art.plot(ax)

def ArtPiece2():
  fig, ax = plt.subplots(1, 1, figsize=(8,8))

  art = Shape("Art Piece #2")

  spiral = GoldenSpiral(7, 16, direction='in', rotation='ccw',
      include=('circular_spiral', 'square_tiling'))
  spiral.rotate(90)

  art.attachShape(spiral)

  art.printTree()

  art.plot(ax)

def ArtPiece3():
  fig, ax = plt.subplots(1, 1, figsize=(8,8))

  art = Shape("Art Piece #3")

  pentagon = RegularPentagon(7)

  art.attachShape(pentagon)

  alpha = RegularPentagon.RotationAngle
  theta = alpha

  for i in range(0,5):
    spiral = GoldenSpiral(pentagon.R(), 6, direction='in', rotation='ccw')
    spiral.rotate(theta)
    art.attachShape(spiral)
    theta += alpha

  art.printTree()

  art.plot(ax)

def ArtPiece4():
  fig, ax = plt.subplots(1, 1, figsize=(8,8))

  art = Shape("Art Piece #4")

  pentagon = RegularPentagon(7)

  art.attachShape(pentagon)

  alpha = RegularPentagon.RotationAngle
  theta = alpha

  for i in range(0, pentagon.numofSides()):
    spiral = GoldenSpiral(pentagon.R(), 6, direction='in', rotation='ccw')
    spiral.rotate(theta)
    art.attachShape(spiral)
    theta += alpha

  pentx, penty = pentagon.shape()
  theta = alpha / 2

  for i in range(0, pentagon.numofSides()):
    j = (i +1) % pentagon.numofSides()
    tri = GoldenTriangle(pentagon.side())

    x = tri.shape()[0][2]
    y = tri.shape()[1][2]

    spiral = GoldenSpiral(tri.h()/2., 6, direction='in', rotation='cw')
    spiral.rotate(180)
    spiral.translate(3.0/5.0 * tri.b(), 1.0/6.0 * tri.h())
    tri.attachShape(spiral)

    tri.rotate(theta)
    tri.translate(pentx[j], penty[j])

    theta += alpha
    art.attachShape(tri)

  art.printTree()

  art.plot(ax)


#--
if __name__ == '__main__':
  #ArtPiece1()
  #ArtPiece2()
  #ArtPiece3()
  ArtPiece4()

  plt.show()
