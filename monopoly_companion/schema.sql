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
  "starting_cash_balance" INTEGER NOT NULL,
  "go_value" INTEGER NOT NULL
);  

CREATE TABLE "property" (
  "property_id" INTEGER PRIMARY KEY,
  "game_version_id" INTEGER NOT NULL,
  "property_name" VARCHAR NOT NULL,
  "property_type" VARCHAR NOT NULL,
  "city" VARCHAR NOT NULL,
  "board_side" INTEGER NOT NULL,
  "color" VARCHAR,
  "house_cost" INTEGER,
  "price" INTEGER NOT NULL,
  "mortgage_value" INTEGER NOT NULL,
  "unmortgage_cost" INTEGER NOT NULL,
  "rent_basic" INTEGER,
  "rent_one_house" INTEGER,
  "rent_two_houses" INTEGER,
  "rent_three_houses" INTEGER,
  "rent_four_houses" INTEGER,
  "rent_hotel" INTEGER,
  "rent_multiplier_one_owned" INTEGER,
  "rent_multiplier_two_owned" INTEGER,
  "rent_two_owned" INTEGER,
  "rent_three_owned" INTEGER,
  "rent_four_owned" INTEGER,
  "rent_monopoly" INTEGER,
  FOREIGN KEY ("game_version_id") REFERENCES "game_version" ("game_version_id")
);

CREATE TABLE "action_type" (
  "action_type_id" INTEGER PRIMARY KEY,
  "action_type_name" VARCHAR NOT NULL,
  "exchange_type" VARCHAR 
);

CREATE TABLE "players" (
  "player_id" INTEGER PRIMARY KEY,
  "player_name" VARCHAR NOT NULL,
  "player_piece" VARCHAR,
  "player_order" INTEGER
);

CREATE TABLE "special_counter" (
  "special_counter_id" INTEGER PRIMARY KEY,
  "counter_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "turn" INTEGER NOT NULL,
  "player_id" INTEGER NOT NULL,
  "jail_counter" INTEGER,
  "free_parking_counter" INTEGER,
  "income_tax_counter" INTEGER,
  "luxury_tax_counter" INTEGER,
  "land_on_start_counter" INTEGER,
  "chance_counter" INTEGER,
  "community_chest_counter" INTEGER,
  FOREIGN KEY ("player_id") REFERENCES "players" ("player_id")
);

CREATE TABLE "property_ownership" (
  "property_id" INTEGER PRIMARY KEY,
  "owner_player_id" INTEGER NOT NULL,
  "mortgaged" boolean NOT NULL,
  "houses" INTEGER NOT NULL,
  "hotels" INTEGER NOT NULL,
  "number_owned" INTEGER NOT NULL,
  "max_number_owned" INTEGER NOT NULL,
  "monopoly" boolean AS (CASE WHEN "number_owned" = "max_number_owned" THEN TRUE ELSE FALSE END) STORED,
  FOREIGN KEY ("property_id") REFERENCES "property" ("property_id"),
  FOREIGN KEY ("owner_player_id") REFERENCES "players" ("player_id")
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
  "net_worth" INTEGER AS ("cash_balance" + "net_property_value" + "improvement_value") STORED,
  FOREIGN KEY ("player_id") REFERENCES "players" ("player_id")  
);

CREATE TABLE "net_worth_log" (
  "net_worth_log_id" INTEGER PRIMARY KEY,
  "net_worth_time" TIMESTAMP NOT NULL,
  "turn" INTEGER NOT NULL,
  "player_id" INTEGER NOT NULL,
  "cash_balance" INTEGER NOT NULL,
  "net_property_value" INTEGER NOT NULL,
  "improvement_value" INTEGER NOT NULL,
  "gross_property_value" INTEGER NOT NULL,
  "net_worth" INTEGER NOT NULL,
  FOREIGN KEY ("player_id") REFERENCES "players" ("player_id")  
);

CREATE TABLE "transactions" (
  "transaction_id" INTEGER PRIMARY KEY,
  "transaction_time" TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "turn" INTEGER NOT NULL,
  "party_player_id" INTEGER NOT NULL,
  "counterparty_player_id" INTEGER NOT NULL,
  "action_type_id" INTEGER NOT NULL,
  "property_id" INTEGER,
  "cash_received" INTEGER,
  "cash_paid" INTEGER,
  "asset_value_received" INTEGER,
  "asset_value_paid" INTEGER,
  FOREIGN KEY ("property_id") REFERENCES "property" ("property_id"),
  FOREIGN KEY ("action_type_id") REFERENCES "action_type" ("action_type_id"),
  FOREIGN KEY ("party_player_id") REFERENCES "players" ("player_id"),
  FOREIGN KEY ("counterparty_player_id") REFERENCES "players" ("player_id")
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