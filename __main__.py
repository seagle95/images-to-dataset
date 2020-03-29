import argparse
import logging
from extract_tfrecords import partition_data

logging.basicConfig(level=logging.INFO)
parser = argparse.ArgumentParser()
parser.add_argument("-data_root", required=True)
parser.add_argument("-output_dir", required=True, help="path to the output file")
parser.add_argument("-n_splits", type=int, required=True)
parser.add_argument("-seed", type=int, required=False)
args = parser.parse_args()

partition_data(data_root=args.data_root, output_dir=args.output_dir, n_splits=args.n_splits, seed=args.seed)