"""Sciences Tricorder — PDF 112-114. Run: Blender -b -P model-source/blender/sciences_tricorder.py [-- closed|section <out_dir>]
Shared case/head model in tricorder.py; this builds the open arrangement (PDF 113) for the site, lower circuitry section closed."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tricorder
tricorder.run('sciences-tricorder')
