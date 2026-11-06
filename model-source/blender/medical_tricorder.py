"""Medical Tricorder — PDF 124-126. Run: Blender -b -P model-source/blender/medical_tricorder.py [-- closed|section <out_dir>]
Shared case/head model in tricorder.py; open arrangement (PDF 125): R/P lid open, life-form sensor/analyzer bay exposed,
lower compartment lid partially open."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tricorder
tricorder.run('medical-tricorder')
