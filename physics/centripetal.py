"""
Centripetal acceleration - physics classical mechanics.

Key Equations:
  a_c = v * w = v^2 / r
  v   = w * r
  w   = 2 * pi / T

Common Symbols:
  v   tangential velocity in meters/second
  w   angular velocty omega in radians/second
  T   time period in seconds
  a   acceleration in meters/second^2
  g   acceleration in earth standard g's
"""

import math as m
from enum import Enum

# Surface gravities of Solar System hard bodies (m/s^2).
g_earth     = 9.80665   # eoroe, Terra, Gaia, center of the universe
g_moon      = 1.62      # month, Luna, Selene
g_mercury   = 3.7       # Hermes
g_venus     = 8.87      # morning and evening stars as one
g_mars      = 3.72076   # the red planet Ares
g_ceres     = 0.029     # largest dwarf planet in the asteroid belt
g_io        = 1.796     # Jupiter I third largest moon
g_europa    = 1.314     # Jupiter II fourth largest moon
g_ganymede  = 1.428     # Jupiter III largest moon
g_callisto  = 1.235     # Jupiter IV second largest moon
g_titan     = 1.352     # largest moon of Saturn
g_enceladus = 0.113     # sixth largest moon of Saturn
g_titania   = 0.379     # largest moon of Uranus
g_triton    = 0.779     # largest moon of Neptune
g_pluto     = 0.620     # dwarf planet in the kuiper belt
g_eris      = 0.824     # most massive TNO dwarf planet

g_n         = g_earth   # standard gravity

class Units(Enum):
  """ Units enumeration class. """
  SI        = 'si'        # international system of units (context specific)
  LEN       = 'm'         # meters
  TIME      = 's'         # seconds
  MASS      = 'kg'        # kilograms
  V         = 'm/s'       # velocity in meters/second
  V_LIN     = 'm/s'       # linear/tangential velocity in meters/second
  W         = 'rad/s'     # angular velocity in radians/second
  V_ANG     = 'rad/s'     # angular velocity in radians/second
  V_ANG_DEG = 'deg/s'     # angular velocity in degrees/second
  A         = 'm/s^2'     # acceleration in meters/second squared
  G         = 'g'         # acceleration in standard g's
  T         = 's'         # rotational period in seconds
  HZ        = 'hz'        # frequency
  RPM       = 'rpm'       # rotations/minute
  KPH       = 'kph'       # kilometers/hour

  @classmethod
  def toenum(cls, obj):
    """ Return object as Units enum. """ 
    if isinstance(obj, cls):
      return obj
    elif isinstance(obj, str):
      return cls(obj)
    else:
      raise ValueError(f"'{repr(obj)}' cannot be converted to enum")

  @classmethod
  def tovalue(cls, obj):
    """ Return string value of Units enum or object. """ 
    if isinstance(obj, cls):
      return obj.value
    elif isinstance(obj, str):
      return obj
    else:
      return str(obj)

class Eq:
  """ Equations 'namespace' class. """
  _emsg0 = "Eq.{0}(): '{1}' units not supported"

  @staticmethod
  def stdg(a):
    """
    Convert SI acceleration to standard g's.

    Parameters:
      a   Acceleration (m/s^2)

    Return:
      standard g's
    """
    return a / g_n

  @staticmethod
  def accel(g):
    """
    Convert standard g's to SI acceleration.

    Parameters:
      g   Number of standard g's.

    Return:
      meters/second^2
    """
    return g * g_n

  @staticmethod
  def T(x, xunits=Units.HZ):
    """
    Calculate the rotation period.

    Paramaters:
      x       Hertz, angular velocity, or rpm.
      xunits  Units of x. One of: Units.HZ Units.V_ANG Units.RPM

    Return:
      seconds
    """
    xunits = Units.toenum(xunits)
    if xunits == Units.HZ:
      return 1.0 / x
    elif xunits == Units.V_ANG:
      return m.tau / x
    elif xunits == Units.RPM:
      return 60.0 / x
    else:
      raise ValueError(Eq._emsg0.format('T', Units.tovalue(xunits)))

  @staticmethod
  def hz(T):
    """ Return the frequency in hertz given the period T (s). """
    return 1.0 / T

  @staticmethod
  def rpm(T):
    """ Return the rotations/minute given the period T (s). """
    return 60.0 / T

  @staticmethod
  def omega(T):
    """ Return radians/second given the rotation period T (s). """
    return m.tau / T

  @staticmethod
  def T_rv(r, v):
    """ Return rotation period (s) given the radius and tangential velocity. """
    return (m.tau * r) / v

  def kph(v):
    """ Return kilometers/hour given meters/second. """
    return v * 3600.0 / 1000.0

  @staticmethod
  def v(r, x, xunits=Units.V_ANG):
    """
    Calculate the tangential velocity associated with an instantaneous
    uniform circular motion.

    Paramaters:
      r       Radius of curvature in meters.
      x       Rotation angular velocity, acceleration, or period.
      xunits  Units of x. One of: Units.V_ANG Units.A Units.T

    Return:
      meters/second
    """
    xunits = Units.toenum(xunits)
    if xunits == Units.V_ANG:   # v = w*r
      return x * r
    elif xunits == Units.A:     # v = sqrt(a*r)
      return m.sqrt(x * r)
    elif xunits == Units.T:     # v = (2pi*r)/T
      return (m.tau * r) / x
    else:
      raise ValueError(Eq._emsg0.format('v', Units.tovalue(xunits)))

  @staticmethod
  def w(r, x, xunits=Units.V_LIN):
    """
    Calculate the angular velocity associated with an instantaneous
    uniform circular motion.

    Paramaters:
      r       Radius of curvature in meters.
      x       Rotation tangential velocity or centripetal acceleration.
      xunits  Units of x. One of: Units.V_LIN Units.A

    Return:
      radians/second
    """
    xunits = Units.toenum(xunits)
    if xunits == Units.V_LIN:     # w = v/r
      return x / r
    elif xunits == Units.A:       # w = a/v, v = sqrt(a/r)
      return x / m.sqrt(x * r)
    else:
      raise ValueError(Eq._emsg0.format('w', Units.tovalue(xunits)))

  @staticmethod
  def a(r, x, xunits=Units.V_LIN):
    """
    Calculate the centripetal acceleration associated with an instantaneous
    uniform circular motion.

    Paramaters:
      r       Radius of curvature in meters.
      x       Rotation tangential velocity, angular velocity, or period.
      xunits  Units of x. One of: Units.V_LIN Units.V_ANG Units.T

    Return:
      meters/second^2
    """
    xunits = Units.toenum(xunits)
    if xunits == Units.V_LIN:     # a = v^2/r
      return (x * x) / r
    elif xunits == Units.V_ANG:   # a = w^2*r
      return x * x * r
    elif xunits == Units.T:       # a = v*w, w = 2pi/T, v = w * r
      return (m.tau * m.tau)/(x * x) * r
    else:
      raise ValueError(Eq._emsg0.format('a', Units.tovalue(xunits)))

def rotation_properties(r, x, xunits=Units.G):
  """
  Calculate the centripetal properties of a body experiencing uniform
  circular motion.

  Parameters:
    r       Radius.
    x       Rotation kinetic.
    xunits  Rotation kinetic units.

  Return:
    Dictionary of centripetal parameters.
  """
  xunits = Units.toenum(xunits)
  if xunits == Units.G:
    a = Eq.accel(x)
    v = Eq.v(r, a, Units.A)
    T = Eq.T_rv(r, v)
    w = Eq.omega(T)
  elif xunits == Units.A:
    a = x
    v = Eq.v(r, a, Units.A)
    T = Eq.T_rv(r, v)
    w = Eq.omega(T)
  elif xunits == Units.V_LIN:
    v = x
    a = Eq.a(r, v, Units.V_LIN)
    T = Eq.T_rv(r, v)
    w = Eq.omega(T)
  elif xunits == Units.V_ANG:
    w = x
    v = Eq.v(r, w, Units.V_ANG)
    a = Eq.a(r, v, Units.V_LIN)
    T = Eq.T_rv(r, v)
  elif xunits == Units.V_ANG_DEG:
    w = m.radians(x)
    v = Eq.v(r, w, Units.V_ANG)
    a = Eq.a(r, v, Units.V_LIN)
    T = Eq.T_rv(r, v)
  elif xunits == Units.T:
    T = x
    v = Eq.v(r, T, Units.T)
    a = Eq.a(r, v, Units.V_LIN)
    w = Eq.omega(T)
  elif xunits == Units.RPM:
    T = Eq.T(x, Units.RPM)
    v = (m.tau * r) / T
    a = Eq.a(r, v, Units.V_LIN)
    w = Eq.omega(T)
  else:
    raise ValueError("rotation_properties(): "
                    f"'{Units.tovalue(xunits)}' units not supported")
  return {'r': r, 'a': a, 'v': v, 'w': w, 'T': T}

def print_properties(props, what=None):
  """ Print rotation properties. """
  if what is None:
    what = "rotation properties"
  print(f"""{what}:
  r:   {props['r']:7.2f}   {Units.LEN.value}
  a:   {props['a']:9.4f} {Units.A.value}
  g:   {Eq.stdg(props['a']):8.3f}  {Units.G.value}
  v:   {props['v']:7.2f}   {Units.V_LIN.value} \
({Eq.kph(props['v']):.2f} {Units.KPH.value})
  w:   {props['w']:9.4f} {Units.V_ANG.value} \
({m.degrees(props['w']):.2f} {Units.V_ANG_DEG.value})
  T:   {props['T']:7.2f}   {Units.T.value}
  hz:  {Eq.hz(props['T']):9.4f} {Units.HZ.value}
  rpm: {Eq.rpm(props['T']):7.2f}   {Units.RPM.value}""")

def test_equations():
  """ Test Eq class. """
  print('Test Eq.T() - rotation time period')
  tdata = [(Units.HZ, 0.25), (Units.V_ANG, m.radians(60.0)), (Units.RPM, 3),
      (Units.MASS, 42), ('hz', 5), ('anon', 10)]
  for u, x in tdata:
    print(f"  {x:6.3f} {Units.tovalue(u):<6} -> ", end='')
    try:
      y = Eq.T(x, u)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.T.value}")

  print('Test Eq.hz() - rotation frequency')
  tdata = [0.25, 4]
  for t in tdata:
    print(f"  {t:6.3f} {Units.T.value:<6} -> ", end='')
    try:
      y = Eq.hz(t)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.HZ.value}")

  print('Test Eq.rpm() - rotations/minute')
  tdata = [10, 3]
  for t in tdata:
    print(f"  {t:6.3f} {Units.T.value:<6} -> ", end='')
    try:
      y = Eq.rpm(t)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.RPM.value}")

  print('Test Eq.omega() - angular velocity (independent of radius)')
  tdata = [30.0]
  for t in tdata:
    print(f"  {t:6.3f} {Units.T.value:<6} -> ", end='')
    try:
      y = Eq.omega(t)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.W.value} "
            f"({m.degrees(y):5.2f} {Units.V_ANG_DEG.value})")

  print('Test Eq.T_rv() - rotation time period from radius and tan. velocity')
  tdata = [(100.0, 30.0), (150.0, 12.0),]
  for r, v in tdata:
    print(f"  {r:5.1f} r, {v:6.3f} {Units.V.value:<6} -> ", end='')
    try:
      y = Eq.T_rv(r, v)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.T.value}")

  print('Test Eq.v() - tangential velocity')
  tdata = [(50.0, m.radians(60.0), Units.V_ANG), (25.0, Eq.accel(0.5), Units.A),
        (100.0, 30.0, Units.T), (50.0,  42.0, Units.LEN), (100.0, 30.0, 's'),
        (10.0, 33.9, 'atom'),]
  for r, x, u in tdata:
    print(f"  {r:5.1f} r, {x:6.3f} {Units.tovalue(u):<6} -> ", end='')
    try:
      y = Eq.v(r, x, u)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.V.value}")

  print('Test Eq.w() - angular velocity')
  tdata = [(50.0, 10.0, Units.V_LIN), (25.0, Eq.accel(0.5), Units.A),
        (25.0, Eq.accel(0.5), 'm/s^2'), (100.0, 30.0, Units.T),
        (50.0,  42.0, Units.MASS)]
  for r, x, u in tdata:
    print(f"  {r:5.1f} r, {x:6.3f} {Units.tovalue(u):<6} -> ", end='')
    try:
      y = Eq.w(r, x, u)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.W.value} "
            f"({m.degrees(y):5.2f} {Units.V_ANG_DEG.value})")

  print('Test Eq.a() - centripetal acceleration')
  tdata = [(50.0, 10.0, Units.V_LIN), (25.0, m.radians(180), Units.V_ANG),
        (100.0, 30.0, Units.T), (50.0,  42.0, Units.MASS),
        (50.0,  42.0, 'palm/s')]
  for r, x, u in tdata:
    print(f"  {r:5.1f} r, {x:6.3f} {Units.tovalue(u):<6} -> ", end='')
    try:
      y = Eq.a(r, x, u)
    except ValueError as e:
      print(e)
    else:
      print(f"{y:5.2f} {Units.A.value}")

def test_props(r=50.0, x=1.0, xunits=Units.G):
  """ Test rotation_properties(). """
  print(f"""\
input:
  r: {r:.2f} {Units.LEN.value}
  x: {x:.4f} {Units.tovalue(xunits)}""")
  props = rotation_properties(r, x, xunits)
  print_properties(props, "properties")

def test_props_equiv():
  """ Test rotation_properties() equivalencies. """
  r = 50.0
  g = 1.0
  props = rotation_properties(r, g, Units.G)
  tdata = [(props['a'], Units.A), (Eq.stdg(props['a']), Units.G),
      (props['v'], Units.V_LIN),
      (props['w'], Units.V_ANG), (m.degrees(props['w']), Units.V_ANG_DEG),
      (props['T'], Units.T),
      (Eq.rpm(props['T']), Units.RPM),
      ]
  print(f"Test {len(tdata)} equivalent rotation_properties()")
  for x, u in tdata:
    test_props(r, x, u)

def reference_space_station(r_rim=50.0, g_rim=1.0):
  """
  Determine the properties of a simple reference design of a space station.

  See: https://www.artificial-gravity.com/sw/SpinCalc/
  """
  # The rim is made from connected pressurized cylindrical modules.
  rim_mod_diameter      = 8.0     # outer diameter
  rim_mod_height        = 13.0    # outer height
  rim_mod_deck_spacing  = 3.0     # interior deck spacing
  rim_mod_decks_numof   = 4       # number of decks

  # Pressurized spokes connect the rim and hub.
  spokes_numof    = 6       # number of spokes
  spoke_diameter  = 8.0     # outer diameter

  # The hub is made from connected pressurized cylindrical modules.
  hub_mod_diameter      = 8.0     # outer diameter
  hub_mod_height        = 6.0     # outer height
  hub_mod_deck_spacing  = 3.0     # interior deck spacing
  hub_mod_decks_numof   = 2       # number of decks

  # A cargo hub module supports cargo handling between space craft and
  # the station. Each cargo module has one or more air locks facing hubward.
  hub_cargo_diameter = 8.0
  hub_cargo_height = 10.0
  hub_cargo_decks_numof = 2
  hub_cargo_deck_height = 5.0
  hub_cargo_airlock_door_width = 6.0
  hub_cargo_airlock_door_height = 5.0

  # The center of the station is open to facilitate space craft docking
  # operations.
  docking_radius      = 8.0   # open, unpressurized radius
  docking_latch_width = 4.0   # space craft latch mechanism width

  print(f"""\
                   Reference Space Station
The spinning space station comprises a rim, spokes, and hub pressurized zones,
plus one unpressurized, open vacuum docking zone at the station center. The
decks are numbered from lowest (outer) level inward within each zone.

The input r_rim specifies the lowest (outer) rim deck radius from the center of
rotation, while g_rim specifes the target centripetal acceleration at r_rim.
-------------------------------------------------------------------------------
input:
  r_rim: {r_rim:.2f} {Units.LEN.value}
  g_rim: {g_rim:.3f} {Units.G.value}""")

  ss = rotation_properties(r_rim, g_rim, Units.G)

  print_properties(ss, "rotation properties")

  print(f"rim decks at {rim_mod_deck_spacing} {Units.LEN.value} spacing:")
  rim_decks = []
  for i in range(rim_mod_decks_numof):
    r = r_rim - rim_mod_deck_spacing * i
    rim_decks.append(Eq.stdg(Eq.a(r, ss['w'], Units.W)))
    print(f"  deck {i}: {r:7.2f} {Units.LEN.value}, "
          f"{rim_decks[i]:.3f} {Units.G.value}")

  print(f"hub work decks at {hub_mod_deck_spacing} {Units.LEN.value} spacing:")
  hub_decks = []
  for i in range(hub_mod_decks_numof):
    r = docking_radius + hub_mod_height - hub_mod_deck_spacing * i
    hub_decks.append(Eq.stdg(Eq.a(r, ss['w'], Units.W)))
    print(f"  deck {i}: {r:7.2f} {Units.LEN.value}, "
          f"{hub_decks[i]:.3f} {Units.G.value}")

  print(f"hub cargo decks at {hub_cargo_deck_height} "
        f"{Units.LEN.value} spacing:")
  cargo_decks = []
  for i in range(hub_cargo_decks_numof):
    r = docking_radius + hub_cargo_height - hub_cargo_deck_height * i
    cargo_decks.append(Eq.stdg(Eq.a(r, ss['w'], Units.W)))
    print(f"  deck {i}: {r:7.2f} {Units.LEN.value}, "
          f"{cargo_decks[i]:.3f} {Units.G.value}")

  print(f"central docking:")
  hull = {}
  hull['g'] = Eq.stdg(Eq.a(docking_radius, ss['w'], Units.W))
  hull['v'] = Eq.v(docking_radius, ss['w'], Units.W)
  print(f"  hull (od = {docking_radius:.2f} {Units.LEN.value}):")
  print(f"    {hull['g']:.3f} {Units.G.value}")
  print(f"    {hull['v']:.3f} {Units.V.value} "
        f"({Eq.kph(hull['v']):0.2f} {Units.KPH.value})")
  r = docking_latch_width/2.0
  latch = {}
  latch['g'] = Eq.stdg(Eq.a(r, ss['w'], Units.W))
  latch['v'] = Eq.v(r, ss['w'], Units.W)
  print(f"  latch (half-span = {r:.2f} {Units.LEN.value}):")
  print(f"    {latch['g']:.3f} {Units.G.value}")
  print(f"    {latch['v']:.3f} {Units.V.value} "
        f"({Eq.kph(latch['v']):0.2f} {Units.KPH.value})")
