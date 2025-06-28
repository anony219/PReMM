import csv
import os

import utils
from basic_framework.main_graph import main_agent
from defects4j_tools.defects4j import prepare_project, get_necessary_path, test_project
from defects4j_tools.fault_localization import fault_locate
from logger import Logger

d4j_bus = ['Lang-3', 'Math-37', 'Math-30', 'Lang-4', 'Math-39', 'Math-55', 'Math-52', 'Time-7', 'Math-99', 'Math-64',
           'Math-90', 'Math-103', 'Math-97', 'Time-9', 'Math-63', 'Math-38', 'Lang-5', 'Math-31', 'Math-36', 'Lang-2',
           'Time-8', 'Math-62', 'Math-96', 'Math-105', 'Math-91', 'Math-65', 'Math-102', 'Math-53', 'Math-98', 'Time-6',
           'Math-54', 'Time-1', 'Closure-31', 'Lang-44', 'Closure-36', 'Mockito-38', 'Lang-43', 'Mockito-31',
           'Mockito-36', 'Closure-38', 'Closure-107', 'Lang-26', 'Closure-98', 'Math-5', 'Time-10', 'Lang-19',
           'Closure-53', 'Math-2', 'Lang-21', 'Closure-100', 'Closure-54', 'Time-17', 'Mockito-7', 'Lang-17',
           'Closure-62', 'Time-21', 'Closure-109', 'Lang-28', 'Closure-96', 'Time-19', 'Mockito-9', 'Closure-131',
           'Lang-10', 'Closure-91', 'Time-26', 'Closure-65', 'Closure-39', 'Mockito-37', 'Mockito-30', 'Closure-37',
           'Lang-42', 'Closure-30', 'Lang-45', 'Mockito-8', 'Time-18', 'Lang-11', 'Closure-130', 'Closure-64',
           'Closure-90', 'Time-27', 'Lang-16', 'Time-20', 'Closure-97', 'Lang-29', 'Closure-108', 'Closure-63',
           'Math-3', 'Closure-101', 'Lang-20', 'Mockito-6', 'Time-16', 'Closure-55', 'Closure-99', 'Lang-27',
           'Closure-106', 'Math-4', 'Closure-52', 'Mockito-1', 'Lang-18', 'Closure-70', 'Closure-84', 'Chart-9',
           'Closure-3', 'Closure-124', 'Closure-83', 'Closure-77', 'Closure-123', 'Closure-48', 'Closure-4', 'Chart-7',
           'Closure-41', 'Lang-34', 'Closure-115', 'Closure-46', 'Closure-79', 'Closure-112', 'Lang-33', 'Chart-17',
           'Closure-12', 'Lang-58', 'Lang-60', 'Mockito-24', 'Chart-10', 'Mockito-12', 'Chart-19', 'Closure-23',
           'Chart-26', 'Mockito-15', 'Lang-51', 'Chart-21', 'Closure-24', 'Chart-1', 'Closure-47', 'Lang-32',
           'Closure-113', 'Closure-78', 'Closure-40', 'Chart-6', 'Closure-114', 'Lang-35', 'Closure-76', 'Closure-82',
           'Closure-5', 'Closure-49', 'Closure-122', 'Closure-85', 'Closure-71', 'Closure-125', 'Closure-2', 'Chart-8',
           'Mockito-14', 'Lang-50', 'Closure-25', 'Chart-20', 'Chart-18', 'Mockito-13', 'Lang-57', 'Closure-22',
           'Lang-61', 'Mockito-25', 'Chart-11', 'Closure-14', 'Mockito-22', 'Lang-59', 'Closure-13', 'Chart-16',
           'Math-49', 'Math-76', 'Math-82', 'Math-85', 'Math-71', 'Math-78', 'Math-47', 'Math-40', 'Math-14', 'Math-13',
           'Math-25', 'Math-22', 'Math-41', 'Math-79', 'Math-46', 'Math-70', 'Math-84', 'Math-48', 'Math-83', 'Math-77',
           'Math-23', 'Math-15', 'Math-51', 'Time-4', 'Math-56', 'Time-3', 'Math-69', 'Math-94', 'Math-60', 'Math-67',
           'Math-93', 'Math-58', 'Math-100', 'Math-33', 'Lang-7', 'Math-34', 'Lang-9', 'Math-92', 'Math-66', 'Math-101',
           'Math-59', 'Math-61', 'Math-95', 'Math-106', 'Math-57', 'Time-2', 'Math-68', 'Math-50', 'Time-5', 'Lang-8',
           'Math-35', 'Lang-1', 'Lang-6', 'Math-32', 'Closure-68', 'Math-1', 'Closure-103', 'Lang-22', 'Closure-57',
           'Mockito-4', 'Time-14', 'Closure-104', 'Time-13', 'Mockito-3', 'Closure-50', 'Lang-13', 'Closure-132',
           'Closure-59', 'Closure-92', 'Time-25', 'Closure-66', 'Lang-14', 'Closure-61', 'Math-8', 'Time-22',
           'Closure-95', 'Closure-35', 'Lang-40', 'Closure-32', 'Lang-47', 'Mockito-35', 'Lang-49', 'Mockito-32',
           'Lang-15', 'Time-23', 'Math-9', 'Closure-94', 'Closure-60', 'Closure-58', 'Closure-133', 'Lang-12',
           'Closure-67', 'Closure-93', 'Time-24', 'Closure-105', 'Lang-24', 'Math-7', 'Closure-51', 'Mockito-2',
           'Time-12', 'Closure-102', 'Closure-69', 'Time-15', 'Mockito-5', 'Closure-56', 'Lang-48', 'Mockito-33',
           'Mockito-34', 'Closure-33', 'Lang-46', 'Closure-34', 'Lang-41', 'Lang-63', 'Mockito-27', 'Closure-29',
           'Mockito-18', 'Chart-13', 'Closure-16', 'Lang-64', 'Mockito-20', 'Closure-11', 'Chart-14', 'Closure-18',
           'Mockito-16', 'Lang-52', 'Closure-27', 'Chart-22', 'Mockito-29', 'Mockito-11', 'Lang-55', 'Chart-25',
           'Closure-20', 'Closure-80', 'Closure-74', 'Closure-120', 'Closure-7', 'Closure-73', 'Closure-118',
           'Closure-87', 'Lang-39', 'Closure-127', 'Chart-3', 'Closure-45', 'Closure-9', 'Lang-30', 'Closure-129',
           'Closure-42', 'Chart-4', 'Closure-116', 'Closure-89', 'Lang-37', 'Mockito-10', 'Lang-54', 'Closure-21',
           'Chart-24', 'Mockito-17', 'Lang-53', 'Closure-19', 'Mockito-28', 'Chart-23', 'Closure-26', 'Lang-65',
           'Mockito-21', 'Chart-15', 'Closure-10', 'Closure-28', 'Lang-62', 'Closure-17', 'Chart-12', 'Chart-5',
           'Closure-43', 'Closure-128', 'Lang-36', 'Closure-88', 'Closure-117', 'Closure-8', 'Closure-44', 'Chart-2',
           'Closure-110', 'Lang-31', 'Lang-38', 'Closure-86', 'Closure-119', 'Closure-72', 'Closure-126', 'Closure-1',
           'Closure-75', 'Closure-81', 'Closure-6', 'Closure-121', 'Math-10', 'Math-17', 'Math-28', 'Math-21',
           'Math-26', 'Math-19', 'Math-86', 'Math-72', 'Math-75', 'Math-81', 'Math-88', 'Math-43', 'Math-44', 'Math-27',
           'Math-18', 'Math-20', 'Math-16', 'Math-29', 'Math-11', 'Math-45', 'Math-89', 'Math-42', 'Math-80', 'Math-74',
           'Math-73', 'Math-87']
d4jv2_bugs = ['JacksonCore-4', 'JxPath-2', 'JacksonCore-3', 'JxPath-5', 'Csv-14', 'Cli-4', 'JacksonXml-4',
              'Compress-40', 'Cli-3', 'Compress-47', 'JacksonXml-3', 'Compress-13', 'Csv-7', 'Codec-4', 'JxPath-10',
              'Compress-14', 'JxPath-17', 'Codec-3', 'Csv-9', 'JxPath-21', 'Compress-25', 'JxPath-19', 'Jsoup-6',
              'Cli-2', 'Compress-46', 'Cli-5', 'Jsoup-1', 'Csv-15', 'Compress-41', 'JacksonXml-5', 'Jsoup-8',
              'JacksonCore-5', 'JxPath-3', 'Compress-24', 'Csv-8', 'Compress-23', 'JxPath-20', 'Compress-15',
              'Codec-2', 'Csv-1', 'JxPath-16', 'Compress-12', 'JxPath-11', 'Csv-6', 'Codec-5', 'JacksonDatabind-49',
              'Cli-12', 'JacksonDatabind-76', 'JacksonDatabind-82', 'Cli-15', 'JacksonDatabind-85', 'Compress-4',
              'JacksonDatabind-71', 'Cli-23', 'Jsoup-32', 'JacksonDatabind-47', 'Cli-24', 'Gson-5', 'Jsoup-61',
              'JacksonDatabind-100', 'Closure-138', 'Jsoup-59', 'JacksonDatabind-13', 'JacksonDatabind-107',
              'JacksonDatabind-25', 'Closure-136', 'Jsoup-50', 'Jsoup-68', 'Jsoup-57', 'Cli-25', 'Jsoup-34',
              'JacksonDatabind-41', 'Closure-152', 'JacksonDatabind-79', 'Jsoup-33', 'Cli-22', 'JacksonDatabind-46',
              'Collections-25', 'Cli-14', 'JacksonDatabind-70', 'Compress-5', 'Cli-13', 'JacksonDatabind-48',
              'JacksonDatabind-83', 'Closure-164', 'JacksonDatabind-77', 'JacksonDatabind-24', 'Jsoup-51', 'Cli-40',
              'Jsoup-58', 'JacksonDatabind-12', 'Jsoup-67', 'JacksonDatabind-106', 'Jsoup-93', 'Jsoup-60',
              'JacksonDatabind-101', 'Jsoup-42', 'Jsoup-89', 'JacksonDatabind-37', 'Jsoup-45', 'JacksonCore-14',
              'JacksonCore-22', 'JacksonDatabind-39', 'JacksonDatabind-112', 'Jsoup-80', 'Jsoup-74', 'JacksonCore-25',
              'Closure-146', 'Cli-31', 'Jsoup-20', 'Jsoup-18', 'Closure-141', 'JacksonDatabind-52', 'Jsoup-27',
              'JacksonDatabind-99', 'JacksonDatabind-64', 'JacksonDatabind-90', 'JacksonDatabind-97', 'Cli-38',
              'Jsoup-29', 'JacksonDatabind-63', 'Jsoup-16', 'Jsoup-75', 'JacksonCore-24', 'Jsoup-81', 'Jsoup-86',
              'JacksonCore-23', 'Jsoup-72', 'Jsoup-44', 'JacksonCore-15', 'Jsoup-43', 'JacksonDatabind-36', 'Jsoup-88',
              'JacksonDatabind-62', 'Closure-171', 'JacksonDatabind-96', 'Cli-39', 'JacksonDatabind-91',
              'JacksonDatabind-65', 'Closure-176', 'Jsoup-10', 'Jsoup-19', 'Closure-140', 'Cli-37',
              'JacksonDatabind-98', 'Jsoup-26', 'Closure-147', 'JacksonDatabind-54', 'Cli-30', 'Compress-30',
              'Compress-37', 'Compress-39', 'Gson-17', 'JacksonDatabind-8', 'JacksonDatabind-1', 'Codec-15',
              'JacksonDatabind-6', 'Compress-38', 'Compress-36', 'Compress-31', 'JacksonDatabind-7', 'Codec-13',
              'Gson-18', 'JacksonDatabind-9', 'Gson-16', 'Compress-17', 'JxPath-14', 'Csv-3', 'Compress-28',
              'Compress-10', 'Csv-4', 'Codec-7', 'Compress-26', 'Compress-19', 'Codec-9', 'Compress-21', 'JxPath-22',
              'JxPath-6', 'JacksonCore-7', 'JxPath-1', 'Cli-9', 'JxPath-8', 'Csv-10', 'Compress-44', 'JacksonCore-9',
              'Compress-43', 'Codec-8', 'Compress-20', 'Compress-27', 'Compress-18', 'Compress-11', 'JxPath-12',
              'Csv-5', 'Codec-6', 'Compress-16', 'Codec-1', 'Csv-2', 'JxPath-15', 'Jsoup-2', 'Compress-42',
              'JacksonCore-8', 'Jsoup-5', 'Csv-11', 'Cli-1', 'JacksonXml-1', 'Compress-45', 'JacksonCore-6', 'Cli-8',
              'JacksonCore-1', 'Jsoup-91', 'JacksonDatabind-104', 'JacksonDatabind-17', 'JacksonDatabind-28',
              'Jsoup-54', 'Closure-135', 'Jsoup-53', 'JacksonDatabind-19', 'Cli-16', 'Cli-29', 'Compress-7',
              'Closure-161', 'Closure-159', 'Cli-11', 'Closure-166', 'JacksonDatabind-75', 'JacksonDatabind-88',
              'Cli-27', 'JacksonDatabind-43', 'Closure-150', 'Gson-6', 'Cli-18', 'Cli-20', 'Closure-168', 'Gson-1',
              'JacksonDatabind-44', 'JacksonDatabind-27', 'Jsoup-52', 'JacksonDatabind-16', 'Jsoup-63',
              'JacksonDatabind-102', 'JacksonDatabind-29', 'JacksonDatabind-11', 'Jsoup-64', 'Jsoup-90', 'Cli-21',
              'JacksonDatabind-45', 'Compress-8', 'Cli-26', 'Jsoup-37', 'Cli-19', 'Gson-7', 'JacksonDatabind-42',
              'Cli-10', 'Compress-1', 'JacksonDatabind-80', 'JacksonDatabind-74', 'Collections-26', 'Cli-17',
              'Closure-160', 'JacksonDatabind-73', 'Jsoup-39', 'Cli-28', 'Compress-6', 'Closure-142',
              'JacksonDatabind-51', 'Cli-35', 'Closure-145', 'JacksonDatabind-56', 'Cli-32', 'Jsoup-23',
              'JacksonDatabind-69', 'JacksonDatabind-94', 'Closure-173', 'JacksonDatabind-67', 'Closure-174',
              'JacksonDatabind-93', 'Jsoup-12', 'JacksonDatabind-58', 'Jsoup-46', 'JacksonCore-17',
              'JacksonDatabind-33', 'Jsoup-79', 'JacksonCore-10', 'Jsoup-41', 'JacksonDatabind-34', 'Jsoup-77',
              'JacksonCore-26', 'JacksonCore-19', 'Jsoup-48', 'JacksonCore-21', 'JacksonDatabind-111', 'Jsoup-70',
              'Jsoup-84', 'Jsoup-13', 'JacksonDatabind-61', 'Closure-172', 'JacksonDatabind-95', 'JacksonDatabind-57',
              'Jsoup-22', 'JacksonDatabind-68', 'Cli-33', 'Closure-143', 'Cli-34', 'Jsoup-85', 'JacksonCore-20',
              'JacksonDatabind-110', 'Jsoup-82', 'JacksonCore-18', 'Jsoup-49', 'JacksonCore-11', 'Jsoup-40',
              'JacksonDatabind-35', 'Jsoup-47', 'JacksonDatabind-32', 'Jsoup-78', 'Gson-13', 'Codec-18', 'Gson-14',
              'JacksonDatabind-5', 'JacksonDatabind-2', 'Compress-34', 'Codec-10', 'JacksonDatabind-3', 'Codec-17',
              'JacksonDatabind-4', 'Gson-15', 'Gson-12', 'Compress-32', 'Compress-35']


def run_repair_defects4j(tries, version_name, dataset, bug_id):
    utils.OUTPUT_DIR = "output" + os.sep + utils.MODEL_NAME + os.sep + version_name + os.sep + dataset
    if not os.path.exists(utils.OUTPUT_DIR):
        os.makedirs(utils.OUTPUT_DIR)
    if bug_id != "all":
        run_repair_project(tries, dataset, bug_id)
    else:
        if dataset == "defects4j":
            for bug in d4j_bus:
                if os.path.exists(os.path.join(utils.OUTPUT_DIR, bug.split("-")[0])):
                    if os.path.exists(os.path.join(utils.OUTPUT_DIR, bug.split("-")[0], f'repair_result-{utils.MAX_ITERATIONS}.csv')):
                        find = False
                        with open(os.path.join(utils.OUTPUT_DIR, bug.split("-")[0], f'repair_result-{utils.MAX_ITERATIONS}.csv')) as f:
                            for line in f:
                                if bug in line:
                                    find = True
                                    break
                        if find:
                            continue
                run_repair_project(tries, dataset, bug)
        elif dataset == "defects4jv2":
            for bug in d4jv2_bugs:
                if os.path.exists(os.path.join(utils.OUTPUT_DIR, bug.split("-")[0])):
                    if os.path.exists(os.path.join(utils.OUTPUT_DIR, bug.split("-")[0], f'repair_result-{utils.MAX_ITERATIONS}.csv')):
                        find = False
                        with open(os.path.join(utils.OUTPUT_DIR, bug.split("-")[0], f'repair_result-{utils.MAX_ITERATIONS}.csv')) as f:
                            for line in f:
                                if bug in line:
                                    find = True
                                    break
                        if find:
                            continue
                run_repair_project(tries, dataset, bug)


def run_repair_project(tries, dataset, bug_id):
    if not os.path.exists(os.path.join(utils.OUTPUT_DIR, bug_id.split("-")[0])):
        os.makedirs(os.path.join(utils.OUTPUT_DIR, bug_id.split("-")[0]))
    utils.test_cases_codes_map = utils.load_test_cases_codes_map(dataset, bug_id)
    repair_result_file = (
                utils.OUTPUT_DIR + os.sep + bug_id.split("-")[0] + os.sep + f'repair_result-{utils.MAX_ITERATIONS}.csv')
    repair_count = 0
    utils.Repair_Process_Logger = Logger(
        utils.OUTPUT_DIR + os.sep + bug_id.split("-")[0] + os.sep + f"{bug_id}-{utils.MAX_ITERATIONS}.log")
    root_dir = os.path.join(utils.TEMP_DIR, bug_id)
    if not os.path.exists(root_dir):
        prepare_project(dataset, bug_id, root_dir)
    repository_info = {}
    repository_info['compile_jar_path'], repository_info['source_dir_path'], repository_info['class_dir_path'], \
        repository_info['test_build_path'], repository_info['test_source_dir_path'] = (
        get_necessary_path(dataset, root_dir))
    _, initial_failing_tests = test_project(dataset, bug_id, root_dir, repository_info.get('test_source_dir_path'))
    fault_loc_file = fault_locate(dataset, bug_id)
    while (not utils.Repair_Result) and repair_count < tries:
        main_agent.invoke({'bug_id': bug_id, "database_name": dataset, "working_dir": root_dir,
                           'compile_jar_path': repository_info.get('compile_jar_path'),
                           'source_dir_path': repository_info.get('source_dir_path'),
                           'class_dir_path': repository_info.get('class_dir_path'),
                           'test_source_dir_path': repository_info.get('test_source_dir_path'),
                           'test_build_path': repository_info.get('test_build_path'),
                           'fault_location_file': fault_loc_file,
                           'failed_test_cases': initial_failing_tests}, {"recursion_limit": 100})
        repair_count += 1
        # time.sleep(20)
    row = [f"{bug_id}", utils.Repair_Result, repair_count, utils.Repair_Iterative_Count, utils.Prompt_Tokens,
           utils.Completion_Tokens, utils.Total_Prompt_Token, utils.Total_Completion_Token]
    with open(repair_result_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row)
    utils.remove_temp_dir(os.path.join(utils.TEMP_DIR, f"{bug_id}"))
    utils.output_test_cases_codes_map(dataset, bug_id)
