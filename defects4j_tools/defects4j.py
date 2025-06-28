import multiprocessing
import os
import re
import signal
import subprocess
import time
import jpype
import utils
from logger import Logger


def run_command(command, logger, cwd=None):
    start_time = time.time()
    """Run a command in the shell and print its output."""
    result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
    logger.log(result.stdout)
    if result.returncode != 0:
        logger.log(result.stderr)
        raise Exception(f"{result.stderr}")
    logger.log(f"cmd execution time: {time.time() - start_time}")


def prepare_project(database_name, bug_id, working_dir):
    # working_dir = os.path.join(utils.TEMP_DIR, bug_id)
    prepare_dataset_env_cmd = ""
    if database_name == "defects4j" or database_name == "Defects4j":
        prepare_dataset_env_cmd = utils.Defects4J_CMD
    elif database_name == "defects4jv2":
        prepare_dataset_env_cmd = utils.Defects4J_V2_CMD
    project_name = bug_id.split("-")[0]
    id = int(bug_id.split("-")[1])
    checkout_cmd = f"defects4j checkout -p {project_name} -v {id}b -w {working_dir}"
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


def get_test_code(working_dir, test_source_dir, test_name):
    if utils.test_cases_codes_map.get(test_name) is None:
        test_class = test_name.split("::")[0]
        test_method = test_name.split("::")[1]
        # test_source_dir = "test"
        test_file = os.path.join(working_dir, test_source_dir, "/".join(test_class.split(".")) + ".java")
        codes = get_method_code(test_file, test_method)
        utils.test_cases_codes_map[test_name] = codes
    return utils.test_cases_codes_map.get(test_name)


def get_method_code(file_path, method_name, including_line=-1):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        java_code = f.read()
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        data = f.readlines()
    start_line, end_line = get_method_position(java_code, method_name, including_line)
    code_snippet = ""
    for i in range(start_line - 1, end_line):
        code_snippet += data[i]
    return code_snippet


def get_method_position_working(queue, java_code, method_name, in_line):
    jvm_path = jpype.getDefaultJVMPath()
    javaparser_path = os.path.join(".", "java_lib", "context-extractor.jar")
    jpype.startJVM(jvm_path, "-ea", "-Djava.class.path=%s" % javaparser_path)
    JClass = jpype.JClass("ProgramAnalysis")
    position = JClass.getMethodPosition(java_code, method_name, in_line)
    queue.put(str(position))
    # Shut down JVM
    jpype.shutdownJVM()
    return position


def get_method_position(java_code, method_name, in_line=-1):
    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=get_method_position_working,
                                      args=(queue, java_code, method_name, in_line))
    process.start()
    process.join()
    position = queue.get()
    return int(position.split(",")[0]), int(position.split(",")[1])


def run_single_test(database_name, working_dir, test_source_dir, test_case):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4j" or database_name == "Defects4j":
        prepare_dataset_env_cmd = utils.Defects4J_CMD
    elif database_name == "defects4jv2":
        prepare_dataset_env_cmd = utils.Defects4J_V2_CMD
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
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir, failing_test.get("test_method"))
            failing_test["failing_info"] = error_string
            return {test_case:failing_test}
        elif time.time() - while_begin > 15:
            error_file.close()
            # print('time out error')
            os.killpg(os.getpgid(test_result.pid), signal.SIGTERM)
            timed_out = True
            failing_test = {"test_method": test_case}
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir, failing_test.get("test_method"))
            failing_test["failing_info"] = "Time out error"
            return {test_case:failing_test}
        else:
            time.sleep(1)
    log = Returncode
    if len(log) > 0 and log[-1].decode('utf-8') == "Failing tests: 0\n":
        return {}
    else:
        return get_test_info(database_name, working_dir, test_source_dir)


def run_test_cases(database_name, working_dir, test_source_dir, test_cases):
    # working_dir = os.path.join(utils.TEMP_DIR, bug_id)
    test_results = {}
    for test_case in test_cases:
        try:
            test_result = run_single_test(database_name, working_dir, test_source_dir, test_case)
            test_results.update(test_result)
        except Exception as e:
            test_result = {}
            failing_test = {"test_method": test_case}
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir, failing_test.get("test_method"))
            failing_test["failing_info"] = f"Exception: {e}"
            test_result[test_case] = failing_test
            test_results.update(test_result)

    return test_results


def test_project(database_name, bug_id, working_dir, test_source_dir):
    # working_dir = os.path.join(utils.TEMP_DIR, bug_id)
    prepare_dataset_env_cmd = ""
    if database_name == "defects4j" or database_name == "Defects4j":
        prepare_dataset_env_cmd = utils.Defects4J_CMD
    elif database_name == "defects4jv2":
        prepare_dataset_env_cmd = utils.Defects4J_V2_CMD
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
            return failing_tests, get_test_info(database_name, working_dir, test_source_dir, 30)
    except Exception as e:
        return 1, e


def compile_project(database_name, bug_id, working_dir):
    # working_dir = os.path.join(utils.TEMP_DIR, bug_id)
    prepare_dataset_env_cmd = ""
    if database_name == "defects4j" or database_name == "Defects4j":
        prepare_dataset_env_cmd = utils.Defects4J_CMD
    elif database_name == "defects4jv2":
        prepare_dataset_env_cmd = utils.Defects4J_V2_CMD
    cd_working_dir_cmd = f"cd {working_dir}"
    test_cmd = f"defects4j compile"
    execute_cmd = " && ".join([prepare_dataset_env_cmd, cd_working_dir_cmd, test_cmd])
    if not os.path.exists("output"):
        os.makedirs("output")
    logger = Logger(os.path.join("output", bug_id + "_result.txt"))
    run_command(execute_cmd, logger)


def get_test_info(database_name, working_dir, test_source_dir, num_tests=1):
    prepare_dataset_env_cmd = ""
    if database_name == "defects4j" or database_name == "Defects4j":
        prepare_dataset_env_cmd = utils.Defects4J_CMD
    elif database_name == "defects4jv2":
        prepare_dataset_env_cmd = utils.Defects4J_V2_CMD
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
            failing_test["test_case_code"] = get_test_code(working_dir, test_source_dir, failing_test.get("test_method"))
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
    if database_name == "defects4j" or database_name == "Defects4j":
        prepare_dataset_env_cmd = utils.Defects4J_CMD
    elif database_name == "defects4jv2":
        prepare_dataset_env_cmd = utils.Defects4J_V2_CMD
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
            test_build_dir = path
            break
    test_source_dir = os.popen(" && ".join([prepare_dataset_env_cmd, "defects4j export -p dir.src.tests -w " +
                                            working_dir])).readlines()[-1].strip()
    return compile_jar_path, source_dir, classes_build_dir, test_build_dir, test_source_dir


def javac_compile(database_name, working_dir, classes_path, target_file_path):
    compiled_result = {}
    prepare_dataset_env_cmd = ""
    if database_name == "defects4j" or database_name == "Defects4j":
        prepare_dataset_env_cmd = utils.Defects4J_CMD
    elif database_name == "defects4jv2":
        prepare_dataset_env_cmd = utils.Defects4J_V2_CMD
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

