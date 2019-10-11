"""
Command-line argument parsing and pretty printing.

Package:
  RoadNarrows fun package.

Link:
  https://github.com/roadnarrows-robotics/

Copyright:
  (c) 2019. RoadNarrows LLC
  https://www.roadnarrows.com
  All Rights Reserved

License:
  MIT
"""

from __future__ import print_function

import argparse
import textwrap

class SmartFormatter(argparse.RawTextHelpFormatter):
  """
  Extend the argparse formatter to support indented multiline help.
  """

  def _split_lines(self, text, width):
    """
    Smart split of text.

    Parameters:
      text    String.
      width   Maximum width.

    Returns:
      Returns list of lines.
    """
    if text.startswith('R|'):
      return text[2:].splitlines()
    else:
      # this is the RawTextHelpFormatter._split_lines
      return argparse.HelpFormatter._split_lines(self, text, width)

def add_subparsers(argparser, helptext):
  """
  Conditionally add subparsers to argument parser.

  An ArgumentParser can only have one assigned subparsers.

  The subparsers object is added to the argparser attributes.
    argparser.subparsers

  Parameters:
    argparser   ArgumentParser object.
    helptext    Help text.

  Returns:
    Returns subparsers object.
  """
  try:
    if argparser.subparsers is None:
      argparser.subparsers = argparser.add_subparsers(help=helptext)
  except AttributeError:
    argparser.subparsers = argparser.add_subparsers(help=helptext)
  return argparser.subparsers
