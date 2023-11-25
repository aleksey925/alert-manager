from alert_manager.enums.grafana import GrafanaAlertState
from alert_manager.services.slack.message import MessageBuilder, truncate_block_length


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


def test_truncate_block_length__non_section():
    # arrange
    blocks = [{'type': 'non-section', 'text': {'text': 'a' * 4000}}]

    # act
    result = truncate_block_length(blocks)

    # assert
    assert result == blocks


def test_truncate_block_length__section():
    # arrange
    blocks = [{'type': 'section', 'text': {'text': 'a' * 4000}}]

    # act
    result = truncate_block_length(blocks)

    # assert
    assert len(result[0]['text']['text']) == 3000
    assert result[0]['text']['text'].endswith('...')


def test_truncate_block_length__section_fields():
    # arrange
    blocks = [{'type': 'section', 'fields': [{'text': 'a' * 3000}, {'text': 'a' * 3000}]}]

    # act
    result = truncate_block_length(blocks)

    # assert
    assert len(result[0]['fields'][0]['text']) == 2000
    assert result[0]['fields'][0]['text'].endswith('...')
    assert len(result[0]['fields'][1]['text']) == 2000
    assert result[0]['fields'][1]['text'].endswith('...')
