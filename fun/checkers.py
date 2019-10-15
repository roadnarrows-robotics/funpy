import sys
import os
from enum import Enum
import collections
import re

def enumfactory(enum, value):
  """
  Convert value to enumeration class object.

  Parameters:
    enum    EnumMeta class.
    value   Value to convert into enum. String, integer, enum.


  Return:
    Converted enum.
  """
  try:
    if isinstance(value, str):
      return enum[value.upper()]
    else:
      return enum(value)
  except (KeyError, ValueError):
    raise CheckersError(f"{value!r}", f"not a valid {enum.__name__} value")

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
    return f"{self._color.name.lower()} {self._caste.name.lower()}"

  def fqname(self):
    """ Return fully-qualified piece name string. """
    return f"{self.color.name.lower()}.{self.caste.name.lower()}.{self.ident}"

  def copy(self):
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

    self.dark_squares_per_row  = self._size // 2

    self._rnum_min  = 1
    self._rnum_max  = self.dark_squares_per_row * self._size
    self._kings_row = { CheckersPiece.Color.BLACK: self._size-1,
                        CheckersPiece.Color.WHITE: 0 }

    self._pieces = {}

  def __repr__(self):
    return f"{self.__module__}.{self.__class__.__name__}"\
      f"(size={self._size!r})"

  def __str__(self):
    return f"{self._size}x{self._size} checker board"

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
    """ Return dictionary of pieces rnum key. """
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

  def kings_row(self, color):
    color = enumfactory(CheckersPiece.Color, color)
    return self._kings_row[color]

  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  # Visualize
  # . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

  def print_board(self, with_pieces=False, with_annot=False, soi=[],
                        **print_kwargs):
    """
    Print the board in unicode. Print default is to sys.stdout.

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
    Token generator.

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
    Tokenize notation.

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
      [rnum, '-', rnum1].

    A jump move generates one or more paths:
      [rnum, 'x', rnum1]
      [rnum, 'x', rnum1, 'x', rnum2]
        ...
      [rnum, 'x', rnum1, 'x', rnum2, ..., 'x' rnumN]

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
    # First pass: validate
    if len(path) < 3:
      raise CheckersError(f"{path!r}", "move path too short")
    rnum0 = path[0]
    piece = game.board.at(rnum0)
    if piece.color != game.turn:
      raise CheckersError(f"{piece}", f"it's {game.turn.name.lower()}'s turn")
    candidate_paths = self.find_move_paths(game, rnum0)
    if path not in candidate_paths:
      raise CheckersError(f"{self.path_to_nota(path)}", "not a legal move")

    # Second pass: execute move
    promoted  = piece.caste == CheckersPiece.Caste.KING
    rnum_i    = rnum0
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
        game.board.promote_piece(rnum0, only_kings_row=False)
        promoted= True
      i += 2
    game.board.move_piece(rnum0, rnum_i)

  def jumped_square(self, game, rnum0, rnum1):
    row0,col0 = game.board.rowcol(rnum0)
    row1,col1 = game.board.rowcol(rnum1)
    if row1 > row0:
      rowj = row1 - 1
    else:
      rowj = row1 + 1
    if col1 > col0:
      colj = col1 - 1
    else:
      colj = col1 + 1
    return game.board.rnum(rowj, colj)

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

  def max_path(self, paths):
    """
    Return the move path of maximum length. If two or move paths have the
    same maximum length, the first path is returned.

    Paramaters:
      paths   List of move paths.

    Return:
      Returns path of maximum length. May be empty.
    """
    path  = []
    for p in paths:
      if len(p) > len(path):
        path = p
    return path

  def rnums_in_paths(self, paths):
    rnums = []
    for path in paths:
      for p in path:
        if str(p) in Checkers.MopSym.ANY:
          continue
        elif p not in rnums:
          rnums.append(p)
    return rnums

  def path_to_nota(self, path):
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
  
  class EoG(Enum):
    NO_EOG  = 0
    ABORT   = 1
    RESIGN  = 2
    DEFEAT  = 3
    DRAW    = 4
  
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

  def __repr__(self):
    return  f"{self.__module__}.{self.__class__.__name__}"\
            f"({self._name!r}, {self._board.size!r}, {self._mop!r})"

  def __str__(self):
    return f"{self.board.size}x{self.board.size} {self.name}"

  def clear(self):
    self._board.clear()
    self._kur[CheckersPiece.Color.BLACK] = []
    self._kur[CheckersPiece.Color.WHITE] = []
    self._history   = []
    self._state     = Checkers.State.NOT_STARTED
    self._move_num  = 0
    self._turn      = CheckersPiece.Color.BLACK
    self._eog       = Checkers.EoG.NO_EOG
    self._winner    = None
  
  def setup(self):
    """ Starting position. """
    self.clear()
    self._state     = Checkers.State.NOT_STARTED
    self._move_num  = 1
    self._turn      = CheckersPiece.Color.BLACK

  def make_a_move(self, path):
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
    if not self.is_game_over(foe):
      self._turn = foe
      if self.turn == CheckersPiece.Color.BLACK:
        self._move_num += 1

  def take_a_peek(self, rnum):
    return self.mop.find_move_paths(self, rnum)

  def goto_hell(self, piece):
    self._kur[piece.color].append(piece)

  def start(self):
    if self.board.numof_black_pieces() == 0:
      raise CheckersError("no black pieces on board to play a game.")
    if self.board.numof_white_pieces() == 0:
      raise CheckersError("no white pieces on board to play a game.")
    self._state     = Checkers.State.IN_PLAY
    self._move_num  = 1
    self._turn      = CheckersPiece.Color.BLACK
    # RDK add timer here
    self.add_event_to_history("STARTED(t)")

  def stop(self):
    self._state   = Checkers.State.GAME_OVER  # game is aborted
    self._eog     = Checkers.EoG.ABORT
    self._winner  = None
    self.add_event_to_history("ABORTED")

  def resign(self, color):
    self._state   = Checkers.State.GAME_OVER  # game is over loosa loosa
    self._eog     = Checkers.EoG.RESIGN
    self._winner  = CheckersPiece.opposite_color(color)
    self.add_event_to_history(f"RESIGNED({color.name.lower()})")

  def is_game_over(self, color):
    print(f"rdk: 0: {color.name}")
    n = 0
    for rnum,piece in self.board.pieces.items():
      if piece.color == color:
        n += 1
        if self.mop.has_a_move(self, rnum):
          return False
    print(f"rdk: 1: {n}")
    if n == 0:
      self._eog       = Checkers.EoG.DEFEAT
      self._winner    = CheckersPiece.opposite_color(color)
      self.add_event_to_history(f"DEFEATED({color.name.lower()})")
    else:
      self._eog       = Checkers.EoG.DRAW
      self._winner    = None
      self.add_event_to_history(f"DRAW")
    self._state = Checkers.State.GAME_OVER
    return True

  def add_event_to_history(self, event):
    self._history.append(event)

  def add_move_to_history(self, path):
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
    if 'end' in print_kwargs:
      del print_kwargs['end']
    for color in [CheckersPiece.Color.BLACK, CheckersPiece.Color.WHITE]:
      print(f"{color.name.lower()}: ", **print_kwargs, end='')
      for cursed in self.kur[color]:
        print(f"{cursed.fqname()} ", **print_kwargs, end='')
      print('', **print_kwargs, end='\n')

  def print_history(self, **print_kwargs):
    if 'end' in print_kwargs:
      del print_kwargs['end']
    for event in self.history:
      print(f"{event} ", **print_kwargs, end='')
    print('', **print_kwargs, end='\n')

#------------------------------------------------------------------------------
# Class EnglishDraughts
#------------------------------------------------------------------------------
class EnglishDraughts(Checkers):
  """ Also American Checkers """
  StdSize = 8   # 8x8 board

  def __init__(self):
    Checkers.__init__(self, "English Draughts", EnglishDraughts.StdSize)

  def setup(self):
    Checkers.setup(self)
    for rnum in range(1, 13):
      self.board.add_new_piece(rnum, 'black', 'man')
    for rnum in range(21, 33):
      self.board.add_new_piece(rnum, 'white', 'man')

##-
class EnglishDraughtsVariation(Checkers):
  def __init__(self, size):
    pass

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

  def __repr__(self):
    return f"{self.__module__}.{self.__class__.__name__}"\
      f"()"

  def __str__(self):
    return f"{self.__class__.__name__}"

  def token_generator(self, nota):
    """
    Token generator.

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
    Tokenize notation.

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

  def find_move_paths(self, game, rnum, jumps_only=False):
    """
    Find all possible move paths associated with the game and board state.
    No moves are actually made.

    A path is a list:
      [rnum, mop, rnum ...]

    Minimum assumptions are made of the game. There must exist a simple move
    and a jump move.

    A simple move only generates one path:
      [rnum, '-', rnum1].

    A jump move generates one or more paths:
      [rnum, 'x', rnum1]
      [rnum, 'x', rnum1, 'x', rnum2]
        ...
      [rnum, 'x', rnum1, 'x', rnum2, ..., 'x' rnumN]

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
    deltas = game.get_move_pattern(piece)

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
    try:
      piece = game.board.at(rnum)
    except CheckersError:
      return False

    row, col = game.board.rowcol(rnum)
    deltas = game.get_move_pattern(piece)

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

  def jumped_square(self, game, rnum0, rnum1):
    row0,col0 = game.board.rowcol(rnum0)
    row1,col1 = game.board.rowcol(rnum1)
    if row1 > row0:
      rowj = row1 - 1
    else:
      rowj = row1 + 1
    if col1 > col0:
      colj = col1 - 1
    else:
      colj = col1 + 1
    return game.board.rnum(rowj, colj)

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

  def max_path(self, paths):
    """
    Return the move path of maximum length. If two or move paths have the
    same maximum length, the first path is returned.

    Paramaters:
      paths   List of move paths.

    Return:
      Returns path of maximum length. May be empty.
    """
    path  = []
    for p in paths:
      if len(p) > len(path):
        path = p
    return path

  def rnums_in_paths(self, paths):
    rnums = []
    for path in paths:
      for p in path:
        if str(p) in Checkers.MopSym.ANY:
          continue
        elif p not in rnums:
          rnums.append(p)
    return rnums

  def path_to_nota(self, path):
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
# Class CheckersCli
#------------------------------------------------------------------------------
class CheckersCli:
  """ Checkers text command-line interface. """

  uRArrow   = "\u2192"
  uArcArrow = "\u21ba"

  HelpStr = f"""\
The checkers command-line interface has three play states S:
  nogame    Game has not started.
  inplay    Game is in-play.
  gameover  Game has finished but a new game has not started.

ANY is any of the above play states.

Commands may be valid in only a subset of the play states and may cause
transitions to new states. The user prompt string indicates the play state.

add RNUM COLOR CASTE  Manually add a piece to the board.
                        RNUM    Reachable number specifying board square.
                        COLOR   One of: black white
                        CASTE   One of: man king
                      S: nogame{uArcArrow}

autoshow ENDIS TOBJ [TOBJ...] 
                      Enable or disable autoshow of game tableau object(s).
                      If enabled, the object(s) are automatically showed after
                      every display altering event (e.g. move).
                        ENDIS   One of: enable disable on off true false
                        TOBJ    See 'show' command.
                      S: ANY{uArcArrow}

clear                 Clear game and board state.
                      S: ANY {uRArrow} nogame

config                List configuration.
                      S: ANY{uArcArrow}

game [GAME] [SIZE]    Specify game type and size.
                        GAME    One of:   englishdraughts
                                Default:  englishdraughts
                        SIZE    Size of board in squares >= 4.
                                Default: 8
                      S: ANY {uRArrow} nogame

MOVE                  Specify a move in standard checkers notation.
                        RNUM - RNUM
                        RNUM x RNUM [x RNUM...]
                      where:
                        RNUM  Reachable number specifying board square.
                        -     Simple adjacent square slide move.
                        x     Jump capture move.
                      S: nogame {uRArrow} inplay   (auto-start)
                         inplay {uRArrow} inplay
                         inplay {uRArrow} gameover (if a winner)

peek RNUM             List (and show) candidate moves of a piece.
                        RNUM  Reachable number specifying board square.
                      S: nogame {uRArrow} nogame
                         inplay {uRArrow} inplay

quit                  Quit command-line interface mainloop and exit.

remove RNUM           Manually remove a piece from the board.
                        RNUM    Reachable number specifying board square.
                      S: nogame{uArcArrow}

resign                Resign from game (you loose).
                      S: inplay {uRArrow} gameover

setup                 Set up game in the standard starting position.
                      S: nogame{uArcArrow}

show TOBJ [TOBJ...]   Show game tableau object(s)
                        TOBJ   Game tableau object. One of:
                          board     Board with pieces and annotation.
                          history   Game history.
                          kur       Pieces sent to Sumerian hell.
                          winner    Any winner and reason.
                      S: ANY{uArcArrow}

start                 Start the game. There must be at least one piece of each
                      color on the board to begin play.
                      S: nogame {uRArrow} inplay

stop                  Stop the game. There will be no winner.
                      S: inplay {uRArrow} gameover

help                  Print this help.
"""

  # parsed token container
  Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

  class InputError(Exception):
    """ Checkers command-line interface input exception class. """

    def __init__(self, *args, token=None, line=None, column=None):
      """
      Initializer.

      Parameters:
        args    One or more error message strings.
        token   Associated token where the error occurred.
        line    Error line number.
        column  Error column number in line.
      """
      self.args   = args
      self.token  = token
      self.line   = line
      self.column = column
      if self.token is not None:
        self.line   = token.line
        self.column = token.column

    def __repr__(self):
      return f"{self.__module__}.{self.__class__.__name__}"\
            f"({', '.join([repr(s) for s in self.args])}, "\
            f"token={self.token}, line={self.line}, column={self.column})"

    def __str__(self):
      return ': '.join(self.args)

  def __init__(self):
    """ Initializer. """
    self.game = EnglishDraughts()
    self.config = {
      'autoshow': {
        'board': False, 'history': False, 'kur': False,
        'winner': False
      },
      'game': f"{self.game}"
    }
    self.init_tokenizer()
    self.line         = 0
    self.done         = False
    self.interactive  = True
    self.script       = None
    self.move_paths   = []
    self.move_rnums   = []

  def __repr__(self):
    return  f"{self.__module__}.{self.__class__.__name__}"\
            f"()"

  def __str__(self):
    return  f"{self.__class__.__name__}"

  def init_tokenizer(self):
    """ Initialize the tokenizer data. """
    # command-line interface commands
    self.cmds = {
      'help':     self.exec_help,
      'quit':     self.exec_quit,
      'autoshow': self.exec_autoshow,
      'config':   self.exec_config,
      'show':     self.exec_show,
      'setup':    self.exec_setup,
      'add':      self.exec_add_piece,
      'clear':    self.exec_clear,
      'peek':     self.exec_peek,
      'remove':   self.exec_remove_piece,
      'clear':    self.exec_clear,
      'resign':   self.exec_resign,
      'start':    self.exec_start,
      'stop':     self.exec_stop,
    }

    # show subcommands
    self.show_subcmds = {
      'board':      self.exec_show_board,
      'history':    self.exec_show_history,
      'kur':        self.exec_show_kur,
      'winner':     self.notimpl,
    }

    # specific sets of keywords
    self.kw_cmds    = set(self.cmds)
    self.kw_true    = {'on', 'enable', 'true'}
    self.kw_false   = {'off', 'disable', 'false'}
    self.kw_game    = {'englishdraughts'}
    self.kw_tableau = set(self.show_subcmds)
    self.kw_color   = {'black', 'white'}
    self.kw_caste   = {'man', 'king'}

    # all keywords
    self.keywords = self.kw_cmds.copy()
    self.keywords.update( self.kw_true,
                          self.kw_false,
                          self.kw_game,
                          self.kw_tableau,
                          self.kw_color,
                          self.kw_caste )

    # interface token specification
    self.token_specification = [
      ('NUMBER',    r'\d+'),                      # non-negative integer
      ('MOP',       f'[{Checkers.MopSym.ANY}]'),  # move operators
      ('ID',        r'[A-Za-z]+'),                # keywords and identifiers
      ('NEWLINE',   r'\n'),                       # line endings
      ('SKIP',      r'[ \t]+'),                   # skip over spaces and tabs
      ('MISMATCH',  r'.'),                        # any other character
    ]

    # build regular expression
    self.tok_regex = '|'.join('(?P<%s>%s)' % \
                              pair for pair in self.token_specification)

  def token_generator(self, input_line):
    """
    Token generator.

    Parameters:
      input_line    Line of input text.

    Yield:
      Token.
    """
    for mo in re.finditer(self.tok_regex, input_line):
      kind    = mo.lastgroup
      value   = mo.group()
      column  = mo.start()
      if kind == 'NUMBER':
        value = int(value)
      elif kind == 'ID':
        if value in self.kw_true:
          kind = 'BOOLEAN'
          value = True
        elif value in self.kw_false:
          kind = 'BOOLEAN'
          value = False
        elif value in self.kw_color:
          kind = 'COLOR'
          value = CheckersPiece.Color[value.upper()]
        elif value in self.kw_caste:
          kind = 'CASTE'
          value = CheckersPiece.Caste[value.upper()]
        elif value in self.kw_cmds:
          kind = 'CMD'
        #else:
        #  kind = value
      elif kind == 'NEWLINE':
        #self.line += 1
        continue
      elif kind == 'SKIP':
        continue
      elif kind == 'MISMATCH':
        raise CheckersCli.InputError(f"{value!r}", "unexpected token",
                            line=self.line, column=column)
      yield CheckersCli.Token(kind, value, self.line, column)

  def tokenize(self, input_line):
    """
    Tokenize line of input.

    Parameters:
      input_line    Line of input text.

    Return:
      Returns list of parsed tokens.
    """
    # lexically parse and tokenize input
    tokens = []
    for tok in self.token_generator(input_line):
      #print('DBG:', tok)
      tokens.append(tok)
    return tokens

  def prompt(self):
    """ Create prompt strig from game state. """
    if not self.interactive:
      return ''
    elif self.game.state == Checkers.State.NOT_STARTED:
      ps1 = "nogame> "
    elif self.game.state == Checkers.State.IN_PLAY:
      ps1 = f"{self.game.move_num}. {self.game.turn.name.lower()}> "
    elif self.game.state == Checkers.State.GAME_OVER:
      ps1 = "gameover> "
    else:
      ps1 = "huh? "
    return f"[{self.line}] {ps1}"

  def error(self, *emsgs):
    """ Print user input error in fixed format. """
    if self.script is None:
      print(f"[{self.line}] error: {': '.join(e for e in emsgs)}")
    else:
      print(f"{os.path.basename(self.script)} [{self.line}] "\
            f"error: {': '.join(str(e) for e in emsgs)}")

  def rsp(self, rmsg):
    """ Print command response in fixed format. """
    print(f"[{self.line}] {rmsg}")

  def _chk_arg_cnt(self, tokens, min_cnt=1, max_cnt=None):
    """
    Check command argument count. Raises InputError if check fails.

    Parameters:
      tokens    List of tokens with tokens[0] being the command.
      min_cnt   Minimum number of arguments including the command.
      max_cnt   Maximum number of arguments including the command. If None
                then no maximum.
    """
    ntoks = len(tokens)
    if ntoks < min_cnt:
      raise CheckersCli.InputError(f"{tokens[0].value!r}",
                    f"{min_cnt} arguments required, but {ntoks} specified",
                    token=tokens[0])
    if max_cnt is not None and ntoks > max_cnt:
      raise CheckersCli.InputError(f"{tokens[0].value!r}",
                    f"{max_cnt} arguments allowed, but {ntoks} specified",
                    token=tokens[0])

  def _chk_ftypes(self, tokens, *ftypes):
    """
    Check command arguments are of the expected types.

    Parameters:
      tokens    List of tokens with tokens[0] being the command.
      ftypes    Sequence of expected field types.
    """
    n = 0
    for ft in ftypes:
      if tokens[n].type != ft:
        raise CheckersCli.InputError(f"{tokens[n].value!r}",
                f"expected field type {ft!r}, but parsed {tokens[n].type!r}",
                token=tokens[n])
      n += 1

  def _chk_state(self, tokens, *states):
    """
    Check if command is in allowed game play state. Raises InputError if
    check fails.

    Parameters:
      tokens    List of tokens with tokens[0] being the command.
      states    Valid state(s).
    """
    if self.game.state not in states:
      raise CheckersCli.InputError(f"{tokens[0].value!r}",
                f"command invalid in {self._s_state(self.game.state)!r} state",
                token=tokens[0])

  def _s_state(self, state):
    """ Convert game play state to string. """
    if self.game.state == Checkers.State.NOT_STARTED:
      return "nogame"
    elif self.game.state == Checkers.State.IN_PLAY:
      return "inplay"
    elif self.game.state == Checkers.State.GAME_OVER:
      return "gameover"
    else:
      return "wtf"

  def autoshow(self):
    """ Auto show configured game components. """
    if self.config['autoshow']['board']:
      self.game.board.print_board(with_pieces=True, with_annot=True,
                                  soi=self.move_rnums)

  def mainloop(self, script=None):
    """ Process and execute user input main loop. """
    self.line         = 0
    self.done         = False
    self.script       = script
    self.interactive  = sys.stdin.isatty()
    self.move_paths   = []
    self.move_rnums   = []

    # script file specified - open
    if self.script is not None:
      try:
        scrin = open(self.script, 'r')
      except (FileNotFoundError, IOError) as e:
        self.error(*e.args)
        scrin = None
    else:
      scrin = None

    while not self.done:
      self.line += 1

      # read line from script file
      if scrin is not None:
        try:
          input_line = scrin.readline()
        except IOError as e:
          self.error(*e.args)
          scrin.close()
          scrin = None
        else:
          if not input_line:
            scrin.close()
            scrin = None
            self.line = 0

      # read line from stdin, prompting if interactive
      else:
        try:
          input_line = input(self.prompt())
        except EOFError:
          self.done = True

      # lexically parse and tokenize input
      try:
        tokens = self.tokenize(input_line)
      except CheckersCli.InputError as e:
        self.error(*e.args)
        continue

      # empty line
      if len(tokens) == 0:
        continue

      # exec command
      try:
        if tokens[0].value in self.cmds:
          self.cmds[tokens[0].value](tokens)
        elif tokens[0].type == 'NUMBER':
          self.exec_move(tokens);
        else:
          raise CheckersCli.InputError(f"{tokens[0].value!r}",
                                      'unknown command',
                                      token=tokens[0])
      except CheckersCli.InputError as e:
        self.error(*e.args)
      except CheckersError as e:
        self.error(*e.args)

  def notimpl(self, tokens):
    """ [Sub]command not implemented. """
    cmd = ' '.join(str(tok.value) for tok in tokens)
    raise CheckersCli.InputError(f"{cmd!r}", "not implemented")

  def exec_help(self, tokens):
    """ Execute help command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    print(CheckersCli.HelpStr)

  def exec_quit(self, tokens):
    """ Execute quit command. """
    self.done = True

  def exec_autoshow(self, tokens):
    """ Execute autoshow command. """
    self._chk_arg_cnt(tokens, min_cnt=3)
    self._chk_ftypes(tokens[1:], 'BOOLEAN', 'ID')
    v = tokens[1].value
    for tok in tokens[2:]:
      if tok.value in self.kw_tableau:
        self.config['autoshow'][tok.value] = v
      else:
        raise CheckersCli.InputError(f"{tok.value!r}",
            'unknown tableau game object',
            token=tok)
    s = ''
    for k,v in self.config['autoshow'].items():
      s += f"{k}({str(v).lower()}) "
    self.rsp(f"autoshow: {s}")

  def exec_config(self, tokens):
    """ Execute config command. """
    s = f"    game:     {self.config['game']}\n"
    s += "    autoshow: "
    for k,v in self.config['autoshow'].items():
      s += f"{k}({str(v).lower()}) "
    self.rsp(f"configuration:\n{s}")

  def exec_show(self, tokens):
    """ Execute show command. """
    self._chk_arg_cnt(tokens, min_cnt=2)
    for tok in tokens[1:]:
      if tok.value in self.show_subcmds:
        self.show_subcmds[tok.value](tokens)
      else:
        raise CheckersCli.InputError(f"{tok.value!r}",
            'unknown tableau game object',
            token=tok)

  def exec_show_board(self, tokens):
    """ Execute show board subcommand. """
    self.game.board.print_board(with_pieces=True, with_annot=True,
                                soi=self.move_rnums)

  def exec_show_kur(self, tokens):
    """ Execute show kur (captured pieces hell) subcommand. """
    self.game.print_kur()

  def exec_show_history(self, tokens):
    """ Execute show history subcommand. """
    self.game.print_history()

  def exec_clear(self, tokens):
    """ Execute clear command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self.game.clear()
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game reset to cleared state")
    self.autoshow()

  def exec_setup(self, tokens):
    """ Execute setup command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self._chk_state(tokens, Checkers.State.NOT_STARTED)
    self.game.setup()
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game setup in standard game position")
    self.autoshow()

  def exec_add_piece(self, tokens):
    """ Execute add piece command. """
    self._chk_arg_cnt(tokens, min_cnt=4, max_cnt=4)
    self._chk_state(tokens, Checkers.State.NOT_STARTED)
    self._chk_ftypes(tokens[1:], 'NUMBER', 'COLOR', 'CASTE')
    rnum, color, caste  = tokens[1].value, tokens[2].value, tokens[3].value
    try:
      self.game.board.add_new_piece(rnum, color, caste)
    except CheckersError as e:
      raise CheckersCli.InputError(*e.args)
    piece = self.game.board.at(rnum)
    self.move_paths = []
    self.move_rnums = []
    self.rsp(f"{piece} added to square {rnum}")
    self.autoshow()

  def exec_remove_piece(self, tokens):
    """ Execute add piece command. """
    self._chk_arg_cnt(tokens, min_cnt=2, max_cnt=2)
    self._chk_state(tokens, Checkers.State.NOT_STARTED)
    self._chk_ftypes(tokens[1:], 'NUMBER')
    rnum = tokens[1].value
    try:
      piece = self.game.board.remove_piece(rnum)
    except CheckersError as e:
      raise CheckersCli.InputError(*e.args)
    self.move_paths = []
    self.move_rnums = []
    self.rsp(f"{piece} removed from square {rnum}")
    self.autoshow()

  def exec_start(self, tokens):
    """ Execute start command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self._chk_state(tokens, Checkers.State.NOT_STARTED)
    try:
      self.game.start()
    except CheckersError as e:
      raise CheckersCli.InputError(*e.args)
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game started")

  def exec_stop(self, tokens):
    """ Execute stop command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self._chk_state(tokens, Checkers.State.IN_PLAY)
    try:
      self.game.stop()
    except CheckersError as e:
      raise CheckersCli.InputError(*e.args)
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game stopped with no winner")

  def exec_resign(self, tokens):
    """ Execute resign command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self._chk_state(tokens, Checkers.State.IN_PLAY)
    self.game.resign(self.game.turn)
    self.move_paths = []
    self.move_rnums = []
    self.rsp(f"player {self.game.turn.name.lower()} resigned")

  def exec_move(self, tokens):
    """ Execute a checkers move. """
    self._chk_arg_cnt(tokens, min_cnt=3)
    self._chk_state(tokens, Checkers.State.NOT_STARTED, Checkers.State.IN_PLAY)
    self._chk_ftypes(tokens, 'NUMBER', 'MOP', 'NUMBER')
    path = [tok.value for tok in tokens]
    #nota = ''.join(f"{tok.value}" for tok in tokens)
    self.game.make_a_move(path)
    color = self.game.board.at(path[-1]).color
    self.rsp(f"{color.name.lower()} moved from {path[0]} to {path[-1]}")
    self.autoshow()


  def exec_peek(self, tokens):
    """ Execute peek moves command. """
    self._chk_arg_cnt(tokens, min_cnt=2, max_cnt=2)
    self._chk_state(tokens, Checkers.State.NOT_STARTED, Checkers.State.IN_PLAY)
    self._chk_ftypes(tokens[1:], 'NUMBER')
    rnum = tokens[1].value
    piece = self.game.board.at(rnum)
    self.move_paths = self.game.take_a_peek(rnum)
    self.move_rnums = self.game.mop.rnums_in_paths(self.move_paths)
    s = '    '.join(str(p)+'\n' for p in self.move_paths)
    self.rsp(f"{piece} on {rnum} candidate moves:\n    {s}")
    self.autoshow()

#------------------------------------------------------------------------------
# Unit Test Main
#------------------------------------------------------------------------------
if __name__ == '__main__':
  import random

  if len(sys.argv) > 1:
    fname = sys.argv[1]
  else:
    fname = None

  cli = CheckersCli()
  cli.mainloop(script=fname)

  sys.exit(0)
  """
  def add_rand_pieces(board):
    n = random.randint(1, board.rnum_max)
    for k in range(0, n):
      has_pos = False
      while not has_pos:
        for tries in range(0,4):
          rnum = random.randint(board.rnum_min, board.rnum_max)
          if board.is_square_empty(rnum):
            has_pos = True
            break
      if has_pos:
        color = random.choice(list(CheckersPiece.Color))
        caste = random.choice(list(CheckersPiece.Caste))
        board.add_new_piece(rnum, color, caste)

  def test_nrc(board):
    print("* Test rnum to row,col to rnum methods")
    for n0 in range(1,33):
      tup = board.rowcol(n0)
      n1 = board.rnum(*tup)
      if n0 == n1:
        res = 'ok'
      else:
        res = 'X'
      print(f"{n0:>2} --> {tup} --> {n1:>2} {res}")

  def test_bad_n(board):
    print("* Test bad rnum to row,col method exceptions")
    for n in [-2, 0, 33, 103]:
      try:
        tup = board.rowcol(n)
        print(f"{n:>2} --> {tup} should have failed")
      except CheckersError as inst:
        print(f"Caught expected error: {inst}")

  def test_bad_rc(board):
    print("* Test bad row,col to rnum method exceptions")
    for tup in [(-2, 2), (1,-1), (0,0), (7,7), (4,6), (8,6), (6,8)]:
      try:
        n = board.rnum(*tup)
        print(f"{tup} --> {n} should have failed")
      except CheckersError as inst:
        print(f"Caught expected error: {inst}")

  def test_repr_str(board, piece_list):
    print("* Test class repr and str methods")
    ce = CheckersError('this is arg 0', 'this is arg 1',
                        'this is the final arg')
    print("    class CheckersError")
    print(f"{repr(ce)}")
    print(f"{ce}")
    print("    class CheckersBoard")
    print(f"{repr(board)}")
    print(f"{board}")
    print("    class CheckersPiece")
    for piece in piece_list:
      print(f"{repr(piece)}")
      print(f"{piece}")

  def test_print_board(board):
    print("* Test print_board")
    add_rand_pieces(board)
    print("    with no pieces and no annotation")
    board.print_board();
    print("    with pieces and no annotation")
    board.print_board(with_pieces=True);
    print("    with pieces and annotation")
    board.print_board(with_pieces=True, with_annot=True,
        file=sys.stderr, end='abc\n');
    board.clear()

  board = CheckersBoard(8)

  some_pieces = [
      CheckersPiece(0, 0), CheckersPiece('white', 'king', ident=53),
      CheckersPiece('black', 'king'), CheckersPiece('white', 'man') ]

  test_nrc(board)
  print("")

  test_bad_n(board)
  print("")
  
  test_bad_rc(board)
  print("")
  
  test_repr_str(board, some_pieces)
  print("")
  """
  """
  
  test_print_board(board)
  print("")
  """
