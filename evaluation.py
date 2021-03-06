#!/usr/bin/env python
import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
from pygeotile.point import Point

class Csv:
    def __init__(self, var_directory_csv):
        self.directory_csv = var_directory_csv
        self.data = pd.read_csv(self.directory_csv, index_col=0)

    def get_target_column(self, var):
        return self.data.loc[:, var].to_numpy(dtype='float')

class Trajectory:
    def __init__(self):
        self.index_first_frame = -1
        self.gt_rtk_with_timestamp = []
        self.gt_trj_with_timestamp = []
        self.gt_interp_trj_with_timestamp = []
        self.es_trj_with_timestamp = []

    def find_first_frame(self, table, val, begin=0):
        # Check the round values.
        table_round = np.around(table, decimals=4)
        temp = np.sum(np.absolute(table_round - val), axis=1)
        ind_candidate = np.where(temp == 0.0)
        # Find the closest.
        temp = np.sum(np.absolute(table[ind_candidate] - val), axis=1)
        ind = np.nanargmin(temp)
        # Locate the first frame.
        self.index_first_frame = ind_candidate[0][ind] + begin

    def get_gt_rtk_with_timestamp(self, table):
        self.gt_rtk_with_timestamp = table[self.index_first_frame:, :]
        # The timestamp is reorganized according to first frame.
        self.gt_rtk_with_timestamp[:, 0] = self.gt_rtk_with_timestamp[:, 0] - self.gt_rtk_with_timestamp[0, 0]

    def get_gt_trj_with_timestamp(self, table):
        self.gt_trj_with_timestamp = table[self.index_first_frame:, :]
        # The timestamp is reorganized according to first frame.
        self.gt_trj_with_timestamp[:, 0] = self.gt_trj_with_timestamp[:, 0] - self.gt_trj_with_timestamp[0, 0]
        for ind in range(len(self.gt_trj_with_timestamp)):
            x, y, z = self.convert_lon_lat_2_x_y(self.gt_trj_with_timestamp[ind, 1], self.gt_trj_with_timestamp[ind, 2])
            self.gt_trj_with_timestamp[ind, 1:] = [x, y]

    def get_est_trj_with_timestamp(self, directory_est_tum):
        # Take first three column, including timestamp, x and y only.
        self.es_trj_with_timestamp =  np.genfromtxt(directory_est_tum, delimiter=' ')[:, :3]

    # The interpolation is based on the timestamp of estimated trajectory, because the frequency of gt is higher than es.
    def interp_gt_trj_with_timestamp(self, trj_gt, trj_es):
        self.gt_interp_trj_with_timestamp = np.zeros(shape=(len(trj_es), 3), dtype='float')
        last_ind_gt = 0
        for ind_es in range(len(trj_es)):
            # timestamp handling.
            if trj_es[ind_es, 0] >= trj_gt[-1, 0]:
                self.gt_interp_trj_with_timestamp[ind_es] = trj_gt[-1, :]
                print('The timestamp of estimated trj. is longer than ground-truth trj. Use last ground-truth position.')
                continue
            elif trj_es[ind_es, 0] < trj_gt[0, 0]:
                self.gt_interp_trj_with_timestamp[ind_es] = trj_gt[0, :]
                print('The timestamp of estimated trj. is shorter than ground-truth trj. Use initial ground-truth position')
                continue
            else:
                for ind_gt in range(last_ind_gt, len(trj_gt)):
                    # Find interpolation timestamp.
                    if trj_gt[ind_gt, 0] <= trj_es[ind_es, 0] < trj_gt[ind_gt + 1, 0]:
                        r = (trj_es[ind_es, 0] - trj_gt[ind_gt, 0]) / (trj_gt[ind_gt + 1, 0] - trj_gt[ind_gt, 0])
                        self.gt_interp_trj_with_timestamp[ind_es] = [trj_es[ind_es, 0], \
                                                                     trj_gt[ind_gt, 1] + (trj_gt[ind_gt + 1, 1] - trj_gt[ind_gt, 1]) * r, \
                                                                     trj_gt[ind_gt, 2] + (trj_gt[ind_gt + 1, 2] - trj_gt[ind_gt, 2]) * r]
                        last_ind_gt = ind_gt
                        break

    def convert_lon_lat_2_x_y(self, longitude, latitude, altitude=0.0):
        point = Point.from_latitude_longitude(latitude, longitude)
        # The source code of from_latitude_longitude method.
        # EARTH_RADIUS = 6378137.0
        # ORIGIN_SHIFT = 2.0 * math.pi * EARTH_RADIUS / 2.0
        # meter_x = longitude * ORIGIN_SHIFT / 180.0
        # meter_y = math.log(math.tan((90.0 + latitude) * math.pi / 360.0)) / (math.pi / 180.0)
        # meter_y = meter_y * ORIGIN_SHIFT / 180.0
        return point.meters[0], point.meters[1], 0.0

class Evaluation:
    def __init__(self):
        self.dist_traveled = 0.0
        self.rmse = 0.0
        self.errs = []

    def statistic(self, trj_interp_gt, trj_es):
        if len(trj_interp_gt) != len(trj_es):
            print('Estimated trajectory has different length with interpolated gt, check estimated trajectory size.')
        self.dist_traveled = np.sum(np.linalg.norm(np.diff(trj_interp_gt, axis=0)[:, 1:], axis=1))
        self.rmse = np.sqrt(np.sum(np.power(trj_es[:, 1:] - trj_interp_gt[:, 1:], 2)) / len(trj_interp_gt))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Evaluation script')
    parser.add_argument('--directory_to_gt', required=True, type=str, help='directory of ground-truth related files')
    parser.add_argument('--sequence', required=True, type=str, help='the sequence, e.g. FLY070')
    parser.add_argument('--align_var', required=True, type=str, help='the variables for time alignment')
    parser.add_argument('--align_val', required=True, type=str, help='the values corresponding to variables')
    parser.add_argument('--gt_var', required=True, type=str, help='the variables of ground truth')
    args = parser.parse_args()

    # Init directory_gt_csv.
    directory_gt_csv = os.path.join(args.directory_to_gt, args.sequence) + '.csv'
    # Init directory_es_tum.
    directory_es_tum = os.path.join(args.directory_to_gt, args.sequence) + '_EST'
    # Init align_var, gt_var.
    align_var = args.align_var.split(',')
    gt_var = args.gt_var.split(',')
    # Init align_val.
    align_val = np.asarray(args.align_val.split(','), dtype=np.float)

    # Read .csv file and split specific columns.
    table_whole = Csv(directory_gt_csv)
    table_align = table_whole.get_target_column(align_var)
    table_rtk = table_whole.get_target_column(gt_var)

    # Trajectory object.
    trj = Trajectory()
    # Find first frame according to alignment variables and target values.
    trj.find_first_frame(table_align, align_val)
    # Get ground truth based on x-y coordinate.
    trj.get_gt_trj_with_timestamp(table_rtk)
    # Get estimated trajectory which is based on x-y coordinate.
    # tum format: https://github.com/MichaelGrupp/evo/wiki/Formats#tum---tum-rgb-d-dataset-trajectory-format
    trj.get_est_trj_with_timestamp(directory_es_tum)
    trj.interp_gt_trj_with_timestamp(trj.gt_trj_with_timestamp, trj.es_trj_with_timestamp)
    # Translate estimated trj. according to the first frame of gt.
    trj.es_trj_with_timestamp[:, 1:] = trj.es_trj_with_timestamp[:, 1:] - trj.es_trj_with_timestamp[0, 1:] + trj.gt_interp_trj_with_timestamp[0, 1:]

    # Evaluation
    eval = Evaluation()
    eval.statistic(trj.gt_interp_trj_with_timestamp, trj.es_trj_with_timestamp)
    # Print messages.
    print('Distance traveled: %.5f (m)' % eval.dist_traveled)
    print('RMSE is %.5f (m)' % eval.rmse)

    # Plot trajectory, gt and es.
    plt.plot(trj.gt_interp_trj_with_timestamp[:, 1], trj.gt_interp_trj_with_timestamp[:, 2], 'r-')
    plt.plot(trj.es_trj_with_timestamp[:, 1], trj.es_trj_with_timestamp[:, 2], 'b-')
    plt.plot(trj.gt_interp_trj_with_timestamp[0, 1], trj.gt_interp_trj_with_timestamp[0, 2], 'k^')
    plt.legend(['Ground truth', 'Estimated trj.', 'First frame'])
    # Add title, labels, grid, etcs.
    plt.title(args.sequence)
    plt.xlabel('x(m)')
    plt.ylabel('y(m)')
    plt.grid(True)
    plt.show()
