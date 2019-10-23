"""
The game of checkers (draughts).

Package:
  RoadNarrows fun package.

Link:
  https://github.com/roadnarrows-robotics/

Copyright:
  (C) 2019. RoadNarrows LLC
  http://www.roadnarrows.com
  All Rights Reserved

License:
  MIT
"""

from enum import Enum
import collections
import re
import time
from datetime import timedelta
import random

def enumfactory(enummeta, value):
  """
  Convert value to enumeration class object.

  Parameters:
    enummeta  EnumMeta class.
    value     Value to convert into enum. String, integer, enum.


  Return:
    Converted enum.
  """
  try:
    if isinstance(value, str):
      return enummeta[value.upper()]
    else:
      return enummeta(value)
  except (KeyError, ValueError):
    raise CheckersError(f"{value!r}", f"not a valid {enummeta.__name__} value")

#
# Enumeration value helpers.
#
# enum is instance of Enum
#
enumlower       = lambda enum: enum.name.lower()
enumupper       = lambda enum: enum.name.upper()
enumcapitalize  = lambda enum: enum.name.capitalize()

# numeric superscript unicode mappings
SupMapping = {
  '0': '\u2070', '1': '\u00b9', '2': '\u00b2', '3': '\u00b3', '4': '\u2074',
  '5': '\u2075', '6': '\u2076', '7': '\u2077', '8': '\u2078', '9': '\u2079',
}
  
# numeric subscript unicode mappings
SubMapping = {
  '0': '\u2080', '1': '\u2081', '2': '\u2082', '3': '\u2083', '4': '\u2084',
  '5': '\u2085', '6': '\u2086', '7': '\u2087', '8': '\u2088', '9': '\u2089',
}

def superscript(n):
  """
  Generate unicode superscript string.

  Parameters:
    n     Non-negative integer

  Returns:
    Superscript encoded string.
  """
  s = str(n).strip()
  ss = ''
  for c in s:
    ss += SupMapping[c]
  return ss

def subscript(n):
  """
  Generate unicode subscript string.

  Parameters:
    n     Non-negative integer

  Returns:
    subscript encoded string.
  """
  s = str(n).strip()
  ss = ''
  for c in s:
    ss += SubMapping[c]
  return ss

# Common ANSI terminal color escape sequences
C_pre   = '\033['
C_sep   = ';'
C_post  = 'm'
C_dft   = ''          # terminal default color

# intensity
C_norm  = '0'
C_bold  = '1'
C_faint = '2'

# foreground (character) color
C_fg_black    = '30'
C_fg_red      = '31'
C_fg_green    = '32'
C_fg_yellow   = '33'
C_fg_blue     = '34'
C_fg_magenta  = '35'
C_fg_cyan     = '36'
C_fg_white    = '37'
    
# background color
C_bg_black    = '40'
C_bg_red      = '41'
C_bg_green    = '42'
C_bg_yellow   = '43'
C_bg_blue     = '44'
C_bg_magenta  = '45'
C_bg_cyan     = '46'
C_bg_white    = '47'

# reset terminal to defaults sequence '\033[0m'
C_Reset     = C_pre + C_norm + C_post

# Build ANSI color escape sequence.
#   i   foreground intensity
#   fg  foreground color
#   bg  background color
ansi_color = lambda i, fg, bg: C_pre + i + C_sep + fg + C_sep + bg + C_post


#------------------------------------------------------------------------------
# Class CheckersError
#------------------------------------------------------------------------------
class CheckersError(Exception):
  """ Checkers error exception class. """

  def __init__(self, *args):
    """
    Initializer.

    Parameters:
      args    One or more error message strings.
    """
    self.args = args

  def __repr__(self):
    return f"{self.__module__}.{self.__class__.__name__}"\
            '(' + ', '.join([repr(s) for s in self.args]) + ')'

  def __str__(self):
    return ': '.join(self.args)

#------------------------------------------------------------------------------
# Class CheckersPiece
#------------------------------------------------------------------------------
class CheckersPiece:
  """ Checkers piece class. """

  # Piece (symbolic) color
  class Color(Enum):
    BLACK = 0 
    WHITE = 1

  # Okay, type or class are better names but they are also keywords...
  class Caste(Enum):
    MAN   = 0 
    KING  = 1

  # Unicode versions of black/white man/king.
  # Note: The white and black codes can be reversed on dark square colors
  #       for better clarity.
  Figurines = {
    Color.BLACK: {Caste.MAN: '\u26c2', Caste.KING: '\u26c3'},
    Color.WHITE: {Caste.MAN: '\u26c0', Caste.KING: '\u26c1'},
  }

  def __init__(self, color, caste, ident=0):
    """
    Initializer.

    Parameters:
      color   Color of piece. One of:
                'black', 'white', 0, 1, Color.BLACK, Color.WHITE
      caste   Piece caste. One of:
                'man', 'king', 0, 1, Caste.MAN, Caste.KING
      ident   Piece unique identity carried to the grave and beyond.
    """
    self._color  = enumfactory(CheckersPiece.Color, color)
    self._caste  = enumfactory(CheckersPiece.Caste, caste)
    self._ident  = ident

  def __repr__(self):
    return f"{self.__module__}.{self.__class__.__name__}"\
      f"({self._color.name!r}, {self._caste.name!r}, ident={self._ident!r})"

  def __str__(self):
    return f"{enumlower(self._color)} {enumlower(self._caste)}"

  def fqname(self):
    """ Return fully-qualified piece name string. """
    return f"{enumlower(self.color)}.{enumlower(self.caste)}.{self.ident}"

  def copy(self):
    """ Copy piece. """
    return CheckersPiece(self.color, self.caste, ident=self.indet)

  @property
  def color(self):
    return self._color

  @property
  def caste(self):
    return self._caste

  @caste.setter
  def caste(self, caste):
    self._caste = enumfactory(CheckersPiece.Caste, caste)

  @property
  def ident(self):
    return self._ident

  @property
  def figurine(self):
    return self.Figurines[self.color][self.caste]

  def foe(self):
    """ 
    Get this piece's foe's color.

    Return:
      CheckersPiece.Color enum.
    """
    if self.color == CheckersPiece.Color.BLACK:
      return CheckersPiece.Color.WHITE
    else:
      return CheckersPiece.Color.BLACK

  @classmethod
  def opposite_color(klass, color):
    """ 
    Get the opposite color to the given color.

    Parameters:
      color   Color of piece. One of:
                'black', 'white', 0, 1, Color.BLACK, Color.WHITE

    Return:
      CheckersPiece.Color enum.
    """
    thegoodside = enumfactory(CheckersPiece.Color, color)
    if thegoodside == CheckersPiece.Color.BLACK:
      return CheckersPiece.Color.WHITE
    else:
      return CheckersPiece.Color.BLACK

#------------------------------------------------------------------------------
# Class CheckersBoard
#------------------------------------------------------------------------------
class CheckersBoard:
  """ Checkers board class. """

  BoardDefaultSize = 8

  # Square symbolic color or shade
  class SquareColor(Enum):
    DARK  = 0 
    LIGHT = 1

  def __init__(self, size):
    """
    Initializer.

    Parameters:
      size    Side length of board in squares. The board will be size x size.
    """
    if size <= 0:           # bad range
      size = BoardDefaultSize
    elif size % 2 == 1:     # must be even
      size = size + 1
    self._size = size

    self._dark_squares_per_row = self._size // 2

    self._rnum_min  = 1
    self._rnum_max  = self.dark_squares_per_row * self._size
    self._kings_row = { CheckersPiece.Color.BLACK: self._size-1,
                        CheckersPiece.Color.WHITE: 0 }

    self._pieces = {}

  def __repr__(self):
    return f"{self.__module__}.{self.__class__.__name__}"\
      f"(size={self._size!r})"

  def __str__(self):
    return f"{self._size}x{self._size} checkers board"

  def __getitem__(self, rnum):
    """ __getitem__(self, rnum) <==> pieces[rnum] """
    return self._pieces[rnum]

  def __setitem__(self, rnum, piece):
    """ __setitem__(self, rnum, piece) <==> pieces[rnum] = piece """
    self._pieces[rnum] = piece

  def __delitem__(self, rnum):
    """ __delitem__(self, rnum, piece) <==> del pieces[rnum] """
    del self._pieces[rnum]

  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  # Piece manipulation methods
  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

  def add_new_piece(self, rnum, color, caste):
    """
    Add a new piece to the board. The square must be empty.

    Parameters:
      rnum    Reachable number in standardized checkers notation.
      color   Color of piece. One of:
                'black', 'white', 0, 1, Color.BLACK, Color.WHITE
      caste   Piece caste. One of:
                'man', 'king', 0, 1, Caste.MAN, Caste.KING

    Return:
      Added piece.
    """
    self._chk_rnum(rnum)
    if self.is_square_occupied(rnum):
      raise CheckersError(self._s_pos(rnum),
                          f"{self._pieces[rnum]} occupies square")
    self._pieces[rnum] = CheckersPiece(color, caste, ident=rnum)
    return self.at(rnum)

  def remove_piece(self, rnum):
    """
    Remove a piece from the board. The piece must exists.

    Parameters:
      rnum    Reachable number in standardized checkers notation.

    Return:
      Returns removed piece.
    """
    self._chk_rnum(rnum)
    if self.is_square_empty(rnum):
      raise CheckersError(self._s_pos(rnum), "no piece found")
    return self._pieces.pop(rnum)

  def replace_piece(self, rnum, piece):
    """
    Replace a piece that was temporarily removed from the board. May be in
    a different location. The square must be empty.

    Parameters:
      rnum    Reachable number in standardized checkers notation.
      piece   Checkers piece.
    """
    self._chk_rnum(rnum)
    if self.is_square_occupied(rnum):
      raise CheckersError(self._s_pos(rnum),
                          f"{self._pieces[rnum]} occupies square")
    self._pieces[rnum] = piece

  def move_piece(self, rnum_from, rnum_to):
    """
    Move a piece. The source square must contain a piece and the destination
    must be empty. No validation of any move rules are made. Move rules are
    determined by the derived Checkers.

    Parameters:
      rnum_from   Source square specified by a reachable number in
                  standardized checkers notation.
      rnum_to     Desination square specified by a reachable number in
                  standardized checkers notation.
    """
    self._chk_rnum(rnum_from)
    self._chk_rnum(rnum_to)
    if self.is_square_empty(rnum_from):
      raise CheckersError(self._s_pos(rnum_from), "no piece found")
    if self.is_square_occupied(rnum_to):
      raise CheckersError(self._s_pos(rnum_to),
                          f"{self._pieces[rnum_to]} occupies square")
    self._pieces[rnum_to] = self._pieces.pop(rnum_from)

  def promote_piece(self, rnum, only_kings_row=True):
    """
    Promote piece to a king. The piece must exists, and conditionally,
    must be positioned on its king's row.

    Parameters:
      rnum            Reachable number in standardized checkers notation.
      only_kings_row  If True then promotion is only allowed if the piece
                      is on its respective king's row.
    """
    self._chk_rnum(rnum)
    if self.is_square_empty(rnum):
      raise CheckersError(self._s_pos(rnum), "no piece found")
    if only_kings_row:
      row,col = self.rowcol(rnum)
      krow = self.kings_row(self._pieces[rnum].color)
      if row != krow:
        raise CheckersError(self._s_pos(rnum), f"piece not on kings row {krow}")
    self._pieces[rnum].caste = 'king'

  def demote_piece(self, rnum):
    """
    Demote piece to a man. The piece must exists.

    Parameters:
      rnum            Reachable number in standardized checkers notation.
    """
    self._chk_rnum(rnum)
    if self.is_square_empty(rnum):
      raise CheckersError(self._s_pos(rnum), "no piece found")
    self._pieces[rnum].caste = 'man'

  def promotable(self, rnum, only_kings_row=True):
    """
    Test if a piece is promotable.

    Parameters:
      rnum            Reachable number in standardized checkers notation.
      only_kings_row  If True then promotion is only allowed if the piece
                      is on its respective king's row.

    Return:
      True or False.
    """
    self._chk_rnum(rnum)
    if self.is_square_empty(rnum):
      raise CheckersError(self._s_pos(rnum), "no piece found")
    piece = self.at(rnum)
    if piece.caste != CheckersPiece.Caste.MAN:
      return False
    elif not only_kings_row:
      return True
    else:
      row,col = self.rowcol(rnum)
      return row == self.kings_row(piece.color)

  def clear(self):
    """ Clear board of all pieces. """
    self._pieces = {}

  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  # Board methods
  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

  def is_square_occupied(self, *pos):
    """
    Test if square is occupied.

    Parameters:
      pos   Board position specified as a reachable number rnum or in
            row,col coordinates.

    Return:
      True or False.
    """
    if len(pos) == 1:
      rnum = pos[0]
    elif len(pos) == 2:
      rnum = self.rnum(*pos)
    else:
      raise TypeError(f"is_square_occupied() takes 1 or 2 positional arguments"\
                      " but {len(pos)} were given") 
    self._chk_rnum(rnum)
    return rnum in self._pieces
    
  def is_square_empty(self, *pos):
    """
    Test if square is empty.

    Parameters:
      pos   Board position specified as a reachable number rnum or in
            row,col coordinates.

    Return:
      True or False.
    """
    if len(pos) == 1:
      rnum = pos[0]
    elif len(pos) == 2:
      rnum = self.rnum(*pos)
    else:
      raise TypeError(f"is_square_empty() takes 1 or 2 positional arguments"\
                      " but {len(pos)} were given") 
    self._chk_rnum(rnum)
    return not rnum in self._pieces

  def at(self, *pos):
    """
    Retrieve piece at specified location. The piece must exists.

    Parameters:
      pos   Board position specified as a reachable number rnum or in
            row,col coordinates.

    Return:
      Returns piece.
    """
    if self.is_square_empty(*pos):
      raise CheckersError(self._s_pos(*pos), "no piece found")
    if len(pos) == 1:
      return self._pieces[pos[0]]
    else:
      return self._pieces[self.rnum(*pos)]

  def numof_pieces(self):
    """ Return the number of pieces currently on the board. """
    return len(self._pieces)

  def numof_black_pieces(self):
    """ Return the number of black pieces currently on the board. """
    n = 0
    for rnum,piece in self._pieces.items():
      if piece.color == CheckersPiece.Color.BLACK:
        n += 1
    return n

  def numof_white_pieces(self):
    """ Return the number of white pieces currently on the board. """
    n = 0
    for rnum,piece in self._pieces.items():
      if piece.color == CheckersPiece.Color.WHITE:
        n += 1
    return n

  def listof_positions(self):
    """ Retrieve list of all piece positions in ascending order by rnum. """
    l = []
    for rnum in range(self.rnum_min, self.rnum_max+1):
      if rnum in self._pieces:
        l.append(rnum)
    return l

  @property
  def pieces(self):
    """ Return dictionary of pieces with rnum as key. """
    return self._pieces

  @property
  def rnum_min(self):
    """ Return minimum rnum. """
    return self._rnum_min

  @property
  def rnum_max(self):
    """ Return maximum rnum. """
    return self._rnum_max

  @classmethod
  def is_dark_square(klass, row, col):
    """
    Determine if square is a dark color. Color is determined by alternating
    light/dark patterns.

    Parameters:
      row     Zero based board row index sequencing from top to bottom,
              with black's back row equal to 0.
      col     Zero based board column index sequencing from left to right,
              given black's back row equal to 0.

    Return:
      True or False.
    """
    if row % 2 == 0:
      return col % 2 == 1
    else:
      return col % 2 == 0

  @classmethod
  def is_light_square(klass, row, col):
    """
    Determine if square is a light color. Color is determined by alternating
    light/dark patterns.

    Parameters:
      row     Zero based board row index sequencing from top to bottom,
              with black's back row equal to 0.
      col     Zero based board column index sequencing from left to right,
              given black's back row equal to 0.

    Return:
      True or False.
    """
    return not klass.is_dark_square(row, col)

  def is_pos_on_board(self, *pos):
    """
    Test if row,column position is on the board.

    This method does not raise an exception.

    Parameters:
      pos   Board position specified as a reachable number rnum or in
            row,col coordinates.

    Return:
      True or False
    """
    if len(pos) == 1:
      return (pos[0] >= self.rnum_min) and (pos[0] <= self.rnum_max)
    elif len(pos) == 2:
      return  (pos[0] >= 0) and (pos[0] < self._size) and \
              (pos[1] >= 0) and (pos[1] < self._size)
    else:
      return False

  @classmethod
  def square_color(klass, row, col):
    """
    Retrieve square color at the given row and column.

    Parameters:
      row     Zero based board row index sequencing from top to bottom,
              with black's back row equal to 0.
      col     Zero based board column index sequencing from left to right,
              given black's back row equal to 0.

    Return:
      CheckersBoard.Square color.
    """
    if klass.is_dark_square(row, col):
      return CheckersBoard.SquareColor.DARK
    else:
      return CheckersBoard.SquareColor.LIGHT

  def rnum(self, row, col):
    """
    Convert a board's row,column position to the equivalent standardized
    numbering notation of reachable positions.

    Parameters:
      row     Zero based board row index sequencing from top to bottom,
              with black's back row equal to 0.
      col     Zero based board column index sequencing from left to right,
              given black's back row equal to 0.

    Return:
      Returns reachable number in standardized checkers notation.
    """
    if not self.is_pos_on_board(row, col):
      raise CheckersError(f"(row,col)=({row},{col})", "off-board position")
    elif not self.is_dark_square(row, col):
      raise CheckersError(f"(row,col)=({row},{col})", "not a reachable square")
    return  (row * self.dark_squares_per_row) + \
            (col + CheckersBoard._rowadj(row)) // 2

  def rowcol(self, rnum):
    """
    Convert a board's position specified in the standardized reachable number
    notation to zero based row,column tuple.

    Parameters:
      rnum    Reachable number in standardized checkers notation.

    Return:
      Return 2-tuple (row,col) where:
        row   Zero based board row index sequencing from top to bottom,
              with black's back row equal to 0.
        col   Zero based board column index sequencing from left to right,
              given black's back row equal to 0.
    """
    self._chk_rnum(rnum)
    row = (rnum - 1) // self.dark_squares_per_row
    col = rnum - row * self.dark_squares_per_row
    col = 2 * col - CheckersBoard._rowadj(row)
    if not self.is_pos_on_board(row, col):
      raise CheckersError("BUG", f"position {rnum} -> ({row}, {col})",
                      "off-board position")
    return (row, col)

  @property
  def size(self):
    return self._size

  @property
  def dark_squares_per_row(self):
    return self._dark_squares_per_row

  def kings_row(self, color):
    color = enumfactory(CheckersPiece.Color, color)
    return self._kings_row[color]

  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  # Visualize
  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

  def print_board(self, with_pieces=False, with_annot=False, soi=[],
                        **print_kwargs):
    """
    Print the board in unicode. Print output default is to sys.stdout.

    Parameters:
      with_pieces   Do [not] print any board pieces.
      with_annot    Do [not] print any board annotation.
      soi           Squares of interest. These squares will be highlighted. 
      print_kwargs  Any print() control keyword arguments.
    """
    colorDark           = ansi_color(C_bold, C_fg_black, C_bg_white)
    colorLight          = ansi_color(C_bold, C_fg_black, C_bg_black)
    colorBlackOnDark    = ansi_color(C_bold, C_fg_black, C_bg_white)
    colorWhiteOnDark    = ansi_color(C_bold, C_fg_red, C_bg_white)

    colorDarkSoI        = ansi_color(C_bold, C_fg_black, C_bg_cyan)
    colorBlackOnDarkSoI = ansi_color(C_bold, C_fg_black, C_bg_cyan)
    colorWhiteOnDarkSoI = ansi_color(C_bold, C_fg_red, C_bg_cyan)

    colorSquare   = { CheckersBoard.SquareColor.DARK:  colorDark,
                      CheckersBoard.SquareColor.LIGHT: colorLight }
    colorPiece    = { CheckersPiece.Color.BLACK: colorBlackOnDark,
                      CheckersPiece.Color.WHITE: colorWhiteOnDark }
    colorPieceSoI = { CheckersPiece.Color.BLACK: colorBlackOnDarkSoI,
                      CheckersPiece.Color.WHITE: colorWhiteOnDarkSoI }


    qwidth  = 4                         # square width in characters
    qheight = 2                         # square height in characters
    bwidth  = qwidth * self.size        # board width in characters
    bheight = qheight * self.size       # board height in characters
    sqempty = ' ' * qwidth              # empty square line
    if with_annot:                      # indentation
      indent = '  '
    else:
      indent = ''

    if 'end' in print_kwargs:
      del print_kwargs['end']

    if with_annot:
      print(f"{indent}{'Black':>{bwidth//2+3}}", **print_kwargs, end='\n')
      print(f"{indent}", **print_kwargs, end='')
      for col in range(0, self.size):
        print(f"{col:>{qwidth-1}} ", **print_kwargs, end='')
      print('', **print_kwargs, end='\n')

    for row in range(0, self.size):
      # annotation row
      print(f"{indent}", **print_kwargs, end='')
      for col in range(0, self.size):
        darklight = self.square_color(row, col)
        color     = colorSquare[darklight]
        sq        = sqempty
        if darklight == CheckersBoard.SquareColor.DARK:
          rnum = self.rnum(row, col)
          if rnum in soi:
            color = colorDarkSoI
          if with_annot:
            sq = f"{superscript(rnum):<{qwidth}}"
        print(f"{color}{sq}{C_Reset}", **print_kwargs, end='')
      print('', **print_kwargs, end='\n')

      if with_annot:
        print(f"{row:>2}", **print_kwargs, end='')

      # piece figurine row
      for col in range(0, self.size):
        darklight = self.square_color(row, col)
        color     = colorSquare[darklight]
        sq        = sqempty
        if darklight == CheckersBoard.SquareColor.DARK:
          rnum = self.rnum(row, col)
          if rnum in soi:
            color = colorDarkSoI
          if with_pieces:
            if self.is_square_occupied(rnum):
              piece = self.at(rnum)
              if rnum in soi:
                color = colorPieceSoI[piece.color]
              else:
                color = colorPiece[piece.color]
              sq = f"  {CheckersPiece.Figurines[piece.color][piece.caste]} "
        print(f"{color}{sq}{C_Reset}", **print_kwargs, end='')

      if with_annot:
        print(f"{row:>2}", **print_kwargs, end='\n')
      else:
        print("", **print_kwargs, end='\n')

    if with_annot:
      print(f"{indent}", **print_kwargs, end='')
      for col in range(0, self.size):
        print(f"{col:>{qwidth-1}} ", **print_kwargs, end='')
      print('', **print_kwargs, end='\n')
      print(f"{indent}{'White':>{bwidth//2+3}}", **print_kwargs, end='\n')

  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  # Helpers
  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

  # row adjustment
  _rowadj = lambda row: 1 + row % 2

  def _chk_rnum(self, rnum):
    if rnum < self.rnum_min or rnum > self.rnum_max:
      raise CheckersError(f"{rnum}", "invalid reachable number")

  def _s_pos(self, *pos):
    try:
      if len(pos) == 1:
        rnum = pos[0]
        row, col = self.rowcol(rnum)
      elif len(pos) == 2:
        row, col = pos
        rnum = self.rnum(row, col)
      else:
        return f"position {pos} badly formed"
    except CheckersError:
      return f"position {pos} ?)"
    return f"position {rnum} ({row},{col})"

#------------------------------------------------------------------------------
# Class CheckersMove
#------------------------------------------------------------------------------
class CheckersMove:
  """
  CheckersMove class
  
  Class defines move operations given a game with board.
  """

  # parsed token container
  Token = collections.namedtuple('Token', ['type', 'value', 'column'])

  def __init__(self):
    """ Initializer. """
    self.token_specification = [
      ('RNUM',      r'[1-9]+'),                   # reachable number > 0
      ('MOP',       f'[{Checkers.MopSym.ANY}]'),  # move operators
      ('SKIP',      r'[ \t]+'),                   # skip over spaces and tabs
      ('MISMATCH',  r'.'),                        # any other character
    ]

    self.tok_regex = '|'.join('(?P<%s>%s)' % \
                              pair for pair in self.token_specification)

  def token_generator(self, nota):
    """
    Checkers move token generator.

    Parameters:
      nota    String specifying move in standard notation.

    Yield:
      Token.
    """
    for mo in re.finditer(self.tok_regex, nota):
      kind    = mo.lastgroup
      value   = mo.group()
      column  = mo.start()
      if kind == 'RNUM':
        value = int(value)
      elif kind == 'SKIP':
        continue
      elif kind == 'MISMATCH':
        raise RuntimeError(f"{value!r}", "unexpected token")
      yield CheckersMove.Token(kind, value, column)

  def tokenize(self, nota):
    """
    Checkers move tokenize notation.

    Parameters:
      nota    String specifying move in standard notation.

    Return:
      Returns list of parsed tokens.
    """
    tokens = []
    for tok in self.token_generator(nota):
      #print('DBG:', tok)
      tokens.append(tok)
    return tokens

  def get_move_pattern(self, piece):
    """
    Get the immediate move pattern of the given piece.

    The pattern is a list of deltas from the current (unspecified) position.
      delta := (drow, dcol)

    Parameters:
      piece   Checkers piece with color and caste key data.

    Return:
      List of deltas
    """
    if piece.caste == CheckersPiece.Caste.KING:
      return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    elif piece.color == CheckersPiece.Color.BLACK:
      return [(1, -1), (1, 1)]
    elif piece.color == CheckersPiece.Color.WHITE:
      return [(-1, -1), (-1, 1)]
    else:
      return []

  def find_move_paths(self, game, rnum, jumps_only=False):
    """
    Find all possible move paths associated with the game and board state.
    No moves are actually made.

    A path is a list:
      [rnum, mop, rnum ...]

    Minimum assumptions are made of the game. There must exist a simple move
    and a jump move.

    A simple move only generates one path:
      [rnum, '-', rnum_1].

    A jump move generates one or more paths:
      [rnum, 'x', rnum_1]
      [rnum, 'x', rnum_1, 'x', rnum_2]
        ...
      [rnum, 'x', rnum_1, 'x', rnum_2, ..., 'x' rnum_N]

    Parameters:
      game        The checkers game the move will operate on.
      rnum        Starting move (and piece) position.
      jumps_only  Do [not] only consider jump moves.
      
    Return:
      Returns a list of zero or more paths.
    """
    paths = []
    try:
      piece = game.board.at(rnum)
    except CheckersError:
      return paths
    row, col = game.board.rowcol(rnum)
    deltas = self.get_move_pattern(piece)

    # check all directions for moves
    for drow, dcol in deltas:
      row_adj = row + drow
      col_adj = col + dcol

      # adjacent is still on the board
      if game.board.is_pos_on_board(row_adj, col_adj):
        rnum_adj = game.board.rnum(row_adj ,col_adj)

        # adjacent is occupied
        if game.board.is_square_occupied(rnum_adj):
          piece_adj = game.board.at(rnum_adj)

          # occupied by the opponent
          if piece.foe() == piece_adj.color:
            row_jmp = row_adj + drow
            col_jmp = col_adj + dcol

            # jump move
            if  game.board.is_pos_on_board(row_jmp, col_jmp) and \
                game.board.is_square_empty(row_jmp, col_jmp):

              rnum_jmp = game.board.rnum(row_jmp ,col_jmp)
              path_jmp = [rnum, Checkers.MopSym.JUMP, rnum_jmp]
              #path_jmp = [rnum, (Checkers.MopSym.JUMP, rnum_adj), rnum_jmp]
              paths.append(path_jmp)

              # virtual move
              game.board.move_piece(rnum, rnum_jmp)
              piece_cap = game.board.remove_piece(rnum_adj)

              if game.board.promotable(rnum_jmp):
                game.board.promote_piece(rnum_jmp)
                undo_promo = True
              else:
                undo_promo = False

              paths_move = self.find_move_paths(game, rnum_jmp, jumps_only=True)
              for p in paths_move:
                paths.append(self.join(path_jmp, p))

              # undo virtual move
              game.board.replace_piece(rnum_adj, piece_cap)
              game.board.move_piece(rnum_jmp, rnum)
              if undo_promo:
                game.board.demote_piece(rnum)

        # simple move
        elif not jumps_only:    # empty
          paths.append([rnum, Checkers.MopSym.SIMPLE, rnum_adj])

    return paths

  def has_a_move(self, game, rnum):
    """
    Test if piece has any valid moves.

    Parameters:
      game        The checkers game the move will operate on.
      rnum        Piece position.
      
    Return:
      True or False.
    """
    try:
      piece = game.board.at(rnum)
    except CheckersError:
      return False

    row, col = game.board.rowcol(rnum)
    deltas = self.get_move_pattern(piece)

    # check all directions for moves
    for drow, dcol in deltas:
      row_adj = row + drow
      col_adj = col + dcol

      # adjacent is still on the board
      if game.board.is_pos_on_board(row_adj, col_adj):
        rnum_adj = game.board.rnum(row_adj ,col_adj)

        # simple move available
        if game.board.is_square_empty(rnum_adj):
          return True

        # adjacent is occupied
        else:
          piece_adj = game.board.at(rnum_adj)

          # occupied by the opponent
          if piece.foe() == piece_adj.color:
            row_jmp = row_adj + drow
            col_jmp = col_adj + dcol

            # jump move available
            if  game.board.is_pos_on_board(row_jmp, col_jmp) and \
                game.board.is_square_empty(row_jmp, col_jmp):
              return True

    return False

  def execute_move(self, game, path):
    """
    Execute a move.

    Parameters:
      game    The checkers game the move will operate on.
      path    Move path as a list or string in standard notation.
    """
    # First pass: validate
    if len(path) < 3:
      raise CheckersError(f"{path!r}", "move path too short")
    rnum_0 = path[0]
    piece = game.board.at(rnum_0)
    if piece.color != game.turn:
      raise CheckersError(f"{piece}", f"it's {enumlower(game.turn)}'s turn")
    candidate_paths = self.find_move_paths(game, rnum_0)
    if path not in candidate_paths:
      raise CheckersError(f"{self.path_to_nota(path)}", "not a legal move")

    # Second pass: execute move
    promoted  = piece.caste == CheckersPiece.Caste.KING
    rnum_i    = rnum_0
    i         = 1
    while i < len(path):
      mop     = path[i]
      rnum_j  = path[i+1]
      if mop == Checkers.MopSym.SIMPLE:
        pass
      elif mop == Checkers.MopSym.JUMP:
        rnum_jmp = self.jumped_square(game, rnum_i, rnum_j)
        game.goto_hell(game.board.remove_piece(rnum_jmp))
      rnum_i = rnum_j
      row_i, col_i = game.board.rowcol(rnum_i)
      if not promoted and row_i == game.board.kings_row(piece.color):
        game.board.promote_piece(rnum_0, only_kings_row=False)
        promoted= True
      i += 2
    game.board.move_piece(rnum_0, rnum_i)

  def jumped_square(self, game, rnum_0, rnum_1):
    """
    Determined square jumped from source square to destination square.

    Parameters:
      game      The checkers game the move will operate on.
      rnum_0    Source square as reachable number.
      rnum_1    Destination square as reachable number.

    Return:
      Returns jumped square as reachable number.
    """
    row0,col0 = game.board.rowcol(rnum_0)
    row1,col1 = game.board.rowcol(rnum_1)
    if row1 > row0:
      row0_j = row0 + 1
      row1_j = row1 - 1
    else:
      row0_j = row0 - 1
      row1_j = row1 + 1
    if col1 > col0:
      col0_j = col0 + 1
      col1_j = col1 - 1
    else:
      col0_j = col0 - 1
      col1_j = col1 + 1
    if row0_j != row1_j or col0_j != col1_j:
      raise CheckersError("cannot jump from {rnum_0} to {rnum_1}")
    return game.board.rnum(row0_j, col0_j)

  def join(self, path0, path1):
    """
    Join two move paths into one path.

    The last destination square specified in the first path must match the
    first source square in the second path.

    Parameters:
      path0   Move path to prepend.
      path1   Move path to append.

    Return:
      Move path.
    """
    if len(path0) == 0:
      return path1
    elif len(path1) == 0:
      return path0
    elif path0[-1] == path1[0]:
      return path0 + path1[1:]
    else:
      raise CheckersError(f"path0 {path0[-1]} != path1 {path1[0]}")

  @classmethod
  def max_paths(klass, paths):
    """
    Find the move paths of maximum length.

    Length here is the distance traveled in number of squares.

    Paramaters:
      paths   List of move paths.

    Return:
      List of paths of maximum length. May be empty.
    """
    maxlen   = 0
    maxpaths = []
    for path in paths:
      m = klass.path_len(path)
      if m > maxlen:
        maxlen   = m
        maxpaths = [path]
      elif m == maxlen:
        maxpaths.append(path)
    return maxpaths

  @classmethod
  def max_path_len(klass, paths):
    maxlen = 0
    for path in paths:
      m = klass.path_len(path)
      if m > maxlen:
        maxlen = m
    return m

  @classmethod
  def path_len(klass, path):
    m = 0
    i = 1
    while i < len(path):
      if path[i] == Checkers.MopSym.SIMPLE:
        m += 1
      elif path[i] == Checkers.MopSym.JUMP:
        m += 2
      i += 2
    return m

  @classmethod
  def rnums_in_paths(klass, paths):
    """
    Build list of unique rnums listed in paths.

    Parameters:
      paths   List of move paths.

    Return:
      List of rnums.
    """
    rnums = []
    for path in paths:
      for p in path:
        if str(p) in Checkers.MopSym.ANY:
          continue
        elif p not in rnums:
          rnums.append(p)
    return rnums

  @classmethod
  def path_to_nota(klass, path):
    """
    Convert move path to standard checkers notation.

    Parameters:
      path    Move path.

    Return:
      String
    """
    return ''.join(f"{v}" for v in path)

  def nota_to_path(self, nota):
    """
    Convert notation string to move path

    Parameters:
      nota  String in standard checkers notation.

    Return:
      Move path list.
    """
    try:
      tokens = self.tokenize(nota)
    except RunTimeError as e:
      raise CheckersError(*e.args)
    path = []
    expect = ['RNUM', 'MOP']
    i = 0
    for tok in tokens:
      if tok.type == expect[i]:
        path.append(tok.value)
      else:
        raise CheckersError(f"{nota!r}", f"{tok.value!r}",
              f"expected {expect[i].lower()!r}, got {tok.type.lower()!r}")
      i = (i + 1) % 2
    if len(tokens) % 2 == 0:
      raise CheckersError(f"{nota!r}", "missing last rnum")
    return path

#------------------------------------------------------------------------------
# Class Checkers
#------------------------------------------------------------------------------
class Checkers:
  """ Checkers game abstract base class. """

  # game state
  class State(Enum):
    NOT_STARTED = 0   # game not started
    IN_PLAY     = 1   # game in play
    GAME_OVER   = 2   # game is over

  # move operator symbols
  class MopSym:
    SIMPLE  = '-'   # simple diagonal adjacent square move
    JUMP    = 'x'   # jump diagonal capture move 
    ANY     = '-x'  # any move
  
  # end of game outcomes
  class EoG(Enum):
    NO_EOG  = 0   # no end of game
    ABORT   = 1   # game was aborted (stopped)
    RESIGN  = 2   # player A resigned
    DEFEAT  = 3   # player A defeated player B
    DRAW    = 4   # game ended in a draw
  
  def __init__(self, name, size, mop=CheckersMove):
    """
    Initializer.

    Parameters:
      name    Name (type) of game string.
      size    Board side size (squares).
      mop     Checkers game move operator of pieces.
    """
    self._name      = name                              # name of this game
    self._mop       = mop()                             # move operator object
    self._board     = CheckersBoard(size=size)          # the board
    self._kur       = { CheckersPiece.Color.BLACK: [],
                        CheckersPiece.Color.WHITE: [] } # ancient Sumerian hell
    self._history   = []                                # game history

    self._state     = Checkers.State.NOT_STARTED        # game not started
    self._move_num  = 0                                 # move number
    self._turn      = CheckersPiece.Color.BLACK         # black goes first
    self._eog       = Checkers.EoG.NO_EOG               # end-of-game reason
    self._winner    = None                              # game winner

    self.tstart     = 0                                 # start time
    self.tend       = 0                                 # end time

  def __repr__(self):
    return  f"{self.__module__}.{self.__class__.__name__}"\
            f"({self._name!r}, {self._board.size!r}, {self._mop!r})"

  def __str__(self):
    return f"{self.board.size}x{self.board.size} {self.name}"

  def clear(self):
    """ Clear game state including removing all pieces from the board. """
    self._board.clear()
    self._kur[CheckersPiece.Color.BLACK] = []
    self._kur[CheckersPiece.Color.WHITE] = []
    self._history   = []
    self._state     = Checkers.State.NOT_STARTED
    self._move_num  = 0
    self._turn      = CheckersPiece.Color.BLACK
    self._eog       = Checkers.EoG.NO_EOG
    self._winner    = None
    self.tstart     = 0
    self.tend       = 0
  
  def setup(self):
    """ Setup game with the standard starting position. """
    self.clear()
    self._state     = Checkers.State.NOT_STARTED
    self._move_num  = 1
    self._turn      = CheckersPiece.Color.BLACK

  def make_a_move(self, path):
    """
    Make a move.

    The move is validated including make sure its the player's turn.

    Parameters:
      path      Move path as a list or string in standard notation.
    """
    #print(f'DBG: make_a_move({path})')
    if self._state == Checkers.State.NOT_STARTED:
      self.start()  # auto-start
    elif self._state == Checkers.State.GAME_OVER:
      raise CheckersError("game not setup")
    if isinstance(path, str):
      path = self.mop.nota_to_path(path)
      #print(f'DBG: make_a_move: {path}')
    self.mop.execute_move(self, path)
    self.add_move_to_history(path)
    foe = CheckersPiece.opposite_color(self.turn)
    if not self.check_is_game_over(foe):
      self._turn = foe
      if self.turn == CheckersPiece.Color.BLACK:
        self._move_num += 1

  def take_a_peek(self, rnum):
    """
    Take a peek of all posible moves for a piece at rnum.

    Parameters:
      rnum    Reachable number in standardized checkers notation.

    Return:
      Returns a list of zero or more paths.
    """
    return self.mop.find_move_paths(self, rnum)

  def has_a_move(self, rnum):
    """
    Test if piece has any valid moves.

    Parameters:
      rnum  Piece position.
      
    Return:
      True or False.
    """
    return self._mop.has_a_move(self, rnum)

  def goto_hell(self, piece):
    """
    Send a captured piece to hell.

    Parameters:
      piece   The damned piece.
    """
    self._kur[piece.color].append(piece)

  def start(self):
    """
    Start a game of checkers.

    There must exist at least one piece of each color.
    """
    if self.board.numof_black_pieces() == 0:
      raise CheckersError("no black pieces on board to play a game.")
    if self.board.numof_white_pieces() == 0:
      raise CheckersError("no white pieces on board to play a game.")
    self._state     = Checkers.State.IN_PLAY
    self._move_num  = 1
    self._turn      = CheckersPiece.Color.BLACK
    self.tstart     = time.time()
    self.tend       = 0
    ts = time.localtime(self.tstart)
    tstr = f"{ts.tm_hour:02}:{ts.tm_min:02}:{ts.tm_sec:02}"
    self.add_event_to_history(f"STARTED@{tstr}")

  def stop(self):
    """ Stop (abort) an in-play game. """
    self._state   = Checkers.State.GAME_OVER  # game is aborted
    self._eog     = Checkers.EoG.ABORT
    self._winner  = None
    self.tend     = time.time()
    ts = time.localtime(self.tend)
    tstr = f"{ts.tm_hour:02}:{ts.tm_min:02}:{ts.tm_sec:02}"
    self.add_event_to_history(f"ABORTED@{tstr}")

  def resign(self, color):
    """
    Player resigns from the game.

    Parameters:
      color   Color of player resigning.
    """
    self._state   = Checkers.State.GAME_OVER  # game is over loosa loosa
    self._eog     = Checkers.EoG.RESIGN
    self._winner  = CheckersPiece.opposite_color(color)
    self.tend     = time.time()
    ts = time.localtime(self.tend)
    tstr = f"{ts.tm_hour:02}:{ts.tm_min:02}:{ts.tm_sec:02}"
    self.add_event_to_history(f"RESIGNED({enumlower(color)})@{tstr}")

  def check_is_game_over(self, color):
    """
    Check if the game is over for a player. Usually this is called after
    the player's opponent has made a move.

    If it is game over, the appropriate game state is set.

    Parameters:
      color   Player's color.

    Return:
      Returns True if game over, else False.
    """
    n = 0
    for rnum,piece in self.board.pieces.items():
      if piece.color == color:
        n += 1
        if self.has_a_move(rnum):
          return False
    self.tend = time.time()
    ts = time.localtime(self.tend)
    tstr = f"{ts.tm_hour:02}:{ts.tm_min:02}:{ts.tm_sec:02}"
    if n == 0:
      self._eog       = Checkers.EoG.DEFEAT
      self._winner    = CheckersPiece.opposite_color(color)
      self.add_event_to_history(f"DEFEATED({enumlower(color)})@{tstr}")
    else:
      self._eog       = Checkers.EoG.DRAW
      self._winner    = None
      self.add_event_to_history(f"DRAW@{tstr}")
    self._state = Checkers.State.GAME_OVER
    return True

  def add_event_to_history(self, event):
    """
    Add an event to game history.

    Parameters:
      event   Event to add.
    """
    self._history.append(str(event))

  def add_move_to_history(self, path):
    """
    Add a move to game history.

    Parameters:
      path  Move path as a list or a string in standard notation.
    """
    if isinstance(path, str):
      nota = path
    else:
      nota = self.mop.path_to_nota(path)
    if self.turn == CheckersPiece.Color.BLACK:
      self._history.append(f" {self.move_num}. " + nota)
    else:
      self._history.append(nota)

  @property
  def name(self):
    return self._name

  @property
  def board(self):
    return self._board

  @property
  def mop(self):
    return self._mop

  @property
  def kur(self):
    return self._kur

  @property
  def history(self):
    return self._history

  @property
  def state(self):
    return self._state

  @property
  def move_num(self):
    return self._move_num

  @property
  def turn(self):
    return self._turn

  @property
  def eog(self):
    return self._eog

  @property
  def winner(self):
    return self._winner

  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  # Visualize
  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

  def print_kur(self, **print_kwargs):
    """
    Print the Sumerian hell of captured pieces.

    Print output default is to sys.stdout.

    Parameters:
      print_kwargs  Any print() control keyword arguments.
    """
    if 'end' in print_kwargs:
      del print_kwargs['end']
    print("  Captured:", **print_kwargs, end='\n')
    for color in [CheckersPiece.Color.BLACK, CheckersPiece.Color.WHITE]:
      print(f"{enumcapitalize(color)}: ", **print_kwargs, end='')
      for cursed in self.kur[color]:
        print(f"{cursed.fqname()} ", **print_kwargs, end='')
      print('', **print_kwargs, end='\n')

  def print_history(self, **print_kwargs):
    """
    Print the game history.

    Print output default is to sys.stdout.

    Parameters:
      print_kwargs  Any print() control keyword arguments.
    """
    print("  History:", **print_kwargs, end='\n')
    if 'end' in print_kwargs:
      del print_kwargs['end']
    for event in self.history:
      print(f"{event} ", **print_kwargs, end='')
    print('', **print_kwargs, end='\n')

  def print_outcome(self, **print_kwargs):
    """
    Print the game outcome.

    Print output default is to sys.stdout.

    Parameters:
      print_kwargs  Any print() control keyword arguments.
    """
    if 'end' in print_kwargs:
      del print_kwargs['end']
    if self.state == Checkers.State.NOT_STARTED:
      print("Game not started.", **print_kwargs, end=' ')
    elif self.state == Checkers.State.IN_PLAY:
      print(f"Game is in play with no final outcome.", **print_kwargs, end=' ')
    elif self.state == Checkers.State.GAME_OVER:
      if self.winner is not None:
        winner  = enumcapitalize(self.winner)
        loser   = enumcapitalize(CheckersPiece.opposite_color(self.winner))
      else:
        winner  = 'NoWinner'
        loser   = 'NoLoser'
      if self.eog == Checkers.EoG.NO_EOG:
        print("BUG: Game is over but EoG reason is no end-of-game.",
            **print_kwargs, end=' ')
      elif self.eog == Checkers.EoG.ABORT:
        print(f"Game was aborted on move {self.move_num}.",
            **print_kwargs, end=' ')
      elif self.eog == Checkers.EoG.RESIGN:
        print(f"{winner} won on move {self.move_num} as {loser} resigned.",
            **print_kwargs, end=' ')
      elif self.eog == Checkers.EoG.DEFEAT:
        print(f"{winner} defeated {loser} on move {self.move_num}.",
            **print_kwargs, end=' ')
      elif self.eog == Checkers.EoG.DRAW:
        print(f"Game ended in a draw on move {self.move_num}.",
            **print_kwargs, end=' ')
    if self.tstart > 0:
      if self.tend > 0:
        elapse = self.tend - self.tstart
      else:
        elapse = self.tend - time.time()
    else:
      elapse = 0
    if elapse > 0:
      #print(f"Elapse time {elapse:.2f}s", **print_kwargs, end='\n')
      print(f"Elapse time {str(timedelta(seconds=elapse))}",
          **print_kwargs, end='\n')
    else:
      print('', **print_kwargs, end='\n')

#------------------------------------------------------------------------------
# Class EnglishDraughtsVariation
#------------------------------------------------------------------------------
class EnglishDraughtsVariation(Checkers):
  def __init__(self, name, size, num_rows_per_side):
    Checkers.__init__(self, name, size)
    self._num_rows_per_side = num_rows_per_side
    n = self.num_rows_per_side * self.board.dark_squares_per_row
    self._num_pieces_per_side = n
    self._black_rnum_start    = self.board.rnum_min
    self._black_rnum_end      = self.black_rnum_start + n - 1
    self._white_rnum_end      = self.board.rnum_max
    self._white_rnum_start    = self.white_rnum_end - n + 1

  def setup(self):
    """ Setup game with the standard starting position. """
    Checkers.setup(self)
    for rnum in range(self.black_rnum_start, self.black_rnum_end+1):
      self.board.add_new_piece(rnum, 'black', 'man')
    for rnum in range(self.white_rnum_start, self.white_rnum_end+1):
      self.board.add_new_piece(rnum, 'white', 'man')

  @property
  def num_rows_per_side(self):
    """ Standard starting position number of rows per side. """
    return self._num_rows_per_side

  @property
  def num_pieces_per_side(self):
    """ Standard starting position number of pieces per side. """
    return self._num_pieces_per_side

  @property
  def black_rnum_start(self):
    """ Standard starting position black starting reachable number. """
    return self._black_rnum_start

  @property
  def black_rnum_end(self):
    """ Standard starting position black ending reachable number. """
    return self._black_rnum_end

  @property
  def white_rnum_start(self):
    """ Standard starting position white starting reachable number. """
    return self._white_rnum_start

  @property
  def white_rnum_end(self):
    """ Standard starting position white ending reachable number. """
    return self._white_rnum_end

#------------------------------------------------------------------------------
# Class EnglishDraughts
#------------------------------------------------------------------------------
class EnglishDraughts(EnglishDraughtsVariation):
  """ Also American Checkers """
  StdSize = 8   # 8x8 board
  StdRows = 3   # rows per side

  def __init__(self):
    EnglishDraughtsVariation.__init__(self, "English Draughts",
                                  EnglishDraughts.StdSize,
                                  EnglishDraughts.StdRows)

  def setup(self):
    """ Setup game with the standard starting position. """
    EnglishDraughtsVariation.setup(self)

#------------------------------------------------------------------------------
# Class CheckersBot
#------------------------------------------------------------------------------
class CheckersBot:
  """ Checkers autonmous bot player abstract base class. """

  def __init__(self, tag, color):
    """
    Initializer.

    Parameters:
      tag     Short one-word tag identifying type of player bot.
      color   This bot player's color.
    """
    self._tag   = tag
    self._color = enumfactory(CheckersPiece.Color, color);

  def __repr__(self):
    return  f"{self.__module__}.{self.__class__.__name__}"\
            f"({self._tag!r}, {self._color!r})"

  def __str__(self):
    return self.fqname()

  def fqname(self):
    """ Return fully-qualified name. """
    return f"{enumlower(self.color)}.{self.tag}"

  def make_a_move(self, game):
    """
    Make a bot move. Implement in derived class.

    Parameters:
      game  The active checkers game.

    Return:
      Returns move path executed or empty list if no move is possible.
    """
    raise NotImplementedError("not implemented in CheckersBot abstract class")

  @property
  def tag(self):
    return self._tag

  @property
  def color(self):
    return self._color

#------------------------------------------------------------------------------
# Class CheckersRandomBot
#------------------------------------------------------------------------------
class CheckersRandomBot(CheckersBot):
  """ Checkers autonomous bot player that plays the game by random choices. """
  
  def __init__(self, color):
    """
    Initializer.

    Parameters:
      color   This bot player's color.
    """
    CheckersBot.__init__(self, "random", color)

  def make_a_move(self, game):
    """
    Randomly make a move.

    A piece of this autonomous player's color that has a move is chosen. Of
    the possible moves made by the piece, the longest move path is chosen
    and the move is executed.

    Parameters:
      game  The active checkers game.

    Return:
      Returns move path executed or empty list if no move is possible.
    """
    rnums = list(game.board.pieces)
    while len(rnums) > 0:
      i = random.randint(0, len(rnums)-1)
      rnum = rnums[i]
      if game.board.at(rnum).color != self.color:
        del rnums[i]
      elif game.has_a_move(rnum):
        paths = game.take_a_peek(rnum)
        path = random.choice(paths)
        game.make_a_move(path)
        return path
      else:
        del rnums[i]
    return []

#------------------------------------------------------------------------------
# Class CheckersRandLongestBot
#------------------------------------------------------------------------------
class CheckersRandLongestBot(CheckersBot):
  """
  Checkers autonomous bot player the plays the game by random choosing a
  longest path from the pieces with longest paths.

  A more selective random bot variation.
  """
  
  def __init__(self, color):
    """
    Initializer.

    Parameters:
      color   This player's color.
    """
    CheckersBot.__init__(self, "randlongest", color)

  def make_a_move(self, game):
    """
    Randomly make a move.

    A piece of this autonomous player's color that has a move is chosen. Of
    the possible moves made by the piece, the longest move path is chosen
    and the move is executed.

    Parameters:
      game  The active checkers game.

    Return:
      Returns move path executed or empty list if no move is possible.
    """
    rnums     = list(game.board.pieces)
    maxlen    = 0
    maxpaths  = {}
    for rnum in  rnums:
      if game.board.at(rnum).color != self.color:
        continue
      elif game.has_a_move(rnum):
        paths = game.mop.max_paths(game.take_a_peek(rnum))
        m = game.mop.path_len(paths[0]) # has a move, so must exist one path
        if m > maxlen:
          maxlen   = m
          maxpaths = {}
          maxpaths[rnum] = paths
        elif m == maxlen:
          maxpaths[rnum] = paths
    if len(maxpaths) > 0:
      rnum = random.choice(list(maxpaths))    # randomly choose a piece
      path = random.choice(maxpaths[rnum])    # randomly choose a path
      game.make_a_move(path)
      return path
    else:
      return []

#------------------------------------------------------------------------------
# Unit Test Main
#------------------------------------------------------------------------------
if __name__ == '__main__':

  # ..... CheckersPiece

  print("  ** UT: CheckersPiece **")

  pieces = [  CheckersPiece('black', 'man'), CheckersPiece('black', 'king'),
              CheckersPiece('white', 'man'), CheckersPiece('white', 'king') ]

  for piece in pieces:
    print("repr()    ", repr(piece))
    print("str()     ", piece)
    print("fqname()  ", piece.fqname())
    print("figurine  ", piece.figurine)
    print("foe()     ", piece.foe())
    print('')

  # ..... CheckersBoard

  print("  ** UT: CheckersBoard **")

  board = CheckersBoard(8)

  print("repr()               ", repr(board))
  print("str()                ", board)
  print("size                 ", board.size)
  print("dark_squares_per_row ", board.dark_squares_per_row)
  print("kings_row('black')   ", board.kings_row('black'))
  print("kings_row('white')   ", board.kings_row('white'))
  print('')

  board.print_board()
  print('')

  print("add_new_piece(1, 'black', 'man')")
  board.add_new_piece(1, 'black', 'man')

  rnum = 13
  for piece in pieces:
    print(f"board[{rnum}] = piece")
    board[rnum] = piece
    rnum += 1

  board.print_board(with_pieces=True, with_annot=False)
  print('')

  print("add_new_piece(32, 'white', 'king')")
  board.add_new_piece(32, 'white', 'king')

  board.print_board(with_pieces=True, with_annot=True)
  print('')

  print("is_square_occupied(14)   ", board.is_square_occupied(14))
  print("is_square_occupied(3,2)  ", board.is_square_occupied(3,2))
  print("is_square_empty(14)      ", board.is_square_empty(14))
  print("is_square_empty(3,2)     ", board.is_square_empty(3,2))
  print("is_square_occupied(27)   ", board.is_square_occupied(27))
  print("is_square_occupied(6,5)  ", board.is_square_occupied(6,5))
  print("is_square_empty(27)      ", board.is_square_empty(27))
  print("is_square_empty(6,5)     ", board.is_square_empty(6,5))
  print("numof_pieces()           ", board.numof_pieces())
  print("numof_black_pieces()     ", board.numof_black_pieces())
  print("numof_white_pieces()     ", board.numof_white_pieces())
  print("listof_positions()       ", board.listof_positions())
  print("at(15)                   ", board.at(15))
  print("pieces                   ", board.pieces)
  print("rnum_min:                ", board.rnum_min)
  print("rnum_max:                ", board.rnum_max)
  print("is_dark_square(2,9)      ", CheckersBoard.is_dark_square(2,9))
  print("is_light_square(2,9)     ", CheckersBoard.is_light_square(2,9))
  print("is_dark_square(6,8)      ", CheckersBoard.is_dark_square(6,8))
  print("is_light_square(6,8)     ", CheckersBoard.is_light_square(6,8))
  print("is_pos_on_board(27)      ", board.is_pos_on_board(27))
  print("is_pos_on_board(6,5)     ", board.is_pos_on_board(6,5))
  print("is_pos_on_board(33)      ", board.is_pos_on_board(33))
  print("is_pos_on_board(8,5)     ", board.is_pos_on_board(8,5))
  print("square_color(1,1)        ", CheckersBoard.square_color(1,1))
  print("square_color(1,12)       ", CheckersBoard.square_color(1,12))

  print('')
  print("move_piece(32,27)")
  board.move_piece(32, 27)
  print("piece = remove_piece(14)")
  piece = board.remove_piece(14)
  print("promote_piece(1, only_kings_row=False)")
  board.promote_piece(1, only_kings_row=False)
  print("replace_piece(4, piece)")
  board.replace_piece(4, piece)

  board.print_board(with_pieces=True, with_annot=True)
  print('')

  board = CheckersBoard(12)

  print("repr()               ", repr(board))
  print("str()                ", board)
  print("size                 ", board.size)
  print("dark_squares_per_row ", board.dark_squares_per_row)
  print("kings_row('black')   ", board.kings_row('black'))
  print("kings_row('white')   ", board.kings_row('white'))
  print('')

  board.print_board(with_pieces=True, with_annot=True)
  print('')

  # ..... Checkers

  print("  ** UT: EnglishDraughts **")

  draughts = EnglishDraughts()

  print("repr()               ", repr(draughts))
  print("str()                ", draughts)

  print("setup()")
  draughts.setup()

  draughts.board.print_board(with_pieces=True, with_annot=True)
  print('')

  print("mop          ", str(draughts.mop))
  print("state        ", draughts.state)
  print("move_num     ", draughts.move_num)
  print("turn         ", draughts.turn)
  print("eog          ", draughts.eog)
  print("winner       ", draughts.winner)
  print('')

  print("make_a_move('9-14')")
  draughts.make_a_move('9-14')
  print("make_a_move('23-18')")
  draughts.make_a_move('23-18')

  print("has_a_move(31)        ", draughts.has_a_move(31))
  print("has_a_move(14)        ", draughts.has_a_move(14))

  paths = draughts.take_a_peek(14)
  rnums = draughts.mop.rnums_in_paths(paths)

  print("take_a_peek(14)       ", paths)
  print("rnums_in_paths(paths) ", rnums)

  draughts.board.print_board(with_pieces=True, with_annot=True, soi=rnums)
  print('')
