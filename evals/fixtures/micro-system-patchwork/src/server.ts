// MICRO-SYSTEM-PATCHWORK: the only thing the two features share is this file,
// and all it does is start two servers on two ports. There is no shared
// transport, no shared auth middleware, no shared logger, no shared config
// loader and no shared error shape. Adding a third feature means writing a
// third copy of all five.
import { startBilling } from "./billing/index.js";
import { startReports } from "./reports/index.js";

startBilling();
startReports();
