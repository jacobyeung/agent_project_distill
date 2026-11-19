"""Regressions for bounded lookahead, shutdown, refusals and startup validation."""
import copy
import os
import threading
import unittest
import weakref
from types import SimpleNamespace
from unittest.mock import patch

import torch
from student_pilot import c1_cpu_prefetch as prefetch, c1_switches as switches
from student_pilot import carrier_c1_run as run, c1_decoded_cache
from tests.so_helpers import root, inputs, native, plan, TinyProcessor, assert_nested


class ReviewTests(unittest.TestCase):
    def setUp(self):
        from tests.so_helpers import reset_switches
        reset_switches(self)

    def test_startup_values_errors_cross_rank_and_frozen_settings(self):
        with patch.dict(os.environ, C1_CPU_PREFETCH='0', C1_DECODED_CACHE_MIB='0', C1_BATCH_METRICS='0'):
            for name, bad in [('C1_CPU_PREFETCH','2'), ('C1_BATCH_METRICS','yes'),
                              ('C1_DECODED_CACHE_MIB','bad'), ('C1_DECODED_CACHE_MIB','4097')]:
                with patch.dict(os.environ, {name:bad}):
                    self.assertIn('startup refusal', switches.accept(switches.startup({}), ('0','0','0')))
            self.assertIn('differ across ranks', switches.accept(switches.startup({}), ('1','0','0')))
            self.assertIsNone(switches.accept(switches.startup({}), ('0','0','0')))
            os.environ['C1_CPU_PREFETCH'] = '1'
            self.assertEqual(switches.get('C1_CPU_PREFETCH'), '0')

    def test_refusal_list_and_group_cap(self):
        for fields in [dict(training_mode='mixed'), dict(geometry_online={'gf1':{}}),
                       dict(geometry_connector='gf1'), dict(gf1=True), dict(mdg=True)]:
            model = SimpleNamespace(**dict(dict(training_mode='final'), **fields))
            with self.assertRaises(ValueError):
                switches.prefetch_supported(model)
        with self.assertRaisesRegex(ValueError, 'MDG'):
            switches.prefetch_supported(SimpleNamespace(training_mode='final'), ['mdg'])
        with self.assertRaisesRegex(ValueError, '1..8'):
            next(prefetch.fetch_groups(None, SimpleNamespace(training_mode='final'),
                 [[('vqa',[0])]*9], 0, None, False))

    def test_group_tensor_budget_error_is_deferred(self):
        rows = SimpleNamespace(get=lambda *a:(torch.ones(3), None, {}), close=lambda:None)
        producer = prefetch.Producer(lambda:rows)
        try:
            with patch.object(prefetch, 'MAX_GROUP_TENSOR_BYTES', 16):
                values = producer.pool.submit(producer.prepare, 'vqa', [0,1], lambda *a:None, None).result()
            self.assertTrue(values[0][0])
            self.assertFalse(values[1][0])
            self.assertIn('budget', str(values[1][1]))
            self.assertIsNone(values[1][1].__traceback__)
        finally:
            producer.close()

    def test_nonowner_close_refused_and_owner_closes(self):
        producer = prefetch.Producer(lambda:None)
        errors = []
        def other():
            try:
                producer.close()
            except RuntimeError as exc:
                errors.append(str(exc))
        worker = threading.Thread(target=other)
        worker.start(); worker.join()
        self.assertEqual(len(errors), 1)
        producer.close()

    def test_replay_releases_consumed_rows_and_consumer_failure_drains_future(self):
        entered, release, finished = threading.Event(), threading.Event(), threading.Event()
        refs = []
        class Rows:
            def count(self, stream): return 8
            def cpu_prefetch_factory(self): return Rows
            def get(self, stream, index):
                if index >= 2:
                    entered.set()
                    if not release.wait(10): raise RuntimeError('test release timeout')
                    finished.set()
                value = torch.ones(1)
                refs.append(weakref.ref(value))
                return value, None, {}
            def close(self): pass
        rows = Rows()
        def fetch_nominal(source,stream,indices,*a,**kw):
            return [source.get(stream,index) for index in indices]
        groups = [[('vqa',[i]) for i in (0,1)], [('vqa',[i]) for i in (2,3)]]
        with patch.object(run,'check_row',lambda *a:None), patch.object(run,'fetch_nominal',fetch_nominal):
            iterator = prefetch.fetch_groups(rows,SimpleNamespace(training_mode='final'),groups,0,None,False)
            first = next(iterator)
            self.assertTrue(entered.wait(10))
            del first
            second = next(iterator)
            self.assertIsNone(refs[0]())
            try:
                raise ValueError('consumer failed mid-group')
            except ValueError:
                release.set()
                iterator.close()
            self.assertTrue(finished.is_set())
            rows._c1_cpu_producer.close()

    def test_first_and_last_group_failure_and_combined_cache_at_1_4_8_threads(self):
        receipt = inputs(root())
        model = native()
        original = run.Rows.get
        try:
            for threads in (1,4,8):
                torch.set_num_threads(threads)
                for failure in (None,'pose','pointing'):
                    outcomes=[]
                    for enabled in ('0','1'):
                        draws=[]
                        def get(rows,stream,index):
                            self.assertEqual(torch.get_num_threads(), threads)
                            draws.append((stream,index))
                            if stream == failure and index == 0:
                                raise ValueError('planted boundary failure')
                            return original(rows,stream,index)
                        with patch.dict(os.environ,C1_CPU_PREFETCH=enabled,
                                        C1_DECODED_CACHE_MIB=enabled), patch.object(run.Rows,'get',get):
                            rows=run.Rows(receipt,TinyProcessor())
                            values=[]; error=None
                            iterator=run.fetch_plan(rows,model,plan(),0)
                            try:
                                values.extend(iterator)
                            except ValueError as exc:
                                error=str(exc)
                            finally:
                                iterator.close();rows.close()
                            outcomes.append((draws,values,error))
                    assert_nested(self,*outcomes)
                    self.assertEqual(len(outcomes[0][1]), {'pose':0,'pointing':6,None:8}[failure])
            stats=c1_decoded_cache.stats()
            self.assertGreater(stats['hits'],0)
            self.assertGreater(stats['misses'],0)
            self.assertLessEqual(stats['bytes'],stats['capacity_bytes'])
        finally:
            torch.set_num_threads(8)
