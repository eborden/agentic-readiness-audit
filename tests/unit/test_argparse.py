import argparse
from claude_md_audit.argparse import build_parser, parse_args


def test_build_parser_returns_argument_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_parse_args_no_args_succeeds(monkeypatch):
    monkeypatch.setattr("sys.argv", ["prog"])
    result = parse_args()
    assert result is not None
