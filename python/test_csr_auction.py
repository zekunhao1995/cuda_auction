#!/usr/bin/env python

"""
    test_dot_auction.py
"""

from __future__ import print_function

import sys
assert sys.version_info.major == 3, "sys.version_info.major != 3"

import sys
import json
import argparse
import numpy as np
from time import time
from scipy import sparse
from lap import lapjv

from lap_auction import dot_auction
from lap_auction import dense_lap_auction, csr_lap_auction


# --
# Run


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dim', type=int, default=128)
    parser.add_argument('--k', type=int, default=None)
    parser.add_argument('--density', type=float, default=0.5)
    parser.add_argument('--max-value', type=float, default=10)
    parser.add_argument('--seed', type=int, default=123)
    args = parser.parse_args()
    if args.k is None:
        args.k = args.dim
    return args

if __name__ == "__main__":
    args = parse_args()
    np.random.seed(args.seed)
    
    _ = dense_lap_auction(np.random.choice(10, (10, 10)))
    
    # --
    # Generate data
    
    t = time()
    X = sparse.rand(args.dim, args.dim, density=args.density, format='csr')
    X.eliminate_zeros()
    X = X.tocsr()
    gen_time = time() - t
    print('gen_time  ', gen_time, file=sys.stderr)
    
    np.savetxt('.indptr', X.indptr, fmt='%d')
    np.savetxt('.indices', X.indices, fmt='%d')
    np.savetxt('.data', X.data, fmt='%f')
    
    # --
    # Run JV algorithm
    
    print('-' * 50, file=sys.stderr)
    t = time()
    Xd = np.asarray(X.todense())
    _, src_ass, _ =  lapjv((Xd.max() - Xd))
    jv_time  = int(1000 * (time() - t))
    assigned = X[(np.arange(X.shape[0]), src_ass)]
    jv_worst = (X >= assigned.reshape(-1, 1)).sum(axis=1).max()
    jv_score = assigned.sum()
    
    print({
        "jv_time"  : jv_time,
        "jv_worst" : jv_worst,
        "jv_score" : jv_score,
    }, file=sys.stderr)
    
    assert args.k >= jv_worst, "args.k too small"
    
    # --
    # Run CSR GPU auction
    
    print('-' * 50, file=sys.stderr)
    t = time()
    auc_ass = csr_lap_auction(X,
        verbose=True, num_runs=3,
        auction_max_eps=1.0, auction_min_eps=1.0, auction_factor=0.0)
    sparse_auction_time  = int(1000 * (time() - t))
    assert len(set(auc_ass)) == args.dim
    sparse_auction_score = int(X[(np.arange(X.shape[0]), auc_ass)].sum())
    
    print({
        "sparse_auction_time"  : sparse_auction_time,
        "sparse_auction_score" : sparse_auction_score,
    }, file=sys.stderr)
    