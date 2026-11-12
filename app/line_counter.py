class LineCounter:
    """
    Counts people whose centre point crosses a horizontal line.

    Moving up the frame (away from the camera)   -> "in"
    Moving down the frame (towards the camera)   -> "out"

    In the sample video the camera looks into a store aisle, so walking
    up the frame means walking into the aisle.

    The tracker gives every person an ID, so I store the last y position
    of each ID and compare it with the new one. If the line lies between
    the two positions, that person has crossed it.
    """

    def __init__(self, line_y):
        self.line_y = line_y
        self.entered = 0
        self.exited = 0
        self.last_y = {}          # track_id -> last centre y
        self.counted_ids = set()  # each person is counted only once

    @property
    def total(self):
        return self.entered + self.exited

    def update(self, track_id, y):
        """Update the position of one person. Returns "in", "out" or None."""
        prev_y = self.last_y.get(track_id)
        self.last_y[track_id] = y

        # first time we see this person, or already counted
        if prev_y is None or track_id in self.counted_ids:
            return None

        # note: y grows downwards in images, so "up" means y gets smaller
        if prev_y >= self.line_y > y:
            self.entered += 1
            self.counted_ids.add(track_id)
            return "in"

        if prev_y < self.line_y <= y:
            self.exited += 1
            self.counted_ids.add(track_id)
            return "out"

        return None
