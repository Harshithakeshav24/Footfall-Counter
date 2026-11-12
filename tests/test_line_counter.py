from app.line_counter import LineCounter


def test_moving_up_counts_as_in():
    counter = LineCounter(line_y=100)
    counter.update(1, 150)
    assert counter.update(1, 90) == "in"
    assert counter.entered == 1
    assert counter.total == 1


def test_moving_down_counts_as_out():
    counter = LineCounter(line_y=100)
    counter.update(1, 80)
    assert counter.update(1, 120) == "out"
    assert counter.exited == 1
    assert counter.total == 1


def test_no_crossing_no_count():
    counter = LineCounter(line_y=100)
    for y in [10, 30, 50, 70, 95]:
        counter.update(1, y)
    assert counter.total == 0


def test_first_position_is_not_counted():
    # someone who first appears above the line has not crossed it
    counter = LineCounter(line_y=100)
    assert counter.update(1, 50) is None
    assert counter.total == 0


def test_same_person_counted_only_once():
    # standing on the line and moving back and forth should not add more counts
    counter = LineCounter(line_y=100)
    for y in [110, 95, 105, 90, 102, 80]:
        counter.update(7, y)
    assert counter.total == 1


def test_different_people_counted_separately():
    counter = LineCounter(line_y=100)
    counter.update(1, 150)
    counter.update(2, 50)
    counter.update(1, 60)   # person 1 goes up
    counter.update(2, 140)  # person 2 goes down
    assert counter.entered == 1
    assert counter.exited == 1
    assert counter.total == 2
