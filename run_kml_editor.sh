#/bin/bash

ORG_FILE='/home/hcchou/Project/evaluation_tool/GT/FLY081.kml'
DST_FILE='/home/hcchou/Project/evaluation_tool/GT/FLY081_Seg.kml'
PATTERN_BEGIN='114.2148150167855,22.69755436204876,179.43312'
PATTERN_END='114.20679506919177,22.68951369964839,200.9918'

python kml_editor.py --org_file ${ORG_FILE} --dst_file ${DST_FILE} --begin ${PATTERN_BEGIN} --end ${PATTERN_END}