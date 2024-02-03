/* PostgreSQL schema of database
*/

DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS special_counter;
DROP TABLE IF EXISTS property_ownership;
DROP TABLE IF EXISTS net_worth;
DROP TABLE IF EXISTS transactions;

CREATE TABLE "game_version" (
  "game_version_id" INTEGER PRIMARY KEY,
  "game_version_name" VARCHAR NOT NULL,
  "game_version_language" VARCHAR NOT NULL,
  "total_cash" INTEGER NOT NULL,
  "starting_cash_balance" INTEGER NOT NULL
);  

CREATE TABLE "property" (
  "property_id" INTEGER PRIMARY KEY,
  "game_version_id" INTEGER NOT NULL,
  "property_name" VARCHAR NOT NULL,
  "property_type" VARCHAR NOT NULL,
  "city" VARCHAR NOT NULL,
  "board_side" INTEGER NOT NULL,
  "color" VARCHAR NOT NULL,
  "house_cost" INTEGER NOT NULL,
  "price" INTEGER NOT NULL,
  "mortgage_value" INTEGER NOT NULL,
  "unmortgage_cost" INTEGER NOT NULL,
  "rent_basic" INTEGER NOT NULL,
  "rent_one_house" INTEGER NOT NULL,
  "rent_one_houses" INTEGER NOT NULL,
  "rent_three_houses" INTEGER NOT NULL,
  "rent_four_houses" INTEGER NOT NULL,
  "rent_hotel" INTEGER NOT NULL,
  "rent_multiplier_one_owned" INTEGER NOT NULL,
  "rent_multiplier_two_owned" INTEGER NOT NULL,
  "rent_two_owned" INTEGER NOT NULL,
  "rent_three_owned" INTEGER NOT NULL,
  "rent_four_owned" INTEGER NOT NULL,
  FOREIGN KEY (game_version_id) REFERENCES game_version (game_version_id)
);

CREATE TABLE "action_type" (
  "action_type_id" INTEGER PRIMARY KEY,
  "action_type_name" VARCHAR NOT NULL,
  "exchange_type" VARCHAR NOT NULL
);

CREATE TABLE "players" (
  "player_id" INTEGER PRIMARY KEY,
  "player_name" VARCHAR NOT NULL,
  "player_piece" VARCHAR NOT NULL,
  "player_order" INTEGER NOT NULL
);

CREATE TABLE "special_counter" (
  "special_counter_id" INTEGER PRIMARY KEY,
  "counter_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "turn" INTEGER NOT NULL,
  "player_id" INTEGER NOT NULL,
  "jail_counter" INTEGER NOT NULL,
  "free_parking_counter" INTEGER NOT NULL,
  "income_tax_counter" INTEGER NOT NULL,
  "luxury_tax_counter" INTEGER NOT NULL,
  "land_on_start_counter" INTEGER NOT NULL,
  "chance_counter" INTEGER NOT NULL,
  "community_chest_counter" INTEGER NOT NULL,
  FOREIGN KEY (player_id) REFERENCES players (player_id)
);

CREATE TABLE "property_ownership" (
  "property_id" INTEGER PRIMARY KEY,
  "owner_player_id" INTEGER NOT NULL,
  "mortgaged" boolean,
  "houses" INTEGER NOT NULL,
  "hotels" INTEGER NOT NULL,
  "number_owned" INTEGER NOT NULL,
  FOREIGN KEY (property_id) REFERENCES property (property_id),
  FOREIGN KEY (owner_player_id) REFERENCES players (player_id)
);

CREATE TABLE "net_worth" (
  "net_worth_id" INTEGER PRIMARY KEY,
  "net_worth_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "turn" INTEGER NOT NULL,
  "player_id" INTEGER NOT NULL,
  "cash_balance" INTEGER NOT NULL,
  "net_property_value" INTEGER NOT NULL,
  "improvement_value" INTEGER NOT NULL,
  "gross_property_value" INTEGER NOT NULL,
  "net_worth" INTEGER NOT NULL,
  FOREIGN KEY (player_id) REFERENCES players (player_id)  
);

CREATE TABLE "transactions" (
  "transaction_id" INTEGER PRIMARY KEY,
  "transaction_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "turn" INTEGER NOT NULL,
  "party_player_id" INTEGER NOT NULL,
  "counterparty_player_id" INTEGER NOT NULL,
  "action_type_id" INTEGER NOT NULL,
  "property_id" INTEGER NOT NULL,
  "transaction_value" INTEGER NOT NULL,
  FOREIGN KEY (property_id) REFERENCES property (property_id),
  FOREIGN KEY (action_type_id) REFERENCES action_type (action_type_id),
  FOREIGN KEY (party_player_id) REFERENCES players (player_id),
  FOREIGN KEY (counterparty_player_id) REFERENCES players (player_id)

);

/*
These foreign keys should be reversed
ALTER TABLE "property" ADD FOREIGN KEY ("game_version_id") REFERENCES "game_version" ("game_version_id");

ALTER TABLE "transactions" ADD FOREIGN KEY ("property_id") REFERENCES "property" ("property_id");

ALTER TABLE "property" ADD FOREIGN KEY ("property_id") REFERENCES "property_ownership" ("property_id");

ALTER TABLE "transactions" ADD FOREIGN KEY ("action_type_id") REFERENCES "action_type" ("action_type_id");

ALTER TABLE "transactions" ADD FOREIGN KEY ("party_player_id") REFERENCES "players" ("player_id");

ALTER TABLE "transactions" ADD FOREIGN KEY ("counterparty_player_id") REFERENCES "players" ("player_id");

ALTER TABLE "property_ownership" ADD FOREIGN KEY ("owner_player_id") REFERENCES "players" ("player_id");

ALTER TABLE "net_worth" ADD FOREIGN KEY ("player_id") REFERENCES "players" ("player_id");

ALTER TABLE "special_counter" ADD FOREIGN KEY ("player_id") REFERENCES "players" ("player_id");
*/