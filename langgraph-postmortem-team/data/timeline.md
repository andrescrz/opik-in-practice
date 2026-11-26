# Incident INC-2291 timeline: Tidewater checkout outage, 12 March (all times UTC)

14:02 Config release cfg-2026.03.12-b starts rolling out to payments-api. It is the first release built from the new config template.

14:09 Rollout reaches 100% of payments-api pods. Each pod now starts with DB_POOL_MAX=20 instead of the previous 200.

14:17 Checkout p99 latency climbs from 310 ms to 2.4 s. Customers begin seeing the "Payment pending" spinner.

14:24 Checkout error rate passes 8%. Client apps retry failed payments up to 5 times with no backoff, which multiplies load on payments-api.

14:31 First customer-facing page fires (checkout error rate above 5%). On-call engineer Ines Vaughn acknowledges.

14:48 Ines rolls back the application image to the previous version. Errors do not improve, which rules out the application code.

15:20 Ines and Tomas Brandt notice the pool size in the pod environment differs from the previous release. Rollback of the config release begins.

15:34 Config rollback complete, pool size back to 200. Latency recovers over the next six minutes.

15:41 Error rate back under 0.5%. Incident downgraded.

16:05 Incident closed. Total customer impact window: 14:17 to 15:41, 84 minutes.
