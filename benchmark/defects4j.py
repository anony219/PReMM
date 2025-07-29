import os
import re
import shutil
import signal
import subprocess
import time
import utils
from benchmark.benchmark import Benchmark, BenchmarkRegistry
from logger import Logger


environment_config = utils.read_json("Config/defects4j_environment.json")
JAVA_7_HOME = environment_config["JAVA_7_HOME"]
JAVA_8_HOME = environment_config["JAVA_8_HOME"]
Defects4J_DIR = environment_config["Defects4J_DIR"]
Defects4J_V2_DIR = environment_config["Defects4J_V2_DIR"]
JAVA7_CMD = (" && ".join([f"export JAVA_HOME=\"{JAVA_7_HOME}\"", "export CLASS_PATH=\"$JAVA_HOME/lib\"",
                          "export PATH=.$PATH:\"$JAVA_HOME/bin\""]))
JAVA8_CMD = (" && ".join([f"export JAVA_HOME=\"{JAVA_8_HOME}\"", "export CLASS_PATH=\"$JAVA_HOME/lib\"",
                          "export PATH=.:\"$JAVA_HOME/bin\":$PATH"]))
Defects4J_CMD = (" && ".join([JAVA7_CMD, f"export PATH=.$PATH:\"{Defects4J_DIR}/framework/bin\""]))
Defects4J_V2_CMD = (" && ".join([JAVA8_CMD, f"export PATH=.$PATH:\"{Defects4J_V2_DIR}/framework/bin\""]))
TEMP_DIR = environment_config["TEMP_DIR"]


@BenchmarkRegistry.register("defects4j")
class Defects4j(Benchmark):
    def __init__(self, database_name):
        super().__init__(database_name)
        self.compile_jar_path = ""

    def checkout(self, bug_id):
        self.work_dir = os.path.join(TEMP_DIR, bug_id)
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)
        if not os.path.exists(self.work_dir):
            prepare_project(self.database_name, bug_id, self.work_dir)
        self.compile_jar_path, self.source_dir, self.build_dir, self.test_source_dir, self.test_build_dir = (
            get_necessary_path(self.database_name, self.work_dir))
        self.fault_location_file = fault_locate(self.database_name, bug_id)
        try:
            _, self.init_failing_tests = test_project(self.database_name, bug_id, self.work_dir, self.test_source_dir)
        except Exception as e:
            raise Exception("The project failed to init failing test cases (it encounters time out when testing)."
                            " Please check your project.")

    def compile_files(self, files: list):
        try:
            compile_results = compile_files(self.database_name, self.work_dir, self.compile_jar_path, files)
            result = True
            compile_error_info = ""
            if compile_results is not None:
                for compile_result in compile_results:
                    if not compile_result.get('compiled_result'):
                        result = False
                        compile_error_info += compile_result.get('compiled_info')
            return result, compile_error_info
        except Exception as e:
            print(e)
            result = False
            compile_error_info = str(e)
            return result, compile_error_info

    def compile_project(self):
        try:
            compile_project(self.database_name, self.bug_id, self.work_dir)
            return True, ""
        except Exception as e:
            return False, str(e)

    def test_failed_test_cases(self, failed_test_cases: list):
        test_result = run_test_cases(self.database_name, self.work_dir, self.test_source_dir, failed_test_cases)
        return test_result

    def test_project(self):
        failing_test_num, test_result = test_project(self.database_name, self.bug_id, self.work_dir,
                                                     self.test_source_dir)
        return failing_test_num, test_result

    def recover_files(self, file_list):
        self.compile_files(file_list)

    def get_all_bugs(self):
        d4j_bus = ['Lang-3', 'Math-37', 'Math-30', 'Lang-4', 'Math-39', 'Math-55', 'Math-52', 'Time-7', 'Math-99',
                   'Math-64',
                   'Math-90', 'Math-103', 'Math-97', 'Time-9', 'Math-63', 'Math-38', 'Lang-5', 'Math-31', 'Math-36',
                   'Lang-2',
                   'Time-8', 'Math-62', 'Math-96', 'Math-105', 'Math-91', 'Math-65', 'Math-102', 'Math-53', 'Math-98',
                   'Time-6',
                   'Math-54', 'Time-1', 'Closure-31', 'Lang-44', 'Closure-36', 'Mockito-38', 'Lang-43', 'Mockito-31',
                   'Mockito-36', 'Closure-38', 'Closure-107', 'Lang-26', 'Closure-98', 'Math-5', 'Time-10', 'Lang-19',
                   'Closure-53', 'Math-2', 'Lang-21', 'Closure-100', 'Closure-54', 'Time-17', 'Mockito-7', 'Lang-17',
                   'Closure-62', 'Time-21', 'Closure-109', 'Lang-28', 'Closure-96', 'Time-19', 'Mockito-9',
                   'Closure-131',
                   'Lang-10', 'Closure-91', 'Time-26', 'Closure-65', 'Closure-39', 'Mockito-37', 'Mockito-30',
                   'Closure-37',
                   'Lang-42', 'Closure-30', 'Lang-45', 'Mockito-8', 'Time-18', 'Lang-11', 'Closure-130', 'Closure-64',
                   'Closure-90', 'Time-27', 'Lang-16', 'Time-20', 'Closure-97', 'Lang-29', 'Closure-108', 'Closure-63',
                   'Math-3', 'Closure-101', 'Lang-20', 'Mockito-6', 'Time-16', 'Closure-55', 'Closure-99', 'Lang-27',
                   'Closure-106', 'Math-4', 'Closure-52', 'Mockito-1', 'Lang-18', 'Closure-70', 'Closure-84', 'Chart-9',
                   'Closure-3', 'Closure-124', 'Closure-83', 'Closure-77', 'Closure-123', 'Closure-48', 'Closure-4',
                   'Chart-7',
                   'Closure-41', 'Lang-34', 'Closure-115', 'Closure-46', 'Closure-79', 'Closure-112', 'Lang-33',
                   'Chart-17',
                   'Closure-12', 'Lang-58', 'Lang-60', 'Mockito-24', 'Chart-10', 'Mockito-12', 'Chart-19', 'Closure-23',
                   'Chart-26', 'Mockito-15', 'Lang-51', 'Chart-21', 'Closure-24', 'Chart-1', 'Closure-47', 'Lang-32',
                   'Closure-113', 'Closure-78', 'Closure-40', 'Chart-6', 'Closure-114', 'Lang-35', 'Closure-76',
                   'Closure-82',
                   'Closure-5', 'Closure-49', 'Closure-122', 'Closure-85', 'Closure-71', 'Closure-125', 'Closure-2',
                   'Chart-8',
                   'Mockito-14', 'Lang-50', 'Closure-25', 'Chart-20', 'Chart-18', 'Mockito-13', 'Lang-57', 'Closure-22',
                   'Lang-61', 'Mockito-25', 'Chart-11', 'Closure-14', 'Mockito-22', 'Lang-59', 'Closure-13', 'Chart-16',
                   'Math-49', 'Math-76', 'Math-82', 'Math-85', 'Math-71', 'Math-78', 'Math-47', 'Math-40', 'Math-14',
                   'Math-13',
                   'Math-25', 'Math-22', 'Math-41', 'Math-79', 'Math-46', 'Math-70', 'Math-84', 'Math-48', 'Math-83',
                   'Math-77',
                   'Math-23', 'Math-15', 'Math-51', 'Time-4', 'Math-56', 'Time-3', 'Math-69', 'Math-94', 'Math-60',
                   'Math-67',
                   'Math-93', 'Math-58', 'Math-100', 'Math-33', 'Lang-7', 'Math-34', 'Lang-9', 'Math-92', 'Math-66',
                   'Math-101',
                   'Math-59', 'Math-61', 'Math-95', 'Math-106', 'Math-57', 'Time-2', 'Math-68', 'Math-50', 'Time-5',
                   'Lang-8',
                   'Math-35', 'Lang-1', 'Lang-6', 'Math-32', 'Closure-68', 'Math-1', 'Closure-103', 'Lang-22',
                   'Closure-57',
                   'Mockito-4', 'Time-14', 'Closure-104', 'Time-13', 'Mockito-3', 'Closure-50', 'Lang-13',
                   'Closure-132',
                   'Closure-59', 'Closure-92', 'Time-25', 'Closure-66', 'Lang-14', 'Closure-61', 'Math-8', 'Time-22',
                   'Closure-95', 'Closure-35', 'Lang-40', 'Closure-32', 'Lang-47', 'Mockito-35', 'Lang-49',
                   'Mockito-32',
                   'Lang-15', 'Time-23', 'Math-9', 'Closure-94', 'Closure-60', 'Closure-58', 'Closure-133', 'Lang-12',
                   'Closure-67', 'Closure-93', 'Time-24', 'Closure-105', 'Lang-24', 'Math-7', 'Closure-51', 'Mockito-2',
                   'Time-12', 'Closure-102', 'Closure-69', 'Time-15', 'Mockito-5', 'Closure-56', 'Lang-48',
                   'Mockito-33',
                   'Mockito-34', 'Closure-33', 'Lang-46', 'Closure-34', 'Lang-41', 'Lang-63', 'Mockito-27',
                   'Closure-29',
                   'Mockito-18', 'Chart-13', 'Closure-16', 'Lang-64', 'Mockito-20', 'Closure-11', 'Chart-14',
                   'Closure-18',
                   'Mockito-16', 'Lang-52', 'Closure-27', 'Chart-22', 'Mockito-29', 'Mockito-11', 'Lang-55', 'Chart-25',
                   'Closure-20', 'Closure-80', 'Closure-74', 'Closure-120', 'Closure-7', 'Closure-73', 'Closure-118',
                   'Closure-87', 'Lang-39', 'Closure-127', 'Chart-3', 'Closure-45', 'Closure-9', 'Lang-30',
                   'Closure-129',
                   'Closure-42', 'Chart-4', 'Closure-116', 'Closure-89', 'Lang-37', 'Mockito-10', 'Lang-54',
                   'Closure-21',
                   'Chart-24', 'Mockito-17', 'Lang-53', 'Closure-19', 'Mockito-28', 'Chart-23', 'Closure-26', 'Lang-65',
                   'Mockito-21', 'Chart-15', 'Closure-10', 'Closure-28', 'Lang-62', 'Closure-17', 'Chart-12', 'Chart-5',
                   'Closure-43', 'Closure-128', 'Lang-36', 'Closure-88', 'Closure-117', 'Closure-8', 'Closure-44',
                   'Chart-2',
                   'Closure-110', 'Lang-31', 'Lang-38', 'Closure-86', 'Closure-119', 'Closure-72', 'Closure-126',
                   'Closure-1',
                   'Closure-75', 'Closure-81', 'Closure-6', 'Closure-121', 'Math-10', 'Math-17', 'Math-28', 'Math-21',
                   'Math-26', 'Math-19', 'Math-86', 'Math-72', 'Math-75', 'Math-81', 'Math-88', 'Math-43', 'Math-44',
                   'Math-27',
                   'Math-18', 'Math-20', 'Math-16', 'Math-29', 'Math-11', 'Math-45', 'Math-89', 'Math-42', 'Math-80',
                   'Math-74',
                   'Math-73', 'Math-87']
        d4jv2_bugs = ['JacksonCore-4', 'JxPath-2', 'JacksonCore-3', 'JxPath-5', 'Csv-14', 'Cli-4', 'JacksonXml-4',
                      'Compress-40', 'Cli-3', 'Compress-47', 'JacksonXml-3', 'Compress-13', 'Csv-7', 'Codec-4',
                      'JxPath-10',
                      'Compress-14', 'JxPath-17', 'Codec-3', 'Csv-9', 'JxPath-21', 'Compress-25', 'JxPath-19',
                      'Jsoup-6',
                      'Cli-2', 'Compress-46', 'Cli-5', 'Jsoup-1', 'Csv-15', 'Compress-41', 'JacksonXml-5', 'Jsoup-8',
                      'JacksonCore-5', 'JxPath-3', 'Compress-24', 'Csv-8', 'Compress-23', 'JxPath-20', 'Compress-15',
                      'Codec-2', 'Csv-1', 'JxPath-16', 'Compress-12', 'JxPath-11', 'Csv-6', 'Codec-5',
                      'JacksonDatabind-49',
                      'Cli-12', 'JacksonDatabind-76', 'JacksonDatabind-82', 'Cli-15', 'JacksonDatabind-85',
                      'Compress-4',
                      'JacksonDatabind-71', 'Cli-23', 'Jsoup-32', 'JacksonDatabind-47', 'Cli-24', 'Gson-5', 'Jsoup-61',
                      'JacksonDatabind-100', 'Closure-138', 'Jsoup-59', 'JacksonDatabind-13', 'JacksonDatabind-107',
                      'JacksonDatabind-25', 'Closure-136', 'Jsoup-50', 'Jsoup-68', 'Jsoup-57', 'Cli-25', 'Jsoup-34',
                      'JacksonDatabind-41', 'Closure-152', 'JacksonDatabind-79', 'Jsoup-33', 'Cli-22',
                      'JacksonDatabind-46',
                      'Collections-25', 'Cli-14', 'JacksonDatabind-70', 'Compress-5', 'Cli-13', 'JacksonDatabind-48',
                      'JacksonDatabind-83', 'Closure-164', 'JacksonDatabind-77', 'JacksonDatabind-24', 'Jsoup-51',
                      'Cli-40',
                      'Jsoup-58', 'JacksonDatabind-12', 'Jsoup-67', 'JacksonDatabind-106', 'Jsoup-93', 'Jsoup-60',
                      'JacksonDatabind-101', 'Jsoup-42', 'Jsoup-89', 'JacksonDatabind-37', 'Jsoup-45', 'JacksonCore-14',
                      'JacksonCore-22', 'JacksonDatabind-39', 'JacksonDatabind-112', 'Jsoup-80', 'Jsoup-74',
                      'JacksonCore-25',
                      'Closure-146', 'Cli-31', 'Jsoup-20', 'Jsoup-18', 'Closure-141', 'JacksonDatabind-52', 'Jsoup-27',
                      'JacksonDatabind-99', 'JacksonDatabind-64', 'JacksonDatabind-90', 'JacksonDatabind-97', 'Cli-38',
                      'Jsoup-29', 'JacksonDatabind-63', 'Jsoup-16', 'Jsoup-75', 'JacksonCore-24', 'Jsoup-81',
                      'Jsoup-86',
                      'JacksonCore-23', 'Jsoup-72', 'Jsoup-44', 'JacksonCore-15', 'Jsoup-43', 'JacksonDatabind-36',
                      'Jsoup-88',
                      'JacksonDatabind-62', 'Closure-171', 'JacksonDatabind-96', 'Cli-39', 'JacksonDatabind-91',
                      'JacksonDatabind-65', 'Closure-176', 'Jsoup-10', 'Jsoup-19', 'Closure-140', 'Cli-37',
                      'JacksonDatabind-98', 'Jsoup-26', 'Closure-147', 'JacksonDatabind-54', 'Cli-30', 'Compress-30',
                      'Compress-37', 'Compress-39', 'Gson-17', 'JacksonDatabind-8', 'JacksonDatabind-1', 'Codec-15',
                      'JacksonDatabind-6', 'Compress-38', 'Compress-36', 'Compress-31', 'JacksonDatabind-7', 'Codec-13',
                      'Gson-18', 'JacksonDatabind-9', 'Gson-16', 'Compress-17', 'JxPath-14', 'Csv-3', 'Compress-28',
                      'Compress-10', 'Csv-4', 'Codec-7', 'Compress-26', 'Compress-19', 'Codec-9', 'Compress-21',
                      'JxPath-22',
                      'JxPath-6', 'JacksonCore-7', 'JxPath-1', 'Cli-9', 'JxPath-8', 'Csv-10', 'Compress-44',
                      'JacksonCore-9',
                      'Compress-43', 'Codec-8', 'Compress-20', 'Compress-27', 'Compress-18', 'Compress-11', 'JxPath-12',
                      'Csv-5', 'Codec-6', 'Compress-16', 'Codec-1', 'Csv-2', 'JxPath-15', 'Jsoup-2', 'Compress-42',
                      'JacksonCore-8', 'Jsoup-5', 'Csv-11', 'Cli-1', 'JacksonXml-1', 'Compress-45', 'JacksonCore-6',
                      'Cli-8',
                      'JacksonCore-1', 'Jsoup-91', 'JacksonDatabind-104', 'JacksonDatabind-17', 'JacksonDatabind-28',
                      'Jsoup-54', 'Closure-135', 'Jsoup-53', 'JacksonDatabind-19', 'Cli-16', 'Cli-29', 'Compress-7',
                      'Closure-161', 'Closure-159', 'Cli-11', 'Closure-166', 'JacksonDatabind-75', 'JacksonDatabind-88',
                      'Cli-27', 'JacksonDatabind-43', 'Closure-150', 'Gson-6', 'Cli-18', 'Cli-20', 'Closure-168',
                      'Gson-1',
                      'JacksonDatabind-44', 'JacksonDatabind-27', 'Jsoup-52', 'JacksonDatabind-16', 'Jsoup-63',
                      'JacksonDatabind-102', 'JacksonDatabind-29', 'JacksonDatabind-11', 'Jsoup-64', 'Jsoup-90',
                      'Cli-21',
                      'JacksonDatabind-45', 'Compress-8', 'Cli-26', 'Jsoup-37', 'Cli-19', 'Gson-7',
                      'JacksonDatabind-42',
                      'Cli-10', 'Compress-1', 'JacksonDatabind-80', 'JacksonDatabind-74', 'Collections-26', 'Cli-17',
                      'Closure-160', 'JacksonDatabind-73', 'Jsoup-39', 'Cli-28', 'Compress-6', 'Closure-142',
                      'JacksonDatabind-51', 'Cli-35', 'Closure-145', 'JacksonDatabind-56', 'Cli-32', 'Jsoup-23',
                      'JacksonDatabind-69', 'JacksonDatabind-94', 'Closure-173', 'JacksonDatabind-67', 'Closure-174',
                      'JacksonDatabind-93', 'Jsoup-12', 'JacksonDatabind-58', 'Jsoup-46', 'JacksonCore-17',
                      'JacksonDatabind-33', 'Jsoup-79', 'JacksonCore-10', 'Jsoup-41', 'JacksonDatabind-34', 'Jsoup-77',
                      'JacksonCore-26', 'JacksonCore-19', 'Jsoup-48', 'JacksonCore-21', 'JacksonDatabind-111',
                      'Jsoup-70',
                      'Jsoup-84', 'Jsoup-13', 'JacksonDatabind-61', 'Closure-172', 'JacksonDatabind-95',
                      'JacksonDatabind-57',
                      'Jsoup-22', 'JacksonDatabind-68', 'Cli-33', 'Closure-143', 'Cli-34', 'Jsoup-85', 'JacksonCore-20',
                      'JacksonDatabind-110', 'Jsoup-82', 'JacksonCore-18', 'Jsoup-49', 'JacksonCore-11', 'Jsoup-40',
                      'JacksonDatabind-35', 'Jsoup-47', 'JacksonDatabind-32', 'Jsoup-78', 'Gson-13', 'Codec-18',
                      'Gson-14',
                      'JacksonDatabind-5', 'JacksonDatabind-2', 'Compress-34', 'Codec-10', 'JacksonDatabind-3',
                      'Codec-17',
                      'JacksonDatabind-4', 'Gson-15', 'Gson-12', 'Compress-32', 'Compress-35']
        if self.database_name == "defects4jv1.2":
            return d4j_bus
        elif self.database_name == "defects4jv2":
           return d4jv2_bugs
        elif self.database_name == "defects4j-trans":
            json_file = os.path.join(utils.ROOT_PATH, "datasets", "defects4j-trans", "enhanced_single_function_repair_trans_final_fl.json")
            data = utils.read_json(json_file)
            return list(data.keys())


def get_loc_file(dataset_name: str, bug_id, perfect):
    dirname = utils.ROOT_PATH
    if perfect:
        loc_file = os.path.join("datasets", dataset_name.lower(), "fault_location", "groundtruth",
                                bug_id.split("-")[0].lower(),
                                bug_id.split("-")[1])
    else:
        loc_file = os.path.join("datasets", dataset_name.lower(), "fault_location", "ochiai",
                                bug_id.split("-")[0].lower(),
                                bug_id.split("-")[1])
    loc_file = os.path.join(dirname, loc_file)
    if os.path.isfile(loc_file):
        return os.path.abspath(loc_file)
    else:
        # print(loc_file)
        return ""


def fault_locate(dataset_name, bug_id, perfect=True):
    loc_file = get_loc_file(dataset_name, bug_id, perfect)
    return loc_file


def run_command(command, logger, cwd=None):
    try:
        start_time = time.time()
        """Run a command in the shell and print its output."""
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=30)
        logger.log(result.stdout)
        if result.returncode != 0:
            logger.log(result.stderr)
            raise Exception(f"{result.stderr}")
        logger.log(f"cmd execution time: {time.time() - start_time}")
    except subprocess.TimeoutExpired as e:
        logger.log(f"Time out: {str(e)}")
        raise Exception(f"Time out: {str(e)}")


def prepare_project(database_name, bug_id, working_dir):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4jv1.2" or database_name == "Defects4jv1.2":
        prepare_dataset_env_cmd = Defects4J_CMD
    elif database_name == "defects4jv2" or database_name == "defects4j-trans":
        prepare_dataset_env_cmd = Defects4J_V2_CMD
    project_name = bug_id.split("-")[0]
    idd = int(bug_id.split("-")[1])
    checkout_cmd = f"defects4j checkout -p {project_name} -v {idd}b -w {working_dir}"
    cd_working_dir_cmd = f"cd {working_dir}"
    compile_cmd = "defects4j compile"
    # test_cmd = "defects4j test"
    # test_methods = f"defects4j export -w {working_dir} -p tests.trigger"
    execute_cmd = " && ".join([prepare_dataset_env_cmd, checkout_cmd, cd_working_dir_cmd, compile_cmd])
    # execute_cmd = " && ".join([prepare_dataset_env_cmd, test_methods])
    if not os.path.exists("output"):
        os.makedirs("output")
    logger = Logger(os.path.join("output", bug_id + "_result.txt"))

    run_command(execute_cmd, logger)
    if database_name == "defects4j-trans":
        init_defects4j_trans_env(bug_id, working_dir)
        compile_project(database_name, bug_id, working_dir)


def init_defects4j_trans_env(bug_id, working_dir):
    json_file = f"datasets/defects4j-trans/enhanced_single_function_repair_trans_final_fl.json"
    single_function_bugs = utils.read_json(json_file)
    code_info = single_function_bugs.get(bug_id)
    print(f"Initializing defects4j-trans ({bug_id}):\n1. Replace the original code with transform code.\n2. Compile Project.")
    utils.modify_file_pre(working_dir, code_info)


def get_test_code(working_dir, test_source_dir, test_name):
    test_class = test_name.split("::")[0]
    test_method = test_name.split("::")[1]
    return utils.get_test_code(working_dir, test_source_dir, test_class, test_method)


def run_single_test(database_name, working_dir, test_source_dir, test_case):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4jv1.2" or database_name == "Defects4jv1.2":
        prepare_dataset_env_cmd = Defects4J_CMD
    elif database_name == "defects4jv2" or database_name == "defects4j-trans":
        prepare_dataset_env_cmd = Defects4J_V2_CMD
    test_cmd = f"defects4j test -w {working_dir} -t {test_case}"
    execute_cmd = " && ".join([prepare_dataset_env_cmd, test_cmd])
    error_file = open("stderr.txt", "wb")
    test_result = subprocess.Popen(execute_cmd, shell=True, stdout=subprocess.PIPE, stderr=error_file, bufsize=-1,
                                   start_new_session=True)
    while_begin = time.time()
    error_string = ""
    Returncode = ""
    timed_out = False
    failing_tests = []
    while True:
        Flag = test_result.poll()
        if Flag == 0:
            Returncode = test_result.stdout.readlines()  # child.stdout.read()
            # print(b"".join(Returncode).decode('utf-8'))
            # error_file.close()
            break
        elif Flag != 0 and Flag is not None:
            compile_fail = True
            error_file.close()
            with open("stderr.txt", "rb") as f:
                r = f.readlines()
            for line in r:
                if re.search(':\serror:\s', line.decode('utf-8')):
                    error_string = line.decode('utf-8')
                    break
            failing_test = {"test_method": test_case}
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir,
                                                           failing_test.get("test_method"))
            failing_test["failing_info"] = error_string
            return {test_case: failing_test}
        elif time.time() - while_begin > 15:
            error_file.close()
            # print('time out error')
            os.killpg(os.getpgid(test_result.pid), signal.SIGTERM)
            timed_out = True
            failing_test = {"test_method": test_case}
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir,
                                                           failing_test.get("test_method"))
            failing_test["failing_info"] = "Time out error"
            return {test_case: failing_test}
        else:
            time.sleep(1)
    log = Returncode
    if len(log) > 0 and log[-1].decode('utf-8') == "Failing tests: 0\n":
        return {}
    else:
        return get_test_info(database_name, working_dir, test_source_dir)


def run_test_cases(database_name, working_dir, test_source_dir, test_cases):
    test_results = {}
    for test_case in test_cases:
        try:
            test_result = run_single_test(database_name, working_dir, test_source_dir, test_case)
            test_results.update(test_result)
        except Exception as e:
            test_result = {}
            failing_test = {"test_method": test_case}
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir,
                                                           failing_test.get("test_method"))
            failing_test["failing_info"] = f"Exception: {e}"
            test_result[test_case] = failing_test
            test_results.update(test_result)

    return test_results


def test_project(database_name, bug_id, working_dir, test_source_dir):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4jv1.2" or database_name == "Defects4jv1.2":
        prepare_dataset_env_cmd = Defects4J_CMD
    elif database_name == "defects4jv2" or database_name == "defects4j-trans":
        prepare_dataset_env_cmd = Defects4J_V2_CMD
    cd_working_dir_cmd = f"cd {working_dir}"
    test_cmd = f"defects4j test"
    execute_cmd = " && ".join([prepare_dataset_env_cmd, cd_working_dir_cmd, test_cmd])
    if not os.path.exists("output"):
        os.makedirs("output")
    logger = Logger(os.path.join("output", bug_id + "_result.txt"))
    try:
        run_command(execute_cmd, logger)
        with open(os.path.join("output", bug_id + "_result.txt"), 'r', encoding='utf-8') as file:
            first_line = file.readline().strip()
            failing_tests = int(first_line.split(": ")[1])
        if failing_tests < 30:
            return failing_tests, get_test_info(database_name, working_dir, test_source_dir, failing_tests)
        else:
            # return failing_tests, get_test_info(database_name, working_dir, test_source_dir, 30)
            return failing_tests, {}
    except Exception as e:
        raise Exception(e)
    # return 1, e


def compile_project(database_name, bug_id, working_dir):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4jv1.2" or database_name == "Defects4jv1.2":
        prepare_dataset_env_cmd = Defects4J_CMD
    elif database_name == "defects4jv2" or database_name == "defects4j-trans":
        prepare_dataset_env_cmd = Defects4J_V2_CMD
    cd_working_dir_cmd = f"cd {working_dir}"
    test_cmd = f"defects4j compile"
    execute_cmd = " && ".join([prepare_dataset_env_cmd, cd_working_dir_cmd, test_cmd])
    if not os.path.exists("output"):
        os.makedirs("output")
    logger = Logger(os.path.join("output", bug_id + "_result.txt"))
    run_command(execute_cmd, logger)


def get_test_info(database_name, working_dir, test_source_dir, num_tests=1):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4jv1.2" or database_name == "Defects4jv1.2":
        prepare_dataset_env_cmd = Defects4J_CMD
    elif database_name == "defects4jv2" or database_name == "defects4j-trans":
        prepare_dataset_env_cmd = Defects4J_V2_CMD
    cd_working_dir_cmd = f"cd {working_dir}"
    cat_test_info = "cat failing_tests"
    execute_cmd = " && ".join([prepare_dataset_env_cmd, cd_working_dir_cmd, cat_test_info])
    test_result = subprocess.Popen(execute_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=-1,
                                   start_new_session=True)
    failing_tests = {}
    test_info = test_result.stdout.read().decode("utf-8")
    flag = False
    failing_test = {}
    i = 0
    for line in test_info.split("\n"):
        if line.startswith("---"):
            flag = True
            failing_test["test_method"] = line.split(" ")[1]
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir,
                                                           failing_test.get("test_method"))
        elif flag:
            flag = False
            failing_test["failing_info"] = line
            failing_tests[failing_test.get("test_method")] = failing_test
            failing_test = {}
            i += 1
            if i >= num_tests:
                break
    return failing_tests


def get_necessary_path(database_name, working_dir):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4jv1.2" or database_name == "Defects4jv1.2":
        prepare_dataset_env_cmd = Defects4J_CMD
    elif database_name == "defects4jv2" or database_name == "defects4j-trans":
        prepare_dataset_env_cmd = Defects4J_V2_CMD
    source_dir = os.popen(
        " && ".join([prepare_dataset_env_cmd, "defects4j export -p dir.src.classes -w " + working_dir])).readlines()[
        -1].strip()
    class_path_cmd = " && ".join([prepare_dataset_env_cmd, "defects4j export -p cp.compile -w " +
                                  working_dir])
    compile_jar_path = os.popen(class_path_cmd).readlines()[-1].strip()
    classes_build_dir = \
        os.popen(
            prepare_dataset_env_cmd + " && " + "defects4j export -p dir.bin.classes -w " + working_dir).readlines()[
            -1].strip()
    test_build_dir = os.popen(
        prepare_dataset_env_cmd + " && " + "defects4j export -p cp.test -w " + working_dir).readlines()[
        -1].strip()
    for path in test_build_dir.split(os.pathsep):
        if path.endswith("test") or path.endswith("tests") or path.endswith("test-classes"):
            if path.find("src") != -1:
                continue
            if path.find(working_dir) != -1:
                test_build_dir = path[path.find(working_dir) + len(working_dir) + 1:]
            else:
                test_build_dir = path
            break
    test_source_dir = os.popen(" && ".join([prepare_dataset_env_cmd, "defects4j export -p dir.src.tests -w " +
                                            working_dir])).readlines()[-1].strip()
    return compile_jar_path, source_dir, classes_build_dir, test_source_dir, test_build_dir


def javac_compile(database_name, working_dir, classes_path, target_file_path):
    compiled_result = {}
    prepare_dataset_env_cmd = ""
    if database_name == "defects4jv1.2" or database_name == "Defects4jv1.2":
        prepare_dataset_env_cmd = Defects4J_CMD
    elif database_name == "defects4jv2" or database_name == "defects4j-trans":
        prepare_dataset_env_cmd = Defects4J_V2_CMD
    cd_working_dir_cmd = f"cd {working_dir}"
    javac_compile_cmd = f"javac -cp {classes_path} {os.path.join(working_dir, target_file_path)}"
    exec_cmd = " && ".join([prepare_dataset_env_cmd, cd_working_dir_cmd, javac_compile_cmd])
    result = subprocess.run(exec_cmd, shell=True, capture_output=True, text=True)
    compiled_info = result.stdout
    if result.returncode != 0:
        compiled_result["compiled_file"] = target_file_path
        compiled_result["compiled_result"] = False
        compiled_result["compiled_info"] = result.stderr
    else:
        compiled_result["compiled_file"] = target_file_path
        compiled_result["compiled_result"] = True
        compiled_result["compiled_info"] = compiled_info
    return compiled_result


def compile_files(database_name, working_dir, class_path, file_list: list):
    compile_results = []
    for file_path in file_list:
        compile_result = javac_compile(database_name, working_dir, class_path, file_path)
        compile_results.append(compile_result)
    return compile_results
