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
        turnKnobsOff(session, [])
        #setKnobTuningRange(session, "", session.hardware.RAM * 2)

