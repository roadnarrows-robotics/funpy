"""
Tower of Hanoi puzzle.

Package:
  RoadNarrows fun package.

File:
  hanoi.py

Link:
  https://github.com/roadnarrows-robotics/

Copyright:
  (c) 2019. RoadNarrows LLC
  https://www.roadnarrows.com
  All Rights Reserved

License:
  MIT
"""

# unicode line and block drawing elements to visualize the game
uDblHoriz       = "\u2550"
uDblVert        = "\u2551"
uDblUpTee       = "\u2569"
uDblVert1Horiz  = "\u256b"
uHeavyHoriz     = "\u2501"
uBlkLowQtr      = "\u2582"
uBlkLowHalf     = "\u2584"
uBlkLow58       = "\u2585"

##-
class CharBox:
  """ Lines by columns character box class. """
  def __init__(self, lines=0, columns=0):
    """
    Initializer.

    Parameters:
      lines   Number of lines.
      columns Number of character columns.
    """
    self.lines    = lines
    self.columns  = columns

  def isdefined(self):
    """ Return if character box is [not] defined. """
    return self.lines > 0 and self.columns > 0

RENDER_AS_VALUE  = 'value'
RENDER_AS_SYMBOL = 'symbol'

##-
class Peg:
  """
  Peg of disks class.
  """
  def __init__(self, label, disks=[]):
    """
    Initializer.

    Parameters:
      label   String label associated with this peg.
      disks   List of disk values. Can be numbers, strings, etc. Values
              are assumed to be sorted from smallest to largest, however
              the concept of size is defined by the user.
    """
    self.label = label
    self.disks = disks.copy()

  def __repr__(self):
    """ String representation. """
    return f"{self.label}: {self.disks}"

  def __len__(self):
    """ Number of disks on peg. """
    return len(self.disks)

  def __getitem__(self, i):
    """ x.__getitem__(i) <==> x.disks[i] """
    return self.disks[i]

  def copy(self):
    """ Shallow copy of self. """
    return Peg(self.label, self.disks)

  def calc_charbox(self, render=RENDER_AS_VALUE):
    """
    Given a set of disks, calculate the minimum character box required
    to draw the peg of disks.

    Parameters:
      render  Render peg of disks as ascii disk values or symbolically
              in unicode blocks. One of:
                RENDER_AS_VALUE  (== 'value')
                RENDER_AS_SYMBOL (== 'symbol')
    Returns:
      CharBox class instance.
    """
    n = len(self.disks)
    box = CharBox()
    box.lines = 3 + n # pegtip + disks + pegbase + label
    if render == RENDER_AS_SYMBOL:
      box.columns = n * 2 + 1
    else:
      box.columns = 3
      for i in range(n):
        w = len(f"{self.disks[i]}")
        if w > box.columns:
          box.columns = w
    return box

  def bake(self, box, render=RENDER_AS_VALUE):
    ndisks  = len(self.disks)     # number of disks on this peg
    h_shaft = box.lines - 3       # peg shaft height (lines)
    w       = box.columns         # peg width (chars)

    # center text block functionette
    def ctext(w, s):
      spl = max((w - len(s))//2, 0)         # left spacing count
      spr = max(w - len(s) - spl, 0)        # right spacing count
      return f"{'':>{spl}}{s}{'':>{spr}}"   # centered text block

    if render == RENDER_AS_SYMBOL:
      peg_tip       = '' #uDblVert
      peg_shaft_seg = uDblVert
      peg_base      = uDblHoriz + uDblUpTee + uDblHoriz
    else:
      peg_tip       =  '' #'.'
      peg_shaft_seg =  '' #'|'
      peg_base      = '-^-'
      
    self.box    = box
    self.baked  = []

    self.baked.append(ctext(w, peg_tip))
    self.baked_shaft_seg = ctext(w, peg_shaft_seg)
    for i in range(h_shaft-ndisks):
      self.baked.append(self.baked_shaft_seg)
    for i in range(ndisks):
      if render == RENDER_AS_SYMBOL:
        horiz = uBlkLowHalf * (i + 1)
        disk = horiz + uDblVert1Horiz + horiz
      else:
        disk = f"{self.disks[i]}"
      self.baked.append(ctext(w, disk))
    self.baked.append(ctext(w, peg_base))
    self.baked.append(ctext(w, self.label))

  def raster(self):
    for line in range(len(self.baked)):
      draw_seg(line, 0)
      print("")

  def draw_seg(self, line, indent):
    print(f"{'':>{indent}}{self.baked[line]}", end='')

  def move_top_disk(self, peg_dst):
    i = self.disknum_to_linenum(0)
    disk = self.disks.pop(0)
    peg_dst.disks.insert(0, disk)
    j = peg_dst.disknum_to_linenum(0)
    peg_dst.baked[j] = self.baked[i]
    self.baked[i] = self.baked_shaft_seg

  def disknum_to_linenum(self, disknum):
    ndisks    = len(self.disks)       # number of disks on this peg
    i_bottom  = len(self.baked) - 2   # baked index of bottom disk
    #print('DBG', ndisks, i_bottom, disknum)
    return i_bottom - ndisks + disknum

##-
class TowerOfHanoi:
  def __init__(self, pegA, pegB=Peg('B'), pegC=Peg('C'),
                      render=RENDER_AS_VALUE, trace=False):
    self.pegs   = [pegA.copy(), pegB.copy(), pegC.copy()]
    self.trace  = trace
    self.bake(render)
    self.numOfMoves = 0

  def bake(self, render=RENDER_AS_VALUE):
    self.box = self.pegs[0].calc_charbox(render)
    for peg in self.pegs:
      peg.bake(self.box, render)
    self.spacing = [0, 1, 1]

  def solve(self):
    ndisks = len(self.pegs[0])
    if ndisks == 0:
      print("No disks to move.")
      return
    self.numOfMoves = 0
    if self.trace:
      self.printstate("Starting state")
    self.raster_draw()
    self.solve_r(self.pegs[0], self.pegs[1], self.pegs[2], ndisks)

  def solve_r(self, pegSrc, pegDst, pegTmp, ndisks):
    """
    Recursively move n disks from source peg to destination peg, using
    the temporary peg for help.
    """
    assert(ndisks > 0)

    # n-1 disks
    ndisks1 = ndisks - 1

    # move the top n-1 disks from source to temporary
    if ndisks1 > 0:
      if self.trace:
        print(f"* Move the top {ndisks1} disks",
              f"from src peg {pegSrc.label} to tmp peg {pegTmp.label}")
      self.solve_r(pegSrc, pegTmp, pegDst, ndisks1)

    # move the n'th disk from source to destination
    self.numOfMoves += 1
    pegSrc.move_top_disk(pegDst)
    if self.trace:
      print(f"* Moved disk '{pegDst[0]}'",
            f"from src peg {pegSrc.label} to dst peg {pegDst.label}")
      self.printstate(f"Move {self.numOfMoves}")
    self.raster_draw()

    # finally move the n-1 disks from temporary to destination
    if ndisks1 > 0:
      if self.trace:
        print(f"* Move top {ndisks1} disks",
              f"from tmp peg {pegTmp.label} to dst peg {pegDst.label}")
      self.solve_r(pegTmp, pegDst, pegSrc, ndisks1)

  def raster_draw(self):
    for line in range(self.box.lines):
      for i in range(len(self.pegs)):
        self.pegs[i].draw_seg(line, self.spacing[i])
      print("")
    print("")

  def printstate(self, what=""):
    if len(what) > 0:
      print(f"  {what}:")
    for peg in self.pegs:
      print(peg)
    print("")

  def tracing(self, onoff):
    self.trace = onoff

# some example ToH starting positions
PegAEmpty = Peg('A')
PegAOdds  = Peg('A', [1, 3, 5, 7, 9])
PegAPoem  = Peg('A',
    ["I", "go", "now", "ergo", "celeb", "Indigo", "loosens", "superego"])

if __name__ == '__main__':
  import sys
  import os
  import argparse
  import textwrap
  from fun.common.args import SmartFormatter

  parser = argparse.ArgumentParser(
      formatter_class=SmartFormatter,
      description="""\
Tower of Hanoi

Setup:
  Three pegs serve to hold disks. At the start, the first peg A
  holds all of disks in ascending order by size. Pegs B and C
  are empty.

Goal:
  Move all disks from peg A to peg B. Peg C serves as a temporary
  helper peg.

Rules:
  1. Only one disk can be moved at a time.
  2. A move consists of popping the top disk from a peg and
     placing it on top of another, possibly empty, stack of 
     disks located on a different peg.
  3. No larger disk may be placed on top of a smaller disk.

This python module solves the ToH puzzle recursively as follows:
  Step 1. Move n-1 disks to temporary helper peg.
  Step 2. Move nth disk to destination peg.
  Step 3. Move n-1 disks from temporary peg to destination peg.
""")

  parser.add_argument('--render',
      type=str,
      required=False,
      choices=[RENDER_AS_VALUE, RENDER_AS_SYMBOL],
      default=RENDER_AS_VALUE,
      help=f"""R|\
Output rendering. One of:
  {RENDER_AS_VALUE}     Render disks in string converted disk
            values.
  {RENDER_AS_SYMBOL}    Render disks in unicode block symbols.
  (default: {RENDER_AS_VALUE})""")

  parser.add_argument('--trace',
      action='store_true',
      help="""Enable debug tracing.""")

  parser.add_argument('DISKS',
      type=str,
      help="""R|\
List of disks to be placed on peg A at start of game.
  N     Integer to generate list [1, 2, ..., N].
  odds  Canned list [1, 3, 5, 7, 9].
  poem  Canned list of words masquerading as a poem.
  LIST  User defined list of format: [value, ...].""")

  def main(argv):
    # Parse command-line.
    argv0 = os.path.basename(argv[0])
    args  = parser.parse_args(argv[1:])

    kwdict = vars(args)

    #print("DBG: args={}".format(kwdict))

    key = 'DISKS'
    sval = kwdict[key]
    if sval == 'odds':
      pegA = PegAOdds
    elif sval == 'poem':
      pegA = PegAPoem
    else:
      try:
        val = eval(sval)
      except SyntaxError as inst:
        print(f"{argv0}: error: {inst.msg} argument: {key}='{sval}'",
            file=sys.stderr)
        return 2
      except Exception as inst:
        print(f"{argv0}: error: {inst}: {key}='{sval}'", file=sys.stderr)
        return 2
      if isinstance(val, int):
        pegA = Peg('A', list(range(1, val+1)))
      elif isinstance(val, list):
        pegA = Peg('A', val)
      elif isinstance(val, tuple):
        pegA = Peg('A', list(val))
      else:
        print(f"{argv0}: error: unsupported argument type: {key}='{sval}'",
            file=sys.stderr)
        return 2

    toh = TowerOfHanoi(pegA, render=kwdict['render'], trace=kwdict['trace'])
    toh.solve()
    
    return 0

  # execute
  sys.exit(main(sys.argv))
