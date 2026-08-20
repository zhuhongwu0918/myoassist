from dataclasses import dataclass, field


@dataclass
class TrainSessionConfigBase:
    total_timesteps: int = 1000

    @dataclass
    class LoggerParams:
        logging_frequency: int = int(1)
        evaluate_frequency: int = int(64)

    logger_params: LoggerParams = field(default_factory=LoggerParams)

    @dataclass
    class EnvParams:
        @dataclass
        class RewardWeights:
            forward_reward: float = 0.01
            muscle_activation_penalty: float = 0.1
            # 设备力矩的代价，单位与 muscle_activation_penalty 相同：两项都是「时间步长 × 平均无量纲出力」。
            # 因为肌肉平均是对 22 个执行器取的、设备平均是对 2 个执行器取的，所以单执行器代价分别是
            # muscle_activation_penalty/22 和 exo_activation_penalty/2 —— 在默认肌肉权重 10 下，
            # exo 权重取 0.1 时，单个设备执行器的出力大约比单个肌肉便宜十倍。默认值 0 保持现有配置不变。
            exo_activation_penalty: float = 0.0
            muscle_activation_diff_penalty: float = 0.1

            # 按步计算的奖励
            footstep_delta_time: float = 0.0
            average_velocity_per_step: float = 0.0
            muscle_activation_penalty_per_step: float = 0.0

            joint_constraint_force_penalty: float = 0.0

            foot_force_penalty: float = 0.0

        reward_keys_and_weights: RewardWeights = field(default_factory=RewardWeights)

        env_id: str = ""
        num_envs: int = 1
        seed: int = 0
        safe_height: float = 0.65
        control_framerate: int = 30
        physics_sim_framerate: int = 1200

        min_target_velocity: float = 0.5
        max_target_velocity: float = 3.0
        min_target_velocity_period: float = 3
        max_target_velocity_period: float = 5

        custom_max_episode_steps: int = 500
        model_path: str = None
        prev_trained_policy_path: str = None
        reference_data_path: str = ""

        enable_lumbar_joint: bool = False
        lumbar_joint_fixed_angle: float = 0.0
        lumbar_joint_damping_value: float = 0.05

        # 渲染时需要隐藏的 geom 分组。哪组放杂物、哪组放硬件，是建模者约定的惯例，
        # 环境无法自动推导，所以放在这里而不是代码里。这取代了原来无条件的「隐藏组 1」——
        # 原注释说那是为了去掉肌肉骨骼皮肤；但 myolegs22 和 myolegs26 在组 1 中没有 geom，
        # 它实际唯一的效果是把 STRIDE_L2 的整个六连杆机构（14 个 geom）藏起来，只留下鞋可见。
        # 仅影响渲染：alpha 不参与接触、质量或约束计算。
        hidden_geom_groups: list[int] = field(default_factory=list)

        observation_joint_pos_keys: list[str] = field(default_factory=list)
        observation_joint_vel_keys: list[str] = field(default_factory=list)
        observation_joint_sensor_keys: list[str] = field(default_factory=list)
        # 约束力惩罚所用的关节限位（约束力）传感器名称。
        # 留空则使用 MyoAssistLegBase.JOINT_LIMIT_SENSOR_NAMES 的默认值。
        joint_limit_sensor_keys: list[str] = field(default_factory=list)

        # A10 组合流水线。当 msk_key 和 device_key 同时设置时，通过
        # myoassist_utils.compose.compose_env_model(...)（人体肌肉骨骼模型 + 辅助设备 + 地形）
        # 组合生成模型，并把得到的 XML 字符串作为模型使用。两者都设为 None 时，
        # 回退到上面的 model_path 原样加载（逃生通道）。terrain 是
        # myoassist_terrains JSON 配置的路径，或为 None 表示默认平地。
        msk_key: str = None
        device_key: str = None
        terrain: str = None

    env_params: EnvParams = field(default_factory=EnvParams)

    """
    用于 TrainAnalyzer
        total_timesteps: int = 300
        min_target_velocity: float = 1.25
        max_target_velocity: float = 1.25
        target_velocity_period: float = 3
        velocity_mode: str = "SINUSOIDAL"
        cam_type: str = "follow"
        cam_distance: float = 2.5
        visualize_activation: bool = True
    """
    evaluate_param_list: list[dict] = field(default_factory=list[dict])

    @dataclass
    class PolicyParams:
        """
        ActorCriticPolicy 参数：
            observation_space: spaces.Space,
            action_space: spaces.Space,
            lr_schedule: Schedule,
            net_arch: Optional[Union[list[int], dict[str, list[int]]]] = None,
            activation_fn: type[nn.Module] = nn.Tanh,
            ortho_init: bool = True,
            use_sde: bool = False,
            log_std_init: float = 0.0,
            full_std: bool = True,
            use_expln: bool = False,
            squash_output: bool = False,
            features_extractor_class: type[BaseFeaturesExtractor] = FlattenExtractor,
            features_extractor_kwargs: Optional[dict[str, Any]] = None,
            share_features_extractor: bool = True,
            normalize_images: bool = True,
            optimizer_class: type[th.optim.Optimizer] = th.optim.Adam,
            optimizer_kwargs: Optional[dict[str, Any]] = None,
        """

        # @dataclass
        # class CustomPolicyParams:
        #     reset_shared_net: bool = False
        #     reset_policy_net: bool = False
        #     reset_value_net: bool = False
        # custom_policy_params: CustomPolicyParams = field(default_factory=CustomPolicyParams)
        @dataclass
        class CustomPolicyParams:
            # 用于课程学习（curriculum learning）
            reset_shared_net_after_load: bool = False
            reset_policy_net_after_load: bool = False
            reset_value_net_after_load: bool = False
            # reset_log_std_after_load: bool = False

            net_arch: dict = field(default_factory=dict)
            log_std_init: float = field(default=-2.0)

            net_indexing_info: dict = field(default_factory=dict)

        custom_policy_params: CustomPolicyParams = field(default_factory=CustomPolicyParams)

    policy_params: PolicyParams = field(default_factory=PolicyParams)

    @dataclass
    class PPOParams:
        learning_rate: float = 3e-4
        n_steps: int = 4096
        batch_size: int = 2048
        n_epochs: int = 10
        gamma: float = 0.99
        gae_lambda: float = 0.95
        clip_range: float = 0.2
        clip_range_vf: float = 0.2
        ent_coef: float = 0.01
        vf_coef: float = 0.5
        max_grad_norm: float = 0.5
        use_sde: bool = False
        sde_sample_freq: int = -1
        target_kl: float = None
        device: str = "cpu"
        # 左右镜像对称惩罚的权重（见 rl_train/train/mirror_ppo.py）。
        # 设为 0 时禁用，PPO 行为与之前完全一致。
        mirror_coef: float = 0.0

    ppo_params: PPOParams = field(default_factory=PPOParams)
