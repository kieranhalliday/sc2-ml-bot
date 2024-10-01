from typing import Union

from sc2.position import Point2, Point3
from sc2.unit import Unit


class Helpers:
    @staticmethod
    def position_around_unit(
        pos: Union[Unit, Point2, Point3],
        grid_width: int,
        grid_height: int,
        distance: int = 1,
        step_size: int = 1,
        exclude_out_of_bounds: bool = True,
    ):
        pos = pos.position.to2.rounded
        positions = {
            pos.offset(Point2((x, y)))
            for x in range(-distance, distance + 1, step_size)
            for y in range(-distance, distance + 1, step_size)
            if (x, y) != (0, 0)
        }
        # filter positions outside map size
        if exclude_out_of_bounds:
            positions = {
                p
                for p in positions
                if 0 <= p[0] < grid_width and 0 <= p[1] < grid_height
            }
        return positions

    @staticmethod
    def neighbors4(position, distance=1):
        p = position
        d = distance
        return {
            Point2((p.x - d, p.y)),
            Point2((p.x + d, p.y)),
            Point2((p.x, p.y - d)),
            Point2((p.x, p.y + d)),
        }

    @staticmethod
    def neighbors8(position, distance=1):
        p = position
        d = distance
        return Helpers.neighbors4(position, distance) | {
            Point2((p.x - d, p.y - d)),
            Point2((p.x - d, p.y + d)),
            Point2((p.x + d, p.y - d)),
            Point2((p.x + d, p.y + d)),
        }
