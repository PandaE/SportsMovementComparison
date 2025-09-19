from .view_models import ActionEvaluationVM, StageVM, MetricVM, TrainingVM, FrameRef, VideoInfo

# Pure mock producer for quick preview (no core dependencies)

def build_mock_vm() -> ActionEvaluationVM:
    # Use real test video assets for frame extraction preview
    user_v = r'D:\\code\SportsMovementComparison\\tests\\experimental\\test_data\\me.mp4'
    std_v = r'D:\\code\SportsMovementComparison\\tests\\experimental\\test_data\\demo.mp4'
    stages = [
        StageVM(
            key='setup',
            name='架拍阶段',
            score=64,
            summary_raw='准备姿势稳定但拍面稍后仰。',
            suggestion='放低球拍准备高度，保持肩部放松。',
            metrics=[
                MetricVM(key='elbow_angle', name='肘部角度', user_value=75, std_value=65, unit='°', deviation=10, status='warn'),
                MetricVM(key='shoulder_abduction', name='肩关节外展', user_value=32, std_value=30, unit='°', deviation=2, status='ok'),
                MetricVM(key='center_height', name='重心高度', user_value=1.12, std_value=1.10, unit='m', deviation=0.02, status='ok'),
            ],
            user_frame=FrameRef(frame_index=60, video_path=user_v),
            standard_frame=FrameRef(frame_index=80, video_path=std_v)
        ),
        StageVM(
            key='backswing',
            name='引拍阶段',
            score=78,
            summary_raw='躯干旋转幅度合适。',
            suggestion='保持核心收紧，避免腰部塌陷。',
            metrics=[
                MetricVM(key='trunk_rotation', name='躯干旋转', user_value=70, std_value=72, unit='°', deviation=-2, status='ok'),
                MetricVM(key='elbow_flex', name='肘屈角', user_value=52, std_value=50, unit='°', deviation=2, status='ok'),
                MetricVM(key='backswing_width', name='后摆宽度', user_value=0.82, std_value=0.85, unit='m', deviation=-0.03, status='ok'),
            ],
            user_frame=FrameRef(frame_index=70, video_path=user_v),
            standard_frame=FrameRef(frame_index=90, video_path=std_v)
        ),
        StageVM(
            key='power',
            name='发力阶段',
            score=58,
            summary_raw='前臂加速不足，髋部提前打开。',
            suggestion='延迟髋部打开顺序，加强前臂鞭击训练。',
            metrics=[
                MetricVM(key='hip_rotation_speed', name='髋部旋转速度', user_value=210, std_value=250, unit='°/s', deviation=-40, status='bad'),
                MetricVM(key='forearm_ang_acc', name='前臂角加速度', user_value=820, std_value=950, unit='°/s²', deviation=-130, status='warn'),
                MetricVM(key='impact_timing', name='挥拍时间点', user_value=0.62, std_value=0.58, unit='s', deviation=0.04, status='warn'),
            ],
            user_frame=FrameRef(frame_index=80, video_path=user_v),
            standard_frame=FrameRef(frame_index=100, video_path=std_v)
        ),
    ]
    training = TrainingVM(
        key_issues=['手肘角度过大', '前臂加速不足'],
        improvement_drills=['靠墙挥拍', '节奏分解练习'],
        next_steps=['加入多球训练', '加强核心稳定性']
    )
    return ActionEvaluationVM(
        sport='羽毛球',
        action_name='正手高远球',
        score=72,
        summary_raw='玩家完成了全部挥拍动作序列。',
        summary_refined='你的架拍过高，导致发力效率下降',
        stages=stages,
        training=training,
    video=VideoInfo(user_video_path=user_v, standard_video_path=std_v)
    )

__all__ = ['build_mock_vm']
