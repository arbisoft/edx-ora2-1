"""
Celery tasks.
"""
import logging
import os

from celery import task
from celery_utils.logged_task import LoggedTask
from celery.schedules import crontab
from submissions.api import _get_submission_model
from opaque_keys.edx.keys import UsageKey  # pylint: disable=import-error
from openassessment.xblock.signals import CODING_TEST_CASES_EVALUATED
from xmodule.modulestore.django import modulestore  # pylint: disable=import-error

from openassessment.xblock.job_sample_grader.utils import is_design_problem, get_error_response
from openassessment.xblock.job_sample_grader.code_grader import CodeGraderMixin

from lms.djangoapps.courseware.models import StudentModule

logger = logging.getLogger(__name__)


@task(base=LoggedTask, name="run_and_save_test_cases_output")
def run_and_save_test_cases_output(
    block_id: str,
    user_id: int,
    saved_response: dict,
    add_staff_cases: bool = False,
    **kwargs):
    """
    A task that executes a candidates code response. Results are saved
    in StudentModule state.

    Args:
        block_id (str): ORA block usage id.
        user_id (int): Student user id.
        saved_response (dict): A dict of shape (example): 
            {
                'executor_id': 'server_shell-python:3.5.2',
                'submission': 'print("YES")'
            }
        add_staff_cases (bool, optional): Whether or not to run staff test cases.
            Defaults to False.
    """
    try:
        ora_block = modulestore().get_item(UsageKey.from_string(block_id))
    except Exception:
        logger.exception(
            'Error retreiving OpenAssessmentBlock with usage id {}'.format(block_id)
        )
        return

    try:
        grade_output = ora_block.grade_response(
            saved_response,
            ora_block.display_name,
            add_staff_cases,
        )
    except Exception as ex:
        logger.exception(
            'Could not grade response for user {} and block {}. {}'.format(
                user_id, block_id, str(ex)
            ),
            exc_info=ex
        )
        code_execution_results = {
            'success': False,
            'message': 'Error grading the code.',
            'error': str(ex),
            'output': {
                'sample': {
                    'error': 'Error grading the code. ' + str(ex),
                }
            },
        }
    except:
        logger.exception(
            'Could not grade response for user {} and block {}.'.format(
                user_id, block_id
            ),
        )
        code_execution_results = {
            'success': False,
            'message': 'Unexpected error grading the code.',
            'error': 'Unexpected error grading the code.',
            'output': {
                'sample': {
                    'error': 'Unexpected error grading the code.',
                }
            },
        }
    else:
        if add_staff_cases:
            # There can be two type of responses from the grading function:
            # 1. List or tuple with one or 2 elements. In this case values will be unpacked as expected
            # 2. List or tuple with one element. In this case the value will be unpacked as a single element and the
            #   second element will be None
            # 3. Single Object. In this case the value will be unpacked as a single element and the second element will
            #   be None

            sample_output, staff_output = None, None
            if (type(grade_output) is tuple or type(grade_output) is list) and len(grade_output) == 2:
                sample_output, staff_output = grade_output
            elif (type(grade_output) is tuple or type(grade_output) is list) and len(grade_output) == 1:
                sample_output = grade_output[0]
            else:
                sample_output = grade_output

        else:
            sample_output, staff_output = grade_output, None

        code_execution_results = {
            'success': True,
            'message': '',
            'output': {
                'sample': sample_output,
                'staff': staff_output,
            }
        }

    ora_block.set_code_execution_results(code_execution_results, user_id)


@task(base=LoggedTask, name="run_and_save_staff_test_cases")
def run_and_save_staff_test_cases(block_id, sub_uuid, problem_name, **kwargs):
    """
    Celery task for running staff test cases and updating the submission
    against a given uuid.

    If the problem is not a design-based problem
    Get the submission against given UUID
    Run the code
    If staff response present, attempt saving it
    If not saved, add a default error response and log the exception
    """
    if is_design_problem(block_id, problem_name):
        CODING_TEST_CASES_EVALUATED.send(
            sender=None,
            block_id=block_id,
            submission_uuid=sub_uuid,
        )
        return

    logger.info(
        "Kicking off run_and_save_staff_test_cases task against sub ID {} and problem {}".format(
            sub_uuid, problem_name
        )
    )
    try:
        submission = _get_submission_model(sub_uuid)
    except Exception:
        logger.exception("Error retrieving submission for problem {} and uuid {}".format(
            problem_name, sub_uuid
        ))
        return

    default_staff_run_error_response = get_error_response('staff', 'Missing Staff Submission')
    answer = submission.answer
    code_submission = answer['submission']
    executor_id = answer['executor_id']
    grader_data = {
        'submission': code_submission,
        'executor_id': executor_id
    }
    try:
        ora_block = modulestore().get_item(UsageKey.from_string(block_id))
    except Exception:
        logger.exception(
            "Error retreiving OpenAssessmentBlock with usage id {} for problem {} and uuid {}."
            .format(
                block_id,
                problem_name,
                sub_uuid
            )
        )
        return

    grade_output = ora_block.grade_response(grader_data, problem_name, add_staff_output=True)

    try:
        staff_run = grade_output[1]
    except IndexError:
        logger.exception(
            "Error retrieving staff submission from UUID {} from grade response for problem {}".format(
                sub_uuid, problem_name
            )
        )
        staff_run = default_staff_run_error_response

    try:
        submission.answer.update({'staff_run': staff_run})
        submission.save()
    except Exception:
        logger.exception("Error Saving Staff submission in Database, Saving default response")
        submission.answer.update({'staff_run': default_staff_run_error_response})
        submission.save()

    CODING_TEST_CASES_EVALUATED.send(
        sender=None,
        block_id=block_id,
        submission_uuid=sub_uuid,
    )


@task(base=LoggedTask, name="cleanup_question_attachments_cache")
def cleanup_question_attachments_cache(**kwargs):
    """
    Periodic task to clean up expired question attachments cache.

    This task runs daily (at 2 AM by default) to:
    - Remove expired cache files (older than CACHE_EXPIRY_DAYS)
    - Manage cache size (keep under MAX_CACHE_SIZE_MB)
    - Log cleanup statistics

    Expected to be scheduled via celery beat:
       CELERY_BEAT_SCHEDULE = {
            'cleanup-question-attachments-cache': {
                'task': 'cleanup_question_attachments_cache',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            },
        }
    """
    logger.info("Starting question attachments cache cleanup task")

    try:
        # Create a CodeGraderMixin instance to access cache management methods
        grader_mixin = CodeGraderMixin()

        # Run cleanup
        grader_mixin._cleanup_expired_cache()

        # Log cache statistics after cleanup
        cache_dir = grader_mixin.CACHE_DIR
        if os.path.exists(cache_dir):
            file_count = 0
            total_size = 0
            for filename in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, filename)
                if os.path.isfile(file_path):
                    file_count += 1
                    total_size += os.path.getsize(file_path)

            size_mb = total_size / (1024 * 1024)
            logger.info(
                "Cache cleanup completed. Files: {}, Size: {:.2f} MB, Directory: {}".format(
                    file_count, size_mb, cache_dir
                )
            )
        else:
            logger.info("Cache directory does not exist: {}".format(cache_dir))

    except Exception as e:
        logger.exception("Error during question attachments cache cleanup: {}".format(str(e)))
        raise
