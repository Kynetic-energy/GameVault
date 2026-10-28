-- Demo credentials (LOCAL DEVELOPMENT ONLY):
-- admin / AdminDemo@123
-- player_one / PlayerDemo@123
-- player_two / PlayerDemo@123
-- Passwords below are Werkzeug-compatible PBKDF2-SHA256 hashes, never plaintext database values.
-- All companies, games, and payment references below are fictional.

USE gamevault;

START TRANSACTION;

INSERT INTO
    publishers (publisher_id, publisher_name)
VALUES (1, 'Pixel Harbor Publishing'),
    (2, 'Orbit Lantern Games'),
    (3, 'Copperleaf Interactive'),
    (4, 'Obsidian Forge'),
    (5, 'Nebula Entertainment'),
    (6, 'Velvet Wave Games'),
    (7, 'Titan Horizon'),
    (8, 'Crimson Crest'),
    (9, 'Aurora Works'),
    (10, 'Zenith Digital');

INSERT INTO
    developers (dev_id, dev_name)
VALUES (1, 'Moonforge Studio'),
    (2, 'Neon Trail Labs'),
    (3, 'Willowbyte Studio'),
    (4, 'Clockwork Kite'),
    (5, 'Ironclad Games'),
    (6, 'Prism Core Labs'),
    (7, 'Thunderstrike Studios'),
    (8, 'Hollow Oak Studio'),
    (9, 'Nova Sphere'),
    (10, 'Apex Polygon');

INSERT INTO
    users (
        user_id,
        username,
        password_hash,
        email,
        email_verified,
        is_admin,
        affiliate_publisher_id
    )
VALUES (
        1,
        'admin',
        'pbkdf2:sha256:1000000$f147e1f32339ee6a$9fb808be94fd9a921d33daf481ae05bb1db46a2c0f1019d74b9ecb57850328a5',
        'admin@example.com',
        0,
        1,
        NULL
    ),
    (
        2,
        'player_one',
        'pbkdf2:sha256:1000000$087b15318a880d96$53ad1a8bafbd714dd4b255a59432ecef992bc428a2eae634757f3a84720bd151',
        'player.one@example.com',
        0,
        0,
        NULL
    ),
    (
        3,
        'player_two',
        'pbkdf2:sha256:1000000$57674fd2e935f29b$193d3c431c5664c277fcb052dab45610623d1f8d6789522d4c838c0164877610',
        'player.two@example.com',
        0,
        0,
        1
    );

INSERT INTO
    genres (genre_id, genre_name)
VALUES (1, 'Action'),
    (2, 'RPG'),
    (3, 'Racing'),
    (4, 'Puzzle'),
    (5, 'Simulation'),
    (6, 'Strategy'),
    (7, 'Adventure'),
    (8, 'Horror'),
    (9, 'FPS'),
    (10, 'Sports'),
    (11, 'Casual'),
    (12, 'Fighting');

INSERT INTO
    platforms (platform_id, platform_name)
VALUES (1, 'Windows'),
    (2, 'Linux'),
    (3, 'macOS'),
    (4, 'PlayStation 5'),
    (5, 'Xbox Series X');

INSERT INTO
    games (
        game_id,
        game_name,
        description,
        thumbnail_url,
        publisher_id,
        developer_id,
        standard_price,
        discount_percent,
        release_date
    )
VALUES (
        1,
        'Emberfall Odyssey',
        'Explore a volcanic kingdom in a story-driven action RPG.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Emberfall+Odyssey',
        1,
        1,
        1499,
        20,
        '2025-03-14'
    ),
    (
        2,
        'Neon Circuit',
        'Race through glowing city circuits and unlock new vehicles.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Neon+Circuit',
        2,
        2,
        999,
        10,
        '2025-06-20'
    ),
    (
        3,
        'Garden of Clouds',
        'Build a peaceful floating garden and trade your harvest.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Garden+of+Clouds',
        3,
        3,
        799,
        0,
        '2025-09-05'
    ),
    (
        4,
        'Clockwork Riddles',
        'Solve mechanical puzzles inside an abandoned observatory.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Clockwork+Riddles',
        1,
        4,
        499,
        50,
        '2024-11-15'
    ),
    (
        5,
        'Starbound Tactics',
        'Command a small fleet in turn-based space battles.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Starbound+Tactics',
        2,
        1,
        1299,
        25,
        '2025-12-12'
    ),
    (
        6,
        'Lantern Valley',
        'Discover hidden paths in a hand-painted adventure world.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Lantern+Valley',
        3,
        3,
        599,
        0,
        '2026-01-23'
    ),
    (
        7,
        'Arena Sparks',
        'A free action game with short arena challenges.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Arena+Sparks',
        2,
        2,
        0,
        0,
        '2026-02-06'
    ),
    (
        8,
        'Frostline Expedition',
        'Lead an expedition through a frozen wilderness.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Frostline+Expedition',
        1,
        4,
        899,
        100,
        '2026-04-10'
    ),
    (
        9,
        'Cyber Strike',
        'A fast-paced futuristic FPS taking place in a sprawling metropolis.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Cyber+Strike',
        4,
        5,
        1999,
        0,
        '2025-01-10'
    ),
    (
        10,
        'Phantom Protocol',
        'Stealth espionage in a corporate-run dystopian city.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Phantom+Protocol',
        5,
        6,
        2499,
        33,
        '2025-04-15'
    ),
    (
        11,
        'Void Runner',
        'High-speed anti-gravity racing across broken space stations.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Void+Runner',
        6,
        7,
        1299,
        15,
        '2023-08-22'
    ),
    (
        12,
        'Iron Assault',
        'Tactical squad-based shooter during an alternate history cold war.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Iron+Assault',
        7,
        8,
        2999,
        0,
        '2026-05-11'
    ),
    (
        13,
        'Crimson Blade',
        'Master the blade in this unforgiving dark fantasy RPG.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Crimson+Blade',
        8,
        9,
        3499,
        20,
        '2024-02-18'
    ),
    (
        14,
        'Echoes of Eternity',
        'An epic JRPG adventure spanning across multiple timelines.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Echoes+of+Eternity',
        9,
        10,
        3999,
        0,
        '2026-08-01'
    ),
    (
        15,
        'Dragons Roar',
        'Tame and ride dragons in a sprawling open world.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Dragons+Roar',
        10,
        1,
        2499,
        50,
        '2022-11-11'
    ),
    (
        16,
        'Astral Nomads',
        'Manage a caravan of space travelers seeking a new home.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Astral+Nomads',
        1,
        2,
        1499,
        10,
        '2025-07-07'
    ),
    (
        17,
        'Whisper Hill',
        'Survive a night in a haunted Appalachian logging town.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Whisper+Hill',
        2,
        3,
        999,
        0,
        '2024-10-30'
    ),
    (
        18,
        'The Ashen House',
        'Psychological horror inside an ever-changing Victorian mansion.',
        'https://placehold.co/600x400/0b132b/4ade80?text=The+Ashen+House',
        3,
        4,
        1299,
        25,
        '2025-10-15'
    ),
    (
        19,
        'Midnight Cabin',
        'A co-op survival game where you defend a cabin against cryptids.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Midnight+Cabin',
        4,
        5,
        899,
        0,
        '2026-09-09'
    ),
    (
        20,
        'Crystal Maze',
        'Navigate through procedurally generated light and mirror puzzles.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Crystal+Maze',
        5,
        6,
        499,
        0,
        '2021-03-22'
    ),
    (
        21,
        'Quantum Shift',
        'Manipulate time to solve environmental puzzles.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Quantum+Shift',
        6,
        7,
        799,
        15,
        '2023-05-19'
    ),
    (
        22,
        'Mind Weavers',
        'Relaxing color-matching puzzles with an ambient soundtrack.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Mind+Weavers',
        7,
        8,
        299,
        0,
        '2024-01-08'
    ),
    (
        23,
        'Cafe Manager 2026',
        'Design, build, and run your dream artisanal coffee shop.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Cafe+Manager+2026',
        8,
        9,
        1199,
        10,
        '2026-01-15'
    ),
    (
        24,
        'Urban Architect',
        'City-building simulation with a focus on green energy logistics.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Urban+Architect',
        9,
        10,
        1999,
        33,
        '2025-06-30'
    ),
    (
        25,
        'Farm Horizon',
        'A cozy farming simulator with deep crop genetics.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Farm+Horizon',
        10,
        1,
        1499,
        0,
        '2026-04-20'
    ),
    (
        26,
        'Apex Drift',
        'Master the art of drifting on neon-lit mountain passes.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Apex+Drift',
        1,
        2,
        999,
        50,
        '2022-09-12'
    ),
    (
        27,
        'Velocity Zero',
        'Arcade racing with explosive power-ups and destructible tracks.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Velocity+Zero',
        2,
        3,
        1499,
        20,
        '2024-07-25'
    ),
    (
        28,
        'Mud Track Mania',
        'Off-road rally racing featuring realistic mud physics.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Mud+Track+Mania',
        3,
        4,
        1999,
        0,
        '2026-03-05'
    ),
    (
        29,
        'Pro Striker 26',
        'The ultimate football simulation experience.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Pro+Striker+26',
        4,
        5,
        4999,
        0,
        '2026-08-20'
    ),
    (
        30,
        'Hoops VR',
        'Step onto the court in this immersive VR basketball game.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Hoops+VR',
        5,
        6,
        1299,
        10,
        '2025-11-18'
    ),
    (
        31,
        'Court King',
        'Fast-paced street basketball with flashy combos.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Court+King',
        6,
        7,
        999,
        0,
        '2024-04-14'
    ),
    (
        32,
        'Empire Builders',
        'Forge a civilization from the Bronze Age to the Space Age.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Empire+Builders',
        7,
        8,
        2999,
        25,
        '2023-12-01'
    ),
    (
        33,
        'Warlords of Aethelgard',
        'Grand strategy set in a crumbling fantasy empire.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Warlords+of+Aethelgard',
        8,
        9,
        2499,
        0,
        '2025-05-17'
    ),
    (
        34,
        'Grid Commander',
        'Turn-based tactical combat on a hex grid.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Grid+Commander',
        9,
        10,
        1499,
        50,
        '2021-08-30'
    ),
    (
        35,
        'Secrets of the Deep',
        'Explore uncharted ocean trenches in a custom submarine.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Secrets+of+the+Deep',
        10,
        1,
        1999,
        15,
        '2026-02-28'
    ),
    (
        36,
        'Desert Nomad',
        'Survive the harsh wasteland and uncover ancient ruins.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Desert+Nomad',
        1,
        2,
        1799,
        0,
        '2025-09-22'
    ),
    (
        37,
        'The Lost Map',
        'A narrative-driven puzzle adventure across the globe.',
        'https://placehold.co/600x400/0b132b/4ade80?text=The+Lost+Map',
        2,
        3,
        1299,
        33,
        '2024-06-14'
    ),
    (
        38,
        'Neon Fighter',
        '2D fighting game featuring a colorful synthwave aesthetic.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Neon+Fighter',
        3,
        4,
        1499,
        10,
        '2023-11-09'
    ),
    (
        39,
        'Combat Legends',
        '3D arena brawler with over 40 distinct martial arts styles.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Combat+Legends',
        4,
        5,
        2999,
        0,
        '2026-07-15'
    ),
    (
        40,
        'Street Brawl',
        'Classic arcade beat-em-up action updated for modern hardware.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Street+Brawl',
        5,
        6,
        799,
        50,
        '2022-04-12'
    ),
    (
        41,
        'Galactic Miner',
        'Automate resource extraction on procedurally generated asteroids.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Galactic+Miner',
        6,
        7,
        899,
        0,
        '2024-12-05'
    ),
    (
        42,
        'Stellar Tycoon',
        'Build and manage the most profitable space station in the sector.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Stellar+Tycoon',
        7,
        8,
        1499,
        20,
        '2025-03-27'
    ),
    (
        43,
        'Rogue Protocol',
        'A roguelike action game where every death upgrades your AI core.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Rogue+Protocol',
        8,
        9,
        1199,
        0,
        '2026-10-01'
    ),
    (
        44,
        'Shadow Syndicate',
        'Command a squad of mercenaries in turn-based cyberpunk heists.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Shadow+Syndicate',
        9,
        10,
        2499,
        10,
        '2025-08-19'
    ),
    (
        45,
        'Abyssal Depths',
        'Lovecraftian horror meets deep-sea diving simulation.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Abyssal+Depths',
        10,
        1,
        1799,
        0,
        '2026-01-28'
    ),
    (
        46,
        'Chrono Quest',
        'An RPG where combat mechanics change depending on the time era.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Chrono+Quest',
        1,
        2,
        2999,
        33,
        '2024-05-15'
    ),
    (
        47,
        'Velocity Xtreme',
        'The fastest anti-grav racer ever made. No brakes allowed.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Velocity+Xtreme',
        2,
        3,
        1999,
        0,
        '2026-06-11'
    ),
    (
        48,
        'Block Builder',
        'A serene sandbox game about building small voxel dioramas.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Block+Builder',
        3,
        4,
        499,
        0,
        '2021-10-20'
    ),
    (
        49,
        'Puzzle Kingdom',
        'Match gems and build your castle to defend against monsters.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Puzzle+Kingdom',
        4,
        5,
        0,
        0,
        '2023-01-13'
    ),
    (
        50,
        'Mecha Warfare',
        'Pilot customizable giant robots in massive destructible cityscapes.',
        'https://placehold.co/600x400/0b132b/4ade80?text=Mecha+Warfare',
        5,
        6,
        3999,
        15,
        '2026-04-30'
    );

INSERT INTO
    game_genres (game_id, genre_id)
VALUES (1, 1),
    (1, 2),
    (1, 7),
    (2, 3),
    (3, 5),
    (4, 4),
    (5, 6),
    (6, 7),
    (7, 1),
    (8, 7),
    (8, 6),
    (9, 9),
    (9, 1),
    (10, 1),
    (10, 7),
    (11, 1),
    (11, 3),
    (12, 9),
    (12, 6),
    (13, 2),
    (13, 1),
    (14, 2),
    (14, 7),
    (15, 2),
    (15, 7),
    (16, 2),
    (16, 6),
    (17, 8),
    (17, 7),
    (18, 8),
    (19, 8),
    (19, 4),
    (20, 4),
    (21, 4),
    (21, 1),
    (22, 4),
    (22, 11),
    (23, 5),
    (23, 11),
    (24, 5),
    (24, 6),
    (25, 5),
    (26, 3),
    (27, 3),
    (27, 1),
    (28, 3),
    (28, 10),
    (29, 10),
    (30, 10),
    (30, 5),
    (31, 10),
    (31, 1),
    (32, 6),
    (32, 5),
    (33, 6),
    (33, 2),
    (34, 6),
    (35, 7),
    (35, 5),
    (36, 7),
    (36, 2),
    (37, 7),
    (37, 4),
    (38, 12),
    (39, 12),
    (39, 1),
    (40, 12),
    (40, 1),
    (41, 5),
    (41, 11),
    (42, 6),
    (42, 5),
    (43, 1),
    (43, 2),
    (44, 1),
    (44, 6),
    (45, 8),
    (45, 7),
    (46, 2),
    (46, 4),
    (47, 3),
    (48, 5),
    (48, 11),
    (49, 4),
    (49, 6),
    (50, 1),
    (50, 6);

INSERT INTO
    game_platforms (game_id, platform_id)
VALUES (1, 1),
    (1, 2),
    (2, 1),
    (3, 1),
    (3, 2),
    (3, 3),
    (4, 1),
    (4, 2),
    (4, 3),
    (5, 1),
    (5, 2),
    (6, 1),
    (6, 3),
    (7, 1),
    (8, 1),
    (8, 2),
    (9, 1),
    (9, 4),
    (9, 5),
    (10, 1),
    (10, 4),
    (11, 1),
    (11, 2),
    (11, 4),
    (11, 5),
    (12, 1),
    (13, 1),
    (13, 4),
    (13, 5),
    (14, 1),
    (14, 4),
    (15, 1),
    (15, 5),
    (16, 1),
    (16, 2),
    (16, 3),
    (17, 1),
    (17, 4),
    (18, 1),
    (18, 2),
    (18, 4),
    (19, 1),
    (19, 5),
    (20, 1),
    (20, 2),
    (20, 3),
    (21, 1),
    (21, 3),
    (22, 1),
    (22, 2),
    (22, 3),
    (23, 1),
    (23, 3),
    (24, 1),
    (24, 2),
    (24, 3),
    (25, 1),
    (25, 3),
    (25, 4),
    (26, 1),
    (26, 4),
    (26, 5),
    (27, 1),
    (27, 2),
    (28, 1),
    (28, 4),
    (28, 5),
    (29, 1),
    (29, 4),
    (29, 5),
    (30, 1),
    (30, 4),
    (31, 1),
    (31, 4),
    (31, 5),
    (32, 1),
    (32, 2),
    (32, 3),
    (33, 1),
    (33, 2),
    (34, 1),
    (34, 3),
    (35, 1),
    (35, 4),
    (36, 1),
    (36, 2),
    (36, 4),
    (36, 5),
    (37, 1),
    (37, 3),
    (38, 1),
    (38, 4),
    (38, 5),
    (39, 1),
    (39, 4),
    (39, 5),
    (40, 1),
    (40, 2),
    (40, 4),
    (41, 1),
    (41, 2),
    (41, 3),
    (42, 1),
    (42, 2),
    (42, 3),
    (43, 1),
    (43, 2),
    (43, 4),
    (44, 1),
    (44, 4),
    (44, 5),
    (45, 1),
    (45, 3),
    (45, 4),
    (46, 1),
    (46, 4),
    (47, 1),
    (47, 4),
    (47, 5),
    (48, 1),
    (48, 2),
    (48, 3),
    (49, 1),
    (49, 3),
    (50, 1),
    (50, 4),
    (50, 5);

INSERT INTO
    payments (
        transaction_id,
        payee_account_no,
        recipient_account_no,
        payment_time,
        amount,
        payment_status
    )
VALUES (
        1,
        'DEMO-PAYER-002',
        'DEMO-GAMEVAULT',
        '2026-10-15 10:00:00',
        2098.30,
        'SUCCESS'
    ),
    (
        2,
        'DEMO-PAYER-003',
        'DEMO-GAMEVAULT',
        '2026-10-15 11:00:00',
        249.50,
        'SUCCESS'
    ),
    (
        3,
        'DEMO-PAYER-002',
        'DEMO-GAMEVAULT',
        '2026-10-16 09:00:00',
        974.25,
        'FAILED'
    ),
    (
        4,
        'DEMO-PAYER-003',
        'DEMO-GAMEVAULT',
        '2026-10-16 12:00:00',
        799.00,
        'REFUNDED'
    );

INSERT INTO
    orders (
        order_id,
        user_id,
        order_date,
        order_status,
        transaction_id
    )
VALUES (
        1,
        2,
        '2026-10-15 10:00:00',
        'PAID',
        1
    ),
    (
        2,
        3,
        '2026-10-15 11:00:00',
        'PAID',
        2
    ),
    (
        3,
        2,
        '2026-10-16 09:00:00',
        'CANCELLED',
        3
    ),
    (
        4,
        3,
        '2026-10-16 12:00:00',
        'REFUNDED',
        4
    ),
    (
        5,
        3,
        '2026-10-17 08:00:00',
        'PENDING',
        NULL
    );

INSERT INTO
    order_items (
        order_item_id,
        order_id,
        game_id,
        price_paid
    )
VALUES (1, 1, 1, 1199.20),
    (2, 1, 2, 899.10),
    (3, 2, 4, 249.50),
    (4, 3, 5, 974.25),
    (5, 4, 3, 799.00),
    (6, 5, 6, 599.00);

INSERT INTO
    cart_items (
        cart_item_id,
        user_id,
        game_id
    )
VALUES (1, 2, 5),
    (2, 2, 3),
    (3, 3, 6),
    (4, 3, 7);

INSERT INTO
    wishlists (wishlist_id, user_id, game_id)
VALUES (1, 2, 4),
    (2, 2, 5),
    (3, 3, 1),
    (4, 3, 8);

INSERT INTO
    reviews (
        user_id,
        game_id,
        rating,
        review_text
    )
VALUES (
        2,
        1,
        4.5,
        'Enjoyed the exploration and character progression.'
    ),
    (
        2,
        2,
        4.0,
        'Fast races and fun tracks; a few more modes would help.'
    ),
    (
        3,
        4,
        5.0,
        'Creative puzzles and a satisfying difficulty curve.'
    );

-- Reconcile cached averages whether or not review triggers are installed.
-- Keeping this in the seed allows loading schema.sql + seed.sql independently.
UPDATE games AS g
LEFT JOIN (
    SELECT game_id, ROUND(AVG(rating), 2) AS calculated_average
    FROM reviews
    GROUP BY
        game_id
) AS r ON r.game_id = g.game_id
SET
    g.average_rating = COALESCE(r.calculated_average, 0.00);

COMMIT;