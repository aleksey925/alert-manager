from alert_manager.libs.text import truncate


def test_truncate__short_text():
    # arrange
    text = 'Short text'

    # act
    result = truncate(text, 20)

    # assert
    assert result == text


def test_truncate__long_text():
    # arrange
    text = 'This is some long text that needs to be truncated'

    # act
    result = truncate(text, 20)

    # assert
    assert result == 'This is some long...'


def test_truncate__exact_length_text():
    # arrange
    text = 'This is 20 chars..'

    # act
    result = truncate(text, 20)

    # assert
    assert result == text
