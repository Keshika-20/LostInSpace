
import heapq


class Pathfinder:
    """Finds a path around obstacles using A*."""

    def find_path(self, start, goal, blocked=None):
        if blocked is None:
            blocked = set()

        if start in blocked or goal in blocked:
            return None

        if start == goal:
            return [start]

        # Priority queue: (estimated total cost, position)
        open_list = []
        heapq.heappush(open_list, (0, start))

        came_from = {}
        cost_so_far = {start: 0}

        while open_list:
            _, current = heapq.heappop(open_list)

            if current == goal:
                path = [current]

                while current in came_from:
                    current = came_from[current]
                    path.append(current)

                path.reverse()
                return path

            x, y = current

            # Four possible directions.
            neighbours = [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1)
            ]

            for neighbour in neighbours:
                if neighbour in blocked:
                    continue

                new_cost = cost_so_far[current] + 1

                if (
                    neighbour not in cost_so_far
                    or new_cost < cost_so_far[neighbour]
                ):
                    cost_so_far[neighbour] = new_cost
                    came_from[neighbour] = current

                    gx, gy = goal

                    # Manhattan distance heuristic.
                    heuristic = abs(gx - neighbour[0]) + abs(
                        gy - neighbour[1]
                    )

                    priority = new_cost + heuristic

                    heapq.heappush(
                        open_list,
                        (priority, neighbour)
                    )

        # No route exists.
        return None
