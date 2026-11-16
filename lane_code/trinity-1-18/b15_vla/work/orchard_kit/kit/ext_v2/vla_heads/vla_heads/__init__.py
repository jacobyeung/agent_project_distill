"""Action heads that turn the student VLM into a VLA. Pure PyTorch; see README.md."""
from .adapters import StubBackbone, StudentAdapter, TokenBinding, left_pad
from .checkpoint import load_checkpoint, rng_state, save_checkpoint, set_rng_state
from .codecs import CharTokenizer, DCTCodec, DigitsCodec, FastCodec, UniformBins, make_codec, nav_text, reserved
from .cond import CondProjector, where_features, withheld_draw
from .config import VLAConfig
from .data import EpochSampler
from .heads import FlowExpert, RegressionHead, TokensHead, make_head
from .interface import ActionHead, HeadInputs
from .policy import QUERY_TOKEN, VLAPolicy, query_positions, query_token_id
from .utils import (ChunkExecutor, Normalizer, ProprioEncoder, TemporalEnsembler, gripper_command, gripper_from_unit,
                    gripper_to_unit, make_chunks, warmup_cosine)

__version__ = '0.3.0'
INTERFACE_VERSION = 'vla_heads_interface_v2'
SCHEMA = 'vla_schema_v2'
