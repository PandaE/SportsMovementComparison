from __future__ import annotations
import os, sys
from PyQt5.QtWidgets import QApplication

# Ensure project root in path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.append(ROOT)

from core.new_evaluation.data_models import (
    KeyframeSet, FrameRef
)
from core.new_evaluation.config_converter import convert
from core.new_evaluation.session import EvaluationSession
from core.experimental.config.sport_configs import SportConfigs
from core.new_evaluation.adapter import UIAdapter
from ui.new_results.results_window import ResultsWindow

# Reuse the same test assets as mock_data
USER_VIDEO = r'D:\code\SportsMovementComparison\tests\experimental\test_data\me.mp4'
STD_VIDEO = r'D:\code\SportsMovementComparison\tests\experimental\test_data\demo.mp4'

# Build real config from experimental sport configs
old_action_cfg = SportConfigs.get_config('Badminton', 'Forehand Clear')
config = convert(old_action_cfg)

keyframes = KeyframeSet(
    user={
        'setup': FrameRef(USER_VIDEO, 46),
        'backswing': FrameRef(USER_VIDEO, 60),
        'power': FrameRef(USER_VIDEO, 69)
    },
    standard={
        'setup': FrameRef(STD_VIDEO, 36),
        'backswing': FrameRef(STD_VIDEO, 57),
        'power': FrameRef(STD_VIDEO, 80)
    }
)

def main():
    session = EvaluationSession(config, keyframes, user_video=USER_VIDEO, standard_video=STD_VIDEO)
    # Evaluate all dirty stages
    session.evaluate()
    state = session.get_state()
    vm = UIAdapter.to_vm(state, keyframes.user, keyframes.standard)

    app = QApplication.instance() or QApplication(sys.argv)
    win = ResultsWindow(vm, session=session, keyframes=keyframes, adapter=UIAdapter)
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
