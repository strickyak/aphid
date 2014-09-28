# NOT SUPPORTED: BOTH "quotes" and (parens) on same line.
# We handle quotes first, then get continuation lines.
# So if quotes are on a continuation line, we will not see it.
# This simplfies the case of parens and semicolons in the quotes,
# which we do handle.

# Demo:
# cat ~/yak/bind/yak/[a-z]*.*[a-z] | p rye run zoner.py  | ../rye/errfilt/errfilt | m

from go import strings
from go import regexp
from go import os
from go import io/ioutil

# [1] is Before the quote, [2] is In the quote, [3] is after.
FindQuote = regexp.MustCompile('^([^;"]*)["]([^"]*)["](.*)$').FindStringSubmatch

# [1] is Before the semicolon.
FindComment = regexp.MustCompile('^([^;]*)[;].*$').FindStringSubmatch

# [1] is first word, [2] is rest.
FindWord = regexp.MustCompile('^([-A-Za-z0-9_.:$@/*]+)\\s*(.*)').FindStringSubmatch

# [1] is rest.
FindWhiteSpace = regexp.MustCompile('^\\s+(.*)').FindStringSubmatch

# [1] ( [2]
FindUnclosedParen = regexp.MustCompile('^([^()]*)[(]([^()]*)$').FindStringSubmatch
# [1] ( [2] ) [3]
FindClosedParen = regexp.MustCompile('^([^()]*)[(]([^()]*)[)]([^()]*)$').FindStringSubmatch

def main(argv):
  code = ioutil.ReadAll(os.Stdin)
  lines = strings.Split(code, '\n')
  i = 0
  n = len(lines)
  while i < n:
    line = lines[i]

    # Try removing quoted from near end of line.
    quoted = []
    while True:
      fq = FindQuote(line)  # Finds first quote.
      if not fq:
        break
      _, front, inside, back = fq
      line = front + ' ' + back
      quoted.append(inside)

    # Try removing semicolon comment.
    fc = FindComment(line)
    if fc:
      _, line = fc

    # Handle open but no close paren.
    fup = FindUnclosedParen(line)
    if fup:
      while not FindClosedParen(line):
        i += 1
        must i < n, ('Missing close paren', line)
        line += lines[i]
        fc = FindComment(line)
        if fc:
          _, line = fc
    fcp = FindClosedParen(line)
    if fcp:
      _, front, middle, _ = fcp
      line = front + ' ' + middle

    # Now we have an entire line.
    orig = line

    # Find first word, which may be missing.
    word1 = None
    fw1 = FindWord(line)
    if fw1:
      _, word1, line = fw1
    else:
      # If did not remove a first word,
      # we didn't remove any white space either,
      # so do it now.
      fws = FindWhiteSpace(line)
      if fws:
        _, line = FindWhiteSpace(line)

    words = [word1]
    while True:
      fw = FindWord(line)
      if not fw:
        break
      words.append(fw[1])
      line = fw[2]

    # Anything left over had better be white space.
    fws = FindWhiteSpace(line)
    if fws:
      _, remnant = fws
      line = remnant
    if line:
        raise 'Bad line had remaining stuff', orig, remnant

    say quoted, words, orig
    i += 1
