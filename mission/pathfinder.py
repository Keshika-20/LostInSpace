
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

        # Queue items: (priority, counter, position)
        open_list = []
        counter = 0

        heapq.heappush(open_list, (0, counter, start))

        came_from = {}
        cost_so_far = {start: 0}

        while open_list:
            _, _, current = heapq.heappop(open_list)

            if current == goal:
                path = [current]

                while current in came_from:
                    current = came_from[current]
                    path.append(current)

                path.reverse()
                return path

            x, y = current

            # Explore right, left, down, and up in this order.
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

                    nx, ny = neighbour
                    gx, gy = goal

                    heuristic = abs(gx - nx) + abs(gy - ny)
                    priority = new_cost + heuristic

                    counter += 1

                    heapq.heappush(
                        open_list,
                        (priority, counter, neighbour)
                    )

        return None
