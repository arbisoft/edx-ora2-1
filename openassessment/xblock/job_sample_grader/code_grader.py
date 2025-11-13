import glob
import logging
import os
import json
import requests
import hashlib
import time
from datetime import datetime, timedelta

from uuid import uuid4

from tempfile import NamedTemporaryFile, TemporaryFile

from collections import OrderedDict
from openassessment.xblock.code_executor.exceptions import CodeCompilationError
from openassessment.xblock.code_executor.factory import (
    CODE_EXECUTOR_CONFIGS,
    CodeExecutorFactory,
)
from openassessment.xblock.code_executor.constants import DEFAULT_LIMITS
from openassessment.xblock.enums import CodeExecutorOption
from openassessment.xblock.job_sample_grader.utils import (
    is_design_problem,
    get_error_response,
    truncate_error_output,
)

from litmustest_djangoapps.core.models import AssessmentQuestionXblockMapping

logger = logging.getLogger(__name__)
SUBMISSION_MAX_SIZE = 1024 * 1024  # 1 MB

ALL_CODE_EXECUTORS = sorted(
    [
        {
            'name': config.get('display_name', config['id']),
            'value': config['id'],
            'language': config.get('language', config['id'].split(':')[0]),
        }
        for config in CODE_EXECUTOR_CONFIGS
    ],
    key=lambda x: x['name'],
)


class CodeGraderMixin(object):

    # Cache configuration
    CACHE_DIR = '/tmp/question_attachments_cache'
    CACHE_EXPIRY_DAYS = 1  # Cache files for 1 day
    MAX_CACHE_SIZE_MB = 500  # Maximum cache size in MB
    SERVER_SHELL_EXECUTORS = list(
        filter(
            lambda executor: executor['value'].startswith(
                CodeExecutorOption.ServerShell.value
            ),
            ALL_CODE_EXECUTORS,
        )
    )

    EPICBOX_EXECUTORS = list(
        filter(
            lambda executor: (
                not executor['value'].startswith(CodeExecutorOption.ServerShell.value)
            ),
            ALL_CODE_EXECUTORS,
        )
    )

    __SECRET_DATA_DIR__ = '/grader_data/'
    __TMP_DATA_DIR__ = '/tmp/'

    def get_code_grader_context(self):
        available_executors = []
        if self.executor == CodeExecutorOption.ServerShell.value:
            available_executors = self.SERVER_SHELL_EXECUTORS
        else:
            available_executors = self.EPICBOX_EXECUTORS

        return {
            'available_code_executors': available_executors,
        }

    def grade(self, response, add_staff_cases=False):
        """
        Set prerequisites and execute code.
            * Submission code is added in directory
            * File name is auto generated unique string
            * For designed problem simply code executes but for other problems code executed with
                test cases.
        Args:
            response (dict):
                problem_name(str)
                submission(str): code submitted by user
                executor_id(str): executor_id of the code executor to use
                add_staff_cases (bool, optional): Defaults to False.
        """
        problem_name = response['problem_name']
        source_code = response['submission']
        executor_id = response.get('executor_id')

        if executor_id is None or executor_id not in [
            e['value'] for e in self.get_code_grader_context()['available_code_executors']
        ]:
            return self.response_with_error_v2('No such language available.')

        output = []
        usage_key = self.get_xblock_id()
        if is_design_problem(usage_key, problem_name):
            try:
                details = self.run_design_code(executor_id, source_code=source_code)
                if len(json.dumps(details)) > SUBMISSION_MAX_SIZE:
                    error = 'Output size exceeded. Maximum allowed size is 1 MB.'
                    output.extend(self.response_with_error_v2(error, is_design_problem(usage_key, problem_name)))
                else:
                    output.append(details)
            except CodeCompilationError as ex:
                output.extend(self.response_with_error_v2(ex.message, is_design_problem(usage_key, problem_name)))
        else:
            try:
                details = self.run_code('sample', executor_id, source_code, problem_name)
                if len(json.dumps(details)) > SUBMISSION_MAX_SIZE:
                    output.extend(self.response_with_error_v2('Output size exceeded. Maximum allowed size is 1 MB.'))
                else:
                    output.append(details)
            except CodeCompilationError as ex:
                output.extend(self.response_with_error_v2(ex.message))
            if add_staff_cases:
                try:
                    details = self.run_code('staff', executor_id, source_code, problem_name)
                    if len(json.dumps(details)) > SUBMISSION_MAX_SIZE:
                        output.extend(self.response_with_error_v2('Output size exceeded. Maximum allowed size is 1 MB.'))
                    else:
                        output.append(details)
                except CodeCompilationError as ex:
                    output.extend(self.response_with_error_v2(ex.message))

        return output

    def response_with_error_v2(self, error, is_design_problem=False):
        """
        To make the incorrect language error compatible with per file test
        case run output.
        """
        return [get_error_response('sample', error, is_design_problem)]

    def _executor_output_to_response_format(self, executor_output):
        response = {'output': '', 'error': '', 'exit_code': executor_output['exit_code']}

        if executor_output['timeout']:
            response['output'] = 'Time limit exceeded.'
        elif executor_output['oom_killed']:
            response['output'] = 'Memory limit exceeded.'
        elif executor_output['stderr']:
            try:
                response['output'] = truncate_error_output(
                    executor_output['stderr'].decode('utf-8')
                )
            except UnicodeError:
                response['output'] = truncate_error_output(
                    'There was an error decoding the error message. '
                    'Please ensure that your stderr logs are utf-8 encodable.'
                )
        elif executor_output['stdout'] is not None:
            try:
                response['output'] = executor_output['stdout'].decode('utf-8')
            except UnicodeError:
                response['output'] = truncate_error_output(
                    'There was an error decoding the output. '
                    'Please ensure that your output is utf-8 encodable.'
                )

        return response

    def read_test_cases_from_db(self, question, run_type):
        """
        Reads test cases from question model's metadata field
        """
        try:
            test_cases = json.loads(question.metadata).get(run_type, {})
        except:
            test_cases = question.metadata.get(run_type, {})

        test_case_files = []

        temporary_directory = os.path.join(self.__TMP_DATA_DIR__, self.__SECRET_DATA_DIR__.lstrip(os.sep))
        os.makedirs(temporary_directory, exist_ok=True)

        for case_number in sorted(test_cases.keys()):
            case = test_cases[case_number]
            test_case_tmp_file_name_prefix = str(uuid4())
            try:
                input_file = NamedTemporaryFile(
                    mode='w+',
                    prefix=test_case_tmp_file_name_prefix,
                    suffix='.in',
                    dir=temporary_directory,
                    delete=False
                )
                input_file.write(case['input'])
                input_file.close()

                expected_output_file = NamedTemporaryFile(
                    mode='w+',
                    prefix=test_case_tmp_file_name_prefix,
                    suffix='.out',
                    dir=temporary_directory,
                    delete=False
                )
                expected_output_file.write(case['output'])
                expected_output_file.close()
            except PermissionError as error:
                logger.error(
                    'The OS user "{}" does not have the permission to create temporary file under "{}". Error: {}'
                    .format(
                        os.getlogin(),
                        temporary_directory,
                        error
                    )
                )
                raise error

            test_case_files.append(
                {
                    'case_number': case_number,
                    'input_file': {
                        'name': input_file.name,
                        'content': bytes(case['input'], 'utf-8'),
                    },
                    'expected_output_file': {'name': expected_output_file.name},
                    'points': case.get('points', 1),
                }
            )

        return test_case_files

    def read_test_cases_from_file(self, problem_name, run_type):
        """
        Reads test cases from grader_data file
        """
        test_case_paths = glob.glob(
            '{}{}/{}/*'.format(self.__SECRET_DATA_DIR__, problem_name, run_type)
        )

        # Sort the test cases based on the test number
        if test_case_paths:
            test_case_paths = sorted(
                test_case_paths, key=lambda test_case: int(test_case.split('/')[-1])
            )

        test_case_files = []

        for case in test_case_paths:
            case_number = int(case.split('/')[-1])
            input_file = '{}/input.in'.format(case)
            expected_output_file = '{}/output.out'.format(case)

            with open(input_file, 'rb') as file:
                input_content = file.read()

            test_case_files.append(
                {
                    'case_number': case_number,
                    'input_file': {
                        # Keeping the file names the same as host.
                        # This will allow us to use the same names
                        # for epicbox and server_shell.
                        'name': input_file,
                        'content': input_content,
                    },
                    'expected_output_file': {'name': expected_output_file},
                    # points not supported for test cases from file
                    'points': 1,
                }
            )

        return test_case_files

    def _get_cache_key(self, file_key):
        """Generate a unique cache key for a file key."""
        return hashlib.md5(file_key.encode('utf-8')).hexdigest()

    def _get_cache_file_path(self, cache_key, filename):
        """Get the full path for a cached file."""
        # Sanitize filename to avoid filesystem issues
        safe_filename = "".join(c for c in filename if c.isalnum() or c in ('.', '-', '_')).rstrip('.')
        return os.path.join(self.CACHE_DIR, "{}_{}".format(cache_key, safe_filename))

    def _is_cache_valid(self, cache_file_path):
        """Check if a cached file is still valid (not expired)."""
        if not os.path.exists(cache_file_path):
            return False

        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file_path))
        return file_age < timedelta(days=self.CACHE_EXPIRY_DAYS)

    def _cleanup_expired_cache(self):
        """Remove expired cache files."""
        try:
            if not os.path.exists(self.CACHE_DIR):
                return

            current_time = datetime.now()
            total_size = 0

            for filename in os.listdir(self.CACHE_DIR):
                file_path = os.path.join(self.CACHE_DIR, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_age > timedelta(days=self.CACHE_EXPIRY_DAYS):
                        os.remove(file_path)
                        logger.info("Removed expired cache file: {}".format(filename))
                    else:
                        total_size += os.path.getsize(file_path)

            # Clean up if cache is too large
            if total_size > self.MAX_CACHE_SIZE_MB * 1024 * 1024:
                self._cleanup_oldest_files(int(total_size * 0.7))  # Keep 70% of max size

        except Exception as e:
            logger.warning("Error during cache cleanup: {}".format(str(e)))

    def _cleanup_oldest_files(self, target_size):
        """Remove oldest files to reach target cache size."""
        try:
            files = []
            for filename in os.listdir(self.CACHE_DIR):
                file_path = os.path.join(self.CACHE_DIR, filename)
                if os.path.isfile(file_path):
                    files.append({
                        'path': file_path,
                        'size': os.path.getsize(file_path),
                        'mtime': os.path.getmtime(file_path)
                    })

            # Sort by modification time (oldest first)
            files.sort(key=lambda x: x['mtime'])

            current_size = 0
            for file_info in files:
                if current_size >= target_size:
                    break
                os.remove(file_info['path'])
                current_size += file_info['size']
                logger.info("Removed old cache file: {}".format(os.path.basename(file_info['path'])))

        except Exception as e:
            logger.warning("Error during old file cleanup: {}".format(str(e)))

    def _copy_cached_file(self, cache_path, target_path):
        """Copy a cached file to the target directory."""
        try:
            import shutil
            shutil.copy2(cache_path, target_path)
            return True
        except Exception as e:
            logger.error("Failed to copy cached file: {}".format(str(e)))
            return False

    def download_question_attachments(self, question, target_directory):
        """Download question attachments with caching support.

        Args:
            question: Question model instance
            target_directory: Directory to copy attachment files to

        Returns:
            list: List of file dictionaries with name and content
        """
        attachment_files = []

        if not question:
            return attachment_files

        # Get attachments from question metadata
        metadata = question.get_parsed_metadata() or {}
        attachments = metadata.get('attachments', [])

        # Create cache directory if it doesn't exist
        if not os.path.exists(self.CACHE_DIR):
            os.makedirs(self.CACHE_DIR)

        for attachment in attachments:
            try:
                file_key = attachment.get('key')
                filename = attachment.get('filename')

                if not file_key or not filename:
                    logger.warning("Missing file_key or filename for attachment: {}".format(attachment))
                    continue

                cache_key = self._get_cache_key(file_key)
                cache_file_path = self._get_cache_file_path(cache_key, filename)
                target_file_path = os.path.join(target_directory, filename)

                # Check if we have a valid cached copy
                if self._is_cache_valid(cache_file_path):
                    logger.info("Using cached copy for: {}".format(filename))
                    try:
                        # Ensure directory exists and is writable
                        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                        if self._copy_cached_file(cache_file_path, target_file_path):
                            attachment_files.append({
                                'name': target_file_path,
                                'filename': filename,
                                'content': open(cache_file_path, 'rb').read(),  # Read from cache
                            })
                            continue
                        else:
                            logger.warning("Failed to copy cached file, downloading fresh")
                    except (OSError, IOError) as e:
                        logger.error("Cannot write to {}: {}. Using fallback directory.".format(target_file_path, str(e)))
                        # Fallback to /tmp if target directory is not writable
                        fallback_dir = '/tmp'
                        fallback_path = os.path.join(fallback_dir, filename)
                        if self._copy_cached_file(cache_file_path, fallback_path):
                            target_file_path = fallback_path
                            attachment_files.append({
                                'name': target_file_path,
                                'filename': filename,
                                'content': open(cache_file_path, 'rb').read(),
                            })
                            logger.info("Using fallback path: {}".format(fallback_path))
                            continue
                        else:
                            logger.warning("Failed to copy cached file even to fallback, downloading fresh")

                # Download fresh copy
                logger.info("Downloading fresh copy for: {}".format(filename))

                # Import fileupload API to generate fresh download URLs
                try:
                    from openassessment.fileupload.backends import get_backend
                    from django.conf import settings
                    fileupload_api = get_backend()

                    # Temporarily override prefix to prevent double prefixing
                    original_prefix = getattr(settings, 'FILE_UPLOAD_STORAGE_PREFIX', 'question_attachments')
                    settings.FILE_UPLOAD_STORAGE_PREFIX = ''

                    download_url = fileupload_api.get_download_url(file_key)

                    if not download_url:
                        logger.warning("Could not generate download URL for file: {}".format(file_key))
                        continue

                    response = requests.get(download_url, timeout=10)
                    response.raise_for_status()

                    # Save to cache
                    with open(cache_file_path, 'wb') as cache_file:
                        cache_file.write(response.content)

                    # Copy to target directory with error handling
                    try:
                        # Ensure directory exists and is writable
                        os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                        with open(target_file_path, 'wb') as target_file:
                            target_file.write(response.content)
                    except (OSError, IOError) as e:
                        logger.error("Cannot write to {}: {}. Using fallback directory.".format(target_file_path, str(e)))
                        # Fallback to /tmp if target directory is not writable
                        fallback_dir = '/tmp'
                        fallback_path = os.path.join(fallback_dir, filename)
                        with open(fallback_path, 'wb') as target_file:
                            target_file.write(response.content)
                        target_file_path = fallback_path
                        logger.info("Using fallback path: {}".format(fallback_path))

                    attachment_files.append({
                        'name': target_file_path,
                        'filename': filename,
                        'content': response.content,
                    })

                    logger.info("Downloaded and cached question attachment: {} -> {}".format(filename, cache_file_path))

                except ImportError:
                    logger.warning("File upload system not available for downloading attachments")
                    continue
                except Exception as e:
                    logger.error("Failed to download attachment {}: {}".format(attachment.get('filename', 'unknown'), str(e)))
                    continue
                finally:
                    # Restore original prefix
                    settings.FILE_UPLOAD_STORAGE_PREFIX = original_prefix

            except Exception as e:
                logger.error("Failed to process attachment {}: {}".format(attachment.get('filename', 'unknown'), str(e)))
                continue

        return attachment_files

    def run_code(self, run_type, executor_id, source_code, problem_name):
        """Run code for all test cases.

        Args:
            run_type (str): sample or staff
            executor_id (str): Code executor id
            source_code (str): Source code
            problem_name (str): ORA problem display name

        Returns:
            dict: output object with format like follows:
                {
                    'run_type': 'sample',
                    'total_tests': 0,
                    'correct': 0,
                    'incorrect': 0,
                    'output': OrderedDict(),
                    'error': None,
                }
        """
        usage_key = self.get_xblock_id()

        test_case_files = []
        question_mapping = AssessmentQuestionXblockMapping.objects.filter(usage_key=usage_key).first()

        if question_mapping:
            question = question_mapping.question
            test_case_files = self.read_test_cases_from_db(question, run_type)

            # Download question attachments
            # Use the same directory as test case files to ensure we have write permissions
            temp_dir = os.path.dirname(test_case_files[0]['input_file']['name']) if test_case_files else '/tmp'
            logger.info("Downloading question attachments to temp directory: {}".format(temp_dir))
            logger.info("Question ID: {}, Question UUID: {}".format(question.id, question.question_uuid))

            # Check metadata for attachments
            metadata = question.get_parsed_metadata() or {}
            attachments = metadata.get('attachments', [])
            logger.info("Found {} attachments in question metadata".format(len(attachments)))

            question_attachments = self.download_question_attachments(question, temp_dir)
            logger.info("Successfully downloaded {} attachment files".format(len(question_attachments)))
        else:
            test_case_files = self.read_test_cases_from_file(problem_name, run_type)

        # Combine test case files and question attachments
        all_files = [files['input_file'] for files in test_case_files] + question_attachments

        logger.info("Total files being passed to CodeExecutor: {}".format(len(all_files)))
        for i, file_dict in enumerate(all_files):
            logger.info("File {}: {} (size: {} bytes)".format(i, file_dict.get('name', 'unknown'), len(file_dict.get('content', b''))))

        code_executor = CodeExecutorFactory.get_code_executor(
            executor_id,
            source_code=source_code,
            files=all_files,
        )
        output = {
            'run_type': run_type,
            'total_tests': len(test_case_files),
            'correct': 0,
            'incorrect': 0,
            'output': OrderedDict(),
            'error': None,
            'scored_points': 0,
            'total_points': 0,
        }
        # for server_shell paths start with / e.g. "/grader_data/..."
        # for epicbox paths are relative to home e.g. "grader_data/..."
        get_file_path = (
            lambda path: path.lstrip(os.sep)
            if self.executor == CodeExecutorOption.Epicbox.value
            else path
        )
        with code_executor:
            for case_file in test_case_files:
                if self.is_code_input_from_file:
                    execution_results = code_executor.run_input_from_file(
                        get_file_path(case_file['input_file']['name']),
                    )
                else:
                    execution_results = code_executor.run_input(
                        input=case_file['input_file']['content'].decode('utf-8'),
                    )

                formatted_results = self._executor_output_to_response_format(execution_results)
                run_output = self.compare_outputs(
                    formatted_results['output'],
                    case_file['expected_output_file']['name'],
                    usage_key=usage_key
                )

                if run_output['correct']:
                    output['correct'] += 1
                    output['scored_points'] += case_file.get('points', 1)
                else:
                    output['incorrect'] += 1

                output['total_points'] += case_file.get('points', 1)

                expected_output = run_output['tests'][0][1]
                actual_output = run_output['tests'][0][2]
                test_input = case_file['input_file']['content'].decode('utf-8')
                case_number = case_file['case_number']
                output['output'][case_number] = {
                    'test_input': test_input,
                    'actual_output': actual_output,
                    'expected_output': expected_output,
                    'correct': run_output['correct'],
                    'points': case_file.get('points', 1)
                }

                input_file_name = case_file['input_file']['name']
                output_file_name = case_file['expected_output_file']['name']

                if question_mapping and os.path.isfile(input_file_name):
                    os.remove(input_file_name)
                if question_mapping and os.path.isfile(output_file_name):
                    os.remove(output_file_name)

        return output

    def run_design_code(self, executor_id, source_code):
        output = {
            'is_design_problem': True,
            'run_type': 'sample',
            'output': None,
            'error': None,
        }

        # Get question attachments for design problems
        usage_key = self.get_xblock_id()
        question_attachments = []

        question_mapping = AssessmentQuestionXblockMapping.objects.filter(usage_key=usage_key).first()
        if question_mapping:
            question = question_mapping.question
            question_attachments = self.download_question_attachments(question, '/tmp')  # Use /tmp for design problems

        # Prepare files for execution
        input_file_name = 'input.txt'
        files = [{'name': input_file_name, 'content': b''}] + question_attachments

        code_executor = CodeExecutorFactory.get_code_executor(
            executor_id, source_code, files=files
        )

        if self.is_code_input_from_file and self.executor == CodeExecutorOption.ServerShell.value:
            input_file = TemporaryFile('r')
            input_file_name = input_file.name

        with code_executor:
            if self.is_code_input_from_file:
                execution_results = code_executor.run_input_from_file(input_file_name)
            else:
                execution_results = code_executor.run_input('')

            response = self._executor_output_to_response_format(execution_results)
            output = {
                **output,
                **response,
            }

        if self.is_code_input_from_file and self.executor == CodeExecutorOption.ServerShell.value:
            input_file.close()

        return output

    def run_quality_check_code(self, code, input):
        output = {
            'output': None,
            'error': None,
        }
        executor = list(
            filter(
                lambda _executor: _executor['language'] == 'python',
                self.EPICBOX_EXECUTORS,
            )
        )[0]
        executor_id = executor['value']
        updated_limits = dict(DEFAULT_LIMITS)
        updated_limits['cputime'] = 120
        updated_limits['realtime'] = 130
        code_executor = CodeExecutorFactory.get_code_executor(
            executor_id, source_code=code, files=[], limits=updated_limits,
        )

        with code_executor:
            execution_results = code_executor.run_input(input)
            response = self._executor_output_to_response_format(execution_results)
            output = {
                **output,
                **response,
            }
        return output

    @classmethod
    def get_test_case_count(cls, problem_name, run_type):
        """
        Return the test case count of a given run type for a problem.

        Returns:
            Count of the test cases or None
        """
        test_cases = glob.glob(
            '{}{}/{}/*'.format(cls.__SECRET_DATA_DIR__, problem_name, run_type)
        )
        return len(test_cases) if test_cases else None

    def respond_with_error(self, message):
        """
        returns error response with message
        """
        return {'correct': False, 'score': 0, 'errors': [message], 'tests': []}

    def compare_outputs(self, actual_output, expected_output_file, usage_key=None):
        """
        compares actual and expected output line by line after stripping
        any whitespaces at the ends. Raises Exception if outputs do not match
        otherwise returns response of correct answer
        Args:
            actual_output(str): output of learner code
            expected_output_file(str): file name containing expected output of test case
            usage_key(str)
        """
        if not is_design_problem(usage_id=usage_key):
            expected_output = open(expected_output_file, 'r').read().rstrip()
            actual_output = actual_output.rstrip()

            expected_output_splited = expected_output.split('\n')
            actual_output_splited = actual_output.split('\n')

            if actual_output_splited != expected_output_splited:
                return {
                    'correct': False,
                    'score': 0,
                    'errors': [],
                    'tests': [[False, expected_output, actual_output]],
                }
            else:
                return {
                    'correct': True,
                    'score': 1,
                    'errors': [],
                    'tests': [[True, expected_output, actual_output]],
                }
        else:
            return {
                'correct': True,
                'score': 1,
                'errors': [],
                'tests': [[True, "", actual_output.strip()]],
            }

    def process_execution_error(self, error):
        """
        Helper method to process and extract the execution error
        """
        try:
            output_error = error[0]
        except IndexError:
            output_error = error
        return truncate_error_output(output_error)

    def grade_response(self, data, problem_name, add_staff_output=False):
        """
        Grade the response with per file test case feature.
        """
        data.update({'problem_name': problem_name})

        output = self.grade(data, add_staff_cases=add_staff_output)

        sample_output = output[0]
        if add_staff_output:
            # If staff output is required, send the original result as it is.
            return output
        return sample_output
