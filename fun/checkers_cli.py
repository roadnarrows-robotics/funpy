"""
Checkers command-line interface.

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

import sys
import os
from enum import Enum
import collections
import re
import random
from io import StringIO
import readline

from checkers import *

#------------------------------------------------------------------------------
# Class CheckersInputError
#------------------------------------------------------------------------------
class CheckersInputError(Exception):
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

#------------------------------------------------------------------------------
# Class CheckersCli
#------------------------------------------------------------------------------
class CheckersCli:
  """ Checkers text command-line interface. """

  uRArrow   = "\u2192"
  uArcArrow = "\u21ba"

  HelpStr = f"""\
Checkers Help:
The checkers command-line interface has three play states S:
  nogame    Game has not started.
  inplay    Game is in-play.
  gameover  Game has finished but a new game has not started.

ANY is any of the above play states. The 'clear' command is the only way to
go back to the 'nogame' state.

Commands may be valid in only a subset of the play states and may cause
transitions to new states. The user prompt string indicates the play state.

add RNUM COLOR CASTE  Manually add a piece to the board.
                        RNUM    Reachable number specifying board square.
                        COLOR   One of: black white
                        CASTE   One of: man king
                      S: nogame{uArcArrow}

autoplay BOT HALFMOVES Use the specified autonomous bot (algorithm) to make a
                      number of half moves. A full move is black then white.
                      A half move is a move of one color only.
                      For example: 'bot random 3' results in black-white-black
                      or white-black-white move sequence, depending on whose
                      initial turn it is.
                        BOT       Autonomous algorithm. See 'bot' command.
                        HALFMOVES Number of half moves.
                      S: inplay {uRArrow} inplay
                         inplay {uRArrow} gameover (on end-of-game condition)

autoshow SWITCH TOBJ [TOBJ...] 
                      Enable or disable autoshow of game tableau object(s).
                      If enabled, the object(s) are automatically showed after
                      every display altering event (e.g. move).
                        SWITCH  One of: enable disable on off true false
                        TOBJ    See 'show' command.
                      S: ANY{uArcArrow}

bot COLOR BOT         Specify a bot (algorithm) as one of the players.
                        COLOR   One of: black white
                        BOT     Autonomous algorithm. One of:
                                  none    unassociate bot
                                  random  randomly choose a piece and move
                                          in a random movable direction
                                  longest randomly choose a longest path from
                                          the pieces with the longest paths
                      S: nogame{uArcArrow}

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
                      S: inplay {uRArrow} inplay
                         inplay {uRArrow} gameover (on end-of-game condition)

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
                          outcome   Game outcome (any winner and reason).
                      S: ANY{uArcArrow}

start                 Start the game. There must be at least one piece of each
                      color on the board to begin play.
                      S: nogame {uRArrow} inplay

stop                  Stop the game. There will be no winner.
                      S: inplay {uRArrow} gameover

help [list]           Print this help or only list command names.
"""

  # parsed token container
  Token = collections.namedtuple('Token', ['type', 'value', 'line', 'column'])

  def __init__(self):
    """ Initializer. """
    self.game = EnglishDraughts()
    self.config = {
      'autoshow': {
        'board': False, 'history': False, 'kur': False, 'outcome': False
      },
      'game': f"{self.game}",
      'bot': {
        CheckersPiece.Color.BLACK:  None,
        CheckersPiece.Color.WHITE:  None
      },
    }
    self.init_tokenizer()
    self.init_readline()
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
      'game':     self.exec_game,
      'config':   self.exec_config,
      'show':     self.exec_show,
      'setup':    self.exec_setup,
      'add':      self.exec_add_piece,
      'clear':    self.exec_clear,
      'autoplay': self.exec_autoplay,
      'bot':      self.exec_bot,
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
      'outcome':    self.exec_show_outcome,
    }

    # bot subcommands
    self.bots = {
      'none':       None,
      'random':     CheckersRandomBot,
      'longest':    CheckersRandLongestBot
    }

    # specific sets of keywords
    self.kw_cmds    = set(self.cmds)
    self.kw_true    = {'on', 'enable', 'true'}
    self.kw_false   = {'off', 'disable', 'false'}
    self.kw_game    = {'englishdraughts'}
    self.kw_tableau = set(self.show_subcmds)
    self.kw_bot     = set(self.bots)
    self.kw_color   = {'black', 'white'}
    self.kw_caste   = {'man', 'king'}

    # all keywords
    self.keywords = self.kw_cmds.copy()
    self.keywords.update( self.kw_true,
                          self.kw_false,
                          self.kw_game,
                          self.kw_tableau,
                          self.kw_bot,
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
    Command-line interface token generator.

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
        elif value in self.kw_tableau:
          kind = 'TABLEAU'
        elif value in self.kw_bot:
          kind = 'BOT'
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
        raise CheckersInputError(f"{value!r}", "unexpected token",
                            line=self.line, column=column)
      yield CheckersCli.Token(kind, value, self.line, column)

  def tokenize(self, input_line):
    """
    Command-line interface tokenize line of input.

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

  def completer(self, text, state):
    #print('\nDBG:', f"text={text!r}", f"state={state!r}")
    options = [i for i in self.kw_cmds if i.startswith(text)]
    if state < len(options):
        return options[state]
    else:
        return None

  def init_readline(self):
    readline.parse_and_bind("tab: complete")
    readline.set_completer(self.completer)

  def prompt(self):
    """ Create prompt strig from game state. """
    if not self.interactive:
      return ''
    elif self.game.state == Checkers.State.NOT_STARTED:
      ps1 = "nogame> "
    elif self.game.state == Checkers.State.IN_PLAY:
      ps1 = f"{self.game.move_num}. {enumlower(self.game.turn)}> "
    elif self.game.state == Checkers.State.GAME_OVER:
      ps1 = "gameover> "
    else:
      ps1 = "huh? "
    return f"[{self.line}] {ps1}"

  def error(self, *emsgs):
    """ Print user/script input error in fixed format.

    Parameters:
      emsgs   One of more error message strings.
    """
    if self.script is None:
      print(f"[{self.line}] error: {': '.join(e for e in emsgs)}")
    else:
      print(f"{os.path.basename(self.script)} [{self.line}] "\
            f"error: {': '.join(str(e) for e in emsgs)}")

  def rsp(self, rmsg, with_line_num=True):
    """
    Print command response in fixed format.

    Parameters:
      rmsg            Response message string.
      with_line_num   Do [not] preface response with the current input line
                      number.
    """
    if with_line_num:
      print(f"[{self.line}] {rmsg}")
    else:
      print(f" {rmsg}")

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
      raise CheckersInputError(f"{tokens[0].value!r}",
                    f"{min_cnt} arguments required, but {ntoks} specified",
                    token=tokens[0])
    if max_cnt is not None and ntoks > max_cnt:
      raise CheckersInputError(f"{tokens[0].value!r}",
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
        raise CheckersInputError(f"{tokens[n].value!r}",
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
      raise CheckersInputError(f"{tokens[0].value!r}",
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
      print('')
    if self.config['autoshow']['kur']:
      if  len(self.game.kur[CheckersPiece.Color.BLACK]) > 0 or \
          len(self.game.kur[CheckersPiece.Color.WHITE]) > 0:
        self.game.print_kur()
        print('')
    if self.config['autoshow']['history']:
      if len(self.game.history) > 0:
        self.game.print_history()
        print('')
    if self.config['autoshow']['outcome']:
      if self.game.state == Checkers.State.GAME_OVER:
        self.game.print_outcome()
        print('')

  def is_bots_turn(self):
    if self.game.state != Checkers.State.IN_PLAY:
      return False
    elif self.config['bot'][self.game.turn] is None:
      return False
    else:
      return True

  def bots_move(self):
    bot = self.config['bot'][self.game.turn]
    path = bot.make_a_move(self.game)
    self.rsp(f"{bot.fqname()} {CheckersMove.path_to_nota(path)}",
              with_line_num=False)

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

    # the loop
    while not self.done:
      if self.is_bots_turn():
        self.bots_move()
        self.autoshow()
        continue

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
      except CheckersInputError as e:
        self.error(*e.args)
        continue

      # empty line
      if len(tokens) == 0:
        continue

      # execute command
      try:
        if tokens[0].value in self.cmds:
          self.cmds[tokens[0].value](tokens)
        elif tokens[0].type == 'NUMBER':
          self.exec_move(tokens);
        else:
          raise CheckersInputError(f"{tokens[0].value!r}", 'unknown command',
                                      token=tokens[0])
      except CheckersInputError as e:
        self.error(*e.args)
      except CheckersError as e:
        self.error(*e.args)

  def notimpl(self, tokens):
    """ [Sub]command not implemented. """
    cmd = ' '.join(str(tok.value) for tok in tokens)
    raise CheckersInputError(f"{cmd!r}", "not implemented")

  def exec_help(self, tokens):
    """ Execute help command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=2)
    if len(tokens) == 1:
      self.rsp(CheckersCli.HelpStr)
    elif tokens[1].value == 'list':
      cmds = list(self.cmds)
      cmds.append('MOVE')
      cmds.sort()
      self.rsp(' '.join(s for s in cmds))
    else:
      raise CheckersInputError(f"{tokens[1].value!r}", 'unknown help argument',
                                token=tokens[1])

  def exec_quit(self, tokens):
    """ Execute quit command. """
    self.rsp('quit')
    self.done = True

  def exec_autoshow(self, tokens):
    """ Execute autoshow command. """
    self._chk_arg_cnt(tokens, min_cnt=3)
    self._chk_ftypes(tokens[1:], 'BOOLEAN', 'TABLEAU')
    v = tokens[1].value
    for tok in tokens[2:]:
      if tok.value in self.kw_tableau:
        self.config['autoshow'][tok.value] = v
      else:
        raise CheckersInputError(f"{tok.value!r}",
                                'unknown tableau game object',
                                token=tok)
    s = ''
    for k,v in self.config['autoshow'].items():
      s += f"{k}({str(v).lower()}) "
    self.rsp(f"autoshow: {s}")

  def exec_config(self, tokens):
    """ Execute config command. """
    s = f"    game:     {self.config['game']}\n"
    s += "    bots:     "
    for color in self.config['bot']:
      if self.config['bot'][color] is None:
        s += f"{enumlower(color)}(none)"
      else:
        s += f"{enumlower(color)}({self.config['bot'][color].tag})"
      s += ' '
    s += '\n'
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
        raise CheckersInputError(f"{tok.value!r}",
                                'unknown tableau game object',
                                token=tok)

  def exec_show_board(self, tokens):
    """ Execute show board subcommand. """
    self.rsp("board state:")
    self.game.board.print_board(with_pieces=True, with_annot=True,
                                soi=self.move_rnums)

  def exec_show_kur(self, tokens):
    """ Execute show kur (captured pieces hell) subcommand. """
    self.rsp("sumerian hell:")
    self.game.print_kur()

  def exec_show_history(self, tokens):
    """ Execute show history subcommand. """
    self.rsp("game history:")
    self.game.print_history()

  def exec_show_outcome(self, tokens):
    """ Execute show outcome subcommand. """
    with StringIO() as output:
      self.game.print_outcome(file=output)
      outcome = output.getvalue()
    if outcome[-1] == '\n':
      outcome = outcome[:-1]
    self.rsp(outcome.lower())

  def exec_clear(self, tokens):
    """ Execute clear command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self.game.clear()
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game reset to cleared state")
    self.autoshow()

  def exec_game(self, tokens):
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=3)
    self._chk_state(tokens, Checkers.State.NOT_STARTED)
    game = 'englishdraughts'
    size = 8
    for tok in tokens[1:]:
      if tok.type == 'ID':
        game = tok.value
        if game != 'englishdraughts':
          raise CheckersInputError(f"{tok.value!r}", 'unsupported game')
      elif tok.type == 'NUMBER':
        size = tok.value
        if size < 4:
          raise CheckersInputError(f"{tok.value!r}", 'size too small')
      else:
        raise CheckersInputError(f"{tok.type!r}", 'expected argument type')
    if size == EnglishDraughts.StdSize:
      self.game = EnglishDraughts()
    else:
      self.game = EnglishDraughtsVariation("English Draught Variation", size, 3)
    self.config['game'] = f"{self.game}"
    self.rsp(self.config['game'])

  def exec_setup(self, tokens):
    """ Execute setup command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self._chk_state(tokens, Checkers.State.NOT_STARTED)
    self.game.setup()
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game set up in standard position")
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
      raise CheckersInputError(*e.args)
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
      raise CheckersInputError(*e.args)
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
      raise CheckersInputError(*e.args)
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game started")
    self.autoshow()

  def exec_stop(self, tokens):
    """ Execute stop command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self._chk_state(tokens, Checkers.State.IN_PLAY)
    try:
      self.game.stop()
    except CheckersError as e:
      raise CheckersInputError(*e.args)
    self.move_paths = []
    self.move_rnums = []
    self.rsp("game stopped with no winner")
    self.autoshow()

  def exec_resign(self, tokens):
    """ Execute resign command. """
    self._chk_arg_cnt(tokens, min_cnt=1, max_cnt=1)
    self._chk_state(tokens, Checkers.State.IN_PLAY)
    self.game.resign(self.game.turn)
    self.move_paths = []
    self.move_rnums = []
    self.rsp(f"player {enumlower(self.game.turn)} resigned")
    self.autoshow()

  def exec_autoplay(self, tokens):
    self._chk_arg_cnt(tokens, min_cnt=3)
    self._chk_state(tokens, Checkers.State.IN_PLAY)
    self._chk_ftypes(tokens[1:], 'BOT', 'NUMBER')
    alg = tokens[1].value
    if self.bots[alg] is None:
      raise CheckersInputError(f"bot cannot be {alg!r}")
    maxmoves = tokens[2].value
    players = { 'black': self.bots[alg]('black'),
                'white': self.bots[alg]('white') }
    self.rsp(f"autoplay {maxmoves} half moves")
    while maxmoves > 0 and self.game.state == Checkers.State.IN_PLAY:
      turn = enumlower(self.game.turn)
      path = players[turn].make_a_move(self.game)
      if len(path) < 3:
        break;
      nota = CheckersMove.path_to_nota(path)
      if turn == 'black':
        self.rsp(f"{self.game.move_num:>3}. {turn}.{players[turn].tag} {nota}",
            with_line_num=False)
      else:
        self.rsp(f"{'':>4} {turn}.{players[turn].tag} {nota}",
            with_line_num=False)
      self.autoshow()
      maxmoves -= 1

  def exec_bot(self, tokens):
    self._chk_arg_cnt(tokens, min_cnt=3, max_cnt=3)
    self._chk_state(tokens, Checkers.State.NOT_STARTED)
    self._chk_ftypes(tokens[1:], 'COLOR', 'BOT')
    color = tokens[1].value
    alg   = tokens[2].value
    if self.bots[alg] is not None:
      self.config['bot'][color] = self.bots[alg](color)
      self.rsp(f"{enumlower(color)} bot set to {self.config['bot'][color].tag}")
    else:
      self.config['bot'][color] = None
      self.rsp(f"{enumlower(color)} bot removed")

  def exec_move(self, tokens):
    """ Execute a checkers move. """
    self._chk_arg_cnt(tokens, min_cnt=3)
    self._chk_state(tokens, Checkers.State.IN_PLAY)
    self._chk_ftypes(tokens, 'NUMBER', 'MOP', 'NUMBER')
    path = [tok.value for tok in tokens]
    #path = ''.join(f"{tok.value}" for tok in tokens)
    self.game.make_a_move(path)
    color = enumlower(self.game.board.at(path[-1]).color)
    nota = CheckersMove.path_to_nota(path)
    self.rsp(f"{color} {nota}")
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
# Command-Line Interface Main
#------------------------------------------------------------------------------
if __name__ == '__main__':

  if len(sys.argv) > 1:
    fname = sys.argv[1]
  else:
    fname = None

  cli = CheckersCli()
  cli.mainloop(script=fname)

  sys.exit(0)
