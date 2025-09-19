"""
Translation keys constants for internationalization.
翻译键常量定义，用于类型安全和IDE支持
"""

class TranslationKeys:
    """翻译键常量类，使用层次化命名"""
    
    # UI相关翻译键
    class UI:
        class MainWindow:
            TITLE = "ui.main_window.title"
            SETTINGS = "ui.main_window.settings"
            EXPERIMENTAL_MODE = "ui.main_window.experimental_mode"
            SPORT_LABEL = "ui.main_window.sport_label"
            ACTION_LABEL = "ui.main_window.action_label"
            IMPORT_USER = "ui.main_window.import_user"
            IMPORT_STANDARD = "ui.main_window.import_standard"
            COMPARE = "ui.main_window.compare"
            COMPARE_ADVANCED = "ui.main_window.compare_advanced"
            COMPARE_BASIC = "ui.main_window.compare_basic"
            ANALYSIS_GROUP = "ui.main_window.analysis_group"
        
        class Settings:
            TITLE = "ui.settings.title"
            LANGUAGE = "ui.settings.language"
            LANGUAGE_CHINESE = "ui.settings.language_chinese"
            LANGUAGE_ENGLISH = "ui.settings.language_english"
            OK = "ui.settings.ok"
            CANCEL = "ui.settings.cancel"
            APPLY = "ui.settings.apply"
        
        class VideoPlayer:
            PLAY = "ui.video_player.play"
            PAUSE = "ui.video_player.pause"
            STOP = "ui.video_player.stop"
            SPEED = "ui.video_player.speed"
            FRAME = "ui.video_player.frame"
            IMPORT_TIP = "ui.video_player.import_tip"
            PREV_TIP = "ui.video_player.prev_tip"
            NEXT_TIP = "ui.video_player.next_tip"
            PLAY_TIP = "ui.video_player.play_tip"
            PAUSE_TIP = "ui.video_player.pause_tip"
            SHOW_POSE = "ui.video_player.show_pose"
            SELECT_VIDEO = "ui.video_player.select_video"
            FRAME_INFO = "ui.video_player.frame_info"
            TIME_INFO = "ui.video_player.time_info"
        
        class Analysis:
            TITLE = "ui.analysis.title"
            VIDEO_PREVIEW = "ui.analysis.video_preview"
            USER_VIDEO = "ui.analysis.user_video"
            STANDARD_VIDEO = "ui.analysis.standard_video"
            STAGE_ANALYSIS = "ui.analysis.stage_analysis"
            COMPARE_GROUP = "ui.analysis.compare_group"
            RESULT_GROUP = "ui.analysis.result_group"
            FRAME = "ui.analysis.frame"
            UPDATE = "ui.analysis.update"
            LOADING = "ui.analysis.loading"
            NO_DATA = "ui.analysis.no_data"
            SCORE = "ui.analysis.score"
            STATUS = "ui.analysis.status"
            MEASUREMENTS = "ui.analysis.measurements"
            USER = "ui.analysis.user"
            STANDARD = "ui.analysis.standard"
            NO_DETAIL = "ui.analysis.no_detail"
            UNKNOWN_RULE = "ui.analysis.unknown_rule"
            SHOW_FAIL = "ui.analysis.show_fail"
            
            # Stage names
            STAGE_SETUP = "ui.analysis.stage_setup"
            STAGE_BACKSWING = "ui.analysis.stage_backswing"
            STAGE_POWER = "ui.analysis.stage_power"
            STAGE_IMPACT = "ui.analysis.stage_impact"
            STAGE_FOLLOW_THROUGH = "ui.analysis.stage_follow_through"
            STAGE_UNKNOWN = "ui.analysis.stage_unknown"
            STAGE_UNKNOWN = "ui.analysis.stage_unknown"
        
        class Results:
            TITLE = "ui.results.title"
            SCORE = "ui.results.score"
            DETAILED_SCORE = "ui.results.detailed_score"
            VIDEO_TAB = "ui.results.video_tab"
            ANALYSIS_TAB = "ui.results.analysis_tab"
            COMBINED_STAGE_TAB = "ui.results.combined_stage_tab"
            DETAILED_TAB = "ui.results.detailed_tab"
            POSE_TAB = "ui.results.pose_tab"
            USER_VIDEO = "ui.results.user_video"
            STANDARD_VIDEO = "ui.results.standard_video"
            KEY_ANALYSIS = "ui.results.key_analysis"
            DETAILED_MEASUREMENTS = "ui.results.detailed_measurements"
            POSE_VISUALIZATION = "ui.results.pose_visualization"
            NO_POSE_IMAGE = "ui.results.no_pose_image"
            USER_POSE = "ui.results.user_pose"
            STANDARD_POSE = "ui.results.standard_pose"
            ANALYSIS_RESULT = "ui.results.analysis_result"
            SUGGESTION = "ui.results.suggestion"
            EVAL_SUMMARY = "ui.results.eval_summary"
            EVAL_STAGE_SCORE = "ui.results.eval_stage_score"
            EVAL_OVERALL_SCORE = "ui.results.eval_overall_score"
            EVAL_MEAS_OK = "ui.results.eval_measure_ok"
            EVAL_MEAS_FAIL = "ui.results.eval_measure_fail"
            EVAL_ALL_ACCEPTABLE = "ui.results.eval_all_acceptable"
            EVAL_NEEDS_IMPROVEMENT = "ui.results.eval_needs_improvement"
            # Frame editing
            EDIT_FRAMES = "ui.results.edit_frames"
            USER_FRAME_IDX = "ui.results.user_frame_idx"
            STANDARD_FRAME_IDX = "ui.results.standard_frame_idx"
            APPLY_CHANGES = "ui.results.apply_changes"
            RERUN_ANALYSIS = "ui.results.rerun_analysis"
            FRAME_OVERRIDE_MODE = "ui.results.frame_override_mode"
            
            # Report text
            COMPARISON_REPORT = "ui.results.comparison_report"
            SPORT_TYPE = "ui.results.sport_type"
            ACTION_TYPE = "ui.results.action_type"
            ANALYSIS_TYPE = "ui.results.analysis_type"
            ADVANCED_ANALYSIS = "ui.results.advanced_analysis"
            BASIC_ANALYSIS = "ui.results.basic_analysis"
            COMPARISON_DATA = "ui.results.comparison_data"
            USER_FRAME = "ui.results.user_frame"
            STANDARD_FRAME = "ui.results.standard_frame"
            RULES_APPLIED = "ui.results.rules_applied"
            TOTAL_COMPARISONS = "ui.results.total_comparisons"
            OVERALL_SCORE = "ui.results.overall_score"
            STAGE = "ui.results.stage"
            STAGE_SCORE = "ui.results.stage_score"
            ERROR_INFO = "ui.results.error_info"
            UNKNOWN = "ui.results.unknown"
            LLM_REFINED_SUMMARY = "ui.results.llm_refined_summary"

        # Backward compatibility alias (some code references TK.UI.RESULTS.*)
        RESULTS = Results
        
        class Dialogs:
            SELECT_VIDEO = "ui.dialogs.select_video"
            VIDEO_FILES = "ui.dialogs.video_files"
            ERROR = "ui.dialogs.error"
            INFO = "ui.dialogs.info"
            WARNING = "ui.dialogs.warning"
            QUESTION = "ui.dialogs.question"
        
        class Common:
            OK = "ui.common.ok"
            CANCEL = "ui.common.cancel"
            APPLY = "ui.common.apply"
            CLOSE = "ui.common.close"
            SAVE = "ui.common.save"
            LOAD = "ui.common.load"
    
    # 分析相关翻译键
    class Analysis:
        class Sports:
            BADMINTON = "analysis.sports.badminton"
        
        class Actions:
            CLEAR_SHOT = "analysis.actions.clear_shot"
            FOREHAND_CLEAR = "analysis.actions.forehand_clear"
        
        class Stages:
            SETUP_STAGE = "analysis.stages.setup_stage"
            BACKSWING_STAGE = "analysis.stages.backswing_stage"
            POWER_STAGE = "analysis.stages.power_stage"
            SETUP_DESCRIPTION = "analysis.stages.setup_description"
            BACKSWING_DESCRIPTION = "analysis.stages.backswing_description"
            POWER_DESCRIPTION = "analysis.stages.power_description"
        
        class Measurements:
            ARM_ANGLE = "analysis.measurements.arm_angle"
            ELBOW_HEIGHT = "analysis.measurements.elbow_height"
            WRIST_BACKSWING = "analysis.measurements.wrist_backswing"
            ARM_EXTENSION = "analysis.measurements.arm_extension"
        
        class Results:
            SCORE = "analysis.results.score"
            EXCELLENT = "analysis.results.excellent"
            GOOD = "analysis.results.good"
            NEEDS_IMPROVEMENT = "analysis.results.needs_improvement"
            POOR = "analysis.results.poor"
    
    # 错误和提示信息
    class Messages:
        class Errors:
            FILE_NOT_FOUND = "messages.errors.file_not_found"
            INVALID_VIDEO = "messages.errors.invalid_video"
            ANALYSIS_FAILED = "messages.errors.analysis_failed"
            NO_POSE_DETECTED = "messages.errors.no_pose_detected"
        
        class Info:
            ANALYSIS_STARTING = "messages.info.analysis_starting"
            ANALYSIS_COMPLETE = "messages.info.analysis_complete"
            VIDEO_LOADED = "messages.info.video_loaded"
            LANGUAGE_CHANGED = "messages.info.language_changed"
        
        class Suggestions:
            KEEP_GOOD_WORK = "messages.suggestions.keep_good_work"
            ADJUST_ARM_ANGLE = "messages.suggestions.adjust_arm_angle"
            IMPROVE_POSTURE = "messages.suggestions.improve_posture"
            PRACTICE_MORE = "messages.suggestions.practice_more"

# 便利的别名
TK = TranslationKeys