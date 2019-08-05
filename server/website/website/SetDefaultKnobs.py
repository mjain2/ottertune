#
# OtterTune - SetDefaultKnobs.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
from .models import DBMSCatalog, Hardware, KnobCatalog, Session, SessionKnob
from .types import DBMSType

def turnKnobsOff(session, knobNames):
    for knobName in knobNames:
        knob = KnobCatalog.filter(dbms=session.dbms, name=knobName)
        SessionKnob.objects.create(session=session,
                                   knob=knob,
                                   minval=knob.minval,
                                   maxval=knob.maxval,
                                   tunable=False)

def setKnobTuningRange(session, knobName, minval, maxval):
    knob = KnobCatalog.filter(dbms=session.dbms, name=knobName)
    SessionKnob.objects.create(session=session,
                               knob=knob,
                               minval=minval,
                               maxval=maxval,
                               tunable=True)

def setDefaultKnobs(session):
    if session.dbms.type==DBMSType.POSTGRES and session.dbms.version=='9.6':
        turnKnobsOff(session, ["global.backend_flush_after", "global.bgwriter_delay",
                               "global.bgwriter_flush_after", "global.bgwriter_lru_multiplier",
                               "global.checkpoint_flush_after", "global.commit_delay",
                               "global.commit_siblings", "global.deadlock_timeout",
                               "global.effective_io_concurrency", "global.from_collapse_limit",
                               "global.join_collapse_limit", "global.maintenance_work_mem",
                               "global.max_worker_processes", "global.min_parallel_relation_size",
                               "global.min_wal_size", "global.seq_page_cost", "global.wal_buffers",
                               "global.wal_sync_method", "global.wal_writer_delay",
                               "global.wal_writer_flush_after"])

        setKnobTuningRange(session, "global.checkpoint_completion_target", 0.1, 0.9)
        setKnobTuningRange(session, "global.checkpoint_timeout", 60000, 1800000)
        setKnobTuningRange(session, "global.default_statistics_target", 100, 2048)
        setKnobTuningRange(session, "global.effective_cache_size", 4294967296, 17179869184)
        setKnobTuningRange(session, "global.max_parallel_workers_per_gather", 0, 8)
        setKnobTuningRange(session, "global.max_wal_size", 268435456, 17179869184)
        setKnobTuningRange(session, "global.random_page_cost", 1, 10)
        setKnobTuningRange(session, "global.shared_buffers", 134217728, 12884901888)
        setKnobTuningRange(session, "global.temp_buffers", 8388608, 1073741824)
        setKnobTuningRange(session, "global.work_mem", 4194304, 1073741824)

