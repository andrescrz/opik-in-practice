# Incident channel excerpts, #inc-2291

14:33 Ines Vaughn: Acknowledged the page. Checkout errors look like timeouts. Checking recent deploys, there was an app release this morning.

14:41 Tomas Brandt: The app release was 09:50, hours before. The config release is more recent, but config releases are normally boring.

14:48 Ines Vaughn: Rolling back the app image anyway, it is the quickest lever we have.

15:02 Ines Vaughn: Rollback finished and nothing changed. So it is not the code.

15:11 Priya Nair (database team): I have been seeing connection saturation alerts on payments-db since 14:26 in our channel. Did you get those?

15:12 Ines Vaughn: No, we did not get anything from the DB channel. Seeing them now.

15:18 Tomas Brandt: Pod env says DB_POOL_MAX=20. The previous release had 200. The new template has a per-pod default that nobody overrode.

15:20 Ines Vaughn: Starting the config rollback. We should have looked at config before the image, our runbook only lists application rollbacks.

15:44 Priya Nair: Saturation cleared. Pool usage is at 60 of 200 per pod at normal traffic.
