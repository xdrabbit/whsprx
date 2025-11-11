import pytest
from whisperx import __main__ as cli
import sys
from unittest.mock import patch

def test_cli_help():
    """
    Tests if the CLI runs with --help without errors.
    """
    with patch.object(sys, 'argv', ['whisperx', '--help']):
        with pytest.raises(SystemExit) as e:
            cli.cli()
        assert e.type == SystemExit
        assert e.value.code == 0
