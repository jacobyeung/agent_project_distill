"""Habitat 0.2.4 navigation. CPU mode loads navmeshes only, with no GL context."""
import math
import numpy as np
from .config import Config
from .paths import SCENES

class Environment:
    def __init__(self, config=None, scenes=SCENES):
        import habitat_sim as hs
        self.hs, self.config, self.scenes = hs, config or Config(), scenes
        self.scene = None
        self.simulator = None
        self.graph = None
        self.agent = None
        self.pathfinder = None

    def _load(self, scene):
        if scene == self.scene:
            return
        self.close()
        hs, c = self.hs, self.config
        cfg = hs.agent.AgentConfiguration()
        cfg.height, cfg.radius = c.agent_height, c.agent_radius
        cfg.sensor_specifications = []
        cfg.action_space = {name: hs.agent.ActionSpec(kind, hs.agent.ActuationSpec(amount=amount))
                            for name, kind, amount in [('forward', 'move_forward', .25),
                                                       ('turn_left', 'turn_left', 15), ('turn_right', 'turn_right', 15)]}
        path = self.scenes / scene / (scene + '.navmesh')
        if not path.is_file():
            raise FileNotFoundError(path)
        if c.render:
            sensor = hs.CameraSensorSpec()
            sensor.uuid, sensor.sensor_type = 'rgb', hs.SensorType.COLOR
            sensor.resolution, sensor.position, sensor.hfov = [c.rgb_px, c.rgb_px], [0, c.height_m, 0], c.hfov_deg
            cfg.sensor_specifications = [sensor]
            sc = hs.SimulatorConfiguration()
            sc.scene_id = str(self.scenes / scene / (scene + '.glb'))
            sc.create_renderer, sc.enable_physics = True, False
            self.simulator = hs.Simulator(hs.Configuration(sc, [cfg]))
            self.pathfinder, self.agent = self.simulator.pathfinder, self.simulator.get_agent(0)
        else:
            self.pathfinder = hs.nav.PathFinder()
            self.graph = hs.scene.SceneGraph()
            self.agent = hs.agent.Agent(self.graph.get_root_node().create_child(), cfg)
        if not self.pathfinder.load_nav_mesh(str(path)):
            raise ValueError('Could not load navmesh ' + str(path))
        self.pathfinder.seed(c.seed)
        self.agent.controls.move_filter_fn = self.pathfinder.try_step
        self.scene = scene

    def reset(self, episode):
        import quaternion
        self._load(episode.scene)
        s = self.hs.AgentState()
        s.position = np.array(episode.start_position, dtype=np.float32)
        x, y, z, w = episode.start_rotation
        s.rotation = np.quaternion(w, x, y, z)
        self.agent.set_state(s)
        self.episode, self.stopped, self.steps = episode, False, 0
        self.positions = [self.position]
        return self.frame()

    @property
    def position(self):
        return self.agent.state.position.astype(float)

    @property
    def heading(self):
        import quaternion
        forward = quaternion.rotate_vectors(self.agent.state.rotation, [0, 0, -1])
        return math.atan2(-forward[0], -forward[2])

    def frame(self):
        if self.simulator:
            return self.simulator.get_sensor_observations()['rgb'][..., :3].copy()
        return None

    def step(self, action):
        if action not in ('stop', 'forward', 'turn_left', 'turn_right'):
            raise ValueError(action)
        if self.stopped or self.steps >= self.config.step_cap:
            return self.frame()
        self.steps += 1
        if action == 'stop':
            self.stopped = True
        else:
            self.agent.act(action)
        self.positions.append(self.position)
        return self.frame()

    def path(self, start, end):
        p = self.hs.ShortestPath()
        p.requested_start, p.requested_end = np.asarray(start, np.float32), np.asarray(end, np.float32)
        found = self.pathfinder.find_path(p)
        return float(p.geodesic_distance), [np.asarray(x, float) for x in p.points] if found else []

    def distance(self, point=None, goal=None):
        return self.path(self.position if point is None else point, self.episode.goal if goal is None else goal)[0]

    def follower(self, radius=.5):
        return self.hs.nav.GreedyGeodesicFollower(self.pathfinder, self.agent, goal_radius=radius,
                                                stop_key='stop', forward_key='forward',
                                                left_key='turn_left', right_key='turn_right')

    def close(self):
        # Agent must release its scene node before the scene graph is destroyed.
        self.agent = None
        if self.simulator is not None:
            self.simulator.close()
        self.simulator, self.graph, self.pathfinder, self.scene = None, None, None, None
