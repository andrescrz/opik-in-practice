# Alert history for INC-2291

alert: checkout-p99-latency-high
state: suppressed from 13:00 to 17:00
note: Muted by a maintenance-window rule created for the unrelated search reindex. The rule matched every service tagged tier=1, including payments-api. The p99 latency alert would have fired at 14:19 had it not been muted.

alert: checkout-error-rate-above-5pct
state: fired at 14:31
note: The first alert that reached a human. It was not muted, but its evaluation window is 5 minutes and it requires two consecutive breaches, so it fired 7 minutes after the error rate first crossed 5%.

alert: payments-db-connections-saturated
state: fired at 14:26, routed to the database team channel only
note: Fired at 14:26 but was routed to the database team's channel, which is not paged during business hours. The on-call engineer for payments never saw it.

alert: config-drift-detected
state: does not exist
note: No alert compares live pod configuration with the previous release. The pool size change was only found by manual inspection.
