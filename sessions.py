#! /usr/local/bin/python3
# -*- utf-8 -*-


"""
Total: 45

0: number of 3-hour defined sessions in the enrollment

1~4: average, standard deviation, maximal, minimal numbers of events in
3-hour defined sessions in the enrollment

5~8: statistics of 3-hour defined sessions: mean, std, max, min of duration

9: number of 1-hour defined sessions in the enrollment

10~13: average, standard deviation, maximal, minimal numbers of events in
1-hour defined sessions in the enrollment

14~17: statistics of 1-hour defined sessions: mean, std, max, min of duration

18: number of 12-hour defined sessions in the enrollment

19~22: average, standard deviation, maximal, minimal numbers of events in
12-hour defined sessions in the enrollment

23~26: statistics of 12-hour defined sessions: mean, std, max, min of duration

27: number of 1-day defined sessions in the enrollment

28~31: average, standard deviation, maximal, minimal numbers of events in
1-day defined sessions in the enrollment

32~35: statistics of 1-day defined sessions: mean, std, max, min of duration

36: number of 7-day defined sessions in the enrollment

37~40: average, standard deviation, maximal, minimal numbers of events in
7-day defined sessions in the enrollment

41~44: statistics of 7-day defined sessions: mean, std, max, min of duration
"""


import logging
import sys
import os
from datetime import timedelta

import numpy as np
import pandas as pd

import IO
import Path
import Util


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format='%(asctime)s %(name)s %(levelname)s\t%(message)s')
logger = logging.getLogger(os.path.basename(__file__))


def extract(base_date):
    logger.debug('prepare datasets ...')

    enroll_all = IO.load_enrollments()
    log_all = IO.load_logs()

    log_all = log_all[log_all['time'] <= base_date]

    logger.debug('datasets prepared')

    # 0: number of 3-hour defined sessions in the enrollment

    # 1~4: average, standard deviation, maximal, minimal numbers of events in
    # 3-hour defined sessions in the enrollment

    # 5~8: statistics of 3-hour defined sessions: mean, std, max, min of
    # duration

    X3H = sessions_of(log_all, timedelta(hours=3))

    logger.debug('0~8')

    # 9: number of 1-hour defined sessions in the enrollment

    # 10~13: average, standard deviation, maximal, minimal numbers of events in
    # 1-hour defined sessions in the enrollment

    # 14~17: statistics of 1-hour defined sessions: mean, std, max, min of
    # duration

    X1H = sessions_of(log_all, timedelta(hours=1))

    logger.debug('9~17')

    # 18: number of 12-hour defined sessions in the enrollment

    # 19~22: average, standard deviation, maximal, minimal numbers of events in
    # 12-hour defined sessions in the enrollment

    # 23~26: statistics of 12-hour defined sessions: mean, std, max, min of
    # duration

    X12H = sessions_of(log_all, timedelta(hours=12))

    logger.debug('18~26')

    # 27: number of 1-day defined sessions in the enrollment

    # 28~31: average, standard deviation, maximal, minimal numbers of events in
    # 1-day defined sessions in the enrollment

    # 32~35: statistics of 1-day defined sessions: mean, std, max, min of
    # duration

    X1D = sessions_of(log_all, timedelta(days=1))

    logger.debug('27~35')

    # 36: number of 7-day defined sessions in the enrollment

    # 37~40: average, standard deviation, maximal, minimal numbers of events in
    # 7-day defined sessions in the enrollment

    # 41~44: statistics of 7-day defined sessions: mean, std, max, min of
    # duration

    X7D = sessions_of(log_all, timedelta(days=7))

    logger.debug('36~44')

    check_dataframe = Util.dataframe_checker(logger)

    check_dataframe(X3H, 'X3H')
    X = pd.merge(enroll_all, X3H, how='left', on='enrollment_id')

    check_dataframe(X1H, 'X1H')
    X = pd.merge(X, X1H, how='left', on='enrollment_id')

    check_dataframe(X12H, 'X12H')
    X = pd.merge(X, X12H, how='left', on='enrollment_id')

    check_dataframe(X1D, 'X1D')
    X = pd.merge(X, X1D, how='left', on='enrollment_id')

    check_dataframe(X7D, 'X7D')
    X = pd.merge(X, X7D, how='left', on='enrollment_id')

    del X['username']
    del X['course_id']

    X.fillna(0, inplace=True)
    check_dataframe(X, 'X')

    return X


def sessions_of(log_all, delta_t):
    def __session__(group):
        group_t = group['time'].sort(inplace=False).reset_index(drop=True)
        dt = (group_t[1:].reset_index() - group_t[:-1].reset_index())['time']
        session_break = dt > delta_t
        breaks_indices = session_break[session_break].index.values

        sessions_indices = []
        i = 0
        for b in breaks_indices:
            if b < i:
                i += 1
            else:
                sessions_indices.append((i, b))
                i = b + 1
        if i < len(group_t):
            sessions_indices.append((i, len(group_t) - 1))

        feature = [len(sessions_indices)]
        indices = ['count']

        nums_of_events = [j - i + 1 for i, j in sessions_indices]
        feature += [f(nums_of_events)
                    for f in [np.average, np.std, np.max, np.min]]
        indices += ['ec_' + i for i in ['mean', 'std', 'max', 'min']]

        sessions = pd.DataFrame(
            [(group_t[i], group_t[j]) for i, j in sessions_indices],
            columns=['st', 'et'])
        duration_ratio = (sessions['et'] - sessions['st']) / delta_t
        feature += [f(duration_ratio) for
                    f in [np.average, np.std, np.max, np.min]]
        indices += ['dr_' + i for i in ['mean', 'std', 'max', 'min']]

        return pd.Series(feature, index=indices)

    return log_all.groupby('enrollment_id').apply(__session__).reset_index()
