"""Test ScaleAnchor + FK on G3T and DA3 on LIBERO renders to quantify 3D lifting accuracy once scale/cross-view pose are anchored."""
import json
from pathlib import Path
import numpy as np
from vla_where import build, geometry_viewset as GV, precheck, renders, scale as S
from vla_where.backends.gt import GTPointer, GTPresence, GTProposals, GTStore
from vla_where.provider import Config, WhereProvider
import run_p1_p4_and_da3_diag as D

raw_eps = list(renders.episodes(D.RENDERS_DIR))
he = S.HandEye.load(D.HAND_EYE_PATH, D.HAND_EYE_SHA)
t11 = json.loads(D.T11_PATH.read_text())


class ScaleAnchorGeometry:
    """Wraps G3T or DA3 ViewSet geometry with ScaleAnchor (per-view depth scale + FK T_wrist<-agent)."""
    def __init__(self, base_geo, store, use_gt_k=True):
        self.base_geo = base_geo
        self.store = store
        self.use_gt_k = use_gt_k

    def pin(self):
        return self.base_geo.pin()

    def sha(self):
        return self.base_geo.sha()

    def run(self, images, views=None):
        res = self.base_geo.run(images, views)
        (_, t0), (_, t1) = views[0], views[1]
        M4 = np.diag([-1.0, 1.0, 1.0, 1.0])
        T_bw = self.store.view(("wrist", t0))["T_base_cam"]
        T_ba = self.store.view(("agent", t1))["T_base_cam"]
        T_wa_fk = np.linalg.inv(T_bw) @ T_ba
        T_wa_mir = (M4 @ T_wa_fk @ M4) if res.mirror else T_wa_fk
        new_depths = list(res.depth)
        for idx, role_step in ((0, ("wrist", t0)), (1, ("agent", t1))):
            g_d = np.asarray(self.store.view(role_step)["depth"], dtype=np.float64)
            m_d = res.depth[idx]
            ok = np.isfinite(g_d) & np.isfinite(m_d) & (g_d > 0.05) & (m_d > 1e-4)
            s_v = float(np.median(g_d[ok] / m_d[ok])) if ok.any() else 1.0
            new_depths[idx] = m_d * s_v
        new_T0 = res.T0.copy()
        new_T0[1] = T_wa_mir
        new_K = res.K.copy()
        if self.use_gt_k:
            new_K[0] = np.abs(self.store.view(("wrist", t0))["K"])
            new_K[1] = np.abs(self.store.view(("agent", t1))["K"])
        return GV.ViewSetResult(
            res.views, new_T0, res.fov, new_K, new_depths, res.conf,
            metric_flag="proprio_handeye", up=res.up, mirror=res.mirror
        )


def main():
    shared = GTStore()
    def make_gen():
        for ep, st, eid in raw_eps:
            shared.bind(st.frames, st.names, st.nouns, st.episode)
            yield ep, shared, eid

    cfg = Config(tau=0.5, history_offsets=(2, 4, 8), g3t_mirror_x=True)
    ref = build.build_provider("reference", config=cfg, hand_eye=he, store=shared)

    g3t_geom = GV.ViewSetG3T.load_pinned(D.G3T_W, D.G3T_C, device="cuda", mirror_x=True)
    da3_model = D.load_da3("cuda")
    da3_geom = D.ViewSetDA3(da3_model, mirror_x=True, process_res=504)

    out = {}
    for name, geom, use_k in [
        ("G3T_ScaleAnchor_FK_predK", g3t_geom, False),
        ("G3T_ScaleAnchor_FK_calibK", g3t_geom, True),
        ("DA3_ScaleAnchor_FK_predK", da3_geom, False),
        ("DA3_ScaleAnchor_FK_calibK", da3_geom, True),
    ]:
        prov_sa = WhereProvider(
            GTPresence(shared), GTPointer(shared), GTProposals(shared),
            ScaleAnchorGeometry(geom, shared, use_gt_k=use_k), he, cfg
        )
        _, summary = precheck.evaluate(prov_sa, ref, make_gen(), stride=2, t11=t11)
        print("\n" + precheck.report(summary, label=name, tau=0.5))
        out[name] = summary

    (D.OUT_DIR / "scale_anchor_fk_diag.json").write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
