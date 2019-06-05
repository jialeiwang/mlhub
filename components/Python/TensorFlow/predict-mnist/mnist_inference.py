from __future__ import print_function
import argparse
import os.path
import sys
import time

from mnist_stream_input import MnistStreamInput
from saved_model import SavedModel


def add_parameters(parser):
    # input arguments
    parser.add_argument("--randomize_input", dest="random", default=False, action='store_true')
    parser.add_argument("--total_records", type=int, dest="total_records", default=1000, required=False)
    parser.add_argument("--input_dir",
                        dest="input_dir",
                        type=str,
                        required=False,
                        help='Directory for caching input data',
                        default="/tmp/mnist_data")
    parser.add_argument("--output_file",
                        dest="output_file",
                        type=str,
                        required=False,
                        help='File for output predictions',
                        default="/tmp/mnist_predictions")
    # TF model arguments
    parser.add_argument("--model_type", dest="model_kind", type=str, default="saved_model",
                        required=False, choices=['saved_model', 'tf_serving'])

    parser.add_argument("--model_dir", dest="model_dir", type=str, required=True)
    parser.add_argument("--sig_name", dest="sig_name", default="predict_images", type=str)

    # TF model arguments for TF Serving
    parser.add_argument("--host_port", dest="host_port", type=str, default='localhost:9000', required=False)
    parser.add_argument("--concurrency", dest="concurrency", type=int, default=1, required=False)

    # Stats arguments
    parser.add_argument("--stats_interval", dest="stats_interval", type=int, default=100, required=False)
    parser.add_argument("--stats_type", dest="stats_type", type=str, default="python", required=False)
    parser.add_argument("--conf_thresh", dest="conf_thresh", help='Confidence threshold for raising alerts',
                        type=int, default=50, required=False)
    parser.add_argument("--conf_percent", dest="conf_percent", help='Confidence percent for raising alerts',
                        type=int, default=10, required=False)

def infer_loop(model, input):

    while True:
        try:
            sample, label = input.get_next_input()
            model.infer(sample, label)

        except EOFError:
            # stop when we hit end of input
            break


def main():
    parser = argparse.ArgumentParser()
    add_parameters(parser)
    args = parser.parse_args()

    print("model should be in: {}".format(args.model_dir))
    if os.path.isdir(args.model_dir):
        print("Found model_dir")
    else:
        print("model dir is not found")
        exit(0)

    input = MnistStreamInput(args.input_dir, args.total_records, args.random)

    output = open(args.output_file, "w")

    if args.model_kind == 'saved_model':
        model = SavedModel(output, args.model_dir, args.sig_name, args.stats_interval, args.stats_type, args.conf_thresh,
            args.conf_percent)

    elif args.model_kind == 'tf_serving':
        # TF serving client API currently only supports python 2.7
        assert sys.version_info >= (2, 7) and sys.version_info <= (2, 8)
        from tensorflow_serving_model import TfServingModel
        model = TfServingModel(output, args.model_dir, args.sig_name, args.stats_interval, args.stats_type,
                               args.conf_thresh, args.conf_percent, sargs.host_port, args.concurrency)

    else:
        raise ValueError("Unsupported model type: ", args.model_kind)

    infer_loop(model, input)

    output.close()
    del model
    del input


if __name__ == "__main__":
    main()
