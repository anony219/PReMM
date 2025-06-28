import os.path
from basic_framework.agent_state import MAgentState, RepairStateEnum, AgentState, RepairState
from defects4j_tools.defects4j import *
from basic_framework.program_analysis import program_analysis, key_token_mining, related_analysis
from utils import get_codes_from_file, modify_files, recover_files, generate_patch_diff, generate_patch_file


def preprocessor(m_state: MAgentState):
    if m_state.get('database_name').startswith("defects4j"):
        if not os.path.exists(os.path.join(utils.ANALYSIS_DIR, m_state.get('database_name'), m_state.get('bug_id'))):
            signature_method_map, methods_tests_map, method_test_path_map = program_analysis_repository(
                m_state.get('working_dir'),
                m_state.get('source_dir_path'),
                m_state.get('class_dir_path'),
                m_state.get('test_build_path'),
                list(m_state.get('failed_test_cases').keys()),
                m_state.get('fault_location_file'))
            utils.output_prepare_info(m_state.get('database_name'), m_state.get('bug_id'),
                                      signature_method_map, methods_tests_map, method_test_path_map)
        else:
            repository_info = {}
            repository_info['compile_jar_path'], repository_info['source_dir_path'], repository_info['class_dir_path'], \
                repository_info['test_build_path'], repository_info['test_source_dir_path'] = (
                get_necessary_path(m_state.get('database_name'), m_state.get('working_dir')))
            signature_method_map, methods_tests_map, method_test_path_map = utils.load_prepare_info(
                m_state.get('database_name'), m_state.get('bug_id'))
        m_state['fault_codes_list'], m_state['fault_files'] = utils.codes_format_transform(
            list(signature_method_map.values()))
        if utils.Enable_FMC:
            faulty_methods_clustering(m_state, signature_method_map, methods_tests_map, method_test_path_map)
        else:
            init_repair_agent(m_state, signature_method_map, method_test_path_map)
    return m_state


def program_analysis_repository(root_dir, source_dir, class_dir, test_build_dir, initial_failing_tests, fault_loc_file):
    signature_method_map, methods_tests_map, method_test_path_map = program_analysis(
        root_dir,
        source_dir,
        class_dir,
        fault_loc_file,
        initial_failing_tests,
        test_build_dir)
    signature_method_map = eval(signature_method_map.strip())
    methods_tests_map = eval(methods_tests_map.strip())
    method_test_path_map = eval(method_test_path_map.strip())
    for fault_code_info in signature_method_map.values():
        fault_code_info['file_path'] = os.path.join(source_dir,
                                                    fault_code_info.get('file_path'))
        fault_code_info['fault_code'] = get_codes_from_file(
            os.path.join(root_dir, fault_code_info['file_path']),
            fault_code_info.get('line_begin'), fault_code_info.get('line_end'))
        fault_code_info['repaired_code'] = fault_code_info['fault_code']
        utils.decode_code_list(fault_code_info['similar_methods'])
        utils.decode_code_list(fault_code_info['fault_line_codes'])
    return signature_method_map, methods_tests_map, method_test_path_map


def get_fault_codes_by_key(signature_method_map, methods):
    fault_codes = {}
    if isinstance(methods, str):
        fault_codes[methods] = signature_method_map.get(methods)
    elif isinstance(methods, tuple):
        for method in methods:
            fault_codes[method] = signature_method_map.get(method)
    return fault_codes


def get_invocation_chain_paths(fault_codes, method_test_path_map):
    """
        This function retrieves and filters invocation chain paths from test methods to faulty methods.

        It ensures that:
        - Only keeps longest unique paths in each branch (removes prefix paths. e.g., 'test->a->b' instead of 'test->a').
        - All unique paths to different methods are preserved.

        Parameters:
            fault_codes (dict): A dictionary containing faulty methods as keys (method names or identifiers).
            method_test_path_map (dict): A mapping from each method to its corresponding invocation path string
                                        from a test method (e.g., 'test->a->b->method').

        Returns:
            list: A list of filtered and deduplicated invocation path strings, each representing a full chain
                  from a test method to a faulty method.
    """
    relative_suspicious_paths = []
    for method, _ in fault_codes.items():
        s_path = method_test_path_map.get(method)
        if s_path is not None:
            if len(relative_suspicious_paths) == 0:
                relative_suspicious_paths.append(s_path)
            else:
                rs_paths_len = len(relative_suspicious_paths)
                i = 0
                flag = False
                while i < rs_paths_len:
                    path = relative_suspicious_paths[i]
                    if isinstance(path, str):
                        if path.find(s_path) == -1:
                            if s_path.find(path) != -1:
                                relative_suspicious_paths[i] = s_path
                                flag = True
                                break
                        else:
                            flag = True
                            break
                    i += 1
                if not flag:
                    relative_suspicious_paths.append(s_path)
    return relative_suspicious_paths


def faulty_methods_clustering(m_state: MAgentState, signature_method_map, methods_tests_map, method_test_path_map):
    pid = 1
    m_state['agent_states'] = []
    for methods, tests in methods_tests_map.items():
        agent_state = {'bug_id': m_state.get('bug_id'), 'database_name': m_state.get('database_name'), 'pid': pid,
                       'failed_test_cases': []}
        for test in tests:
            agent_state['failed_test_cases'].append(m_state.get('failed_test_cases').get(test))
        agent_state['related_tests'] = set()
        agent_state.get('related_tests').update(tests)
        agent_state['fault_codes'] = get_fault_codes_by_key(signature_method_map, methods)
        agent_state['relative_suspicious_paths'] = get_invocation_chain_paths(agent_state.get('fault_codes'),
                                                                              method_test_path_map)
        agent_state['working_dir'] = m_state.get('working_dir')
        agent_state['compile_jar_path'] = m_state.get('compile_jar_path')
        agent_state['source_dir_path'] = m_state.get('source_dir_path')
        agent_state['class_dir_path'] = m_state.get('class_dir_path')
        agent_state['test_build_path'] = m_state.get('test_build_path')
        fault_codes, fault_files = utils.codes_format_transform(list(agent_state.get('fault_codes').values()))
        agent_state['fault_codes_list'] = fault_codes
        agent_state['fault_files'] = fault_files
        agent_state['key_tokens'] = {}
        for fault_file in fault_files:
            agent_state['key_tokens'][fault_file] = key_token_mining(agent_state.get('working_dir'), fault_file)
        agent_state['repair_state'] = RepairState(fault_analysis_result="", repair_count=0,
                                                  repair_result=RepairStateEnum.NOT_REPAIRED, repair_history="",
                                                  repair_exception="", prompt_tokens=0, completion_tokens=0)
        m_state['agent_states'].append(agent_state)
        pid += 1
    group_agents(m_state)


def init_repair_agent(m_state: MAgentState, signature_method_map, method_test_path_map):
    m_state['agent_states'] = []
    agent_state = {'bug_id': m_state.get('bug_id'), 'database_name': m_state.get('database_name'), 'pid': 1,
                   'failed_test_cases': [], 'fault_codes': signature_method_map,
                   'working_dir': m_state.get('working_dir'), 'compile_jar_path': m_state.get('compile_jar_path'),
                   'source_dir_path': m_state.get('source_dir_path'), 'class_dir_path': m_state.get('class_dir_path'),
                   'test_build_path': m_state.get('test_build_path'),
                   'fault_codes_list': m_state.get('fault_codes_list'), 'fault_files': m_state.get('fault_files'),
                   'repair_state': RepairState(fault_analysis_result="", repair_count=0,
                                               repair_result=RepairStateEnum.NOT_REPAIRED, repair_history="",
                                               repair_exception="", prompt_tokens=0, completion_tokens=0),
                   'key_tokens': {}}
    for fault_file in agent_state.get('fault_files'):
        agent_state['key_tokens'][fault_file] = key_token_mining(agent_state.get('working_dir'), fault_file)
    agent_state['relative_suspicious_paths'] = get_invocation_chain_paths(agent_state.get('fault_codes'),
                                                                          method_test_path_map)
    agent_state['failed_test_cases'] = list(m_state.get('failed_test_cases').values())
    m_state['agent_states'].append(agent_state)
    m_state['merged_agents'] = {tuple(m_state.get('failed_test_cases').keys()): [agent_state]}


def group_agents(m_state: MAgentState):
    for agent_state in m_state['agent_states']:
        agent_state['neighbor_agents'] = []
        for other_agent_state in m_state['agent_states']:
            if agent_state is not other_agent_state:
                if agent_state.get('related_tests').intersection(other_agent_state.get('related_tests')):
                    agent_state['neighbor_agents'].append(other_agent_state)
    visited = set()
    groups = []

    def dfs(node, group):
        if node.get('pid') not in visited:
            visited.add(node.get('pid'))
            group.append(node)
            for neighbor in node['neighbor_agents']:
                dfs(neighbor, group)

    for agent in m_state['agent_states']:
        if agent.get('pid') not in visited:
            current_group = []
            dfs(agent, current_group)
            groups.append(current_group)

    m_state['merged_agents'] = {}
    for agent_group in groups:
        test_set = set()
        for agent in agent_group:
            test_set |= agent.get('related_tests')
        test_tuple = tuple(sorted(test_set))
        if test_tuple not in m_state['merged_agents']:
            m_state['merged_agents'][test_tuple] = []
        m_state['merged_agents'][test_tuple].extend(agent_group)


def repairing(a_state: AgentState):
    utils.repair_agent.invoke(a_state, {"recursion_limit": 100})


def multi_repairer(m_state: MAgentState):
    for agent_state in m_state['agent_states']:
        repairing(agent_state)
    return m_state


def combine_and_test(m_state: MAgentState):
    m_state['repair_result'] = RepairStateEnum.REPAIR_TEST_SUCCESS
    for tests, agent_group in m_state['merged_agents'].items():
        file_list = compile_agent_group(m_state, agent_group)
        test_result = run_test_cases(m_state.get('database_name'), m_state.get('working_dir'),
                                     m_state.get('test_source_dir_path'), tests)
        if len(test_result) == 0:
            print("The merged agent group passed all the failed test cases!")
            utils.Repair_Process_Logger.log("The merged agent group passed all the failed test cases!")
            for agent_state in agent_group:
                agent_state['repair_state']['repair_result'] = RepairStateEnum.REPAIR_TEST_SUCCESS
        else:
            print(
                f"The merged agent group did not pass the failed test cases with the following info {str(test_result)}."
                f"Please regenerate the repaired code.")
            utils.Repair_Process_Logger.log(
                f"The merged agent group did not pass the failed test cases with the following info {str(test_result)}."
                f"Please regenerate the repaired code.")
            for agent_state in agent_group:
                agent_state['repair_state']['repair_result'] = RepairStateEnum.REPAIR_TEST_FAILED
                m_state['repair_result'] = RepairStateEnum.REPAIR_TEST_FAILED
        recover_files(m_state.get('working_dir'), file_list)
        compile_files(m_state.get('database_name'), m_state.get('working_dir'),
                      m_state.get('compile_jar_path'), file_list)
    return m_state


def compile_agent_group(m_state: MAgentState, agent_group):
    file_fault_codes_map = {}
    fault_codes = []
    for agent_state in agent_group:
        for fault_code_info in agent_state.get('fault_codes').values():
            file_path = fault_code_info.get('file_path')
            if file_fault_codes_map.get(file_path) is None:
                file_fault_codes_map[file_path] = []
            file_fault_codes_map.get(file_path).append(fault_code_info)
    for file_path, fault_code_snippets in file_fault_codes_map.items():
        fault_codes.append({"file_path": file_path, "fault_code_snippets": fault_code_snippets})
    fault_files = list(file_fault_codes_map.keys())
    modify_files(m_state.get('working_dir'), fault_codes)
    compile_files(m_state.get('database_name'), m_state.get('working_dir'),
                  m_state.get('compile_jar_path'), fault_files)
    return fault_files


def continue_to_overall_compile(m_state: MAgentState):
    # repair_success = True
    modify_files(m_state.get('working_dir'), m_state.get('fault_codes_list'))
    compile_project(m_state.get('database_name'), m_state.get('bug_id'), m_state.get('working_dir'))
    return m_state


def test_analysis(test_result, a_state: AgentState, repair_success):
    failing_test_methods = list(test_result.keys())
    related_tests = related_analysis(a_state.get('working_dir'), a_state.get('source_dir_path'),
                                     a_state.get('class_dir_path'), failing_test_methods,
                                     a_state.get('test_build_path'), list(a_state.get('fault_codes').keys()))
    if len(related_tests) == 0:
        a_state['repair_state']['repair_result'] = repair_success
        a_state['failed_test_cases'] = []
        return True
        # print(f"Repair {a_state.get('fault_files')} successfully!")
    else:
        a_state['repair_state']['repair_result'] = RepairStateEnum.REPAIR_FAILED
        a_state['failed_test_cases'] = list(test_result.values())
        return False


def test_all_cases(m_state: MAgentState):
    # Test All
    try:
        failing_test_num, test_result = test_project(m_state.get('database_name'), m_state.get('bug_id'),
                                                     m_state.get('working_dir'),
                                                     m_state.get('test_source_dir_path'))
        if len(test_result) == 0:
            m_state['repair_result'] = RepairStateEnum.REPAIR_SUCCESS
            for a_state in m_state.get('agent_states'):
                a_state['repair_state']['repair_result'] = RepairStateEnum.REPAIR_SUCCESS
                a_state['failed_test_cases'] = []
            print("The repaired codes passed all the test cases!")
            utils.Repair_Process_Logger.log("The repaired codes passed all the test cases!")
        else:
            if failing_test_num < 30:
                m_state['repair_result'] = RepairStateEnum.REPAIR_SUCCESS
                for a_state in m_state.get('agent_states'):
                    if not test_analysis(test_result, a_state, RepairStateEnum.REPAIR_SUCCESS):
                        m_state['repair_result'] = RepairStateEnum.REPAIR_FAILED
                if m_state['repair_result'] == RepairStateEnum.REPAIR_SUCCESS:
                    print(m_state.get(
                        "bug_id") + f"passed all the related test cases, but failed unrelated test cases: {str(test_result)}.")
                    utils.Repair_Process_Logger.log(m_state.get(
                        "bug_id") + f"passed all the related test cases, but failed unrelated test cases: {str(test_result)}.")
                else:
                    print(f"The repaired codes did not pass the test cases with the following info {str(test_result)}. "
                          f"Please regenerate the repaired code.")
                    utils.Repair_Process_Logger.log(
                        f"The repaired codes did not pass the test cases with the following info {str(test_result)}. "
                        f"Please regenerate the repaired code.")
            else:
                raise Exception(
                    "The repaired codes passed the failed test cases, but when testing the all project, it failed more than 30 test cases.")
    except Exception as e:
        m_state['repair_result'] = RepairStateEnum.REPAIR_EXCEPTION
        for a_state in m_state.get('agent_states'):
            a_state['repair_state']['repair_result'] = RepairStateEnum.REPAIR_EXCEPTION
            a_state['repair_state']['repair_exception'] = str(e)
        utils.Repair_Process_Logger.log(str(e))
        print(str(e))
    return m_state


def recover_codes(m_state: MAgentState):
    # recover code
    recover_files(m_state.get('working_dir'), m_state.get('fault_files'))
    compile_files(m_state.get('database_name'), m_state.get('working_dir'),
                  m_state.get('compile_jar_path'), m_state.get('fault_files'))
    return m_state


def postprocessor(m_state: MAgentState):
    if m_state.get('repair_result') == RepairStateEnum.REPAIR_SUCCESS:
        generate_patch_diff(m_state.get('bug_id'), m_state.get('working_dir'), m_state.get('fault_files'))
        generate_patch_file(m_state.get('bug_id'), m_state.get('fault_codes_list'))
        utils.Repair_Result = True
        max_iterative_count = 0
        for agent_state in m_state.get('agent_states'):
            if agent_state.get('repair_state').get('repair_count') > max_iterative_count:
                max_iterative_count = agent_state.get('repair_state').get('repair_count')
        utils.Repair_Iterative_Count = max_iterative_count

    else:
        print("Repair failed!")
        utils.Repair_Process_Logger.log("Repair failed!")
        utils.Repair_Iterative_Count = utils.MAX_ITERATIONS
    prompt_token = 0
    completion_token = 0
    for agent_state in m_state.get('agent_states'):
        prompt_token += agent_state.get('repair_state').get('prompt_tokens')
        completion_token += agent_state.get('repair_state').get('completion_tokens')
    # if completion_token > utils.Completion_Tokens:
    utils.Completion_Tokens = completion_token
    utils.Prompt_Tokens = prompt_token
    utils.Total_Prompt_Token += prompt_token
    utils.Total_Completion_Token += completion_token
    return m_state
