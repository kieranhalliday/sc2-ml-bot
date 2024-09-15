from enum import Enum

class Actions(Enum):
    DO_NOTHING = "do_nothing"

    # Build buildings
    BUILD_SUPPLY_DEPOT = "build_supply_depot"
    BUILD_GAS = "build_gas"
    BUILD_CC = "build_cc"
    BUILD_BARRACKS = "build_barracks"
    BUILD_GHOST_ACADEMY = "build_ghost_academy"
    BUILD_FACTORY = "build_factory"
    BUILD_STARPORT = "build_starport"
    BUILD_EBAY = "build_ebay"
    BUILD_ARMORY = "build_armory"
    BUILD_FUSION_CORE = "build_fusion_core"
    BUILD_BUNKER = "build_bunker"
    BUILD_TURRET = "build_missle_turret"
    BUILD_SENSOR = "build_sensor_tower"
    BUILD_ORBITAL = "build_orbital"
    BUILD_PF = "build_PF"

    # Train units
    TRAIN_SCV = "train_scv"
    TRAIN_MARINE = "train_marine"
    
    # Orders
    SCOUT = "scout"
    ATTACK = "attack"




bot_actions = [
    Actions.DO_NOTHING,
    
    # Build Buildings
    Actions.BUILD_SUPPLY_DEPOT,
    Actions.BUILD_GAS,
    Actions.BUILD_CC,
    Actions.BUILD_BARRACKS,
    Actions.BUILD_GHOST_ACADEMY,
    Actions.BUILD_FACTORY,
    Actions.BUILD_STARPORT,
    Actions.BUILD_EBAY,
    Actions.BUILD_ARMORY,
    Actions.BUILD_FUSION_CORE,
    Actions.BUILD_BUNKER,
    Actions.BUILD_TURRET,
    Actions.BUILD_SENSOR,
    Actions.BUILD_ORBITAL,
    Actions.BUILD_PF,
    
    # Train Units
    Actions.TRAIN_SCV,
    Actions.TRAIN_MARINE,
    
    # Orders
    Actions.SCOUT,
    Actions.ATTACK
]
