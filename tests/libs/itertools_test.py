from alert_manager.libs.itertools import divide_seq


def test_divide_seq__even_list_division():
    # arrange
    value = [1, 2, 3, 4, 5, 6]

    # act
    part1, part2 = divide_seq(value)

    # assert
    assert part1 == [1, 2, 3]
    assert part2 == [4, 5, 6]


def test_divide_seq__odd_list_division():
    # arrange
    value = [1, 2, 3, 4, 5]

    # act
    part1, part2 = divide_seq(value)

    # assert
    assert part1 == [1, 2, 3]
    assert part2 == [4, 5]


def test_divide_seq__empty_list_division():
    # arrange
    value = []

    # act
    part1, part2 = divide_seq(value)

    # assert
    assert part1 == []
    assert part2 == []


def test_divide_seq__single_element_list_division():
    # arrange
    value = [42]

    # act
    part1, part2 = divide_seq(value)

    # assert
    assert part1 == [42]
    assert part2 == []
