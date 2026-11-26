# Context documents referenced during INC-2291

## Config release process
Config releases to payments-api are reviewed by one engineer and roll out to all pods at once. Unlike application releases, they have no canary stage and no automatic rollback on error rate.

## Config template change
The new config template introduced in cfg-2026.03.12-b replaced explicit values with per-pod defaults. The default for DB_POOL_MAX is 20, which suits small internal services. The review checked that the template rendered without errors, not the rendered values.

## Payments runbook
The checkout-errors runbook lists three steps: check recent application deploys, roll back the application image, scale out payments-api. It does not mention configuration releases or database pool sizing.

## Client retry behaviour
Mobile clients retry failed payment requests up to 5 times with no backoff or jitter. During the outage the retry volume peaked at 3.8 times normal traffic and slowed recovery.
