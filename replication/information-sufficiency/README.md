# Replication package of the information sufficiency article

Replication package of the article "Information sufficiency criteria for exactness under partial observation in the
AIMNER framework" by Necmi Talay, Hakan Acaroğlu, Aslıhan Günal and Fausto Pedro García Márquez. The folder holds
the same files as Supplementary Software 1 of the article, without its copy of netcalc.

- `replication_package/` holds the published data as used, the code of every step of the application and of the
  synthetic exercises, the log of the Stata run and the result files. Its README.md describes every file and the
  run order.
- `capability_checks/` holds the scripts that compute the numerical examples of Supplementary Section S11.

The networks are built with netcalc 2.0.0 at commit 6012f3f of this repository (branch `main`):

    net install netcalc, from("https://raw.githubusercontent.com/aggilitas/stata-networks/6012f3f6b2363e2881ab98a22ac420216ce869c6/")
