#
# OtterTune - mysql.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
'''
Created on Jan 16, 2018

@author: bohan
'''

import re
import logging
from collections import OrderedDict

from .base import BaseParser
from website.models import DBMSCatalog
from website.types import DBMSType, KnobUnitType, MetricType, VarType
from website.utils import ConversionUtil

LOG = logging.getLogger(__name__)

class MySqlParser(BaseParser):

    MYSQL_BYTES_SYSTEM = [
        (1024 ** 5, 'PB'),
        (1024 ** 4, 'TB'),
        (1024 ** 3, 'GB'),
        (1024 ** 2, 'MB'),
        (1024 ** 1, 'kB'),
        (1024 ** 0, 'B'),
    ]

    MYSQL_TIME_SYSTEM = [
        (1000 * 60 * 60 * 24, 'd'),
        (1000 * 60 * 60, 'h'),
        (1000 * 60, 'min'),
        (1, 'ms'),
        (1000, 's'),
    ]

    MYSQL_BASE_KNOBS = {
       # 'session_variables.rocksdb_max_open_files': '-1'
    }

    def __init__(self, dbms_id):
        super(MySqlParser, self).__init__(dbms_id)
        self.valid_true_val = ["ON", "TRUE", "YES", 1]
        self.valid_false_val = ["OFF", "FALSE", "NO", 0]

    @property
    def base_configuration_settings(self):
        return dict(self.MYSQL_BASE_KNOBS)

    @property
    def knob_configuration_filename(self):
        return 'mysql.conf'

    @property
    def transactions_counter(self):
        return 'session_status.queries'

    def latency_timer(self):
        return 'session_status.queries'

    def convert_integer(self, int_value, metadata):
        converted = None

        try:
            converted = super(MySqlParser, self).convert_integer(
                int_value, metadata)
        except ValueError:
            # LOG.info(metadata.unit)
            if metadata.unit == KnobUnitType.BYTES:
                converted = ConversionUtil.get_raw_size(
                    int_value, system=self.MYSQL_BYTES_SYSTEM)
            elif metadata.unit == KnobUnitType.MILLISECONDS:
                converted = ConversionUtil.get_raw_size(
                    int_value, system=self.MYSQL_TIME_SYSTEM)
            else:
                raise Exception('Unknown unit type: {}'.format(metadata.unit))
        if converted is None:
            raise Exception('Invalid integer format for {}: {}'.format(
                metadata.name, int_value))
        return converted

    def format_integer(self, int_value, metadata):
        if metadata.unit != KnobUnitType.OTHER and int_value > 0:
            if metadata.unit == KnobUnitType.BYTES:
                int_value = ConversionUtil.get_human_readable(
                    int_value, MySqlParser.MYSQL_BYTES_SYSTEM)
            elif metadata.unit == KnobUnitType.MILLISECONDS:
                int_value = ConversionUtil.get_human_readable(
                    int_value, MySqlParser.MYSQL_TIME_SYSTEM)
            else:
                raise Exception('Invalid unit type for {}: {}'.format(
                    metadata.name, metadata.unit))
        else:
            int_value = super(MySqlParser, self).format_integer(
                int_value, metadata)
        return int_value

    def parse_version_string(self, version_string):
        dbms_version = version_string.split(',')[0]
        return re.search(r'\d+\.\d+(?=\.\d+)', dbms_version).group(0)

    # moljain: A global variable in mysql could also look like session_variables.x instead of global.x
    def parse_helper(self, scope, valid_variables, view_variables, prefix_view_name):
        for view_name, variables in list(view_variables.items()):
            if scope == 'local':
                for obj_name, sub_vars in list(variables.items()):
                    for var_name, var_value in list(sub_vars.items()):  # local
                        full_name = '{}.{}.{}'.format(view_name, obj_name, var_name)
                        valid_variables[full_name] = var_value
            elif scope == 'global':
                for var_name, var_value in list(variables.items()):  # global
                    full_name = '{}.{}'.format(prefix_view_name, var_name)
                    if var_name == 'join_buffer_size':
                        LOG.info(view_name)
                        LOG.info(prefix_view_name)
                        LOG.info(full_name)
                    valid_variables[full_name] = var_value
                    # full name here: global.join_buffer_size -> session_variables.join_buffer_size
            else:
                raise Exception('Unsupported variable scope: {}'.format(scope))
        return valid_variables

    # global variable fullname: viewname.varname
    # local variable fullname: viewname.objname.varname
    # return format: valid_variables = {var_fullname:var_val}
    # prefixViewNameMySql = session_variables or session_status; this isn't automatically parsed for mysql
    # so adding manual parsing to be able to correctly label the metrics and knobs for tuning
    def parse_dbms_variables(self, variables, prefix_view_name):
        valid_variables = {}
        for scope, sub_vars in list(variables.items()):
            LOG.info("sub_vars")
            # LOG.info(sub_vars) # ex:  ('join_buffer_size', '497403648'),
            if sub_vars is None:
                continue
            if scope == 'global':
                valid_variables.update(self.parse_helper('global', valid_variables, sub_vars, prefix_view_name))
            elif scope == 'local':
                for _, viewnames in list(sub_vars.items()):
                    for viewname, objnames in list(viewnames.items()):
                        for obj_name, view_vars in list(objnames.items()):
                            valid_variables.update(self.parse_helper(
                                'local', valid_variables, {viewname: {obj_name: view_vars}}, prefix_view_name))
            else:
                raise Exception('Unsupported variable scope: {}'.format(scope))
        LOG.info("reaching end of parse_dbms_variables")
        return valid_variables

    # local variable: viewname.objname.varname
    # global variable: viewname.varname
    # This function is to change local variable fullname to viewname.varname, global
    # variable remains same. This is because local varialbe in knob_catalog is in
    # parial format (i,e. viewname.varname)
    @staticmethod
    def partial_name(full_name):
        var_name = full_name.split('.')
        if len(var_name) == 2:  # global variable
            return full_name
        elif len(var_name) == 3:  # local variable
            return var_name[0] + '.' + var_name[2]
        else:
            raise Exception('Invalid variable full name: {}'.format(full_name))

    # local variable: viewname.objname.varname
    # global variable: viewname.varname
    # This function is to change local variable fullname to viewname.varname, global
    # variable remains same. This is because local varialbe in knob_catalog is in
    # parial format (i,e. viewname.varname)
    @staticmethod
    def partial_name_metrics(full_name):
        var_name = full_name.split('.')
        if len(var_name) == 2:  # global variable
            # if ("global" in var_name[0]):
            #     return "{}.{}".format(var_name[1])
            return full_name
        elif len(var_name) == 3:  # local variable
            return var_name[0] + '.' + var_name[2]
        else:
            raise Exception('Invalid variable full name: {}'.format(full_name))

    @staticmethod
    def extract_valid_variables(variables, catalog, default_value=None):
        valid_variables = {}
        diff_log = []
        valid_lc_variables = {k.lower(): v for k, v in list(catalog.items())}
        try:
            # First check that the names of all variables are valid (i.e., listed
            # in the official catalog). Invalid variables are logged as 'extras'.
            # Variable names that are valid but differ in capitalization are still
            # added to valid_variables but with the proper capitalization. They
            # are also logged as 'miscapitalized'.
            for var_name, var_value in list(variables.items()):
                lc_var_name = var_name.lower()
                prt_name = MySqlParser.partial_name_metrics(lc_var_name)
                # LOG.info("prt_name: " + prt_name)

                #moljain add specific parsing for mysql scenario
                if ("." in prt_name):
                    subParts = prt_name.split(".")
                    if len(subParts) == 2 and subParts[0] == "global":  # global variable
                        # prt_name = "{}.{}".format(prefixMySql,subParts[1])
                        LOG.info(prt_name)

                if prt_name in valid_lc_variables:
                    valid_name = valid_lc_variables[prt_name].name
                    if prt_name != valid_name:
                        diff_log.append(('miscapitalized', valid_name, var_name, var_value))
                    valid_variables[prt_name] = var_value
                else:
                    diff_log.append(('extra', None, var_name, var_value))

            # Next find all item names that are listed in the catalog but missing from
            # variables. Missing global variables are added to valid_variables with
            # the given default_value if provided (or the item's actual default value
            # if not) and logged as 'missing'. For now missing local variables are
            # not added to valid_variables
            lc_variables = {MySqlParser.partial_name_metrics(k.lower()): v
                            for k, v in list(variables.items())}
            for valid_lc_name, metadata in list(valid_lc_variables.items()):
                if valid_lc_name not in lc_variables:
                    diff_log.append(('missing', metadata.name, None, None))
                    if metadata.scope == 'global':
                        valid_variables[metadata.name] = default_value if \
                            default_value is not None else metadata.default
        except Exception as e:
            LOG.info(e)
        return valid_variables, diff_log

    def calculate_change_in_metrics(self, metrics_start, metrics_end):
        adjusted_metrics = {}
        for met_name, start_val in list(metrics_start.items()):
            end_val = metrics_end[met_name]
            met_info = self.metric_catalog_[MySqlParser.partial_name_metrics(met_name)]
            if met_info.vartype == VarType.INTEGER or \
                    met_info.vartype == VarType.REAL:
                conversion_fn = self.convert_integer if \
                    met_info.vartype == VarType.INTEGER else \
                    self.convert_real
                start_val = conversion_fn(start_val, met_info)
                end_val = conversion_fn(end_val, met_info)
                # LOG.info("start_val,end_val {},{}".format(start_val,end_val))
                adj_val = end_val - start_val
                #assert adj_val >= 0
                adjusted_metrics[met_name] = adj_val
            else:
                # This metric is either a bool, enum, string, or timestamp
                # so take last recorded value from metrics_end
                adjusted_metrics[met_name] = end_val
        return adjusted_metrics

    def parse_dbms_knobs(self, knobs):
        valid_knobs = self.parse_dbms_variables(knobs, "session_variables")
        # Extract all valid knobs
        return MySqlParser.extract_valid_variables(
            valid_knobs, self.knob_catalog_)

    def parse_dbms_metrics(self, metrics):
        valid_metrics = self.parse_dbms_variables(metrics, "session_status")
        # Extract all valid metrics
        valid_metrics, diffs = MySqlParser.extract_valid_variables(
            valid_metrics, self.metric_catalog_,default_value='0')
        return valid_metrics, diffs

    def convert_dbms_metrics(self, metrics, observation_time, target_objective=None):
        metric_data = {}
        for name, value in list(metrics.items()):
            prt_name = MySqlParser.partial_name_metrics(name)
            if prt_name in self.numeric_metric_catalog_:
                metadata = self.numeric_metric_catalog_[prt_name]
                if metadata.metric_type == MetricType.COUNTER:
                    if ("questions" in prt_name):
                        LOG.info("QUESTIONS:{}".format(name))
                        LOG.info(value)
                        # LOG.info(float(self.convert_integer(value, metadata)) / observation_time)
                    converted = self.convert_integer(value, metadata)
                    metric_data[name] = float(converted) / observation_time
                else:
                    raise Exception('Unknown metric type for {}: {}'.format(
                        name, metadata.metric_type))

        targetObjectiveMetric = self.target_metric(target_objective)()
        LOG.info("target_objective: " + target_objective + " targetObjectiveMetric: " + targetObjectiveMetric)
        LOG.info(metric_data)
        if target_objective is not None and targetObjectiveMetric not in metric_data:
            raise Exception("Cannot find objective function")

        if target_objective is not None:
            metric_data[target_objective] = metric_data[targetObjectiveMetric]
        else:
            # default
            metric_data['throughput_txn_per_sec'] = \
                metric_data[targetObjectiveMetric]
        return metric_data

    def convert_dbms_knobs(self, knobs):
        knob_data = {}
        for name, value in list(knobs.items()):
            prt_name = MySqlParser.partial_name_metrics(name)
            if prt_name in self.tunable_knob_catalog_:
                metadata = self.tunable_knob_catalog_[prt_name]
                assert(metadata.tunable)
                value = knobs[name]
                conv_value = None
                try:
                    if metadata.vartype == VarType.BOOL:
                        conv_value = self.convert_bool(value, metadata)
                    elif metadata.vartype == VarType.ENUM:
                        conv_value = self.convert_enum(value, metadata)
                    elif metadata.vartype == VarType.INTEGER:
                        conv_value = self.convert_integer(value, metadata)
                    elif metadata.vartype == VarType.REAL:
                        conv_value = self.convert_real(value, metadata)
                    elif metadata.vartype == VarType.STRING:
                        conv_value = self.convert_string(value, metadata)
                    elif metadata.vartype == VarType.TIMESTAMP:
                        conv_value = self.convert_timestamp(value, metadata)
                    else:
                        raise Exception(
                            'Unknown variable type: {}'.format(metadata.vartype))
                    if conv_value is None:
                        raise Exception(
                            'Param value for {} cannot be null'.format(name))
                    knob_data[name] = conv_value
                except Exception as e:
                    LOG.info("{}:{}".format(name,value))
                    LOG.info(e)
        return knob_data

    def filter_numeric_metrics(self, metrics):
        return OrderedDict([(k, v) for k, v in list(metrics.items()) if
                            MySqlParser.partial_name_metrics(k) in self.numeric_metric_catalog_])

    def filter_tunable_knobs(self, knobs):
        return OrderedDict([(k, v) for k, v in list(knobs.items()) if
                            MySqlParser.partial_name_metrics(k) in self.tunable_knob_catalog_])


class MySql57Parser(MySqlParser):
    def __init__(self):
        dbms = DBMSCatalog.objects.get(
            type=DBMSType.MYSQL, version='5.7')
        super(MySql57Parser, self).__init__(dbms.pk)