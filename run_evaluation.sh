#/bin/bash

DIR_GT=/home/hcchou/Project/evaluation_tool/GT
SEQUENCE=FLY070
# 設置對齊的比對關鍵數列
ALIGN_VAR='IMU_ATTI(0):Longitude,IMU_ATTI(0):Latitude,osd_data:relativeHeight'
# 根據影片第一禎的數值來查找 gt 的對應的第一禎
ALIGN_VAL='114.2122,22.6955,300.00'
# NOTE: GT_VAR must be timestamp, var1, var2,...
GT_VAR='Clock:offsetTime,RTKdata:Lon_P,RTKdata:Lat_P'

python evaluation.py --directory_to_gt ${DIR_GT} --sequence ${SEQUENCE} \
                     --align_var ${ALIGN_VAR} --align_val ${ALIGN_VAL} \
                     --gt_var ${GT_VAR}