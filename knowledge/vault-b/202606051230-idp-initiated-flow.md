# 202606051230 IdP-initiated vs SP-initiated flow

Both supported. IdP-initiated needs `RelayState` pointing at an allowlisted
path — otherwise it's an open-redirect risk.
