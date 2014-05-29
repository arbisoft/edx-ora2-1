# -*- coding: utf-8 -*-

"""
Tests for message handlers in Open Assessment XBlock.
"""

import mock
import pytz

import datetime as dt
from openassessment.xblock.openassessmentblock import OpenAssessmentBlock
from .base import XBlockHandlerTestCase, scenario


class TestMessageRender(XBlockHandlerTestCase):
    """
    Tests for the Message XBlock Handler
    """

    # Sets up all of the pre-set dates.  Uses base day of today in order to allow
    # comparison regardless of true date.  For this reason, the dates in the XML are
    # ignored and irrelevant (because we patch is_closed)
    TODAY = dt.date.today()
    TODAY = dt.datetime(TODAY.year, TODAY.month, TODAY.day, 0, 0, 0, tzinfo=pytz.utc)
    TOMORROW = TODAY + dt.timedelta(days=1)
    FUTURE = TODAY + dt.timedelta(days=10)
    FAR_FUTURE = TODAY + dt.timedelta(days=100)
    YESTERDAY = TODAY - dt.timedelta(days=1)
    PAST = TODAY - dt.timedelta(days=10)
    FAR_PAST = TODAY - dt.timedelta(days=100)

    def _assert_path_and_context(
        self, xblock, expected_path, expected_context,
        workflow_status, deadline_information, has_peers_to_grade
    ):
        """
        Complete all of the logic behind rendering the message and verify
            1) The correct template and context were used
            2) The rendering occured without an error

        Args:
            xblock (OpenAssessmentBlock): The XBlock we are testing
            expected_path (str): The expected template path
            expected_context (dict): The expected template context
            workflow_status (str or None): The cannonical workflow status
            deadline_information (dict): has the following properties
                - deadline_information.get("submission") has the same properties as is_closed("submission")
                - deadline_information.get("peer-assessment") has the same properties as is_closed("peer-assessment")
                - deadline_information.get("self-assessment") has the same properties as is_closed("self-assessment")
                - (WILL BE DEFAULT) deadline_information.get("over-all") has the same properties as is_closed()
            has_peers_to_grade (bool): A boolean which indicates whether the queue of peer responses is empty

        """

        # Simulate the response from the workflow API
        workflow_info = {
            'status': workflow_status
        }
        xblock.get_workflow_info = mock.Mock(return_value=workflow_info)

        # Mock out the actual rendering of the assessment (we will check what it is called with)
        xblock.render_assessment = mock.Mock()

        # Simulate the field of no_peers based on our test input
        xblock.no_peers = not has_peers_to_grade

        # Mock out the is_closed method from the OpenAssessmentClass
        with mock.patch.object(OpenAssessmentBlock, 'is_closed') as mock_is_closed:

            def closed_side_effect(step="over-all"):
                # The method which will patch xblock.is_closed. Returns values in the form of is_closed, and takes
                # its information from the paramater deadline_information of _assert_path_and_context.
                # Note that if no parameter is provided, we assume the user is asking for is_closed()

                return deadline_information.get(step, "not-found")

            # Sets the side effect of is_closed to be our custom method, completing the patch
            mock_is_closed.side_effect = closed_side_effect

            # self.request(xblock, 'render_message', )

            #from nose.tools import set_trace; set_trace()

            xblock.render_message(None, '')

            # Asserts that the message_mixin correctly derived the path and context to be rendered
            xblock.render_assessment.assert_called_with(expected_path, expected_context)


    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_submission(self, xblock):

        status = None

        deadline_information = {
            'submission': (False, None, self.FAR_PAST, self.FUTURE),
            'peer-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'self-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_open.html'

        expected_context = {
            "approaching": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_no_peer.xml', user_id = "Linda")
    def test_submission_no_peer(self, xblock):

        status = None

        deadline_information = {
            'submission': (False, None, self.FAR_PAST, self.FUTURE),
            'self-assessment': (True, 'start', self.FUTURE, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_open.html'

        expected_context = {
            "approaching": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_submission_approaching(self, xblock):

        status = None

        deadline_information = {
            'submission': (False, None, self.FAR_PAST, self.TOMORROW),
            'peer-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'self-assessment': (True, 'start', self.FUTURE, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_open.html'

        expected_context = {
            "approaching": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_no_self.xml', user_id = "Linda")
    def test_submission_no_self_approaching(self, xblock):

        status = None

        deadline_information = {
            'submission': (False, None, self.FAR_PAST, self.TOMORROW),
            'peer-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_open.html'

        expected_context = {
            "approaching": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_submission_not_yet_open(self, xblock):

        status = None

        deadline_information = {
            'submission': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'peer-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'self-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'over-all': (True, 'start', self.TOMORROW, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_submission_incomplete(self, xblock):

        status = None

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.TODAY),
            'peer-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'self-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_student_training.xml', user_id = "Linda")
    def test_training(self, xblock):

        status = 'training'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'student-training': (False, None, self.YESTERDAY, self.FUTURE),
            'peer-assessment': (False, None, self.YESTERDAY, self.FUTURE),
            'self-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_training.html'

        expected_context = {
            "approaching": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_student_training.xml', user_id = "Linda")
    def test_training_approaching(self, xblock):

        status = 'training'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'student-training': (False, None, self.YESTERDAY, self.TOMORROW),
            'peer-assessment': (False, None, self.YESTERDAY, self.TOMORROW),
            'self-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_training.html'

        expected_context = {
            "approaching": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_student_training.xml', user_id = "Linda")
    def test_training_not_released(self, xblock):

        status = 'training'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.TOMORROW),
            'student-training': (True, 'start', self.TOMORROW, self.FUTURE),
            'peer-assessment': (True, 'start', self.TOMORROW, self.FUTURE),
            'self-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_student_training.xml', user_id = "Linda")
    def test_training_closed(self, xblock):

        status = 'training'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.PAST),
            'student-training': (True, 'due', self.FAR_PAST, self.PAST),
            'peer-assessment': (True, 'due', self.PAST, self.YESTERDAY),
            'self-assessment': (False, None, self.YESTERDAY, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_peer(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (False, None, self.FAR_PAST, self.FUTURE),
            'self-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_peer.html'

        expected_context = {
            "has_self": True,
            "waiting": False,
            "peer_approaching": False,
            "peer_closed": False,
            "peer_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_no_self.xml', user_id = "Linda")
    def test_peer_no_self(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (False, None, self.FAR_PAST, self.FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_peer.html'

        expected_context = {
            "has_self": False,
            "waiting": False,
            "peer_approaching": False,
            "peer_closed": False,
            "peer_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_no_self.xml', user_id = "Linda")
    def test_peer_no_self_approaching(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (False, None, self.FAR_PAST, self.TOMORROW),
            'peer-assessment': (False, None, self.FAR_PAST, self.TOMORROW),
            'over-all': (False, None, self.FAR_PAST, self.TOMORROW)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_peer.html'

        expected_context = {
            "has_self": False,
            "waiting": False,
            "peer_approaching": True,
            "peer_closed": False,
            "peer_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_peer_not_released(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'start', self.TOMORROW, self.FUTURE),
            'self-assessment': (True, 'start', self.TOMORROW, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_peer_incomplete(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'due', self.PAST, self.TODAY),
            'self-assessment': (False, None, self.TODAY, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_peer_no_peers_to_assess(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (False, None, self.FAR_PAST, self.FUTURE),
            'self-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_peer.html'

        expected_context = {
            "has_self": True,
            "waiting": True,
            "peer_approaching": False,
            "peer_closed": False,
            "peer_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_peer_no_peers_to_assess_approaching(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (False, None, self.FAR_PAST, self.TOMORROW),
            'self-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_peer.html'

        expected_context = {
            "has_self": True,
            "waiting": True,
            "peer_approaching": True,
            "peer_closed": False,
            "peer_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_peer_not_open_approaching(self, xblock):

        status = 'peer'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'start', self.TOMORROW, self.FUTURE),
            'self-assessment': (False, None, self.FUTURE, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_self(self, xblock):

        status = 'self'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (False, None, self.FAR_PAST, self.FUTURE),
            'self-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_self.html'

        expected_context = {
            "has_peer": True,
            "self_approaching": False,
            "self_closed": False,
            "self_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_no_peer.xml', user_id = "Linda")
    def test_self_no_peer(self, xblock):

        status = 'self'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'self-assessment': (False, None, self.FAR_PAST, self.FAR_FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FAR_FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_self.html'

        expected_context = {
            "has_peer": False,
            "self_approaching": False,
            "self_closed": False,
            "self_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_no_peer.xml', user_id = "Linda")
    def test_self_no_peer_approaching(self, xblock):

        status = 'self'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'self-assessment': (False, None, self.FAR_PAST, self.TOMORROW),
            'over-all': (False, None, self.FAR_PAST, self.TOMORROW)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_self.html'

        expected_context = {
            "has_peer": False,
            "self_approaching": True,
            "self_closed": False,
            "self_not_released": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_self_closed(self, xblock):

        status = 'self'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'due', self.YESTERDAY, self.TODAY),
            'self-assessment': (True, 'start', self.TOMORROW, self.FUTURE),
            'over-all': (False, None, self.FAR_PAST, self.FUTURE)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario_no_peer.xml', user_id = "Linda")
    def test_self_no_peer_incomplete(self, xblock):

        status = 'self'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'self-assessment': (True, 'due', self.PAST, self.YESTERDAY),
            'over-all': (True, 'due', self.FAR_PAST, self.YESTERDAY)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_closed.html'

        expected_context = {
            "not_yet_open": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_waiting_due(self, xblock):

        status = 'waiting'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'due', self.YESTERDAY, self.TODAY),
            'self-assessment': (True, 'due', self.YESTERDAY, self.TODAY),
            'over-all': (True, 'due', self.FAR_PAST, self.TODAY)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_complete.html'

        expected_context = {
            "waiting": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_waiting_not_due(self, xblock):

        status = 'waiting'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'due', self.YESTERDAY, self.TODAY),
            'self-assessment': (False, None, self.YESTERDAY, self.TOMORROW),
            'over-all': (False, None, self.FAR_PAST, self.TOMORROW)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_complete.html'

        expected_context = {
            "waiting": True
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_done_due(self, xblock):

        status = 'done'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'due', self.YESTERDAY, self.TODAY),
            'self-assessment': (True, 'due', self.YESTERDAY, self.TODAY),
            'over-all': (True, 'due', self.FAR_PAST, self.TODAY)
        }

        has_peers_to_grade = True

        expected_path = 'openassessmentblock/message/oa_message_complete.html'

        expected_context = {
            "waiting": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )

    @scenario('data/message_scenario.xml', user_id = "Linda")
    def test_done_not_due(self, xblock):

        status = 'done'

        deadline_information = {
            'submission': (True, 'due', self.FAR_PAST, self.YESTERDAY),
            'peer-assessment': (True, 'due', self.YESTERDAY, self.TODAY),
            'self-assessment': (False, None, self.YESTERDAY, self.TOMORROW),
            'over-all': (False, None, self.FAR_PAST, self.TOMORROW)
        }

        has_peers_to_grade = False

        expected_path = 'openassessmentblock/message/oa_message_complete.html'

        expected_context = {
            "waiting": False
        }

        self._assert_path_and_context(
            xblock, expected_path, expected_context,
            status, deadline_information, has_peers_to_grade
        )