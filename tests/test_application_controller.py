from application_controller import ApplicationController
from simulation.environment import Environment, OBSTACLE
from simulation.models import Resource
from simulation.rover import MoveResult, Rover


def test_controller_creates_real_environment_and_rover():
    controller = ApplicationController(rows=6, cols=7, base=(1, 2))

    assert isinstance(controller.environment, Environment)
    assert isinstance(controller.rover, Rover)
    assert controller.rover.env is controller.environment
    assert controller.rover.position == (1, 2)
    assert not controller.is_running


def test_successful_move_uses_rover_and_updates_its_state():
    controller = ApplicationController(rows=6, cols=6, vision_radius=1)
    previously_explored = controller.rover.known_map.explored_count()

    result = controller.handle_command("MOVE", (0, 1))

    assert result == MoveResult(True, "ok", 1.0)
    assert controller.rover.position == (0, 1)
    assert controller.rover.energy == 99.0
    assert controller.rover.moves == 1
    assert controller.rover.known_map.explored_count() > previously_explored


def test_rejected_move_preserves_rover_state_and_records_obstacle():
    controller = ApplicationController(rows=6, cols=6, vision_radius=0)
    controller.environment.grid[0][1] = OBSTACLE

    result = controller.handle_command("MOVE", (0, 1))

    assert result == MoveResult(False, "blocked", 0.0)
    assert controller.rover.position == (0, 0)
    assert controller.rover.energy == 100.0
    assert controller.rover.moves == 0
    assert controller.rover.known_map.is_known_obstacle((0, 1))


def test_controller_state_is_the_same_rover_state():
    controller = ApplicationController(rows=6, cols=6)
    rover = controller.rover

    rover.move_to((1, 0))

    assert controller.rover is rover
    assert controller.rover.position == (1, 0)
    assert controller.rover.energy == 99.0
    assert controller.rover.moves == 1
    assert controller.rover.known_map is rover.known_map


def test_reset_restores_configured_environment_and_rover_baseline():
    environment = Environment(6, 6, base=(0, 0))
    environment.grid[2][2] = OBSTACLE
    environment.seed = 23
    environment.resources.append(
        Resource(position=(5, 5), value=42.0, data_size=3.0)
    )
    environment.zone_cells = {(3, 3), (3, 4)}
    controller = ApplicationController(
        energy=75.0,
        vision_radius=1,
        capacity=8.0,
        environment=environment,
    )
    initial_grid = [row.copy() for row in controller.environment.grid]
    initial_resources = [
        (resource.position, resource.value, resource.data_size,
         resource.discovered, resource.collected)
        for resource in controller.environment.resources
    ]
    initial_zones = set(controller.environment.zone_cells)
    initial_seed = controller.environment.seed
    initial_map = [
        [
            controller.rover.known_map.cell_at((row, col))
            for col in range(controller.environment.cols)
        ]
        for row in range(controller.environment.rows)
    ]

    controller.environment.grid[3][3] = OBSTACLE
    controller.environment.resources[0].value = -1.0
    controller.environment.resources[0].collected = True
    controller.environment.zone_cells.clear()
    move_result = controller.rover.move_to((0, 1))
    assert move_result.success
    assert controller.rover.energy == 74.0
    assert controller.rover.moves == 1
    controller.rover.load(2.0)
    controller.rover.uploaded_data = 7.0
    controller.handle_command("START")

    controller.handle_command("RESET")

    assert controller.environment.grid == initial_grid
    assert [
        (resource.position, resource.value, resource.data_size,
         resource.discovered, resource.collected)
        for resource in controller.environment.resources
    ] == initial_resources
    assert controller.environment.zone_cells == initial_zones
    assert controller.environment.seed == initial_seed
    assert controller.rover.env is controller.environment
    assert controller.rover.position == (0, 0)
    assert controller.rover.energy == 75.0
    assert controller.rover.carried_data == 0.0
    assert controller.rover.uploaded_data == 0.0
    assert controller.rover.moves == 0
    assert [
        [
            controller.rover.known_map.cell_at((row, col))
            for col in range(controller.environment.cols)
        ]
        for row in range(controller.environment.rows)
    ] == initial_map
    assert not controller.is_running


def test_repeated_reset_restores_identical_world_and_rover_state():
    environment = Environment(10, 10)
    environment.grid[7][7] = OBSTACLE
    environment.seed = 31
    environment.place_resources(3, seed=37)
    environment.place_comm_zones(count=2, seed=41)
    controller = ApplicationController(environment=environment)

    controller.environment.grid[0][1] = OBSTACLE
    assert controller.rover.move_to((1, 0)).success
    controller.handle_command("START")
    controller.handle_command("RESET")
    first_world = (
        [row.copy() for row in controller.environment.grid],
        [
            (resource.position, resource.value, resource.data_size,
             resource.discovered, resource.collected)
            for resource in controller.environment.resources
        ],
        set(controller.environment.zone_cells),
        controller.environment.seed,
    )
    first_rover = (
        controller.rover.position,
        controller.rover.energy,
        controller.rover.carried_data,
        controller.rover.uploaded_data,
        controller.rover.moves,
        [
            [
                controller.rover.known_map.cell_at((row, col))
                for col in range(controller.environment.cols)
            ]
            for row in range(controller.environment.rows)
        ],
        controller.is_running,
    )

    controller.environment.grid[1][0] = OBSTACLE
    assert controller.rover.move_to((0, 1)).success
    controller.handle_command("START")
    controller.handle_command("RESET")
    second_world = (
        [row.copy() for row in controller.environment.grid],
        [
            (resource.position, resource.value, resource.data_size,
             resource.discovered, resource.collected)
            for resource in controller.environment.resources
        ],
        set(controller.environment.zone_cells),
        controller.environment.seed,
    )
    second_rover = (
        controller.rover.position,
        controller.rover.energy,
        controller.rover.carried_data,
        controller.rover.uploaded_data,
        controller.rover.moves,
        [
            [
                controller.rover.known_map.cell_at((row, col))
                for col in range(controller.environment.cols)
            ]
            for row in range(controller.environment.rows)
        ],
        controller.is_running,
    )

    assert second_world == first_world
    assert second_rover == first_rover
