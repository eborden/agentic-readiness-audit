import argparse


def build_parser():
    parser = argparse.ArgumentParser(description="Audit GitLab projects for CLAUDE.md / AGENTS.md presence")
    return parser


def parse_args():
    return build_parser().parse_args()
