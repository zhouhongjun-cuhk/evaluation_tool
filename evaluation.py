#!/usr/bin/env python
import argparse
import matplotlib.pyplot as plt
import math
import numpy as np
import os
import pandas as pd

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

    def get_est_trj_with_timestamp(self):
        # TODO: import correct dataset.
        self.es_trj_with_timestamp = self.gt_trj_with_timestamp.copy()
        # Rotate trajectory.
        theta = 30.0 * math.pi / 180.0
        for ind in range(len(self.es_trj_with_timestamp)):
            dx = self.es_trj_with_timestamp[ind, 1] - self.es_trj_with_timestamp[0, 1]
            dy = self.es_trj_with_timestamp[ind, 2] - self.es_trj_with_timestamp[0, 2]
            self.es_trj_with_timestamp[ind, 1] = dx * math.cos(theta) - dy * math.sin(theta) + self.es_trj_with_timestamp[0, 1]
            self.es_trj_with_timestamp[ind, 2] = dx * math.sin(theta) + dy * math.cos(theta) + self.es_trj_with_timestamp[0, 2]

    def convert_lon_lat_2_x_y(self, longitude, latitude, altitude=0.0):
        # WGS-84 semi-major axis
        a = 6378137.0
        # WGS-84 first eccentricity squared
        e2 = 6.6943799901377997e-3
        n = a / math.sqrt(1.0 - e2 * math.sin(latitude) * math.sin(latitude))
        x = (n + altitude) * math.cos(latitude) * math.cos(longitude)
        y = (n + altitude) * math.cos(latitude) * math.sin(longitude)
        z = (n * (1.0 - e2) + altitude) * math.sin(latitude)
        # x, y, z are in meter
        return x, y, z

class Evaluation:
    def __init__(self):
        self.gt_interp_trj_with_timestamp = []

    # The interpolation is based on the timestamp of estimated trajectory, because the frequency of gt is higher than es.
    def interp_gt_trj_with_timestamp(self, trj_gt, trj_es):
        self.gt_interp_trj_with_timestamp = np.zeros(shape=(len(trj_es), 3), dtype='float')
        last_ind_gt = 0
        for ind_es in range(len(trj_es)):
            for ind_gt in range(last_ind_gt, len(trj_gt)):
                # timestamp handling.
                if trj_es[ind_es, 0] >= trj_gt[-1, 0]:
                    self.gt_interp_trj_with_timestamp[ind_es] = trj_gt[-1, :]
                    print('The timestamp of estimated trj. is longer than ground-truth trj. Use last ground-truth position.')
                    break
                elif trj_es[ind_es, 0] < trj_gt[0, 0]:
                    self.gt_interp_trj_with_timestamp[ind_es] = trj_gt[0, :]
                    print('The timestamp of estimated trj. is shorter than ground-truth trj. Use initial ground-truth position')
                    break
                # Find interpolation timestamp.
                if trj_gt[ind_gt, 0] <= trj_es[ind_es, 0] < trj_gt[ind_gt + 1, 0]:
                    r = (trj_es[ind_es, 0] - trj_gt[ind_gt, 0]) / (trj_gt[ind_gt + 1, 0] - trj_gt[ind_gt, 0])
                    self.gt_interp_trj_with_timestamp[ind_es] = [trj_es[ind_es, 0], \
                                                                 trj_gt[ind_gt, 1] + (trj_gt[ind_gt + 1, 1] - trj_gt[ind_gt, 1]) * r, \
                                                                 trj_gt[ind_gt, 2] + (trj_gt[ind_gt + 1, 2] - trj_gt[ind_gt, 2]) * r]
                    last_ind_gt = ind_gt
                    break

    def calculate_rmse(self, trj_interp_gt, trj_es):
        if len(trj_interp_gt) != len(trj_es):
            print('Estimated trajectory has different length with interpolated gt, check estimated trajectory size.')
        rmse = np.sqrt(np.sum(np.power(trj_es[:, 1:] - trj_interp_gt[:, 1:], 2)) / len(trj_interp_gt))
        return rmse

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
    # Get estimated trajectory based on x-y coordinate.
    trj.get_est_trj_with_timestamp()

    # Evaluation
    eval = Evaluation()
    eval.interp_gt_trj_with_timestamp(trj.gt_trj_with_timestamp, trj.es_trj_with_timestamp)
    rmse = eval.calculate_rmse(eval.gt_interp_trj_with_timestamp, trj.es_trj_with_timestamp)
    print ('rmse is %.5f (m)' % rmse)

    # Plot trajectory, gt and es.
    plt.plot(trj.gt_trj_with_timestamp[:, 1], trj.gt_trj_with_timestamp[:, 2], 'r-')
    plt.plot(trj.es_trj_with_timestamp[:, 1], trj.es_trj_with_timestamp[:, 2], 'b-')
    plt.plot(trj.gt_trj_with_timestamp[0, 1], trj.gt_trj_with_timestamp[0, 2], 'r^')
    plt.plot(eval.gt_interp_trj_with_timestamp[0, 1], eval.gt_interp_trj_with_timestamp[0, 2], 'b^')
    plt.plot(eval.gt_interp_trj_with_timestamp[:, 1], eval.gt_interp_trj_with_timestamp[:, 2], 'k--')
    plt.legend(['ground truth', 'estimate trj.', 'ground truth, begin', 'estimate trj. begin', 'interpolated ground truth'])
    # Add labels, grid, etcs.
    plt.xlabel('x(m)')
    plt.ylabel('y(m)')
    plt.grid(True)
    plt.show()


