from alert_manager.enums.grafana import GrafanaAlertState
from alert_manager.services.slack.message import MessageBuilder


class TestMessageBuilder:
    def test_create_alert_message__alert_without_message_and_eval_matches__created_alert_without_message_block(
        self, alert_metadata
    ):
        # act
        blocks = MessageBuilder.create_alert_message(
            state=GrafanaAlertState.alerting,
            title=alert_metadata.title,
            rule_url=alert_metadata.rule_url,
            message=None,
            eval_matches=[],
        )

        # assert
        assert len(blocks) == 2
