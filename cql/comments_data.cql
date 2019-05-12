INSERT INTO comments ("id", "author", "content", "date", "articleid") VALUES (uuid(), 'ari@test.com', 'hello world', toUnixTimestamp(now()), 56f90a7b-db3e-44f2-abd9-c0ed6c83d5db);
INSERT INTO comments ("id", "author", "content", "date", "articleid") VALUES (uuid(), 'ari@test.com', 'test', toUnixTimestamp(now()), 56f90a7b-db3e-44f2-abd9-c0ed6c83d5db);
INSERT INTO comments ("id", "author", "content", "date", "articleid") VALUES (uuid(), 'henrik@test.com', 'Lorem ipsum', toUnixTimestamp(now()), 56f90a7b-db3e-44f2-abd9-c0ed6c83d5db);
