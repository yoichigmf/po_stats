#```python:translated.py

import polib
import sys
  
def translated_p(path):
	po = polib.pofile(path)
	return po.percent_translated()

def translated_e(path):

	po = polib.pofile(path)
	ent = po.translated_entries()
	return len(ent)

  

def get_entities( path ):

	po = polib.pofile(path)
	return len(po)

def untranslated_e(path):

	po = polib.pofile(path)
	ent = po.untranslated_entries()
	return len(ent)

if __name__ == '__main__':

	args = sys.argv

	if 2 <= len(args):

		for i in range(1, len(args)):
			ts =translated_e(args[i])
			sz =get_entities(args[i])
			ut = untranslated_e(args[i])

			#   全アイテム数 : 翻訳済数 : 未翻訳数
			print(args[i], ":", sz, ":", ts, ":", ut )

	else:
		print('#error: Arguments are too short')