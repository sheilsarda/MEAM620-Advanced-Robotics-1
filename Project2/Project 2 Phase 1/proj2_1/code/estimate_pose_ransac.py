# Imports

import numpy as np
from scipy.spatial.transform import Rotation
from scipy.linalg import lstsq
from numpy.linalg import norm



# %%

def estimate_pose(uvd1, uvd2, pose_iterations, ransac_iterations, ransac_threshold):
    """
    Estimate Pose by repeatedly calling ransac

    :param uvd1:
    :param uvd2:
    :param pose_iterations:
    :param ransac_iterations:
    :param ransac_threshold:
    :return: Rotation, R; Translation, T; inliers, array of n booleans
    """

    R = Rotation.identity()

    for i in range(0, pose_iterations):
        w, t, inliers = ransac_pose(uvd1, uvd2, R, ransac_iterations, ransac_threshold)
        R = Rotation.from_rotvec(w.ravel()) * R

    return R, t, inliers


def ransac_pose(uvd1, uvd2, R, ransac_iterations, ransac_threshold):
    # find total number of correspondences
    n = uvd1.shape[1]

    # initialize inliers all false
    best_inliers = np.zeros(n, dtype=bool)

    for i in range(0, ransac_iterations):
        # Select 3  correspondences
        selection = np.random.choice(n, 3, replace=False)

        # Solve for w and  t
        w, t = solve_w_t(uvd1[:, selection], uvd2[:, selection], R)

        # find inliers
        inliers = find_inliers(w, t, uvd1, uvd2, R, ransac_threshold)

        # Update best inliers
        if inliers.sum() > best_inliers.sum():
            best_inliers = inliers.copy()

    # Solve for w and t using best inliers
    w, t = solve_w_t(uvd1[:, best_inliers], uvd2[:, best_inliers], R)

    return w, t, find_inliers(w, t, uvd1, uvd2, R, ransac_threshold)



def find_inliers(w, t, uvd1, uvd2, R0, threshold):
    """
    find_inliers core routine used to detect which correspondences are inliers

    :param w: ndarray with 3 entries angular velocity vector in radians/sec
    :param t: ndarray with 3 entries, translation vector
    :param uvd1: 3xn ndarray : normailzed stereo results from frame 1
    :param uvd2:  3xn ndarray : normailzed stereo results from frame 2
    :param R0: Rotation type - base rotation estimate
    :param threshold: Threshold to use
    :return: ndarray with n boolean entries : Only True for correspondences that pass the test
    """

    n = uvd1.shape[1]
    # TODO Your code here replace the dummy return value with a value you compute

    # initialize indicator
    indicator = np.zeros(n, dtype='bool')
    # concatenate w and t
    x = np.concatenate((w.reshape(3, 1), t.reshape(3, 1)), axis=0)

    for corr in range(n):
        a_1 =  np.array([ [1, 0, -uvd1[0, corr]], [0, 1, -uvd1[1, corr]] ])
        # compute y matrix
        y = R0.as_matrix() @ np.array([uvd2[0, corr], uvd2[1, corr], 1]).reshape(3, 1)
        a_2 = np.array([ [0, y[2], -y[1], uvd2[2, corr], 0, 0],
                         [-y[2], 0, y[0], 0, uvd2[2, corr], 0],
                         [y[1], -y[0], 0, 0, 0, uvd2[2, corr]] ])
        b_corr = np.array([[1, 0, -uvd1[0, corr]], [0, 1, -uvd1[1, corr]]]) @ y

        # compute discrepancy
        delta = (a_1 @ a_2 @ x) + b_corr

        # compute norm of delta and compare with threshold
        delta = norm(delta)
        if delta < threshold: indicator[corr] = True

    return indicator

def solve_w_t(uvd1, uvd2, R0):
    """
    solve_w_t core routine used to compute best fit w and t given a set of stereo correspondences

    :param uvd1: 3xn ndarray : normailzed stereo results from frame 1
    :param uvd2: 3xn ndarray : normailzed stereo results from frame 1
    :param R0: Rotation type - base rotation estimate
    :return: w, t : 3x1 ndarray estimate for rotation vector, 3x1 ndarray estimate for translation
    """

    # TODO Your code here replace the dummy return value with a value you compute

    # Initialize matrix a_1 with dimension of (2*n) by (3*n) and a_2 with dim of (3*n) by 6
    n = uvd1.shape[1] # get number of correspondences
    a_1 = np.zeros((2 * n, 3 * n))
    a_2 = np.zeros((3 * n, 6))

    # Initialize column vector of b with dim of 2*n
    b = np.zeros((2 * n, 1))

    for corr in range(n):
        # compute y matrix
        y = R0.as_matrix() @ np.array([uvd2[0, corr], uvd2[1, corr], 1]).reshape(3, 1)
        # compute b column vector for each correspondence
        b_corr = -1 * np.array([[1, 0, -uvd1[0, corr]], [0, 1, -uvd1[1, corr]]]) @ y

        # construct the big matrix a_1, a_2 and b
        a_1[corr * 2: corr * 2 + 2, corr * 3: corr * 3 + 3] = np.array([[1, 0, -uvd1[0, corr]],
                                                                        [0, 1, -uvd1[1, corr]]])
        a_2[corr * 3: corr * 3 + 3, :] = np.array([ [0, y[2], -y[1], uvd2[2, corr], 0, 0],
                                                    [-y[2], 0, y[0], 0, uvd2[2, corr], 0],
                                                    [y[1], -y[0], 0, 0, 0, uvd2[2, corr]] ])
        b[corr * 2: corr * 2 + 2] = b_corr

    # compute the big A matrix
    a = a_1 @ a_2

    # compute lease square fit
    sol, _, _, _ = lstsq(a, b)

    # extract w and t from solution
    sol = sol.reshape(6, 1)
    w = sol[:3]
    t = sol[3:]

    return w, t
